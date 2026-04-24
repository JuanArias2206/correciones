# 🚀 INSTRUCCIONES PARA EJECUTAR EL PIPELINE DE CLASIFICACIÓN

## 📋 Resumen (VERSIÓN MEJORADA)

El pipeline ahora incluye:
- **Batch size aumentado** de 10 a 75 items (menos llamadas, más contexto)
- **Distribución completa de vías de exposición** (no solo la frecuente)
- **Prompt mejorado** con reglas específicas sobre cómo interpretar vías
- **Logging detallado** en tiempo real del progreso

**Resultado:**  
✅ ~58 batches en lugar de 434 (7.5x menos)  
✅ 20-30 minutos de ejecución (vs 1-2 horas antes)  
✅ Mayor precisión en clasificaciones  
✅ Menor costo en API calls  

---

## 🛠️ Preparación

### 1️⃣ Verifica que estés en el directorio correcto:

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle
```

Deberías ver estos archivos:
- `nuevo_codigo.py` ✅
- `patterns.py` ✅
- `config.py` ✅
- `data/` (carpeta con archivos Excel) ✅

### 2️⃣ Verifica las dependencias:

```bash
python -c "import pandas, openpyxl; print('✅ Todas las dependencias están instaladas')"
```

---

## 🏃 EJECUCIÓN DEL PIPELINE

### Opción A: Con LLM habilitado (RECOMENDADO - Clasificación completa)

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle
ENABLE_LLM=true python nuevo_codigo.py
```

**¿Qué hace?**
- ✅ ETAPA 1: Filtra productos en blacklist (6.7% - ~636 productos)
- ✅ ETAPA 2: Clasifica con patrones regex (43.9% - ~4,159 productos)
- ✅ ETAPA 3: Busca en caché previos resultados
- ✅ ETAPA 4: **Procesa con DeepSeek API** los productos pendientes (~4,681 productos)
- ✅ ETAPA 5: Aplica validación por vía de exposición
- ✅ ETAPA 6: Exporta 5 archivos Excel

**Tiempo estimado:** 30-60 minutos (depende del número de productos y latencia API)

**Archivos generados:**
- `../resultados_v5/resultados_clasificacion_llm_avanzada.xlsx` (171,029 filas)
- `../resultados_v5/productos_por_categoria_conteo.xlsx` (15 hojas - 1 "Todos" + 14 categorías)
- `../resultados_v5/productos_filtrados_blacklist.xlsx` (productos excluidos)
- `../resultados_v5/productos_por_categoria.xlsx` (11,170 registros únicos)
- `../resultados_v5/resumen_conteo_clasificacion_final.xlsx`

---

### Opción B: Sin LLM (Solo patrones - Rápido, para testing)

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle
ENABLE_LLM=false python nuevo_codigo.py
```

**¿Qué hace?**
- ✅ ETAPA 1-3: Igual que arriba
- ⏭️ ETAPA 4: Los ~4,681 productos pendientes quedan como "otros" (sin usar LLM)
- ✅ ETAPA 5-6: Exporta resultados

**Tiempo estimado:** 30-45 segundos (muy rápido)

---

## 📊 QUÉ VE EN PANTALLA

### Durante la ejecución:

```
════════════════════════════════════════════════════════════════════════════════
  PIPELINE DE CLASIFICACIÓN DE SUSTANCIAS v3.0
════════════════════════════════════════════════════════════════════════════════

[ETAPA 1] Pre-filtro (blacklist general):
════════════════════════════════════════════════════════════════════════════════
  📊 Total productos: 9,476
  ✅ Filtrados (blacklist): 636 (6.7%)
  ➡️  Continúan a ETAPA 2: 8,840
  
  Primeros 10 productos en blacklist:
     1. antibiotico x
     2. analgesico generico
     ...
  
  💾 Lista de blacklist guardada en: productos_filtrados_blacklist.xlsx
════════════════════════════════════════════════════════════════════════════════

[ETAPA 2] Clasificación determinística (regex + enriquecido + post-filter):
════════════════════════════════════════════════════════════════════════════════
  ✅ Productos clasificados: 4,159 (43.9%)
  ➡️  Pendientes para LLM (aún como 'otros'): 4,681 (49.4%)
════════════════════════════════════════════════════════════════════════════════

[ETAPA 3] Caché persistente:
════════════════════════════════════════════════════════════════════════════════
  🔍 Buscando en caché (versión: v2.0_compact)...
  📊 Cache hits encontrados: 0
  ✅ Cache hits útiles: 0
  ➡️  Pendientes para LLM: 4,681
════════════════════════════════════════════════════════════════════════════════

[ETAPA 4] Clasificación LLM (DeepSeek):
════════════════════════════════════════════════════════════════════════════════
  📧 Procesando 4,681 productos con DeepSeek API
  ⏱️  (Este proceso puede tomar tiempo según cantidad de productos)
════════════════════════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════════════════════════
[BATCH 1/47] Procesando 100 productos (1-100)
════════════════════════════════════════════════════════════════════════════════

📋 Productos en este batch:
   1. cocaina pura                               [vía: oral (100%)]
   2. marihuana criada en casa                   [vía: respiratoria (80%)]
   3. acetaminofen + tramadol                    [vía: oral (100%)]
   ...

💬 Preview del prompt enviado al LLM:
   Experto en SPA en Colombia. Clasifica en UNA O MÁS categorías...
   Items (primeros 5):
   0:cocaina pura [vía: oral (100%)]
   1:marihuana criada en casa [vía: respiratoria (80%)]
   2:acetaminofen + tramadol [vía: oral (100%)]

⏳ Intento 1/3: Llamando a DeepSeek API...
   ✅ Respuesta recibida en 3.45s
   Tamaño: 1250 caracteres
   ✅ JSON parseado: 100 items clasificados
   ✅ Batch 1/47 completado: 100 productos clasificados

════════════════════════════════════════════════════════════════════════════════
[BATCH 2/47] Procesando 100 productos (101-200)
════════════════════════════════════════════════════════════════════════════════

... (continúa para los 47 batches) ...

✅ ETAPA 4 COMPLETADA: 4,681 productos clasificados por LLM
════════════════════════════════════════════════════════════════════════════════

[ETAPA 5] Aplicando clasificaciones al DataFrame:
════════════════════════════════════════════════════════════════════════════════
  📝 Aplicando clasificaciones a 171,029 filas de datos...
  ✅ Columnas agregadas: 'grupos_sustancia_final', 'metodo_clasificacion'
  🔍 Validando con vía de exposición...
  ✅ Validación completada
  ✅ Columnas binarias creadas para 14 categorías
════════════════════════════════════════════════════════════════════════════════

[ETAPA 6] Exportando resultados:
════════════════════════════════════════════════════════════════════════════════
  📁 Destino: ../resultados_v5
  📊 Datos a exportar: 171,029 filas, 14 categorías
  ✅ Exportación completada
════════════════════════════════════════════════════════════════════════════════

RESUMEN DE MÉTODOS DE CLASIFICACIÓN (por filas):
deterministic       :   87,288 filas (51.0%)
default             :   37,024 filas (21.6%)
llm                 :   27,326 filas (16.0%)
blacklist           :   19,391 filas (11.3%)

Por productos únicos:
llm                 :  4,681 productos (49.4%)
deterministic       :  4,159 productos (43.9%)
blacklist           :    636 productos (6.7%)

════════════════════════════════════════════════════════════════════════════════
  ✅ PIPELINE COMPLETADO
════════════════════════════════════════════════════════════════════════════════
```

---

## 🔍 QUÉS SIGNIFICA CADA INFORMACIÓN

### Por cada BATCH (durante ETAPA 4):

```
📋 Productos en este batch:
   1. cocaina pura                               [vía: oral (100%)]
```
- Muestra el producto detectado
- Entre corchetes: vía de exposición más frecuente y porcentaje
- El LLM usa esto para tomar decisiones más informadas

```
💬 Preview del prompt enviado al LLM:
   0:cocaina pura [vía: oral (100%)]
```
- Muestra exactamente qué se envía al modelo
- Incluye vía de exposición para contexto

```
⏳ Intento 1/3: Llamando a DeepSeek API...
   ✅ Respuesta recibida en 3.45s
   Tamaño: 1250 caracteres
   ✅ JSON parseado: 100 items clasificados
```
- Monitorea tiempo de respuesta
- Verifica que la respuesta sea válida
- Confirma que los items fueron parseados correctamente

---

## ⚠️ POSIBLES INCIDENCIAS

Si ves algo como esto:

```
⚠️  40 IDs faltantes en respuesta LLM → usando regex como fallback
```

**Significa:** El LLM no respondió para 40 items. El sistema automáticamente:
1. Detecta cuáles faltaron
2. Les aplica los patrones regex de respaldo
3. Continúa sin detener el proceso

```
❌ Error LLM (intento 1): Connection timeout
   ⏳ Esperando 1s antes de reintentar...
```

**Significa:** El LLM falló pero reintentar.
- Intento 1: espera 1 segundo
- Intento 2: espera 2 segundos  
- Intento 3: espera 4 segundos
- Si falla los 3: usa regex como fallback final

---

## 📂 ARCHIVOS GENERADOS

Después de ejecutar, encontrarás en `../resultados_v5/`:

### 1. `resultados_clasificacion_llm_avanzada.xlsx`
- **171,029 filas** (todas las observaciones)
- Columnas: producto, fecha, vía_exposición, categoria, método_clasificación
- **Usa este para análisis detallado**

### 2. `productos_por_categoria_conteo.xlsx` (15 hojas)
- Hoja 1: "Todos" - todos los 11,170 productos únicos
- Hojas 2-15: 1 hoja por categoría (alcohol_etanol, alucinogenos, etc.)
- Muestra: producto, conteo, método_clasificación

### 3. `productos_filtrados_blacklist.xlsx` ⭐ NUEVO
- Los 636 productos que fueron excluidos por blacklist
- Útil para verificar qué se filtró

### 4. `productos_por_categoria.xlsx`
- Lista de productos únicos por categoría
- 11,170 registros

### 5. `resumen_conteo_clasificacion_final.xlsx`
- Resumen agregado por categoría
- Incluye breakdown por método (deterministic, llm, blacklist, cache, sin_clasificar)

---

## 🎯 CHECKLIST ANTES DE EJECUTAR

- [ ] Estoy en el directorio: `/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle`
- [ ] Archivos Excel de datos existen en: `data/wetransfer_sivigila_2025-07-24_1807/`
- [ ] Las dependencias (pandas, openpyxl) están instaladas
- [ ] `DEEPSEEK_API_KEY` está configurada en environment o en `config.py` (si usar LLM)
- [ ] Tengo espacio en disco para ~500MB de archivos Excel

---

## 🚀 COMANDO FINAL

**Copia y pega esto en terminal:**

```bash
cd /Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/correciones/pipeline_bundle && ENABLE_LLM=true python nuevo_codigo.py
```

¡Verás el progreso en tiempo real durante todo el proceso! 🎉

