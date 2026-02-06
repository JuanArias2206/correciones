# Plantilla de configuración local (COPIA Y EDITA)
# ==================================================
# 1. Copia este contenido a config_local.py
# 2. Reemplaza 'sk-...' con tu API key real de DeepSeek
# 3. Guarda el archivo
# 4. Nunca commits este archivo (ya está en .gitignore)

# Tu API key de DeepSeek (OBLIGATORIA)
DEEPSEEK_API_KEY = "sk-90b9c21e412447b188162cab53fad814"

# Configuración del modelo (opcional)
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

# Tuning del pipeline (opcional)
LLM_DELAY_SECONDS = 5
LLM_BATCH_SIZE = 10
LLM_TIMEOUT_SECONDS = 60
