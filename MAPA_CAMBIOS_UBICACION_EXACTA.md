# 🗂️ MAPA DE CAMBIOS - UBICACIÓN EXACTA POR ARCHIVO

## 📌 PARA ENCONTRAR LOS CAMBIOS RÁPIDAMENTE

---

## 1️⃣ config.py

**Ubicación:** `/pipeline_bundle/config.py`

**Cambios:**
- **Línea ~36:** Agregadas 8 líneas nuevas después de `LLM_TIMEOUT_SECONDS`
  ```
  LLM_BATCH_BUDGET_CHARS = ...
  PROMPT_VERSION = ...
  CACHE_DB_PATH = ...
  ENABLE_CACHE = ...
  ENABLE_DETERMINISTIC = ...
  ENABLE_METRICS = ...
  LLM_TEMPERATURE = ...
  ```

**Líneas alteradas:** 36-44 (aprox)  
**Status:** ✅ VALIDADO

---

## 2️⃣ llm_clients.py

**Ubicación:** `/pipeline_bundle/llm_clients.py`

**Cambios:**
1. **Línea 5:** Parámetro `temperature: float = 0.0` en `DeepSeekClient.__init__()`
2. **Línea 12:** `self._temperature = temperature`
3. **Línea 17:** Parámetro `temperature=self._temperature` en `chat.completions.create()`
4. **Línea 26:** Parámetro `temperature: float = 0.0` en `build_llm_client()`
5. **Línea 34:** Paso a constructor `DeepSeekClient(..., temperature=temperature)`

**Líneas alteradas:** 5, 12, 17, 26, 34  
**Status:** ✅ VALIDADO

---

## 3️⃣ nuevo_codigo.py (REFACTORIZACIÓN MAYOR)

**Ubicación:** `/pipeline_bundle/nuevo_codigo.py`

**Cambios principales:**

### A) Header y Imports (Líneas 1-45)
- Docstring actualizado (v2.0 optimizado)
- Imports nuevos:
  ```python
  from cache_manager import CacheManager
  from deterministic_classifier import DeterministicClassifier
  from collections import defaultdict
  ```
- Parámetros de config nuevos importados:
  ```python
  LLM_BATCH_BUDGET_CHARS, PROMPT_VERSION, CACHE_DB_PATH,
  ENABLE_CACHE, ENABLE_DETERMINISTIC, ENABLE_METRICS, LLM_TEMPERATURE
  ```

### B) Nueva clase PipelineMetrics (después de imports, ~45-75)
```python
class PipelineMetrics:
    def __init__(self):
        # 7 atributos nuevos
    def report(self):
        # Imprime reporte detallado
```

### C) Función build_llm_prompt_compact() (NUEVA, ~180-225)
- Reemplaza `build_llm_prompt()` anterior
- ~40 líneas nuevas
- Retorna prompt compacto + id_to_nom_clean

### D) Función build_llm_prompt() alias (línea ~226)
```python
def build_llm_prompt(nombres_pro_lista):
    """Alias para compatibilidad."""
    return build_llm_prompt_compact(nombres_pro_lista)
```

### E) Función parse_llm_json_compact() (NUEVA, ~228-260)
- Parsea formato compacto: `[{"id":"1","c":["cat"]}]`
- Soporta fallback a formato antiguo

### F) Función parse_llm_json() alias (línea ~262)
```python
def parse_llm_json(texto_respuesta):
    """Wrapper para compatibilidad."""
    return parse_llm_json_compact(texto_respuesta)
```

### G) Clase DynamicBatchLLMClassifier (NUEVA, ~265-360)
- Reemplaza `LLMClassifier` anterior
- Método `_estimate_batch_size()` (~10 líneas)
- Método `classify_batch()` (~80 líneas)
- Atributo `self.incidencias` para logging

### H) Alias de compatibilidad (línea ~362)
```python
LLMClassifier = DynamicBatchLLMClassifier
```

### I) Clases PreFilter, PostFilter, Validator, Exporter, DataLoader, Profiler
- **SIN CAMBIOS** (mantienen interfaz idéntica)

### J) Función run_pipeline() REESCRITA (línea ~500 aprox, ~180 líneas nuevas)
**Estructura:**
```python
def run_pipeline() -> None:
    try:
        # [ETAPA 1] Pre-filtro
        # [ETAPA 2] Deterministic classifier (si ENABLE_DETERMINISTIC)
        # [ETAPA 3] Cache persistente (si ENABLE_CACHE)
        # [ETAPA 4] LLM (solo ambiguos)
        # [ETAPA 5] Post-filtro y validación
        # [ETAPA 6] Exportación y métricas
    except Exception as e:
        # Error handling
```

**Cambios clave:**
- Inicialización de `PipelineMetrics()`
- Inicialización de `CacheManager` (si ENABLE_CACHE)
- Inicialización de `DeterministicClassifier` (si ENABLE_DETERMINISTIC)
- Lógica de 6 etapas (antes: 3 etapas)
- Llamada a `metrics.report()` al final

### K) Clase MetricsTracker ELIMINADA
- Reemplazada por `PipelineMetrics` (más completa)

**Líneas alteradas:** Toda la función run_pipeline() (~500-665)  
**Status:** ✅ VALIDADO

---

## 4️⃣ cache_manager.py (NUEVO)

**Ubicación:** `/pipeline_bundle/cache_manager.py`  
**Tipo:** ARCHIVO NUEVO  
**Líneas:** ~200

**Contenido:**
- Clase `CacheManager` con métodos:
  - `__init__(db_path, prompt_version)`
  - `get(nom_clean)` 
  - `get_batch(noms_clean)`
  - `set(nom_clean, categorias)`
  - `set_batch(results)`
  - `clear_old_versions(keep_version)`
  - `stats()`
  - `_init_db()` (privado)

**Status:** ✅ CREADO Y VALIDADO

---

## 5️⃣ deterministic_classifier.py (NUEVO)

**Ubicación:** `/pipeline_bundle/deterministic_classifier.py`  
**Tipo:** ARCHIVO NUEVO  
**Líneas:** ~150

**Contenido:**
- Clase `DeterministicClassifier` con:
  - Atributo class `STRONG_CONFIDENCE_PATTERNS` (9 categorías)
  - Método `__init__(use_strong_confidence_only=True)`
  - Método `classify(nom_clean)` → List[str] | None
  - Método `classify_batch(noms_clean)` → Dict
  - Método `get_unclassified(noms_clean)` → List[str]

**Status:** ✅ CREADO Y VALIDADO

---

## 📊 RESUMEN DE CAMBIOS

| Archivo | Tipo | Líneas | Status |
|---------|------|--------|--------|
| config.py | Extensión | +8 | ✅ |
| llm_clients.py | Modificación | +5 | ✅ |
| nuevo_codigo.py | Refactorización | +200, -100 | ✅ |
| cache_manager.py | NUEVO | 200 | ✅ |
| deterministic_classifier.py | NUEVO | 150 | ✅ |
| blacklists.py | SIN CAMBIOS | - | ✅ |
| patterns.py | SIN CAMBIOS | - | ✅ |
| main_runner.py | SIN CAMBIOS | - | ✅ |
| otros | SIN CAMBIOS | - | ✅ |

---

## 🔍 CÓMO REVISAR

### Para ver EXACTAMENTE qué cambió:

```bash
# Si estuvieras en git (no está hecho aún)
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones

# Ver diferencias en config.py
diff -u config.py.backup config.py  # (si tuvieras backup)

# O simplemente abre los archivos y busca:
# - config.py: busca "LLM_BATCH_BUDGET_CHARS"
# - llm_clients.py: busca "temperature"
# - nuevo_codigo.py: busca "PipelineMetrics" o "DynamicBatch"
# - Los archivos .py nuevos: están en la raíz de pipeline_bundle/
```

### Validación visual:

```bash
# Terminal: verifica sintaxis
python -m py_compile config.py llm_clients.py cache_manager.py \
  deterministic_classifier.py nuevo_codigo.py
# Salida: ninguna = ✅ OK
```

---

## 📝 PARA CHATGPT

Si pasas FRAGMENTOS_COPY_PASTE_REVISOR.md a ChatGPT, menciona:

> "Los cambios principales están en:
> 
> 1. config.py líneas ~36-44 (7 parámetros nuevos)
> 2. llm_clients.py líneas 5, 12, 17, 26, 34 (parameter temperature)
> 3. nuevo_codigo.py líneas ~180-360 (nuevas funciones y clase)
> 4. nuevo_codigo.py líneas ~500-665 (run_pipeline reescrita)
> 5. cache_manager.py (NUEVO FILE, 200 líneas)
> 6. deterministic_classifier.py (NUEVO FILE, 150 líneas)
> 
> Todos los cambios están hechos. Solo falta tu aprobación clínica."

---

## ✅ CHECKLIST DE CAMBIOS

- [x] config.py: Nuevos parámetros agregados
- [x] llm_clients.py: Parameter temperature agregado
- [x] nuevo_codigo.py: Imports actualizados
- [x] nuevo_codigo.py: PipelineMetrics clase nueva
- [x] nuevo_codigo.py: build_llm_prompt_compact() NUEVA
- [x] nuevo_codigo.py: parse_llm_json_compact() NUEVA
- [x] nuevo_codigo.py: DynamicBatchLLMClassifier NUEVA
- [x] nuevo_codigo.py: run_pipeline() REESCRITA
- [x] nuevo_codigo.py: Aliases para compatibilidad
- [x] cache_manager.py: NUEVO ARCHIVO
- [x] deterministic_classifier.py: NUEVO ARCHIVO
- [x] Validación de sintaxis: PASADO
- [x] Documentación: COMPLETA

---

**Fin del mapa de cambios.**

**Siguiente paso:** Leer INSTRUCCIONES_REVISOR_CHATGPT.md
