"""Procesador de IA para clasificación de solicitudes usando Gemini AI"""
import asyncio
import json
import re
import structlog
from datetime import datetime
from typing import Optional, Literal, List, Tuple
import google.generativeai as genai
try:
    from google.generativeai.types import APIError, InvalidResponseError
except ImportError:
    # Fallback para versiones anteriores de la API
    APIError = Exception
    InvalidResponseError = Exception
from pydantic import BaseModel, Field, field_validator

from agent.core.config import Settings
from agent.core.exceptions import AIClassificationError, ValidationError
from agent.prompts.system_prompts import get_system_prompt

logger = structlog.get_logger(__name__)


class ClassificationResult(BaseModel):
    """Resultado de clasificación de solicitud por IA"""
    app_type: Literal["amerika", "dominio"] = Field(
        ...,
        description="Tipo de aplicación principal detectada"
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nivel de confianza (0.0-1.0)")
    detected_actions: List[str] = Field(..., min_length=1, description="Acciones detectadas para app_type principal")
    reasoning: str = Field(..., max_length=200, description="Explicación de la clasificación")
    extracted_params: dict = Field(default_factory=dict, description="Parámetros extraídos")
    
    # Campos para soportar múltiples aplicaciones
    requires_secondary_app: Optional[bool] = Field(
        False,
        description="True si el usuario también requiere acciones en la otra aplicación"
    )
    secondary_app_actions: Optional[List[str]] = Field(
        None,
        description="Acciones requeridas para la aplicación secundaria (si requires_secondary_app=True)"
    )
    
    raw_classification: str = Field(..., description="Respuesta original de Gemini para auditoría")
    classification_timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="Timestamp ISO8601"
    )
    
    @field_validator('detected_actions')
    @classmethod
    def validate_actions(cls, v):
        valid_actions = ["change_password", "unlock_account"]
        for action in v:
            if action not in valid_actions:
                raise ValueError(f"Acción no válida: {action}")
        return v
    
    @field_validator('secondary_app_actions')
    @classmethod
    def validate_secondary_actions(cls, v, info):
        if v is not None:
            requires_secondary = info.data.get('requires_secondary_app', False)
            if requires_secondary and not v:
                raise ValueError("secondary_app_actions no puede estar vacío si requires_secondary_app=True")
            valid_actions = ["change_password", "unlock_account"]
            for action in v:
                if action not in valid_actions:
                    raise ValueError(f"Acción secundaria no válida: {action}")
        return v


class AIProcessor:
    """Procesador de IA para clasificación de solicitudes usando Gemini AI"""
    
    def __init__(self, settings: Settings):
        """
        Inicializa el procesador de IA.
        
        Args:
            settings: Configuración del agente
        """
        self.settings = settings
        
        # Configurar Gemini AI
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        
        # Cargar System Prompts una vez al inicializar (reutilización)
        self.classification_prompt_base = get_system_prompt("classification_base")
        self.classification_prompt_with_examples = get_system_prompt("classification_with_examples")
        
        logger.info(
            "AIProcessor inicializado",
            model=settings.GEMINI_MODEL,
            temperature=settings.GEMINI_TEMPERATURE,
            max_tokens=settings.GEMINI_MAX_TOKENS
        )
    
    def _get_generation_config(self) -> dict:
        """Retorna configuración de generación optimizada para Gemini"""
        config = {
            "temperature": self.settings.GEMINI_TEMPERATURE,
            "max_output_tokens": self.settings.GEMINI_MAX_TOKENS,
            "top_p": 0.8,
        }
        
        # Gemini 2.5 Flash y 1.5 Pro+ soportan response_mime_type
        if self.settings.GEMINI_MODEL in ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-pro-latest"]:
            config["response_mime_type"] = "application/json"
        
        return config
    
    def _sanitize_user_input(self, description: str) -> str:
        """
        Sanitiza y optimiza la descripción del usuario.
        
        Args:
            description: Descripción original
        
        Returns:
            Descripción sanitizada y optimizada
        """
        # Limitar longitud si es muy larga (primeros 500 caracteres)
        if len(description) > 500:
            description = description[:500] + "..."
        
        # Eliminar espacios múltiples
        description = re.sub(r'\s+', ' ', description)
        
        # Eliminar espacios al inicio y final
        description = description.strip()
        
        return description
    
    def _should_use_few_shot_examples(self, description: str, codcategoria: int) -> bool:
        """
        Determina si se deben usar ejemplos few-shot basándose en la complejidad.
        
        Args:
            description: Descripción de la solicitud
            codcategoria: Categoría seleccionada
        
        Returns:
            True si usar few-shot, False para prompt base
        """
        # Si USE_FEW_SHOT_ALWAYS está habilitado, siempre usar few-shot
        if self.settings.USE_FEW_SHOT_ALWAYS:
            return True
        
        description_lower = description.lower()
        
        # Criterio 1: Descripción muy corta o ambigua (< 20 caracteres)
        if len(description) < self.settings.FEW_SHOT_THRESHOLD_DESCRIPTION_LENGTH:
            return True
        
        # Criterio 2: Palabras clave que sugieren múltiples aplicaciones
        multi_app_keywords = [
            "tanto", "como", "y también", "además", "ambas", "las dos",
            "amerika y dominio", "dominio y amerika", "ambos sistemas"
        ]
        if any(keyword in description_lower for keyword in multi_app_keywords):
            return True
        
        # Criterio 3: Discrepancia potencial (usuario menciona una aplicación pero categoría es otra)
        mentions_amerika = "amerika" in description_lower
        mentions_dominio = "dominio" in description_lower or "dominio corporativo" in description_lower
        
        if mentions_amerika and codcategoria == 300:
            return True
        if mentions_dominio and codcategoria == 400:
            return True
        
        # Criterio 4: Ambigüedad en la descripción
        ambiguity_keywords = [
            "no sé", "no estoy seguro", "creo que", "tal vez",
            "ayuda", "problema", "error", "no funciona"
        ]
        if any(keyword in description_lower for keyword in ambiguity_keywords):
            return True
        
        # Criterio 5: Descripción muy larga (> 500 caracteres) - puede ser compleja
        if len(description) > 500:
            return True
        
        return False
    
    def _build_classification_prompt(
        self,
        description: str,
        codcategoria: int
    ) -> Tuple[str, dict]:
        """
        Construye prompt optimizado para clasificación.
        
        Args:
            description: Descripción de la solicitud (ya sanitizada)
            codcategoria: Categoría seleccionada
        
        Returns:
            Tupla (system_prompt, user_message_dict)
        """
        # PASO 1: Determinar complejidad
        use_few_shot = self._should_use_few_shot_examples(description, codcategoria)
        
        # PASO 2: Seleccionar System Prompt apropiado
        if use_few_shot:
            system_prompt = self.classification_prompt_with_examples
            prompt_type = "with_examples"
        else:
            system_prompt = self.classification_prompt_base
            prompt_type = "base"
        
        # PASO 3: Mapear codcategoria a nombre de categoría
        category_names = {
            300: "Cambio de Contraseña Cuenta Dominio",
            400: "Cambio de Contraseña Amerika"
        }
        category_name = category_names.get(codcategoria, f"Categoría {codcategoria}")
        
        # Construir user message mínimo (solo contexto)
        user_message = f"Categoría: {codcategoria} ({category_name})\nDescripción: {description}"
        
        logger.debug(
            "📋 Prompt construido para Gemini",
            prompt_type=prompt_type,
            codcategoria=codcategoria,
            category_name=category_name,
            description_length=len(description),
            description_included=bool(description and description.strip()),
            user_message_preview=user_message[:400] + "..." if len(user_message) > 400 else user_message,
            user_message_full_length=len(user_message),
            description_in_message=description in user_message if description else False
        )
        
        return system_prompt, {"parts": [user_message]}
    
    def _parse_classification_response(self, response) -> dict:
        """
        Parsea y valida la respuesta de Gemini.
        
        Args:
            response: Respuesta de Gemini
        
        Returns:
            Dict con datos de clasificación parseados
        
        Raises:
            ValueError: Si la respuesta no es válida
        """
        try:
            # Intentar obtener texto de la respuesta
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text
            else:
                raise ValueError("No se pudo extraer texto de la respuesta de Gemini")
            
            # Intentar parsear como JSON
            try:
                classification_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Intentar extraer JSON del texto (por si Gemini agrega texto adicional)
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    classification_data = json.loads(json_match.group())
                else:
                    raise ValueError(f"No se pudo extraer JSON válido de la respuesta: {response_text[:200]}")
            
            # Validar estructura básica
            required_fields = ["app_type", "confidence", "detected_actions", "reasoning"]
            for field in required_fields:
                if field not in classification_data:
                    raise ValueError(f"Campo requerido faltante en respuesta: {field}")
            
            # Validar app_type
            if classification_data["app_type"] not in ["amerika", "dominio"]:
                raise ValueError(f"app_type inválido: {classification_data['app_type']}")
            
            # Validar confidence
            confidence = classification_data["confidence"]
            if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
                raise ValueError(f"confidence inválido: {confidence}")
            
            # Validar detected_actions
            if not isinstance(classification_data["detected_actions"], list) or not classification_data["detected_actions"]:
                raise ValueError("detected_actions debe ser una lista no vacía")
            
            # Truncar reasoning si excede 200 caracteres (límite del modelo Pydantic)
            reasoning = classification_data.get("reasoning", "")
            if len(reasoning) > 200:
                # Truncar de forma inteligente: buscar el último espacio antes del límite
                max_length = 197  # Dejar espacio para "..."
                truncated = reasoning[:max_length]
                # Buscar el último espacio para no cortar palabras
                last_space = truncated.rfind(' ')
                if last_space > 150:  # Solo usar el espacio si está razonablemente cerca del final
                    truncated = truncated[:last_space]
                classification_data["reasoning"] = truncated + "..."
                logger.warning(
                    "Reasoning truncado por exceder 200 caracteres",
                    original_length=len(reasoning),
                    truncated_length=len(classification_data["reasoning"]),
                    original_preview=reasoning[:100]
                )
            
            # Agregar raw_classification para auditoría
            classification_data["raw_classification"] = response_text
            
            return classification_data
            
        except Exception as e:
            logger.error("Error al parsear respuesta de Gemini", error=str(e), exc_info=True)
            raise ValueError(f"Error al parsear respuesta: {str(e)}")
    
    def _get_fallback_classification(
        self,
        codcategoria: int,
        ususolicita: str
    ) -> ClassificationResult:
        """
        Retorna clasificación de fallback basada en categoría.
        
        Args:
            codcategoria: Categoría seleccionada
            ususolicita: Usuario que solicita
        
        Returns:
            ClassificationResult con valores por defecto seguros
        
        Raises:
            ValidationError: Si codcategoria no es 300 ni 400
        """
        # Validar codcategoria primero
        if codcategoria not in [300, 400]:
            raise ValidationError(
                f"codcategoria {codcategoria} no es válida para procesamiento automático. "
                "Debe ser 300 (dominio) o 400 (amerika)."
            )
        
        # Mapear categoría a app_type
        app_type = "dominio" if codcategoria == 300 else "amerika"
        
        logger.warning(
            "Usando clasificación de fallback",
            codcategoria=codcategoria,
            app_type=app_type,
            ususolicita=ususolicita
        )
        
        return ClassificationResult(
            app_type=app_type,
            confidence=0.5,  # Bajo, indica clasificación automática
            detected_actions=["change_password"],  # Acción más común y segura
            reasoning="Clasificación automática por fallo en procesamiento de IA",
            extracted_params={},
            requires_secondary_app=False,
            secondary_app_actions=None,
            raw_classification="FALLBACK - Clasificación automática basada en categoría"
        )
    
    async def classify_request(
        self,
        description: str,
        codcategoria: int,
        ususolicita: str
    ) -> ClassificationResult:
        """
        Clasifica una solicitud usando Gemini AI.
        
        Args:
            description: Descripción de la solicitud
            codcategoria: Categoría seleccionada
            ususolicita: Usuario que solicita
        
        Returns:
            ClassificationResult validado
        
        Raises:
            AIClassificationError: Si la clasificación falla definitivamente
        """
        start_time = datetime.utcnow()
        
        # VALIDACIÓN CRÍTICA: Verificar que la descripción no esté vacía
        if not description or not description.strip():
            logger.error(
                "❌ Descripción vacía recibida en AIProcessor",
                codcategoria=codcategoria,
                ususolicita=ususolicita,
                description_received=description
            )
            raise ValueError("La descripción de la solicitud no puede estar vacía")
        
        sanitized_desc = self._sanitize_user_input(description)
        
        logger.info(
            "🔍 Iniciando clasificación con Gemini",
            codcategoria=codcategoria,
            ususolicita=ususolicita,
            description_original=description,
            description_original_length=len(description),
            description_sanitized=sanitized_desc,
            description_sanitized_length=len(sanitized_desc),
            description_preview=sanitized_desc[:200] + "..." if len(sanitized_desc) > 200 else sanitized_desc
        )
        
        try:
            # Construir prompt optimizado
            system_prompt, user_message = self._build_classification_prompt(sanitized_desc, codcategoria)
            
            # Llamar a Gemini AI
            generation_config = self._get_generation_config()
            
            # Construir modelo con system_instruction
            model = genai.GenerativeModel(
                model_name=self.settings.GEMINI_MODEL,
                system_instruction=system_prompt
            )
            
            # LOGGING: Prompt completo que se envía a Gemini
            user_message_text = user_message["parts"][0] if user_message.get("parts") else "N/A"
            logger.info(
                "🚀 Enviando request a Gemini API",
                codcategoria=codcategoria,
                ususolicita=ususolicita,
                model=self.settings.GEMINI_MODEL,
                system_prompt_preview=system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt,
                system_prompt_length=len(system_prompt),
                user_message_full=user_message_text,
                user_message_length=len(user_message_text),
                generation_config=generation_config
            )
            
            # Usar generate_content_async sin system_instruction (ya está en el modelo)
            response = await model.generate_content_async(
                user_message_text,
                generation_config=generation_config
            )
            
            # LOGGING: Después de recibir respuesta de Gemini
            logger.debug(
                "✅ Respuesta recibida de Gemini",
                codcategoria=codcategoria,
                response_has_text=hasattr(response, 'text'),
                response_has_candidates=hasattr(response, 'candidates')
            )
            
            # Parsear y validar respuesta
            classification_data = self._parse_classification_response(response)
            
            # Crear ClassificationResult validado
            result = ClassificationResult(**classification_data)
            
            elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                "Clasificación exitosa",
                app_type=result.app_type,
                confidence=result.confidence,
                detected_actions=result.detected_actions,
                elapsed_seconds=elapsed_time,
                ususolicita=ususolicita
            )
            
            return result
            
        except APIError as e:
            error_code = getattr(e, 'code', None)
            
            # Rate limit: Reintentar una vez
            if error_code == 429 or "rate limit" in str(e).lower():
                logger.warning("Rate limit de Gemini, reintentando...", attempt=1)
                await asyncio.sleep(5)  # Esperar 5 segundos
                try:
                    # Reintentar una vez
                    system_prompt, user_message = self._build_classification_prompt(sanitized_desc, codcategoria)
                    user_message_text = user_message["parts"][0] if user_message.get("parts") else ""
                    
                    # Construir modelo con system_instruction
                    model = genai.GenerativeModel(
                        model_name=self.settings.GEMINI_MODEL,
                        system_instruction=system_prompt
                    )
                    
                    logger.info(
                        "🔄 Reintentando request a Gemini API después de rate limit",
                        user_message_full=user_message_text
                    )
                    
                    response = await model.generate_content_async(
                        user_message_text,
                        generation_config=self._get_generation_config()
                    )
                    classification_data = self._parse_classification_response(response)
                    return ClassificationResult(**classification_data)
                except Exception:
                    logger.error("Reintento falló, usando fallback", error=str(e))
                    return self._get_fallback_classification(codcategoria, ususolicita)
            
            # Quota excedida: No reintentar, usar fallback
            elif "quota" in str(e).lower():
                logger.error("Quota de Gemini excedida, usando fallback", error=str(e))
                return self._get_fallback_classification(codcategoria, ususolicita)
            
            # Otros errores de API
            else:
                logger.error("Error de API de Gemini", error_code=error_code, error=str(e))
                return self._get_fallback_classification(codcategoria, ususolicita)
        
        except (ValueError, KeyError) as e:
            # Error al parsear JSON o estructura inválida
            logger.error("Error al parsear respuesta de Gemini", error=str(e))
            # Usar fallback directamente (no reintentar con prompt explícito por ahora)
            return self._get_fallback_classification(codcategoria, ususolicita)
        
        except TimeoutError as e:
            logger.error("Timeout en llamada a Gemini", timeout=30.0, error=str(e))
            return self._get_fallback_classification(codcategoria, ususolicita)
        
        except ConnectionError as e:
            logger.error("Error de conexión con Gemini API", error=str(e))
            return self._get_fallback_classification(codcategoria, ususolicita)
        
        except Exception as e:
            logger.error("Error inesperado en clasificación", error=str(e), exc_info=True)
            return self._get_fallback_classification(codcategoria, ususolicita)
    
    def validate_category(
        self,
        codcategoria: int,
        app_type: Literal["amerika", "dominio"]
    ) -> Tuple[bool, Optional[int]]:
        """
        Valida que la categoría coincida con el app_type detectado.
        
        Args:
            codcategoria: Categoría seleccionada por el usuario
            app_type: Tipo de aplicación detectado por la IA
        
        Returns:
            Tupla (is_valid, corrected_codcategoria)
        """
        # Mapeo de categorías
        category_mapping = {
            300: "dominio",
            400: "amerika"
        }
        
        expected_app_type = category_mapping.get(codcategoria)
        
        if expected_app_type == app_type:
            return True, None
        
        # Hay discrepancia, calcular categoría corregida
        corrected_codcategoria = 300 if app_type == "dominio" else 400
        
        logger.warning(
            "Categoría no coincide con app_type detectado",
            codcategoria=codcategoria,
            app_type=app_type,
            corrected_codcategoria=corrected_codcategoria
        )
        
        return False, corrected_codcategoria
    
    def extract_parameters(
        self,
        description: str,
        app_type: Literal["amerika", "dominio"],
        ususolicita: str,
        classification_result: Optional[ClassificationResult] = None
    ) -> dict:
        """
        Extrae parámetros necesarios para ejecutar acciones.
        
        Args:
            description: Descripción de la solicitud
            app_type: Tipo de aplicación
            ususolicita: Usuario que solicita
            classification_result: Resultado de clasificación (opcional)
        
        Returns:
            Dict con parámetros extraídos
        """
        params = {
            "user_id": ususolicita
        }
        
        if app_type == "dominio":
            # Prioridad: extracted_params.user_name > ususolicita
            user_name = None
            
            if classification_result and classification_result.extracted_params:
                user_name = classification_result.extracted_params.get("user_name")
            
            # Validar formato de user_name extraído
            if user_name and user_name.strip():
                user_name = user_name.strip()
                # Validar formato: alfanumérico + guiones bajos, 1-25 caracteres
                if re.match(r'^[a-zA-Z0-9_]{1,25}$', user_name):
                    params["user_name"] = user_name
                else:
                    # Formato inválido, usar ususolicita
                    params["user_name"] = ususolicita.strip()
            else:
                # Intentar extraer de la descripción (procesamiento básico)
                # Buscar patrones como "usuario: xyz" o "nombre: xyz"
                user_name_match = re.search(
                    r'(?:usuario|nombre|user|username)[\s:]+([a-zA-Z0-9_]{1,25})',
                    description,
                    re.IGNORECASE
                )
                if user_name_match:
                    extracted = user_name_match.group(1)
                    if re.match(r'^[a-zA-Z0-9_]{1,25}$', extracted):
                        params["user_name"] = extracted
                    else:
                        params["user_name"] = ususolicita.strip()
                else:
                    # Usar ususolicita como fallback
                    params["user_name"] = ususolicita.strip()
        
        return params
    
    def validate_classification_for_execution(
        self,
        classification_result: ClassificationResult,
        ususolicita: str,
        app_type: str
    ) -> Tuple[bool, List[str], dict]:
        """
        Valida que la clasificación de IA tenga todos los datos necesarios
        antes de ejecutar acciones en el backend.
        
        CRÍTICO: Este método debe ejecutarse ANTES de cualquier intento
        de ejecutar acciones. Si falla, NO se deben ejecutar acciones.
        
        Args:
            classification_result: Resultado de clasificación de IA
            ususolicita: Usuario que solicita
            app_type: Tipo de aplicación esperado
        
        Returns:
            Tupla (is_valid, errors, execution_params)
        """
        errors = []
        execution_params = {}
        
        # Validar app_type
        if classification_result.app_type != app_type:
            errors.append(
                f"app_type no coincide: esperado '{app_type}', "
                f"recibido '{classification_result.app_type}'"
            )
            return False, errors, {}
        
        # Validar detected_actions
        if not classification_result.detected_actions:
            errors.append("detected_actions no puede estar vacío")
            return False, errors, {}
        
        valid_ai_actions = ["change_password", "unlock_account"]
        for action in classification_result.detected_actions:
            if action not in valid_ai_actions:
                errors.append(f"Acción no válida en detected_actions: {action}")
        
        # Validar user_id (ususolicita)
        if not ususolicita or not ususolicita.strip():
            errors.append("ususolicita es requerido y no puede estar vacío")
        elif len(ususolicita) > 25:
            errors.append("ususolicita no puede exceder 25 caracteres")
        
        # Validaciones específicas por app_type
        if app_type == "amerika":
            # Mapear acciones: change_password → generate_password
            action_mapping = {
                "change_password": "generate_password",
                "unlock_account": "unlock_account"
            }
            mapped_actions = []
            for ai_action in classification_result.detected_actions:
                if ai_action in action_mapping:
                    mapped_actions.append(action_mapping[ai_action])
                else:
                    errors.append(f"No se puede mapear acción para Amerika: {ai_action}")
            
            if not errors:
                execution_params = {
                    "mapped_actions": mapped_actions,
                    "user_id": ususolicita.strip()
                }
        
        elif app_type == "dominio":
            # Validar user_name (CRÍTICO)
            extracted_params = classification_result.extracted_params or {}
            user_name = extracted_params.get("user_name")
            
            # Prioridad: extracted_params.user_name > ususolicita
            if not user_name or not user_name.strip():
                user_name = ususolicita.strip()
            
            # Validar formato de user_name
            if not re.match(r'^[a-zA-Z0-9_]{1,25}$', user_name):
                errors.append(
                    f"user_name tiene formato inválido: '{user_name}'. "
                    f"Debe ser alfanumérico con guiones bajos, máximo 25 caracteres"
                )
            
            if not errors:
                execution_params = {
                    "mapped_actions": classification_result.detected_actions,  # Sin mapeo
                    "user_id": ususolicita.strip(),
                    "user_name": user_name
                }
        
        # Validar aplicación secundaria (si aplica)
        if classification_result.requires_secondary_app:
            if not classification_result.secondary_app_actions:
                errors.append("secondary_app_actions no puede estar vacío si requires_secondary_app=True")
            else:
                # Validar acciones secundarias
                for action in classification_result.secondary_app_actions:
                    if action not in valid_ai_actions:
                        errors.append(f"Acción secundaria no válida: {action}")
                
                # Determinar aplicación secundaria
                secondary_app = "dominio" if app_type == "amerika" else "amerika"
                
                # Si aplicación secundaria es dominio, validar user_name
                if secondary_app == "dominio":
                    # Usar mismo user_name de aplicación principal
                    if "user_name" not in execution_params:
                        errors.append("user_name es requerido para aplicación secundaria (dominio)")
                    else:
                        # Mapear acciones secundarias si es Amerika
                        if app_type == "amerika":
                            action_mapping = {
                                "change_password": "generate_password",
                                "unlock_account": "unlock_account"
                            }
                            mapped_secondary_actions = [
                                action_mapping.get(action, action)
                                for action in classification_result.secondary_app_actions
                            ]
                        else:
                            mapped_secondary_actions = classification_result.secondary_app_actions
                        
                        execution_params.update({
                            "requires_secondary_app": True,
                            "secondary_app": secondary_app,
                            "secondary_app_actions": mapped_secondary_actions
                        })
                else:
                    # Aplicación secundaria es Amerika, mapear acciones
                    action_mapping = {
                        "change_password": "generate_password",
                        "unlock_account": "unlock_account"
                    }
                    mapped_secondary_actions = [
                        action_mapping.get(action, action)
                        for action in classification_result.secondary_app_actions
                    ]
                    
                    execution_params.update({
                        "requires_secondary_app": True,
                        "secondary_app": secondary_app,
                        "secondary_app_actions": mapped_secondary_actions
                    })
        
        # Validar confidence (warning, no error)
        if classification_result.confidence < 0.5:
            logger.warning(
                "Confidence muy bajo en clasificación",
                confidence=classification_result.confidence,
                app_type=app_type,
                detected_actions=classification_result.detected_actions
            )
        
        is_valid = len(errors) == 0
        return is_valid, errors, execution_params

