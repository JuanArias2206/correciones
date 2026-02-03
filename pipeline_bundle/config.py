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
# CONFIGURACIÓN DE LA API DE GEMINI
# =========================================================
# Rota entre estas keys si una se agota

#GEMINI_API_KEY = "AIzaSyB7BLl_abUktiP-aitJ4o-pw3gFqO26XvE"    # USADA NO USAR PORQUE COBRAN

GEMINI_API_KEY = "AIzaSyC65dXNYxzlKJG5Wko3AttsXXCPwA3Ogys"  

# GEMINI_API_KEY = "AIzaSyD7jxtM9MkdBQU6Z3bvKXB_HDquUfzx8dw"  
# GEMINI_API_KEY = "AIzaSyC-kC8Ms9lY_w13U3JTvMmU6xXqmKuy9nY"  

# Modelo a utilizar
GEMINI_MODEL = 'gemini-2.5-flash-lite'

# Tiempo de espera entre llamadas al LLM (segundos)
LLM_DELAY_SECONDS = 5

# Tamaño del lote para clasificación con LLM
LLM_BATCH_SIZE = 10

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
