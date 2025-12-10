"""Listener de Realtime para procesar nuevas solicitudes automáticamente"""
import asyncio
import structlog
from datetime import datetime
from typing import Optional, Dict, List, Any
from supabase import create_async_client, AsyncClient
from realtime import AsyncRealtimeChannel

from agent.core.config import Settings
from agent.core.exceptions import (
    ValidationError,
    RateLimitExceededError,
    AIClassificationError,
    ActionExecutionError,
    SupabaseConnectionError
)
from agent.services.action_executor import ActionExecutor
from agent.services.ai_processor import AIProcessor, ClassificationResult
from agent.services.request_validator import RequestValidator

logger = structlog.get_logger(__name__)


def create_empty_ai_classification_data() -> Dict[str, Any]:
    """Crea estructura vacía de AI_CLASSIFICATION_DATA"""
    return {
        "app_type": None,
        "confidence": None,
        "detected_actions": None,
        "reasoning": None,
        "extracted_params": None,
        "requires_secondary_app": None,
        "secondary_app_actions": None,
        "original_codcategoria": None,
        "corrected_codcategoria": None,
        "category_corrected": None,
        "raw_classification": None,
        "classification_timestamp": None,
        "processing_status": None,
        "current_step": None,
        "progress_percentage": None,
        "last_update": None,
        "actions_executed": None,
        "completed_at": None,
        "fallback_used": None,
        "error_details": None,
        "ignored": None,
        "ignore_reason": None,
        "requires_human_review": None,
        "auto_processing_skipped": None,
        "ignored_at": None
    }


def update_ai_classification_data(
    current: Dict[str, Any],
    updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Actualiza AI_CLASSIFICATION_DATA preservando valores existentes"""
    result = current.copy()
    for key, value in updates.items():
        if value is not None or key not in result:
            result[key] = value
    return result


class RealtimeListener:
    """Listener de Realtime para procesar nuevas solicitudes automáticamente"""
    
    def __init__(
        self,
        settings: Settings,
        action_executor: ActionExecutor,
        ai_processor: AIProcessor,
        request_validator: RequestValidator
    ):
        """
        Inicializa el listener de Realtime.
        
        Args:
            settings: Configuración del agente
            action_executor: Ejecutor de acciones
            ai_processor: Procesador de IA
            request_validator: Validador de solicitudes
        """
        self.settings = settings
        self.action_executor = action_executor
        self.ai_processor = ai_processor
        self.request_validator = request_validator
        
        # Crear cliente asíncrono de Supabase (requerido para Realtime)
        self.supabase: Optional[AsyncClient] = None
        self._supabase_url = settings.SUPABASE_URL
        self._supabase_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
        # La verificación de conexión se hará de forma asíncrona en subscribe_to_new_requests
        
        logger.info(
            "RealtimeListener inicializado",
            supabase_url=settings.SUPABASE_URL,
            table="HLP_PETICIONES",
            service_role_configured=bool(settings.SUPABASE_SERVICE_ROLE_KEY)
        )
    
    async def _verify_connection(self):
        """Verifica conexión a Supabase"""
        try:
            if not self.supabase:
                self.supabase = await create_async_client(
                    self._supabase_url,
                    self._supabase_key
                )
            
            result = await self.supabase.table("HLP_PETICIONES")\
                .select("CODPETICIONES", count="exact")\
                .limit(1)\
                .execute()
            
            logger.info(
                "Conexión a Supabase establecida exitosamente",
                supabase_url=self.settings.SUPABASE_URL,
                table="HLP_PETICIONES"
            )
        except Exception as e:
            logger.error("Error al verificar conexión a Supabase", error=str(e))
            raise SupabaseConnectionError(
                user_message="No se pudo conectar con la base de datos.",
                action_suggestion="Verifique la configuración de Supabase.",
                technical_detail=str(e)
            )
    
    async def subscribe_to_new_requests(self) -> AsyncRealtimeChannel:
        """
        Suscribe a eventos INSERT en HLP_PETICIONES.
        
        Returns:
            Canal de Realtime suscrito
        """
        try:
            # Crear cliente asíncrono si no existe
            if not self.supabase:
                self.supabase = await create_async_client(
                    self._supabase_url,
                    self._supabase_key
                )
                await self._verify_connection()
            
            logger.info(
                "Preparando suscripción a eventos Realtime",
                table="HLP_PETICIONES",
                event_type="INSERT",
                filter_state="CODESTADO = 1 (PENDIENTE)",
                supabase_realtime_enabled=True
            )
            
            logger.info(
                "Iniciando suscripción a eventos Realtime de Supabase",
                table="HLP_PETICIONES",
                event_type="INSERT",
                filter_condition="CODESTADO = 1 (PENDIENTE)"
            )
            
            # Crear canal de Realtime
            channel = self.supabase.channel("agent-ai-requests")
            
            # Wrapper síncrono para manejar el callback asíncrono
            def sync_callback(payload: Dict[str, Any]):
                """Wrapper síncrono que programa la ejecución asíncrona"""
                # Crear tarea asíncrona para ejecutar el handler
                asyncio.create_task(self._handle_new_request(payload))
            
            # Suscribirse a eventos INSERT
            # En Supabase Python async, usar on_postgres_changes con parámetros nombrados
            channel.on_postgres_changes(
                event="INSERT",
                schema="public",
                table="HLP_PETICIONES",
                filter="CODESTADO=eq.1",  # Solo solicitudes PENDIENTES
                callback=sync_callback
            )
            
            # Suscribir canal
            await channel.subscribe()
            
            logger.info(
                "✅ Suscripción a eventos Realtime establecida exitosamente",
                table="HLP_PETICIONES",
                event_type="INSERT",
                subscription_active=True,
                message="El agente está escuchando nuevos eventos de creación de solicitudes"
            )
            
            # Log de consola para validación temprana
            print("\n" + "="*70)
            print("🔔 AGENTE AI - LISTENER ACTIVO")
            print("="*70)
            print(f"📊 Tabla: HLP_PETICIONES")
            print(f"📥 Evento: INSERT")
            print(f"🔍 Filtro: CODESTADO = 1 (PENDIENTE)")
            print(f"✅ Estado: ESCUCHANDO eventos de creación de solicitudes")
            print("="*70 + "\n")
            
            return channel
            
        except Exception as e:
            logger.error(
                "❌ Error al crear suscripción Realtime",
                table="HLP_PETICIONES",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            
            print("\n" + "="*70)
            print("❌ ERROR: No se pudo establecer suscripción a eventos Realtime")
            print(f"   Error: {str(e)}")
            print("="*70 + "\n")
            
            # Reintentar con backoff exponencial
            await self._retry_subscription()
            raise
    
    async def _retry_subscription(self, max_retries: int = 5, initial_delay: float = 5.0):
        """Reintenta suscripción con backoff exponencial"""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                await asyncio.sleep(delay)
                subscription = await self.subscribe_to_new_requests()
                logger.info("Reconexión exitosa", attempt=attempt + 1)
                return subscription
            except Exception as e:
                logger.warning("Reintento de suscripción falló", attempt=attempt + 1, error=str(e))
                delay *= 2  # Backoff exponencial
                if attempt == max_retries - 1:
                    logger.error("No se pudo establecer suscripción después de todos los reintentos")
                    raise
    
    async def _handle_new_request(self, payload: Dict[str, Any]):
        """
        Maneja nuevo evento de solicitud.
        
        Args:
            payload: Payload del evento Realtime
        """
        event_timestamp = datetime.utcnow().isoformat()
        
        # Log del payload completo para debugging
        logger.info(
            "🔍 Payload completo recibido",
            payload_type=type(payload).__name__,
            payload_keys=list(payload.keys()) if isinstance(payload, dict) else "N/A",
            payload_str=str(payload)[:500] if payload else "Empty",
            has_new_attr=hasattr(payload, 'new') if not isinstance(payload, dict) else False,
            has_new_key="new" in payload if isinstance(payload, dict) else False,
            has_record_attr=hasattr(payload, 'record') if not isinstance(payload, dict) else False,
            has_data_attr=hasattr(payload, 'data') if not isinstance(payload, dict) else False
        )
        
        # Si payload es un objeto, inspeccionar sus atributos
        if not isinstance(payload, dict) and hasattr(payload, '__dict__'):
            logger.info(
                "🔍 Payload es un objeto, inspeccionando atributos",
                payload_attrs=list(payload.__dict__.keys()) if hasattr(payload, '__dict__') else [],
                payload_dir=[x for x in dir(payload) if not x.startswith('_')][:20]
            )
        
        # Inspeccionar payload['data'] si existe
        if isinstance(payload, dict) and "data" in payload:
            data = payload.get("data", {})
            logger.info(
                "🔍 Inspeccionando payload['data']",
                data_type=type(data).__name__,
                data_keys=list(data.keys()) if isinstance(data, dict) else "N/A",
                data_str=str(data)[:1000] if data else "Empty",
                has_record="record" in data if isinstance(data, dict) else False,
                has_new="new" in data if isinstance(data, dict) else False,
                has_old="old" in data if isinstance(data, dict) else False
            )
            
            # Si data es un objeto, inspeccionar sus atributos
            if not isinstance(data, dict) and hasattr(data, '__dict__'):
                logger.info(
                    "🔍 payload['data'] es un objeto, inspeccionando atributos",
                    data_attrs=list(data.__dict__.keys()) if hasattr(data, '__dict__') else [],
                    data_dir=[x for x in dir(data) if not x.startswith('_')][:20]
                )
        
        # Intentar diferentes estructuras de payload
        request_data = {}
        
        # Estructura 1: payload.new (objeto con atributo)
        if hasattr(payload, 'new'):
            try:
                new_data = payload.new
                if isinstance(new_data, dict):
                    request_data = new_data
                elif hasattr(new_data, '__dict__'):
                    request_data = new_data.__dict__
                logger.info("📦 Datos extraídos usando payload.new", extracted_keys=list(request_data.keys()))
            except Exception as e:
                logger.warning("Error al extraer payload.new", error=str(e))
        
        # Estructura 1b: payload.record (objeto con atributo record)
        if not request_data and hasattr(payload, 'record'):
            try:
                record_data = payload.record
                if isinstance(record_data, dict):
                    request_data = record_data
                elif hasattr(record_data, '__dict__'):
                    request_data = record_data.__dict__
                logger.info("📦 Datos extraídos usando payload.record", extracted_keys=list(request_data.keys()))
            except Exception as e:
                logger.warning("Error al extraer payload.record", error=str(e))
        
        # Estructura 2: payload["new"] (diccionario)
        if not request_data and isinstance(payload, dict):
            if "new" in payload:
                new_data = payload.get("new")
                if isinstance(new_data, dict):
                    request_data = new_data
                elif hasattr(new_data, '__dict__'):
                    request_data = new_data.__dict__
                logger.info("📦 Datos extraídos usando payload['new']", extracted_keys=list(request_data.keys()))
        
        # Estructura 3: payload["data"]["record"] o payload["data"]["new"] (Supabase Realtime Python)
        if not request_data and isinstance(payload, dict) and "data" in payload:
            data = payload.get("data", {})
            if isinstance(data, dict):
                # Intentar data["record"]
                if "record" in data:
                    record = data.get("record")
                    if isinstance(record, dict):
                        request_data = record
                        logger.info("📦 Datos extraídos usando payload['data']['record']", extracted_keys=list(request_data.keys()))
                # Intentar data["new"]
                elif "new" in data:
                    new_data = data.get("new")
                    if isinstance(new_data, dict):
                        request_data = new_data
                        logger.info("📦 Datos extraídos usando payload['data']['new']", extracted_keys=list(request_data.keys()))
                # Intentar data directamente si tiene campos de la tabla
                elif any(key in data for key in ["CODPETICIONES", "CODCATEGORIA", "DESCRIPTION", "USUSOLICITA"]):
                    request_data = data
                    logger.info("📦 Datos extraídos usando payload['data'] directamente", extracted_keys=list(request_data.keys()))
        
        # Estructura 4: payload puede ser directamente los datos
        if not request_data and isinstance(payload, dict):
            if any(key in payload for key in ["CODPETICIONES", "CODCATEGORIA", "DESCRIPTION", "USUSOLICITA"]):
                request_data = payload
                logger.info("📦 Datos extraídos del payload directamente", extracted_keys=list(request_data.keys()))
        
        # Log de los datos extraídos
        logger.info(
            "📦 Datos extraídos del payload",
            request_data_keys=list(request_data.keys()) if request_data else [],
            request_data_sample=dict(list(request_data.items())[:5]) if request_data and len(request_data) > 0 else {},
            request_data_empty=len(request_data) == 0,
            description_present="DESCRIPTION" in request_data if request_data else False,
            description_value=request_data.get("DESCRIPTION") if request_data else None,
            description_length=len(request_data.get("DESCRIPTION", "")) if request_data else 0,
            description_preview=request_data.get("DESCRIPTION", "")[:200] if request_data and request_data.get("DESCRIPTION") else "VACÍA O NO PRESENTE"
        )
        
        codpeticiones = request_data.get("CODPETICIONES") if request_data else None
        
        # LOG INMEDIATO - Validación de que el evento fue recibido
        logger.info(
            "🎯 EVENTO RECIBIDO - Nueva solicitud detectada",
            codpeticiones=codpeticiones,
            event_timestamp=event_timestamp,
            table="HLP_PETICIONES",
            event_type="INSERT",
            payload_keys=list(request_data.keys()) if request_data else [],
            ususolicita=request_data.get("USUSOLICITA") if request_data else None,
            codcategoria=request_data.get("CODCATEGORIA") if request_data else None,
            codestado=request_data.get("CODESTADO") if request_data else None
        )
        
        # Log de consola para validación rápida
        print(f"\n[EVENTO RECIBIDO] Solicitud #{codpeticiones} detectada a las {event_timestamp}")
        if request_data:
            print(f"   Usuario: {request_data.get('USUSOLICITA', 'N/A')}")
            print(f"   Categoría: {request_data.get('CODCATEGORIA', 'N/A')}")
            print(f"   Estado: {request_data.get('CODESTADO', 'N/A')} (PENDIENTE)")
        else:
            print(f"   ⚠️  ADVERTENCIA: No se pudieron extraer datos del payload")
            print(f"   Payload recibido: {str(payload)[:200]}")
        print()
        
        try:
            # Validar que tenga campos requeridos
            if not request_data or not self._validate_request_payload(request_data):
                logger.warning(
                    "Payload de solicitud inválido",
                    payload=request_data,
                    original_payload_type=type(payload).__name__,
                    original_payload_keys=list(payload.keys()) if isinstance(payload, dict) else "N/A",
                    original_payload_str=str(payload)[:500] if payload else "Empty"
                )
                return
            
            # Procesar solicitud
            await self.process_new_request(request_data)
            
        except Exception as e:
            logger.error(
                "Error al procesar nueva solicitud",
                codpeticiones=codpeticiones,
                error=str(e),
                exc_info=True
            )
            # NO lanzar excepción para no detener el listener
            await self._handle_processing_error(request_data, e)
    
    def _validate_request_payload(self, request_data: Dict[str, Any]) -> bool:
        """Valida que el payload tenga campos requeridos"""
        required_fields = ["CODPETICIONES", "CODCATEGORIA", "DESCRIPTION", "USUSOLICITA", "CODESTADO"]
        return all(field in request_data for field in required_fields)
    
    async def _handle_processing_error(self, request_data: Dict[str, Any], error: Exception):
        """Maneja errores durante el procesamiento"""
        codpeticiones = request_data.get("CODPETICIONES")
        try:
            await self.update_request(
                codpeticiones,
                {
                    "CODESTADO": 3,  # SOLUCIONADO
                    "SOLUCION": "Ocurrió un error inesperado al procesar tu solicitud. Nuestro equipo ha sido notificado.",
                    "CODUSOLUCION": "AGENTE-MS",
                    "FESOLUCION": datetime.utcnow().isoformat(),
                    "AI_CLASSIFICATION_DATA": update_ai_classification_data(
                        create_empty_ai_classification_data(),
                        {
                            "processing_status": "error",
                            "current_step": "Error durante el procesamiento",
                            "progress_percentage": 0,
                            "last_update": datetime.utcnow().isoformat(),
                            "error_details": {
                                "error_type": "processing_error",
                                "user_message": "Ocurrió un error inesperado al procesar tu solicitud.",
                                "action_suggestion": "Tu solicitud será reintentada automáticamente. Si el problema persiste, contacta al soporte.",
                                "technical_detail": str(error)
                            }
                        }
                    )
                }
            )
        except Exception as update_error:
            logger.error(
                "Error al actualizar solicitud con error de procesamiento",
                codpeticiones=codpeticiones,
                error=str(update_error)
            )
    
    async def process_new_request(self, request_data: Dict[str, Any]):
        """
        Procesa una nueva solicitud detectada por Realtime.
        
        Args:
            request_data: Datos de la solicitud del evento
        """
        codpeticiones = request_data.get("CODPETICIONES")
        codcategoria = request_data.get("CODCATEGORIA")
        description = request_data.get("DESCRIPTION", "")
        ususolicita = request_data.get("USUSOLICITA")
        codestado = request_data.get("CODESTADO")
        fesolicita_str = request_data.get("FESOLICITA")
        
        # LOGGING: Descripción extraída de solicitud
        logger.info(
            "📝 Descripción extraída de solicitud",
            codpeticiones=codpeticiones,
            description_raw=description,
            description_length=len(description) if description else 0,
            description_empty=not description or not description.strip(),
            all_keys_in_request_data=list(request_data.keys())
        )
        
        # Validación temprana: Verificar que la descripción no esté vacía
        if not description or not description.strip():
            logger.error(
                "❌ Descripción vacía detectada",
                codpeticiones=codpeticiones,
                codcategoria=codcategoria,
                ususolicita=ususolicita,
                request_data_sample=dict(list(request_data.items())[:10])
            )
            await self._update_request_with_rejection(
                codpeticiones,
                "La descripción de la solicitud no puede estar vacía. Por favor, proporciona detalles sobre tu solicitud."
            )
            return
        
        # Parsear fecha de solicitud
        try:
            if fesolicita_str:
                if isinstance(fesolicita_str, str):
                    fesolicita = datetime.fromisoformat(fesolicita_str.replace("Z", "+00:00"))
                else:
                    fesolicita = fesolicita_str
            else:
                fesolicita = datetime.utcnow()
        except Exception:
            fesolicita = datetime.utcnow()
        
        try:
            # Paso 1: Validación inicial
            is_valid, errors = self.request_validator.validate_request_data(request_data)
            if not is_valid:
                logger.warning("Solicitud rechazada por validación", codpeticiones=codpeticiones, errors=errors)
                await self._update_request_with_rejection(
                    codpeticiones,
                    "Los datos de la solicitud no son válidos. " + "; ".join(errors)
                )
                return
            
            # Sanitizar descripción
            description_before_sanitize = description
            try:
                description = self.request_validator.sanitize_description(description)
                logger.info(
                    "🧹 Descripción sanitizada",
                    codpeticiones=codpeticiones,
                    description_before=description_before_sanitize,
                    description_after=description,
                    length_before=len(description_before_sanitize) if description_before_sanitize else 0,
                    length_after=len(description) if description else 0
                )
            except ValidationError as e:
                await self._update_request_with_rejection(
                    codpeticiones,
                    self.request_validator.generate_rejection_message("invalid_description")
                )
                return
            
            # Validar categoría
            is_valid_category, category_error = await self.request_validator.validate_category(codcategoria)
            if not is_valid_category:
                await self._update_request_with_rejection(
                    codpeticiones,
                    self.request_validator.generate_rejection_message("invalid_category")
                )
                return
            
            # Validar usuario
            is_valid_user, user_error = self.request_validator.validate_user(ususolicita)
            if not is_valid_user:
                await self._update_request_with_rejection(
                    codpeticiones,
                    f"Usuario inválido: {user_error}"
                )
                return
            
            # Paso 2: Validación de seguridad (CRÍTICO - antes de enviar a IA)
            is_safe, risk_level, detected_patterns = self.request_validator.validate_security(description)
            if not is_safe and risk_level in ["HIGH", "CRITICAL"]:
                logger.warning(
                    "Solicitud rechazada por seguridad",
                    codpeticiones=codpeticiones,
                    risk_level=risk_level,
                    detected_patterns=detected_patterns
                )
                rejection_message = self.request_validator.generate_security_rejection_message(
                    risk_level,
                    detected_patterns
                )
                await self._update_request_with_rejection(codpeticiones, rejection_message, security_rejection=True)
                return
            
            # Paso 3: Validación de rate limiting
            within_limit, current_count, limit, window_hours = await self.request_validator.check_rate_limit(
                ususolicita,
                codcategoria
            )
            if not within_limit:
                rate_limit_info = await self.request_validator.get_rate_limit_info(ususolicita)
                rejection_message = self.request_validator.generate_rejection_message(
                    "rate_limit_exceeded",
                    rate_limit_info
                )
                await self._update_request_with_rejection(codpeticiones, rejection_message)
                return
            
            # Paso 4: Validación de edad de solicitud
            is_valid_age, age_reason = self.request_validator.validate_request_age(fesolicita)
            if not is_valid_age:
                await self._update_request_with_rejection(
                    codpeticiones,
                    self.request_validator.generate_rejection_message("request_too_old")
                )
                return
            
            # Paso 5: Actualizar estado a TRAMITE con feedback inicial
            ai_data = update_ai_classification_data(
                create_empty_ai_classification_data(),
                {
                    "original_codcategoria": codcategoria,
                    "corrected_codcategoria": None,
                    "category_corrected": False,
                    "processing_status": "validated",
                    "current_step": "Clasificando solicitud con inteligencia artificial...",
                    "progress_percentage": 10,
                    "last_update": datetime.utcnow().isoformat()
                }
            )
            
            await self.update_request(
                codpeticiones,
                {
                    "CODESTADO": 2,  # TRAMITE
                    "SOLUCION": "Su solicitud está siendo procesada. El sistema está analizando su solicitud...",
                    "AI_CLASSIFICATION_DATA": ai_data
                }
            )
            
            # Paso 6: Orquestar procesamiento completo
            await self._orchestrate_processing(
                codpeticiones,
                codcategoria,
                description,
                ususolicita,
                ai_data
            )
            
        except ValidationError as e:
            logger.warning("Solicitud rechazada por validación", codpeticiones=codpeticiones, error=str(e))
            await self._update_request_with_rejection(codpeticiones, str(e))
            return
        
        except RateLimitExceededError as e:
            logger.warning("Solicitud rechazada por rate limit", codpeticiones=codpeticiones, user=ususolicita)
            await self._update_request_with_rejection(codpeticiones, e.user_message)
            return
        
        except Exception as e:
            logger.error(
                "Error inesperado al procesar solicitud",
                codpeticiones=codpeticiones,
                error=str(e),
                exc_info=True
            )
            await self._update_request_with_error(
                codpeticiones,
                "Ocurrió un error inesperado al procesar tu solicitud. Nuestro equipo ha sido notificado.",
                "Tu solicitud será reintentada automáticamente. Si el problema persiste, contacta al soporte."
            )
            return
    
    async def _orchestrate_processing(
        self,
        codpeticiones: int,
        codcategoria: int,
        description: str,
        ususolicita: str,
        ai_data: Dict[str, Any]
    ):
        """Orquesta el procesamiento completo de la solicitud"""
        # Paso 7.1: Clasificación con IA
        await self.update_request_progress(
            codpeticiones,
            "classifying",
            "Analizando su solicitud con inteligencia artificial para determinar el tipo de aplicación y acciones necesarias...",
            30,
            ai_data
        )
        
        # LOGGING: Enviando solicitud a Gemini para clasificación
        logger.info(
            "🤖 Enviando solicitud a Gemini para clasificación",
            codpeticiones=codpeticiones,
            codcategoria=codcategoria,
            ususolicita=ususolicita,
            description_to_send=description,
            description_length=len(description) if description else 0,
            description_valid=bool(description and description.strip())
        )
        
        # Validación antes de enviar
        if not description or not description.strip():
            logger.error(
                "❌ Descripción vacía antes de enviar a Gemini",
                codpeticiones=codpeticiones
            )
            raise ValueError("La descripción no puede estar vacía para clasificación")
        
        try:
            classification_result = await self.ai_processor.classify_request(
                description,
                codcategoria,
                ususolicita
            )
        except Exception as e:
            logger.error("Error en clasificación, usando fallback", codpeticiones=codpeticiones, error=str(e))
            classification_result = self.ai_processor._get_fallback_classification(codcategoria, ususolicita)
            ai_data = update_ai_classification_data(ai_data, {"fallback_used": True})
        
        # Actualizar AI_CLASSIFICATION_DATA con resultados de clasificación
        ai_data = update_ai_classification_data(
            ai_data,
            {
                "app_type": classification_result.app_type,
                "confidence": classification_result.confidence,
                "detected_actions": classification_result.detected_actions,
                "reasoning": classification_result.reasoning,
                "extracted_params": classification_result.extracted_params,
                "requires_secondary_app": classification_result.requires_secondary_app,
                "secondary_app_actions": classification_result.secondary_app_actions,
                "raw_classification": classification_result.raw_classification,
                "classification_timestamp": classification_result.classification_timestamp
            }
        )
        
        # Paso 7.1.5: Detección y corrección de categoría
        is_valid_category, corrected_codcategoria = self.ai_processor.validate_category(
            codcategoria,
            classification_result.app_type
        )
        
        if not is_valid_category and corrected_codcategoria:
            # Actualizar categoría en Supabase
            await self.update_request(codpeticiones, {"CODCATEGORIA": corrected_codcategoria})
            ai_data = update_ai_classification_data(
                ai_data,
                {
                    "corrected_codcategoria": corrected_codcategoria,
                    "category_corrected": True
                }
            )
            codcategoria = corrected_codcategoria  # Usar categoría corregida para siguientes pasos
            logger.info(
                "Categoría corregida automáticamente",
                codpeticiones=codpeticiones,
                original_codcategoria=ai_data.get("original_codcategoria"),
                corrected_codcategoria=corrected_codcategoria,
                app_type_detected=classification_result.app_type
            )
        
        # Paso 7.1.5.1: Validación de categoría para procesamiento automático
        if codcategoria not in [300, 400]:
            # Ignorar solicitud - no procesar automáticamente
            ai_data = update_ai_classification_data(
                ai_data,
                {
                    "ignored": True,
                    "ignore_reason": "Categoría no soportada para procesamiento automático",
                    "requires_human_review": True,
                    "auto_processing_skipped": True,
                    "ignored_at": datetime.utcnow().isoformat(),
                    "processing_status": "ignored",
                    "current_step": "Solicitud clasificada pero requiere atención humana",
                    "progress_percentage": 100,
                    "last_update": datetime.utcnow().isoformat()
                }
            )
            await self.update_request(codpeticiones, {"AI_CLASSIFICATION_DATA": ai_data})
            logger.info(
                "Solicitud ignorada por categoría no válida",
                codpeticiones=codpeticiones,
                codcategoria=codcategoria
            )
            return
        
        # Paso 7.1.6: Validación de Requisitos de Respuesta de IA (CRÍTICO)
        app_type = classification_result.app_type
        is_valid, errors, execution_params = self.ai_processor.validate_classification_for_execution(
            classification_result,
            ususolicita,
            app_type
        )
        
        if not is_valid:
            logger.error(
                "Validación de requisitos de clasificación falló",
                codpeticiones=codpeticiones,
                app_type=app_type,
                errors=errors
            )
            ai_data = update_ai_classification_data(
                ai_data,
                {
                    "validation_failed": True,
                    "validation_errors": errors,
                    "validation_timestamp": datetime.utcnow().isoformat(),
                    "processing_status": "validation_failed",
                    "current_step": "Validación de requisitos falló",
                    "progress_percentage": 45,
                    "error_details": {
                        "error_type": "classification_validation_failed",
                        "user_message": "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación.",
                        "action_suggestion": "Por favor, contacte al soporte para asistencia."
                    }
                }
            )
            await self.update_request(
                codpeticiones,
                {
                    "CODESTADO": 3,  # SOLUCIONADO
                    "SOLUCION": "No se pudo procesar su solicitud debido a datos incompletos o inválidos en la clasificación. Por favor, contacte al soporte.",
                    "CODUSOLUCION": "AGENTE-MS",
                    "FESOLUCION": datetime.utcnow().isoformat(),
                    "AI_CLASSIFICATION_DATA": ai_data
                }
            )
            return
        
        # Paso 7.2: Validación y Extracción
        await self.update_request_progress(
            codpeticiones,
            "validating",
            "Validando información y preparando acciones necesarias...",
            50,
            ai_data
        )
        
        # Paso 7.3: Ejecución de Acciones
        await self._execute_actions(
            codpeticiones,
            app_type,
            execution_params,
            classification_result,
            ai_data
        )
    
    async def _execute_actions(
        self,
        codpeticiones: int,
        app_type: str,
        execution_params: Dict[str, Any],
        classification_result: ClassificationResult,
        ai_data: Dict[str, Any]
    ):
        """Ejecuta las acciones detectadas"""
        actions_executed = []
        
        # Determinar aplicaciones a procesar
        requires_secondary = execution_params.get("requires_secondary_app", False)
        
        # Procesar aplicación principal
        primary_actions = execution_params.get("mapped_actions", execution_params.get("primary_actions", []))
        await self._execute_app_actions(
            codpeticiones,
            app_type,
            primary_actions,
            execution_params,
            actions_executed,
            ai_data,
            is_primary=True
        )
        
        # Procesar aplicación secundaria si aplica
        if requires_secondary:
            secondary_app = execution_params.get("secondary_app")
            secondary_actions = execution_params.get("secondary_app_actions", [])
            await self._execute_app_actions(
                codpeticiones,
                secondary_app,
                secondary_actions,
                execution_params,
                actions_executed,
                ai_data,
                is_primary=False
            )
        
        # Paso 7.4: Finalización
        ai_data = update_ai_classification_data(
            ai_data,
            {
                "actions_executed": actions_executed,
                "processing_status": "completed",
                "progress_percentage": 100,
                "completed_at": datetime.utcnow().isoformat(),
                "last_update": datetime.utcnow().isoformat()
            }
        )
        
        # Generar mensaje final
        solucion_text = self._generate_final_solution_message(
            app_type,
            execution_params,
            actions_executed,
            classification_result
        )
        
        await self.update_request(
            codpeticiones,
            {
                "CODESTADO": 3,  # SOLUCIONADO
                "SOLUCION": solucion_text,
                "CODUSOLUCION": "AGENTE-MS",
                "FESOLUCION": datetime.utcnow().isoformat(),
                "FECCIERRE": datetime.utcnow().isoformat(),
                "CODMOTCIERRE": 5,  # Respuesta Final
                "AI_CLASSIFICATION_DATA": ai_data
            }
        )
    
    async def _execute_app_actions(
        self,
        codpeticiones: int,
        app_type: str,
        actions: List[str],
        execution_params: Dict[str, Any],
        actions_executed: List[Dict[str, Any]],
        ai_data: Dict[str, Any],
        is_primary: bool
    ):
        """Ejecuta acciones para una aplicación específica"""
        user_id = execution_params.get("user_id")
        
        # Para Dominio: SIEMPRE ejecutar find_user PRIMERO
        if app_type == "dominio":
            user_name = execution_params.get("user_name")
            await self.update_request_progress(
                codpeticiones,
                "executing_actions",
                "Buscando información del usuario en el sistema...",
                70,
                ai_data
            )
            
            try:
                print(f"🔌 Invocando API: /api/apps/dominio/execute-action | Acción: find_user | Usuario: {user_id} | Nombre: {user_name}")
                result = await self.action_executor.execute_dominio_action(
                    user_id,
                    "find_user",
                    user_name
                )
                
                actions_executed.append({
                    "app_type": "primary" if is_primary else "secondary",
                    "action_type": "find_user",
                    "endpoint": "/api/apps/dominio/execute-action",
                    "success": result.get("success", False),
                    "result": result.get("result", {}),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                if not result.get("result", {}).get("found", False):
                    # Usuario no encontrado
                    solucion_text = "No se encontró el usuario especificado en el sistema. Por favor, verifique el nombre de usuario o contacte al soporte para aclaración."
                    ai_data = update_ai_classification_data(
                        ai_data,
                        {
                            "actions_executed": actions_executed,
                            "error_details": {
                                "error_type": "user_not_found",
                                "user_message": solucion_text,
                                "action_suggestion": "Verifique que el nombre de usuario sea correcto o contacte al soporte para asistencia."
                            }
                        }
                    )
                    await self.update_request(
                        codpeticiones,
                        {
                            "CODESTADO": 3,
                            "SOLUCION": solucion_text,
                            "CODUSOLUCION": "AGENTE-MS",
                            "FESOLUCION": datetime.utcnow().isoformat(),
                            "AI_CLASSIFICATION_DATA": ai_data
                        }
                    )
                    return
                
            except ActionExecutionError as e:
                actions_executed.append({
                    "app_type": "primary" if is_primary else "secondary",
                    "action_type": "find_user",
                    "endpoint": "/api/apps/dominio/execute-action",
                    "success": False,
                    "result": {"error": e.user_message},
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Continuar con acciones siguientes aunque find_user falle (depende de la lógica de negocio)
        
        # Ejecutar acciones restantes
        for idx, action in enumerate(actions):
            if app_type == "dominio" and action == "find_user":
                continue  # Ya se ejecutó
            
            progress = 70 + int((idx + 1) / len(actions) * 20)
            action_message = self._get_action_message(app_type, action)
            await self.update_request_progress(
                codpeticiones,
                "executing_actions",
                action_message,
                progress,
                ai_data
            )
            
            try:
                endpoint = f"/api/apps/{app_type}/execute-action"
                if app_type == "amerika":
                    print(f"🔌 Invocando API: {endpoint} | Acción: {action} | Usuario: {user_id}")
                    result = await self.action_executor.execute_amerika_action(user_id, action)
                else:  # dominio
                    user_name = execution_params.get("user_name")
                    print(f"🔌 Invocando API: {endpoint} | Acción: {action} | Usuario: {user_id} | Nombre: {user_name}")
                    result = await self.action_executor.execute_dominio_action(user_id, action, user_name)
                
                actions_executed.append({
                    "app_type": "primary" if is_primary else "secondary",
                    "action_type": action,
                    "endpoint": endpoint,
                    "success": result.get("success", False),
                    "result": result.get("result", {}),
                    "generated_password": result.get("generated_password"),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            except ActionExecutionError as e:
                endpoint = f"/api/apps/{app_type}/execute-action"
                actions_executed.append({
                    "app_type": "primary" if is_primary else "secondary",
                    "action_type": action,
                    "endpoint": endpoint,
                    "success": False,
                    "result": {"error": e.user_message, "action_suggestion": e.action_suggestion},
                    "timestamp": datetime.utcnow().isoformat()
                })
                # Continuar con siguiente acción
    
    def _get_action_message(self, app_type: str, action: str) -> str:
        """Retorna mensaje descriptivo para una acción"""
        if action == "generate_password" or action == "change_password":
            return "Generando nueva contraseña para su cuenta..."
        elif action == "unlock_account":
            return "Desbloqueando su cuenta..."
        elif action == "find_user":
            return "Buscando información del usuario en el sistema..."
        else:
            return f"Ejecutando acción: {action}..."
    
    def _generate_final_solution_message(
        self,
        app_type: str,
        execution_params: Dict[str, Any],
        actions_executed: List[Dict[str, Any]],
        classification_result: ClassificationResult
    ) -> str:
        """Genera mensaje final de solución"""
        requires_secondary = execution_params.get("requires_secondary_app", False)
        
        if requires_secondary:
            # Múltiples aplicaciones
            primary_app_name = "AMERIKA" if app_type == "amerika" else "DOMINIO"
            secondary_app = execution_params.get("secondary_app")
            secondary_app_name = "AMERIKA" if secondary_app == "amerika" else "DOMINIO"
            
            primary_messages = []
            secondary_messages = []
            
            for action in actions_executed:
                if action.get("app_type") == "primary":
                    msg = self._format_action_result(action, app_type)
                    if msg:
                        primary_messages.append(msg)
                else:
                    msg = self._format_action_result(action, secondary_app)
                    if msg:
                        secondary_messages.append(msg)
            
            solution = f"Se procesaron sus solicitudes en ambas aplicaciones:\n\n"
            if primary_messages:
                solution += f"**{primary_app_name}**:\n" + "\n".join(primary_messages) + "\n\n"
            if secondary_messages:
                solution += f"**{secondary_app_name}**:\n" + "\n".join(secondary_messages)
            
            return solution
        else:
            # Una sola aplicación
            messages = []
            for action in actions_executed:
                msg = self._format_action_result(action, app_type)
                if msg:
                    messages.append(msg)
            
            return "\n".join(messages) if messages else "Su solicitud ha sido procesada exitosamente."
    
    def _format_action_result(self, action: Dict[str, Any], app_type: str) -> str:
        """Formatea resultado de una acción para el mensaje final"""
        if not action.get("success"):
            return None
        
        action_type = action.get("action_type")
        result = action.get("result", {})
        
        if action_type in ["generate_password", "change_password"]:
            # Buscar contraseña primero en el nivel superior de action, luego en result
            password = action.get("generated_password") or result.get("generated_password") or result.get("password")
            if password:
                app_name = "Amerika" if app_type == "amerika" else "Dominio"
                return f"Se ha generado una nueva contraseña para su cuenta de {app_name}. Su nueva contraseña es: {password}. Por favor, guárdela en un lugar seguro y cámbiela después de iniciar sesión."
            else:
                return f"Se ha generado una nueva contraseña para su cuenta de {app_type}."
        
        elif action_type == "unlock_account":
            app_name = "Amerika" if app_type == "amerika" else "Dominio"
            return f"Su cuenta de {app_name} ha sido desbloqueada exitosamente. Ya puede iniciar sesión normalmente."
        
        return None
    
    async def update_request(self, codpeticiones: int, updates: Dict[str, Any]):
        """Actualiza una solicitud en Supabase"""
        try:
            if not self.supabase:
                self.supabase = await create_async_client(
                    self._supabase_url,
                    self._supabase_key
                )
            
            result = await self.supabase.table("HLP_PETICIONES")\
                .update(updates)\
                .eq("CODPETICIONES", codpeticiones)\
                .execute()
            return result
        except Exception as e:
            logger.error(
                "Error al actualizar solicitud en Supabase",
                codpeticiones=codpeticiones,
                error=str(e)
            )
            raise
    
    async def update_request_progress(
        self,
        codpeticiones: int,
        status: str,
        message: str,
        progress: int,
        ai_data: Dict[str, Any]
    ):
        """Actualiza progreso de procesamiento"""
        ai_data = update_ai_classification_data(
            ai_data,
            {
                "processing_status": status,
                "current_step": message,
                "progress_percentage": progress,
                "last_update": datetime.utcnow().isoformat()
            }
        )
        
        await self.update_request(
            codpeticiones,
            {
                "SOLUCION": message,
                "AI_CLASSIFICATION_DATA": ai_data
            }
        )
    
    async def _update_request_with_rejection(
        self,
        codpeticiones: int,
        message: str,
        security_rejection: bool = False
    ):
        """Actualiza solicitud con mensaje de rechazo"""
        ai_data = update_ai_classification_data(
            create_empty_ai_classification_data(),
            {
                "processing_status": "rejected",
                "current_step": message,
                "progress_percentage": 0,
                "last_update": datetime.utcnow().isoformat(),
                "error_details": {
                    "error_type": "rejection",
                    "user_message": message,
                    "security_rejection": security_rejection
                }
            }
        )
        
        await self.update_request(
            codpeticiones,
            {
                "CODESTADO": 3,  # SOLUCIONADO
                "SOLUCION": message,
                "CODUSOLUCION": "AGENTE-MS",
                "FESOLUCION": datetime.utcnow().isoformat(),
                "AI_CLASSIFICATION_DATA": ai_data
            }
        )
    
    async def _update_request_with_error(
        self,
        codpeticiones: int,
        user_message: str,
        action_suggestion: Optional[str] = None
    ):
        """Actualiza solicitud con mensaje de error"""
        ai_data = update_ai_classification_data(
            create_empty_ai_classification_data(),
            {
                "processing_status": "error",
                "current_step": "Error durante el procesamiento",
                "progress_percentage": 0,
                "last_update": datetime.utcnow().isoformat(),
                "error_details": {
                    "error_type": "processing_error",
                    "user_message": user_message,
                    "action_suggestion": action_suggestion
                }
            }
        )
        
        await self.update_request(
            codpeticiones,
            {
                "CODESTADO": 3,  # SOLUCIONADO
                "SOLUCION": user_message + (f" {action_suggestion}" if action_suggestion else ""),
                "CODUSOLUCION": "AGENTE-MS",
                "FESOLUCION": datetime.utcnow().isoformat(),
                "AI_CLASSIFICATION_DATA": ai_data
            }
        )

