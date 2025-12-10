"""Punto de entrada principal del Agente AI"""
import asyncio
import signal
import sys
import structlog
from typing import Optional

from agent.core.config import get_settings
from agent.core.exceptions import SupabaseConnectionError, ConfigurationError
from agent.services.action_executor import ActionExecutor
from agent.services.ai_processor import AIProcessor
from agent.services.request_validator import RequestValidator
from agent.services.realtime_listener import RealtimeListener

# Configurar logging estructurado
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer() if sys.stdout.isatty() else structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(min_level="INFO"),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Variable global para el listener (para shutdown graceful)
realtime_listener: Optional[RealtimeListener] = None
action_executor: Optional[ActionExecutor] = None


def setup_signal_handlers():
    """Configura handlers para señales de shutdown graceful"""
    def signal_handler(signum, frame):
        logger.info("Señal de shutdown recibida", signal=signum)
        print("\n🛑 Señal de shutdown recibida. Cerrando conexiones...")
        
        # Cerrar recursos
        if action_executor:
            asyncio.create_task(action_executor.close())
        
        logger.info("Agente AI detenido")
        print("✅ Agente AI detenido correctamente")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Función principal del Agente AI"""
    global realtime_listener, action_executor
    
    try:
        # Cargar configuración
        logger.info("Iniciando Agente AI...")
        settings = get_settings()
        
        logger.info(
            "Configuración cargada",
            backend_url=settings.BACKEND_URL,
            gemini_model=settings.GEMINI_MODEL,
            supabase_url=settings.SUPABASE_URL
        )
        
        # Inicializar servicios
        logger.info("Inicializando servicios...")
        action_executor = ActionExecutor(settings)
        ai_processor = AIProcessor(settings)
        request_validator = RequestValidator(settings)
        realtime_listener = RealtimeListener(
            settings,
            action_executor,
            ai_processor,
            request_validator
        )
        
        logger.info("Servicios inicializados correctamente")
        
        # Configurar handlers de señales
        setup_signal_handlers()
        
        # Iniciar listener de Realtime
        logger.info("Iniciando suscripción a eventos Realtime...")
        subscription = await realtime_listener.subscribe_to_new_requests()
        
        if subscription:
            logger.info(
                "✅ Agente AI iniciado correctamente",
                listener_status="ACTIVO",
                supabase_realtime="CONECTADO",
                ready_to_process_requests=True
            )
            print("\n✅ Agente AI está ESCUCHANDO eventos de creación de solicitudes")
            print("   Esperando nuevas solicitudes en tabla HLP_PETICIONES...\n")
        else:
            logger.error("❌ No se pudo establecer suscripción a eventos Realtime")
            print("\n❌ ERROR: No se pudo establecer suscripción a eventos Realtime")
            raise SupabaseConnectionError(
                user_message="No se pudo establecer suscripción a eventos Realtime.",
                action_suggestion="Verifique la configuración de Supabase y que Realtime esté habilitado.",
                technical_detail="Subscription returned None"
            )
        
        # Mantener el proceso corriendo
        logger.info("Agente AI en ejecución. Esperando eventos...")
        while True:
            await asyncio.sleep(1)
    
    except ConfigurationError as e:
        logger.error("Error de configuración", error=str(e))
        print(f"\n❌ ERROR DE CONFIGURACIÓN: {str(e)}")
        print("   Por favor, verifique el archivo .env y las variables de entorno requeridas.")
        sys.exit(1)
    
    except SupabaseConnectionError as e:
        logger.error("Error de conexión con Supabase", error=str(e))
        print(f"\n❌ ERROR DE CONEXIÓN: {str(e)}")
        sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado recibida")
        print("\n🛑 Interrupción por teclado. Cerrando...")
        if action_executor:
            await action_executor.close()
        sys.exit(0)
    
    except Exception as e:
        logger.error("Error inesperado en main", error=str(e), exc_info=True)
        print(f"\n❌ ERROR INESPERADO: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Agente AI detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error("Error fatal en punto de entrada", error=str(e), exc_info=True)
        print(f"\n❌ ERROR FATAL: {str(e)}")
        sys.exit(1)

