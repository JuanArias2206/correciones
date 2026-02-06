# 🎯 ESTADO FINAL - LISTA PARA PRIMERA CORRIDA

## ✅ COMPLETADO

### 1. **API Key Hardcodeada**
```
Ubicación: pipeline_bundle/config.py línea 27
Valor:    sk-90b9c21e412447b188162cab53fad814
Estado:   ✅ Activa y lista
```

### 2. **Variables de Prueba (20% por defecto)**
```
Ubicación: pipeline_bundle/config.py línea 58
Variable:  TEST_PERCENTAGE = 20
Cómo cambiar:
  • Comando:   python run_first_test.py --pct 50
  • Código:    Editar TEST_PERCENTAGE en config.py
  • Enviroment: export TEST_PERCENTAGE=75
```

### 3. **Sistema de Logging Automático**
```
Ubicación: pipeline_bundle/config.py líneas 80-150
Salida:    pipeline_bundle/logs/pipeline_YYYYMMDD_HHMMSS.log
Consola:   Información de progreso en tiempo real
Archivo:   Logs completos y detallados para debugging

Niveles:
  • DEBUG:    Información detallada
  • INFO:     Información general
  • WARNING:  Advertencias
  • ERROR:    Errores encontrados
  • CRITICAL: Errores críticos
```

### 4. **Contadores de Métricas Globales**
```
Clase:  config.PipelineMetrics
Acceso: config.METRICS

Métricas:
  • total_records           → Total registros leídos
  • processed_records       → Registros procesados
  • skipped_records         → Saltados por pre-filtro
  • deterministic_classified → Clasificados por regex
  • cache_hits              → Encontrados en caché
  • llm_calls               → Llamadas al LLM
  • errors                  → Errores encontrados
  • false_positive_corrections → Reglas aplicadas

Métodos:
  • log_error()    → Registra errores con detalles
  • print_summary() → Imprime resumen visual
```

### 5. **Script de Ejecución (run_first_test.py)**
```
Ubicación:  pipeline_bundle/run_first_test.py
Tamaño:     ~350 líneas
Funciones:
  • validate_api_key()      → Valida que API key sea válida
  • test_api_connection()   → Testa conexión a DeepSeek
  • show_configuration()    → Muestra configuración actual
  • show_usage()            → Instrucciones de uso
  • main()                  → Orquestación principal

Opciones:
  python run_first_test.py              # 20% por defecto
  python run_first_test.py --pct 50     # 50% de registros
  python run_first_test.py --pct 100    # Corrida completa
  python run_first_test.py --api-test   # Solo valida API
  python run_first_test.py --show-usage # Muestra instrucciones
```

### 6. **Script de Setup Automático (quick_start.sh)**
```
Ubicación:  pipeline_bundle/quick_start.sh
Funciones:
  ✓ Valida que estés en el directorio correcto
  ✓ Verifica Python 3
  ✓ Crea directorio logs/
  ✓ Verifica dependencias (pandas, tqdm, requests)
  ✓ Valida configuración de config.py
  ✓ Muestra resumen y próximos pasos

Uso: bash quick_start.sh
```

---

## 🚀 CÓMO EJECUTAR (3 FORMAS)

### **Forma 1: Setup Automático + Test (Recomendado)**
```bash
cd pipeline_bundle
bash quick_start.sh
# Luego:
python run_first_test.py
```

### **Forma 2: Ejecución Directa**
```bash
cd pipeline_bundle
python run_first_test.py
```

### **Forma 3: Con Opciones**
```bash
cd pipeline_bundle
python run_first_test.py --pct 50        # 50%
python run_first_test.py --api-test      # Solo API
python run_first_test.py --show-usage    # Ayuda
```

---

## 📊 FLUJO DE EJECUCIÓN

```
$ python run_first_test.py

┌─────────────────────────────────────────┐
│ 1. VALIDACIÓN DE API KEY              │
├─────────────────────────────────────────┤
│ ✅ API Key válida: sk-90b9c21...ad814 │
│ ✅ Formato correcto                    │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 2. TEST DE CONEXIÓN API                │
├─────────────────────────────────────────┤
│ ⏳ Enviando request de prueba...       │
│ ✅ Conexión exitosa a DeepSeek        │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 3. MOSTRAR CONFIGURACIÓN               │
├─────────────────────────────────────────┤
│ Porcentaje: 20%                        │
│ Modo: TEST_MODE = True                 │
│ Logs: pipeline_bundle/logs/            │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 4. INICIAR PROCESAMIENTO               │
├─────────────────────────────────────────┤
│ Pre-filter (blacklist)                 │
│ Deterministic (regex)                  │
│ Cache (SQLite)                         │
│ LLM (solo ambiguos, ~20-40%)          │
│ Post-filter & Validator                │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 5. RESUMEN FINAL EN CONSOLA             │
├─────────────────────────────────────────┤
│ PROCESAMIENTO:                         │
│  • Total: 500                          │
│  • Procesados: 100 (20%)               │
│  • Saltados: 10                        │
│                                        │
│ CLASIFICACIÓN:                         │
│  • Deterministic: 40                   │
│  • Cache hits: 20                      │
│  • LLM calls: 30                       │
│                                        │
│ AHORRO:                                │
│  • % LLM evitados: 70%                │
│  • Costo estimado: $0.01 USD          │
└─────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ ✅ EJECUCIÓN COMPLETADA                │
│ 📁 Logs: pipeline_bundle/logs/         │
└─────────────────────────────────────────┘
```

---

## 📍 DÓNDE BUSCAR INFORMACIÓN

### **Logs en tiempo real**
```bash
tail -f pipeline_bundle/logs/pipeline_*.log
```

### **Solo errores**
```bash
grep ERROR pipeline_bundle/logs/pipeline_*.log
```

### **Conteo de eventos**
```bash
grep LLM_CALL pipeline_bundle/logs/pipeline_*.log | wc -l
grep CACHE_HIT pipeline_bundle/logs/pipeline_*.log | wc -l
```

### **Resumen al final**
Se imprime automáticamente en consola después de ejecutar.

---

## 🔧 PERSONALIZACIÓN

### **Cambiar porcentaje a 50%**

**Opción A (por comando, temporal):**
```bash
python run_first_test.py --pct 50
```

**Opción B (en código, permanente):**
Editar `config.py` línea 58:
```python
TEST_PERCENTAGE = 50  # Cambiar de 20 a 50
```

**Opción C (variable de entorno):**
```bash
export TEST_PERCENTAGE=50
python run_first_test.py
```

### **Cambiar nivel de logging**

En `config.py` líneas 100-120:
```python
file_handler.setLevel(logging.DEBUG)      # Más detallado
console_handler.setLevel(logging.DEBUG)   # Más en consola
```

---

## 🎯 ARCHIVOS DEL SETUP

| Archivo | Tipo | Líneas | Propósito |
|---------|------|--------|----------|
| config.py | Modificado | 27, 55-150 | API key + logging + métricas |
| nuevo_codigo.py | Modificado | 29 | Imports de logger/METRICS |
| run_first_test.py | NUEVO | 350 | Script ejecución principal |
| quick_start.sh | NUEVO | 80 | Setup automático |
| SETUP_LISTA_PRIMERA_CORRIDA.md | NUEVO | - | Este documento |

---

## ✅ CHECKLIST FINAL

- [x] API key hardcodeada en config.py
- [x] TEST_PERCENTAGE = 20 (configurable)
- [x] Logger configurado (archivo + consola)
- [x] METRICS global para contadores
- [x] Directorio logs/ (se crea automáticamente)
- [x] run_first_test.py (script ejecución)
- [x] quick_start.sh (setup automático)
- [x] Scripts ejecutables (chmod +x)
- [x] Sintaxis validada (exit code 0)
- [x] Documentación completa

---

## 🎬 COMANDO FINAL

Copia y ejecuta:

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle && python run_first_test.py
```

O más simple:
```bash
cd pipeline_bundle && python run_first_test.py
```

---

## 📈 MÉTRICAS ESPERADAS (después de 5 min)

```
PROCESAMIENTO (20% de ~500 registros = 100 procesados):
  • Registros saltados (pre-filter): 10 (10%)
  • Registros a clasificar:          90 (90%)

CLASIFICACIÓN:
  • Deterministic (regex):           40 (44%)
  • Cache hits:                      20 (22%)
  • LLM calls:                       30 (34%)

AHORRO:
  • % LLM evitados:                  66%
  • Costo estimado:                  $0.01 USD
  • Tiempo ahorrado:                 ~2 min vs 5 min

ERRORES:
  • Total encontrados:               < 5
  • Falsos positivos corregidos:    2-3
```

---

## 🚨 TROUBLESHOOTING RÁPIDO

### Error: "API Key no encontrada"
```bash
grep DEEPSEEK_API_KEY pipeline_bundle/config.py | head -1
# Debe mostrar: DEEPSEEK_API_KEY = 'sk-90b9c21e...'
```

### Error: "No se pudo conectar a API"
1. Verificar internet
2. Verificar que no haya rate limit
3. Revisar logs: `tail -20 pipeline_bundle/logs/pipeline_*.log`

### Logs no se crean
```bash
mkdir -p pipeline_bundle/logs
chmod 755 pipeline_bundle/logs
```

---

## 💾 SEGURIDAD

⚠️ API key está hardcodeada para conveniencia.

**Para producción:**
1. Mover a variable de entorno: `export DEEPSEEK_API_KEY='sk-...'`
2. O usar config_local.py (no versionado)
3. Nunca commitear keys en git

---

## 📞 RESUMEN

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| Setup | ✅ Listo | Todos los archivos configurados |
| API | ✅ Hardcodeada | sk-90b9c21... |
| Pruebas | ✅ 20% | Configurable |
| Logging | ✅ Automático | pipeline_bundle/logs/ |
| Métricas | ✅ Globales | config.METRICS |
| Scripts | ✅ Ejecutables | run_first_test.py |

---

**🎉 ¡LISTO PARA EJECUTAR!**

```bash
python run_first_test.py
```

Espera 2-5 minutos, verás el resumen en consola + logs en `pipeline_bundle/logs/`
