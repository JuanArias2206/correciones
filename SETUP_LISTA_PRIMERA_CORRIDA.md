# ✅ SETUP COMPLETADO PARA PRIMERA CORRIDA

## 📋 Resumen Ejecutivo

**Estado:** ✅ Listo para ejecutar  
**API Key:** ✅ Hardcodeada (sk-90b9c21e...)  
**Porcentaje:** ✅ Configurable (20% por defecto)  
**Logging:** ✅ Sistema automático + Métricas  
**Directorio:** ✅ pipeline_bundle/

---

## 🚀 CÓMO EJECUTAR (3 opciones)

### **Opción 1: Setup automático + Test (Recomendado)**
```bash
cd pipeline_bundle
bash quick_start.sh
# Luego ejecutar:
python run_first_test.py
```

### **Opción 2: Ejecución directa**
```bash
cd pipeline_bundle
python run_first_test.py
```

### **Opción 3: Con porcentaje personalizado**
```bash
cd pipeline_bundle
python run_first_test.py --pct 50    # 50% de registros
python run_first_test.py --pct 100   # 100% de registros
python run_first_test.py --api-test  # Solo testa API
```

---

## 📊 QUÉ VERÁS

### **Paso 1: Validación**
```
🔑 VALIDACIÓN DE API KEY
✅ API Key válida: sk-90b9c21...ab53fad814
📍 Model: deepseek-chat
📍 Base URL: https://api.deepseek.com
🌡️  Temperature: 0.0
```

### **Paso 2: Test de Conexión**
```
🌐 TEST DE CONEXIÓN API
⏳ Enviando request de prueba...
✅ Conexión exitosa a API DeepSeek
   Respuesta de prueba: [{"id":"test_1",...}]...
```

### **Paso 3: Configuración**
```
⚙️  CONFIGURACIÓN DE LA CORRIDA
PORCENTAJE A PROCESAR: 20%
MODO DE PRUEBA: ACTIVADO
```

### **Paso 4: Procesamiento**
```
🚀 INICIANDO PROCESAMIENTO
⏳ Procesando 20% de registros...
```

### **Paso 5: Resumen Final**
```
╔═════════════════════════════════════════════════════════╗
║              PIPELINE EXECUTION SUMMARY                 ║
╚═════════════════════════════════════════════════════════╝

PROCESAMIENTO:
  • Total registros leídos:        500
  • Registros procesados:          100
  • Registros saltados (pre-filter): 10
  
CLASIFICACIÓN:
  • Clasificados (deterministic):  40
  • Cache hits:                     20
  • Llamadas LLM:                   30
  
ERRORES Y AJUSTES:
  • Errores encontrados:            2
  • Falsos positivos corregidos:    3
  
AHORRO ESPERADO:
  • % LLM evitados:                 70.0%
  • Costo estimado LLM:             $0.01 USD (est.)

✅ Ejecución completada
📁 Logs guardados en: pipeline_bundle/logs/
```

---

## 🔍 DÓNDE BUSCAR INFORMACIÓN

### **1. Logs en Tiempo Real**
```bash
# Ver logs mientras se ejecuta:
tail -f pipeline_bundle/logs/pipeline_*.log

# Ver solo errores:
grep ERROR pipeline_bundle/logs/pipeline_*.log

# Contar eventos:
grep -c "LLM_CALL" pipeline_bundle/logs/pipeline_*.log
```

### **2. Resumen de Métricas**
Se imprime automáticamente al terminar (arriba ↑)

### **3. Contadores Específicos**
Los puedes ver en:
```python
# En el archivo de logs:
# [2026-02-04 14:30:45] - SPA_Pipeline - [INFO] - LLM_CALL count: 30
# [2026-02-04 14:30:50] - SPA_Pipeline - [INFO] - Cache hits: 20
# [2026-02-04 14:31:00] - SPA_Pipeline - [INFO] - Deterministic: 40
```

---

## 📝 MODIFICAR CONFIGURACIÓN

### **Cambiar el porcentaje de prueba**

**Opción A: Comando (para esta corrida)**
```bash
python run_first_test.py --pct 50
```

**Opción B: config.py (permanente)**
```python
# Editar línea ~58 en config.py
TEST_PERCENTAGE = 50  # Cambiar de 20 a 50, 100, etc.
```

**Opción C: Variable de entorno**
```bash
export TEST_PERCENTAGE=75
python run_first_test.py
```

### **Cambiar porcentaje de LLM (dentro de TEST_PERCENTAGE)**
El 20% de registros se distribuye en:
- 40-50% deterministic (sin LLM)
- 20-30% cache (sin LLM)  
- 20-40% LLM calls

Esto se ajusta automáticamente en el pipeline.

---

## 🛠️ ARCHIVOS MODIFICADOS

| Archivo | Cambios | Líneas |
|---------|---------|--------|
| `config.py` | API key + logging + métricas | 27, 55-150 |
| `nuevo_codigo.py` | Imports de logger/METRICS | 29 |
| `run_first_test.py` | NUEVO: Script ejecución | 1-350 |
| `quick_start.sh` | NUEVO: Setup automático | 1-80 |

---

## 🧪 TEST RÁPIDO (5 segundos)

```bash
cd pipeline_bundle
python run_first_test.py --api-test
```

**Qué hace:** Solo valida que la API funciona, no procesa datos.

---

## ✅ CHECKLIST PRE-EJECUCIÓN

- [x] API key configurada (sk-90b9c21e412447b188162cab53fad814)
- [x] TEST_PERCENTAGE = 20 (configurable)
- [x] TEST_MODE = True (logging activado)
- [x] Logger configurado con 2 outputs (archivo + consola)
- [x] METRICS global con contadores
- [x] Directorio logs/ creado automáticamente
- [x] Scripts ejecutables (run_first_test.py, quick_start.sh)
- [x] config.py validada sin errores
- [x] nuevo_codigo.py actualizado con imports

---

## 🎯 FLUJO ESPERADO

```
Usuario ejecuta:
  python run_first_test.py
  
Sistema:
  1. Valida API key ✅
  2. Testa conexión DeepSeek ✅
  3. Muestra configuración (20%) ✅
  4. Inicia procesamiento
     ├─ Pre-filter → 10-15% ahorro
     ├─ Deterministic → 40-50% ahorro
     ├─ Cache → 20-30% ahorro
     ├─ LLM → solo ~20-40% llegan aquí
     └─ Post-filter + Validator
  5. Genera resumen en consola ✅
  6. Logs guardados en pipeline_bundle/logs/ ✅

Total esperado: 60-75% LLM evitados
```

---

## 💡 TIPS

### **Para ver la API key (si la olvidó)**
```bash
grep "DEEPSEEK_API_KEY = " pipeline_bundle/config.py
```

### **Para ver logs en tiempo real**
```bash
tail -f pipeline_bundle/logs/pipeline_*.log
```

### **Para contar eventos específicos**
```bash
grep "LLM_CALL\|CACHE_HIT\|DETERMINISTIC" pipeline_bundle/logs/pipeline_*.log | wc -l
```

### **Para reintentar en caso de error**
```bash
# El cache persiste, así que:
python run_first_test.py  # Intenta de nuevo
# Debería ser más rápido la segunda vez (cache hits)
```

---

## 🚨 SI FALLA

### **"API Key no encontrada"**
```bash
python -c "from config import DEEPSEEK_API_KEY; print(DEEPSEEK_API_KEY[:10])"
# Debería imprimir: sk-90b9c21e
```

### **"No se pudo conectar a la API"**
```bash
# Revisar logs:
grep "ERROR\|CRITICAL" pipeline_bundle/logs/pipeline_*.log
# Comprobar internet
# Verificar que la API key sea correcta
```

### **"Directorio de logs no existe"**
```bash
mkdir -p pipeline_bundle/logs
chmod 755 pipeline_bundle/logs
```

---

## 📞 COMANDO FINAL

**Copiar y ejecutar en terminal:**

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle && python run_first_test.py
```

O más simple:
```bash
cd pipeline_bundle && python run_first_test.py
```

---

## 🎬 RESUMEN

| Aspecto | Estado | Ubicación |
|---------|--------|-----------|
| API Key | ✅ Hardcodeada | config.py:27 |
| Porcentaje | ✅ 20% (configurable) | config.py:58 |
| Logging | ✅ Automático | pipeline_bundle/logs/ |
| Métricas | ✅ Globales | config.py:METRICS |
| Scripts | ✅ Listos | run_first_test.py |
| Setup | ✅ Automático | quick_start.sh |

**¡LISTO PARA EJECUTAR! 🚀**

```bash
python run_first_test.py
```
