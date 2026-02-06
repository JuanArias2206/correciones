# FRAGMENTOS PARA PASAR A REVISOR (ChatGPT) - COPY/PASTE READY

---

## FRAGMENTO 1: config.py - Nuevos parámetros

```python
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
```

---

## FRAGMENTO 2: llm_clients.py - Cambios a DeepSeekClient

```python
class DeepSeekClient:
    def __init__(self, api_key: str, model: str, base_url: str, timeout: int = 60, temperature: float = 0.0):
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY no está configurada")
        try:
            from openai import OpenAI
        except Exception as e:
            raise ImportError("Falta el paquete 'openai'. Instala con: pip install openai") from e
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        self._model = model
        self._temperature = temperature

    def generate(self, prompt: str) -> str:
        """
        Llama a DeepSeek con temperature configurable.
        Temperature=0.0 para máxima consistencia en clasificación.
        """
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self._temperature,
        )
        return resp.choices[0].message.content


def build_llm_client(
    provider: str,
    api_key: str,
    model: str,
    base_url: str = "https://api.deepseek.com",
    timeout: int = 60,
    temperature: float = 0.0,
) -> DeepSeekClient:
    """
    Construye un cliente DeepSeek. El parámetro provider debe ser 'deepseek'.
    """
    provider_norm = (provider or '').strip().lower()
    if provider_norm != 'deepseek':
        raise ValueError(f"Solo DeepSeek está soportado. Se recibió: {provider}")
    return DeepSeekClient(api_key=api_key, model=model, base_url=base_url, timeout=timeout, temperature=temperature)
```

---

## FRAGMENTO 3: cache_manager.py - COMPLETO

[Ver archivo cache_manager.py en el workspace - 200 líneas aprox]

---

## FRAGMENTO 4: deterministic_classifier.py - COMPLETO

[Ver archivo deterministic_classifier.py en el workspace - 150 líneas aprox]

---

## FRAGMENTO 5: nuevo_codigo.py - Imports y PipelineMetrics

```python
# -*- coding: utf-8 -*-
"""
PIPELINE DE CLASIFICACIÓN DE SUSTANCIAS PSICOACTIVAS (SPA) - OPTIMIZADO v2.0
=============================================================================
Versión mejorada con:
- Cache persistente (SQLite) para evitar re-clasificaciones
- Deterministic classifier (regex alta confianza) sin pasar por LLM (~40-50% ahorro)
- Batching dinámico por presupuesto de caracteres (prefix caching friendly)
- Respuesta JSON compacta del LLM (menos output tokens)
- Robustez mejorada (retry, fallbacks, logging de incidencias)
- Métricas de eficiencia (% filtrado, % cache, % deterministic, % LLM)
"""

import os
import re
import json
import time
import unicodedata
import warnings
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

import pandas as pd
from tqdm import tqdm

from llm_clients import build_llm_client
from cache_manager import CacheManager
from deterministic_classifier import DeterministicClassifier

# Importar módulos locales
from config import (
    BASE_DIR, LLM_DELAY_SECONDS, LLM_BATCH_SIZE, LLM_BATCH_BUDGET_CHARS,
    LLM_TIMEOUT_SECONDS, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, DEEPSEEK_BASE_URL,
    PROMPT_VERSION, CACHE_DB_PATH, ENABLE_CACHE, ENABLE_DETERMINISTIC,
    ENABLE_METRICS, LLM_TEMPERATURE,
    file_sheets_map, VIA_EXP_MAP, VIA_EXPOSI_MAP, TERMINOS_A_FILTRAR,
    CATEGORIAS_VALIDAS, OUTPUT_DIR
)
from patterns import compiled_patterns
from blacklists import (
    is_in_general_blacklist,
    filter_categories_with_blacklist
)

warnings.filterwarnings('ignore')

# =========================================================
# MÉTRICAS DE EJECUCIÓN GLOBAL
# =========================================================
class PipelineMetrics:
    """Rastreo de métricas de eficiencia."""
    def __init__(self):
        self.total_nombres = 0
        self.filtrados_pre_blacklist = 0
        self.clasificados_deterministic = 0
        self.recuperados_cache = 0
        self.enviados_llm = 0
        self.llm_calls_saved = 0
        self.tasa_otros_final = 0.0
    
    def report(self):
        print("\n" + "="*70)
        print("MÉTRICAS DE EFICIENCIA")
        print("="*70)
        print(f"Total nombres únicos: {self.total_nombres}")
        print(f"  → Pre-blacklist: {self.filtrados_pre_blacklist} ({100*self.filtrados_pre_blacklist/max(self.total_nombres,1):.1f}%)")
        print(f"  → Deterministic: {self.clasificados_deterministic} ({100*self.clasificados_deterministic/max(self.total_nombres,1):.1f}%)")
        print(f"  → Cache: {self.recuperados_cache} ({100*self.recuperados_cache/max(self.total_nombres,1):.1f}%)")
        print(f"  → LLM (únicamente): {self.enviados_llm} ({100*self.enviados_llm/max(self.total_nombres,1):.1f}%)")
        print(f"Llamadas LLM AHORRADAS: {self.llm_calls_saved} ({100*self.llm_calls_saved/max(self.total_nombres,1):.1f}%)")
        print(f"Tasa otros final: {self.tasa_otros_final:.2%}")
        print("="*70)
```

---

## FRAGMENTO 6: nuevo_codigo.py - build_llm_prompt_compact()

```python
# =========================================================
# 3) PROMPT COMPACTO Y CACHE-FRIENDLY (v2.0)
# =========================================================
def build_llm_prompt_compact(nombres_pro_lista: List[str]) -> Tuple[str, Dict[str, str]]:
    """
    Construye prompt COMPACTO (reduce ~50% output tokens):
    - Items SIEMPRE al final (para prefix caching)
    - Respuesta JSON compacta: [{"id":"1","c":["cocaina_y_derivados"]}]
    - Sin prosa, solo reglas críticas
    """
    id_to_nom_clean: Dict[str, str] = {str(i): clean_text(item) for i, item in enumerate(nombres_pro_lista)}
    
    prompt_txt = """Eres experto en toxicología clínica y vigilancia de SPA.
Clasifica en UNA O MÁS categorías (SOLO JSON compacto):
alucinogenos, cocaina_y_derivados, opioides, estimulantes, inhalantes, 
tranquilizantes_y_sedantes, alcohol_etanol, cannabinoides, escopolamina, PSA_no_clasificado_lista, otros

REGLAS CRÍTICAS (máxima prioridad):
1. Plaguicidas, limpieza, corrosivos, gases industriales → "otros"
2. Ácidos médicos (folico, valproico, sulfurico, muriático) → "otros"
3. Anestésicos locales (-caína): lidocaína, benzocaína → "otros" (¡no cocaína!)
4. Cafeína en analgésicos (aspirina+cafeína, sevedol) → "otros"
5. Antidepresivos puros sin contexto recreativo → "tranquilizantes_y_sedantes" o "otros"
6. Bebidas energéticas sin SPA → "otros"
7. SPA obvias: cocaína/crack/bazuco, marihuana/cannabis/THC, heroína/fentanilo, 
   metanfetamina/anfetamina, cerveza/vino/aguardiente, benzodiacepinas comunes

RESPUESTA (SOLO esto, sin explicación):
[{"id":"0","c":["cocaina_y_derivados"]},{"id":"1","c":["otros"]}]

Items a clasificar:"""
    
    for item_id, nom_clean in id_to_nom_clean.items():
        prompt_txt += f'\n- {item_id}: {nom_clean}'
    
    return prompt_txt, id_to_nom_clean


def build_llm_prompt(nombres_pro_lista: List[str]) -> Tuple[str, Dict[str, str]]:
    """Alias para compatibilidad."""
    return build_llm_prompt_compact(nombres_pro_lista)
```

---

## FRAGMENTO 7: nuevo_codigo.py - parse_llm_json_compact()

```python
# =========================================================
# 4) PARSEO DE JSON COMPACTO DEL LLM
# =========================================================
def parse_llm_json_compact(texto_respuesta: str) -> List[Dict[str, Any]]:
    """
    Parsea respuesta compacta:
    [{"id":"1","c":["cocaina_y_derivados"]}]
    (c = categorías)
    """
    raw = texto_respuesta.strip() if texto_respuesta else ""
    
    # Elimina fences si existen
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl+1:]
        if raw.endswith("```"):
            raw = raw[:-3]
    raw = re.sub(r'^\s*json\s*', '', raw, flags=re.IGNORECASE).strip()
    
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "resultados" in data:
            # Modo antiguo: {"resultados": [...]}
            return data["resultados"]
        elif isinstance(data, list):
            # Modo compacto: [...]
            return data
        else:
            raise ValueError(f"Formato inesperado: {type(data)}")
    except Exception as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"   Raw (primeros 200 chars): {raw[:200]}")
        return []


def parse_llm_json(texto_respuesta: str) -> List[Dict[str, Any]]:
    """Wrapper para compatibilidad."""
    return parse_llm_json_compact(texto_respuesta)
```

---

## FRAGMENTO 8: nuevo_codigo.py - DynamicBatchLLMClassifier

```python
# =========================================================
# 5) CLASIFICACIÓN LLM CON BATCHING DINÁMICO
# =========================================================
class DynamicBatchLLMClassifier:
    """
    Optimizado para:
    - Batching dinámico por presupuesto de caracteres
    - Retry con exponential backoff
    - Fallback a regex para faltantes
    """
    def __init__(self, llm_client, delay_seconds=5, max_retries=3, budget_chars=8000):
        self.llm_client = llm_client
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.budget_chars = budget_chars
        self.incidencias = defaultdict(int)
    
    def _estimate_batch_size(self, nombres_list: List[str]) -> int:
        """Estima cuántos nombres caben en presupuesto de caracteres."""
        prompt_base = 1100  # aprox base del prompt compacto
        available = self.budget_chars - prompt_base
        if not nombres_list:
            return 0
        
        avg_chars = sum(len(n) for n in nombres_list[:min(10, len(nombres_list))]) / min(10, len(nombres_list))
        chars_per_item = avg_chars + 8  # "- ID: " overhead
        batch_size = max(1, available // chars_per_item)
        return min(batch_size, LLM_BATCH_SIZE)
    
    def classify_batch(self, nombres_pro_lista: List[str]) -> Dict[str, List[str]]:
        """Clasifica con retry y fallbacks."""
        if not nombres_pro_lista:
            return {}
        
        dynamic_batch_size = self._estimate_batch_size(nombres_pro_lista)
        all_results = {}
        
        for batch_start in range(0, len(nombres_pro_lista), dynamic_batch_size):
            batch_end = min(batch_start + dynamic_batch_size, len(nombres_pro_lista))
            batch_items = nombres_pro_lista[batch_start:batch_end]
            
            llm_prompt, id_to_nom_clean = build_llm_prompt_compact(batch_items)
            input_ids = set(id_to_nom_clean.keys())
            
            success = False
            for attempt in range(self.max_retries):
                try:
                    time.sleep(self.delay_seconds)
                    texto_llm = self.llm_client.generate(llm_prompt)
                    resultados = parse_llm_json_compact(texto_llm)
                    
                    mapeo_batch = {}
                    ids_vistos = set()
                    
                    for r in resultados:
                        item_id = str(r.get('id', '')).strip()
                        if not item_id or item_id not in id_to_nom_clean:
                            self.incidencias['id_invalido'] += 1
                            continue
                        
                        ids_vistos.add(item_id)
                        nom_clean = id_to_nom_clean[item_id]
                        cats = r.get('c', ['otros'])  # Formato compacto
                        
                        if not isinstance(cats, list) or not cats:
                            cats = ['otros']
                        
                        # Validar categorías
                        cats = [c for c in cats if c in CATEGORIAS_VALIDAS] or ['otros']
                        mapeo_batch[nom_clean] = cats
                    
                    # IDs faltantes -> regex fallback
                    ids_faltantes = input_ids - ids_vistos
                    if ids_faltantes:
                        self.incidencias['ids_faltantes'] += len(ids_faltantes)
                        for mid in ids_faltantes:
                            nom = id_to_nom_clean[mid]
                            mapeo_batch[nom] = classify_substance_regex(nom)
                    
                    all_results.update(mapeo_batch)
                    success = True
                    break
                    
                except Exception as e:
                    self.incidencias['error_llm'] += 1
                    print(f"⚠️  Error LLM (intento {attempt+1}): {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
            
            if not success:
                # Fallback final a regex para TODO el batch
                print(f"⚠️  Batch {batch_start}-{batch_end} falló. Usando regex.")
                for nom in batch_items:
                    all_results[clean_text(nom)] = classify_substance_regex(nom)
        
        return all_results


# Alias para compatibilidad
LLMClassifier = DynamicBatchLLMClassifier
```

---

## FRAGMENTO 9: nuevo_codigo.py - run_pipeline() COMPLETO REFACTORIZADO

[Ver archivo nuevo_codigo.py en el workspace - función run_pipeline() refactorizada - ~180 líneas]

---

# PREGUNTA PARA CHATGPT

Copia y pega esto en ChatGPT:

---

**PREGUNTA:**

> He refactorizado mi pipeline de clasificación de sustancias psicoactivas para reducir costos de LLM en un 60-70%.
> 
> Los cambios principales son:
> 1. **Cache persistente (SQLite)** con versionado automático
> 2. **Deterministic classifier** (regex de alta confianza) para detectar SPA obvia sin LLM
> 3. **Batching dinámico** por presupuesto de caracteres (prefix caching)
> 4. **Respuesta JSON compacta** (50% menos output tokens)
> 5. **Robustez mejorada** (retry, fallbacks, logging)
> 6. **Métricas de eficiencia** 
> 
> **Cambios a los archivos:**
> - config.py: +7 parámetros nuevos (ENABLE_CACHE, ENABLE_DETERMINISTIC, PROMPT_VERSION, etc.)
> - llm_clients.py: + parámetro temperature (0.0 para consistencia)
> - nuevo_codigo.py: + clases PipelineMetrics, DynamicBatchLLMClassifier; reescrita run_pipeline()
> - cache_manager.py: (NUEVO) SQLite con versionado
> - deterministic_classifier.py: (NUEVO) Regex de alta confianza
> 
> **Mi preocupación principal:** ¿Esta optimización mantiene la RIGUROSIDAD CLÍNICA?
> Específicamente:
> 
> 1. ¿El JSON compacto (["id":"1","c":["cocaina_y_derivados"]]) vs verbose pierde información?
> 2. ¿El deterministic classifier es demasiado conservador/agresivo? (solo triggers fuertes como "cocaína", "marihuana", "heroína")
> 3. ¿El cache versionado evita inconsistencias si el prompt cambia?
> 4. ¿El fallback a regex cuando el LLM falla (3 intentos) es clínicamente aceptable?
> 5. ¿Temperature=0.0 es correcto para clasificación toxicológica?
> 
> **Contexto:**
> - 11 categorías de SPA válidas
> - Pre-filtro (blacklist general) para plaguicidas/limpieza/corrosivos
> - Post-filtro (blacklist por categoría)
> - Validación por vía de exposición (inhalantes=respiratoria, alcohol=oral)
> - Reglas clínicas muy específicas en el prompt (ej: benzocaína NO es cocaína, cafeína en analgésicos NO es estimulante)
> 
> ¿Ves algún riesgo en estos cambios? ¿Hay algo que debería ajustar?

---

Espera la respuesta del revisor y ajusta según sus comentarios.

---

**Fin del documento de copy/paste**
