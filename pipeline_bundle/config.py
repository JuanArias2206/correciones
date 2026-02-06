# -*- coding: utf-8 -*-
"""
CONFIGURACIÓN DEL PIPELINE
==========================
Este módulo contiene la configuración general del pipeline:
- API keys
- Rutas de archivos
- Mapas de hojas Excel
- Configuraciones de vías de exposición
"""

import os

# =========================================================
# DIRECTORIO BASE
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================================================
# CONFIGURACIÓN DE DEEPSEEK (ÚNICO PROVEEDOR LLM)
# =========================================================
# API key hardcodeada para primera corrida
DEEPSEEK_API_KEY = 'sk-90b9c21e412447b188162cab53fad814'
DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

# Tiempo de espera entre llamadas al LLM (segundos)
LLM_DELAY_SECONDS = int(os.getenv('LLM_DELAY_SECONDS', '5'))

# Tamaño del lote para clasificación con LLM
LLM_BATCH_SIZE = int(os.getenv('LLM_BATCH_SIZE', '10'))

# Timeout de llamadas al LLM (segundos)
LLM_TIMEOUT_SECONDS = int(os.getenv('LLM_TIMEOUT_SECONDS', '60'))

# Presupuesto dinámico de caracteres para batching (evita batches demasiado grandes)
# Aproximadamente 6k-12k caracteres por batch
LLM_BATCH_BUDGET_CHARS = int(os.getenv('LLM_BATCH_BUDGET_CHARS', '8000'))

# Versión del prompt (para invalidar caché automáticamente)
PROMPT_VERSION = os.getenv('PROMPT_VERSION', 'v2.0_compact')

# Ruta de caché SQLite persistente
CACHE_DB_PATH = os.path.join(BASE_DIR, 'cache', 'classifications_cache.db')

# Habilitadores de optimización
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
ENABLE_DETERMINISTIC = os.getenv('ENABLE_DETERMINISTIC', 'true').lower() == 'true'
ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'

# Temperatura para LLM (reducida para mayor consistencia)
LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE', '0.0'))

# =========================================================
# CONFIGURACIÓN DE PRUEBAS (PRIMER CORRIDA)
# =========================================================
# Porcentaje de registros a procesar (0-100)
# CAMBIAR ESTE VALOR PARA PRUEBAS: 20 = 20%, 100 = 100%
TEST_PERCENTAGE = int(os.getenv('TEST_PERCENTAGE', '20'))

# Habilitar modo de prueba (logs detallados, conteos)
TEST_MODE = os.getenv('TEST_MODE', 'true').lower() == 'true'

# =========================================================
# SISTEMA DE LOGGING Y MONITOREO
# =========================================================
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Crear directorio de logs si no existe
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Archivo de log principal
LOG_FILE = os.path.join(LOGS_DIR, f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

# Configurar logger
logger = logging.getLogger('SPA_Pipeline')
logger.setLevel(logging.DEBUG)

# Handler para archivo (rotante: máx 10MB, máx 5 backups)
file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Formato de logs
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(log_format)
console_handler.setFormatter(log_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# =========================================================
# CONTADORES GLOBALES (PARA MONITOREO)
# =========================================================
class PipelineMetrics:
    """Clase para trackear métricas del pipeline"""
    def __init__(self):
        self.total_records = 0
        self.processed_records = 0
        self.skipped_records = 0  # Pre-filtro
        self.deterministic_classified = 0  # Deterministic
        self.cache_hits = 0  # Cache
        self.llm_calls = 0  # LLM
        self.errors = 0
        self.false_positive_corrections = 0
        self.start_time = None
        self.error_log = []  # Lista de errores detallados
        
    def log_error(self, error_type, details, product_name=""):
        """Registra error con detalles"""
        self.errors += 1
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'product': product_name,
            'details': details
        }
        self.error_log.append(error_entry)
        logger.error(f"[{error_type}] {product_name}: {details}")
    
    def print_summary(self):
        """Imprime resumen de métricas"""
        summary = f"""
╔═════════════════════════════════════════════════════════════════╗
║                    PIPELINE EXECUTION SUMMARY                   ║
╚═════════════════════════════════════════════════════════════════╝

PROCESAMIENTO:
  • Total registros leídos:        {self.total_records}
  • Registros procesados:          {self.processed_records}
  • Registros saltados (pre-filter): {self.skipped_records}
  
CLASIFICACIÓN:
  • Clasificados (deterministic):  {self.deterministic_classified}
  • Cache hits:                     {self.cache_hits}
  • Llamadas LLM:                   {self.llm_calls}
  
ERRORES Y AJUSTES:
  • Errores encontrados:            {self.errors}
  • Falsos positivos corregidos:    {self.false_positive_corrections}
  
AHORRO ESPERADO:
  • % LLM evitados:                 {100 - (self.llm_calls / max(1, self.processed_records) * 100):.1f}%
  • Costo estimado LLM:             ${self.llm_calls * 0.03 / 1000:.2f} USD (est.)

═══════════════════════════════════════════════════════════════════
"""
        logger.info(summary)
        print(summary)
        
        if self.errors > 0:
            print("\nDETALLE DE ERRORES:")
            print("─" * 65)
            for error in self.error_log[:10]:  # Primeros 10 errores
                print(f"⚠️  [{error['type']}] {error['product']}")
                print(f"   → {error['details']}")
                print(f"   @ {error['timestamp']}")
            if len(self.error_log) > 10:
                print(f"\n... y {len(self.error_log) - 10} errores más")

# Instancia global de métricas
METRICS = PipelineMetrics()

# =========================================================
# RUTAS DE ARCHIVOS DE ENTRADA
# =========================================================
file_sheets_map = {
    os.path.join(BASE_DIR, 'data', 'wetransfer_sivigila_2025-07-24_1807', '356_365_2022.xlsx'): {
        '356_2022': 'NA',
        '365_2022': 'NA'
    },
    os.path.join(BASE_DIR, 'data', 'wetransfer_sivigila_2025-07-24_1807', '356_365_2023.xlsx'): {
        '356_2023': 'NA',
        '365_2023': 'NA'
    }
}

# =========================================================
# RUTAS DE SALIDA
# =========================================================
OUTPUT_DIR = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo')

# =========================================================
# MAPAS DE VÍAS DE EXPOSICIÓN
# =========================================================
VIA_EXP_MAP = {
    1: "respiratoria", 
    2: "oral", 
    3: "dermica_mucosas", 
    4: "ocular",
    5: "desconocida", 
    6: "parenteral", 
    8: "transplacentaria"
}

VIA_EXPOSI_MAP = {
    1: "respiratoria", 
    2: "oral", 
    3: "dermica_mucosas", 
    4: "ocular",
    5: "desconocida", 
    6: "parenteral", 
    7: "transplacentaria"
}

# =========================================================
# TÉRMINOS A FILTRAR (van directamente a "otros")
# =========================================================
TERMINOS_A_FILTRAR = {
    'sin nombre', 'sin dato', 'sin informacion', 'desconocido', 'desconocida',
    'desconocidos', 'desconocidas', 'no sabe', 'no recuerda'
}

# =========================================================
# CATEGORÍAS VÁLIDAS PARA CLASIFICACIÓN
# =========================================================
CATEGORIAS_VALIDAS = [
    'alucinogenos', 
    'cocaina_y_derivados', 
    'opioides', 
    'estimulantes',
    'inhalantes', 
    'tranquilizantes_y_sedantes', 
    'alcohol_etanol',
    'cannabinoides', 
    'escopolamina', 
    'PSA_no_clasificado_lista', 
    'otros'
]

# =========================================================
# SOBRESCRITURAS LOCALES (NO VERSIONADAS)
# =========================================================
try:
    from config_local import *  # noqa: F403,F401
except Exception:
    pass
