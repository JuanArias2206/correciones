# 🚀 PRIMERA CORRIDA - SETUP COMPLETADO

## ✅ Lo que está listo

### 1. **API Key Hardcodeada**
- **Dónde:** `config.py` línea 27
- **Valor:** `sk-90b9c21e412447b188162cab53fad814`
- **Estado:** ✅ Configurada y lista

### 2. **Variables de Prueba (20% por defecto)**
- **Dónde:** `config.py` línea 58
- **Variable:** `TEST_PERCENTAGE = 20`
- **Cambiar:** Editar el número para diferentes porcentajes (1-100)

```python
TEST_PERCENTAGE = 20   # Procesa el 20%
TEST_PERCENTAGE = 50   # Procesa el 50%
TEST_PERCENTAGE = 100  # Procesa el 100% (corrida completa)
```

### 3. **Sistema de Logging Automático**
- **Logs guardados en:** `pipeline_bundle/logs/`
- **Nombre:** `pipeline_YYYYMMDD_HHMMSS.log`
- **Contenido:** Todos los eventos, errores, conteos
- **Formato:** `[TIMESTAMP] - [NIVEL] - [MENSAJE]`

**Niveles de log:**
- `DEBUG` → Información detallada
- `INFO` → Información general
- `WARNING` → Advertencias
- `ERROR` → Errores (si los hay)
- `CRITICAL` → Errores críticos

### 4. **Métricas Globales en Consola**
Después de ejecutar, verás automáticamente:

```
╔═════════════════════════════════════════════════════════╗
║              PIPELINE EXECUTION SUMMARY                 ║
╚═════════════════════════════════════════════════════════╝

PROCESAMIENTO:
  • Total registros leídos:        500
  • Registros procesados:          450
  • Registros saltados:            50
  
CLASIFICACIÓN:
  • Clasificados (deterministic):  180
  • Cache hits:                     90
  • Llamadas LLM:                   180
  
ERRORES Y AJUSTES:
  • Errores encontrados:            2
  • Falsos positivos corregidos:    5
  
AHORRO ESPERADO:
  • % LLM evitados:                 60.0%
  • Costo estimado LLM:             $0.05 USD
```

---

## 🎯 CÓMO EJECUTAR

### **Opción 1: Ejecución Rápida (20%)**
```bash
cd pipeline_bundle
python run_first_test.py
```

**Qué hace:**
1. Valida API key
2. Testa conexión a DeepSeek
3. Muestra configuración
4. Procesa 20% de registros
5. Genera resumen de métricas

**Tiempo estimado:** 2-5 minutos

---

### **Opción 2: Prueba Completa (100%)**
```bash
cd pipeline_bundle
python run_first_test.py --pct 100
```

**Mismo proceso pero con 100% de datos**

**Tiempo estimado:** 15-30 minutos

---

### **Opción 3: Test Rápido de API (sin procesar)**
```bash
cd pipeline_bundle
python run_first_test.py --api-test
```

**Solo valida que la API funciona, no procesa datos**

**Tiempo estimado:** 10 segundos

---

### **Opción 4: Ver Instrucciones Completas**
```bash
cd pipeline_bundle
python run_first_test.py --show-usage
```

---

## 📊 DÓNDE VER LOS RESULTADOS

### **1. Resumen en Consola**
Se imprime automáticamente al terminar:
```
✅ Ejecución completada
📁 Logs guardados en: pipeline_bundle/logs/
```

### **2. Logs Detallados**
```bash
# Ver el log actual en tiempo real
tail -f pipeline_bundle/logs/pipeline_*.log

# Ver solo errores
grep ERROR pipeline_bundle/logs/pipeline_*.log

# Ver solo métricas
grep SUMMARY pipeline_bundle/logs/pipeline_*.log
```

### **3. Contador de Llamados**
Dentro del resumen se muestra:
- **Llamadas LLM:** `{METRICS.llm_calls}`
- **Cache hits:** `{METRICS.cache_hits}`
- **Deterministic:** `{METRICS.deterministic_classified}`
- **Errores:** `{METRICS.errors}` (con detalles)

---

## 🔧 CAMBIAR PORCENTAJE DE PRUEBA

### **Opción A: Por comando (temporal)**
```bash
python run_first_test.py --pct 50   # Esta corrida: 50%
python run_first_test.py --pct 100  # Esta corrida: 100%
```

### **Opción B: En config.py (permanente)**
Editar línea 58:
```python
# ANTES:
TEST_PERCENTAGE = int(os.getenv('TEST_PERCENTAGE', '20'))

# DESPUÉS (para 50% siempre):
TEST_PERCENTAGE = int(os.getenv('TEST_PERCENTAGE', '50'))
```

### **Opción C: Variable de entorno**
```bash
export TEST_PERCENTAGE=75
python run_first_test.py  # Procesará 75%
```

---

## 📋 CHECKLIST PRE-EJECUCIÓN

- [ ] API key en `config.py` línea 27 ✅ (ya está: sk-90b9c...)
- [ ] TEST_PERCENTAGE en `config.py` línea 58 ✅ (20 por defecto)
- [ ] Directorio `logs/` creado ✅ (se crea automáticamente)
- [ ] Directorio `cache/` creado ✅ (se crea automáticamente)
- [ ] Python >= 3.8 instalado
- [ ] Dependencias instaladas: `pip install -r requirements.txt`

---

## 🐛 SI ALGO FALLA

### **Error: "API Key no encontrada"**
```bash
# Verificar que está en config.py:
grep "DEEPSEEK_API_KEY = " pipeline_bundle/config.py
```

**Debería mostrar:**
```
DEEPSEEK_API_KEY = 'sk-90b9c21e412447b188162cab53fad814'
```

---

### **Error: "No se pudo conectar a la API"**
```bash
# Revisar logs de error:
tail -50 pipeline_bundle/logs/pipeline_*.log | grep ERROR
```

**Posibles causas:**
1. Internet offline
2. API key expirada
3. Rate limit alcanzado
4. DeepSeek API down

---

### **Error: "Directorio de logs no accesible"**
```bash
# Crear directorio manualmente:
mkdir -p pipeline_bundle/logs
chmod 755 pipeline_bundle/logs
```

---

### **Conteo de errores es alto (>10%)**
Ver detalles en el resumen:
```
DETALLE DE ERRORES:
─────────────────────────────────────────────
⚠️  [API_ERROR] producto_xyz
   → Connection timeout after 60s
   @ 2026-02-04T14:23:45
```

---

## 📈 INTERPRETACIÓN DE MÉTRICAS

| Métrica | Qué significa | Esperado |
|---------|---------------|----------|
| % LLM evitados | Porcentaje filtrado antes de LLM | 60-80% |
| Cache hits | Registros encontrados en caché | 20-40% |
| Deterministic | Clasificados por regex | 40-60% |
| Errores | Problemas encontrados | <5% |
| Falsos positivos corregidos | Reglas aplicadas | Variable |

---

## 🎬 FLUJO COMPLETO

```
1. python run_first_test.py
          ↓
2. ✅ Valida API key
          ↓
3. 🌐 Testa conexión DeepSeek
          ↓
4. ⚙️  Muestra configuración (20% por defecto)
          ↓
5. 🚀 Inicia procesamiento
    ├─ Pre-filter (blacklist) → 10-15% ahorro
    ├─ Deterministic (regex) → 40-50% ahorro
    ├─ Cache (SQLite) → 20-30% ahorro
    ├─ LLM (solo ambiguos)
    └─ Post-filter & Validator
          ↓
6. 📊 Muestra resumen
    ├─ Total registros
    ├─ Errores (si los hay)
    ├─ Métricas de ahorro
    └─ Ubicación de logs
          ↓
7. ✅ Ejecución completada
```

---

## 💾 ARCHIVOS MODIFICADOS PARA ESTA FASE

1. **config.py** (línea 27)
   - API key hardcodeada
   
2. **config.py** (líneas 55-150)
   - Variables TEST_PERCENTAGE, TEST_MODE
   - Sistema de logging completo
   - Clase PipelineMetrics global
   
3. **nuevo_codigo.py** (línea 29)
   - Import de logger y METRICS desde config
   
4. **run_first_test.py** (NUEVO)
   - Script para primera corrida
   - Validación API
   - Test de conexión
   - Resumen de métricas

---

## 🔐 NOTAS DE SEGURIDAD

⚠️ **IMPORTANTE:** La API key está hardcodeada en config.py por conveniencia.

**Para producción:**
1. Mover a variable de entorno: `export DEEPSEEK_API_KEY='sk-...'`
2. O mover a `config_local.py` (no versionado)
3. Nunca commitear keys en git

**Ahora:**
```bash
# Verificar que está configurada:
grep -n "DEEPSEEK_API_KEY = " pipeline_bundle/config.py
```

Debería mostrar línea 27 con el valor.

---

## 📞 RESUMEN RÁPIDO

**Para primera corrida de prueba:**
```bash
cd pipeline_bundle
python run_first_test.py
# Esperar 2-5 minutos
# Ver resumen en consola + logs en pipeline_bundle/logs/
```

**Para cambiar porcentaje:**
- `python run_first_test.py --pct 50`
- O editar `TEST_PERCENTAGE` en config.py

**Logs siempre disponibles en:**
- `pipeline_bundle/logs/pipeline_*.log`

---

**Estado:** ✅ LISTO PARA PRIMERA CORRIDA  
**API Key:** ✅ Configurada  
**Logging:** ✅ Automático  
**Métricas:** ✅ Contadores globales  
**Porcentaje:** ✅ Configurable (20% por defecto)  

```
¡A correr! 🚀
python run_first_test.py
```
