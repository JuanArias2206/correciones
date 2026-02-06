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
    ENABLE_METRICS, LLM_TEMPERATURE, TEST_PERCENTAGE, TEST_MODE,
    logger, METRICS,  # ← Nuevo: logger y métricas globales
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

# =========================================================
# 1) CONFIGURACIÓN DEL CLIENTE DEEPSEEK
# =========================================================
def build_llm_client_from_config():
    if not DEEPSEEK_API_KEY:
        raise ValueError(
            "\n❌ DEEPSEEK_API_KEY NO CONFIGURADA\n\n"
            "Agrega tu key en uno de estos lugares:\n"
            "  1. pipeline_bundle/config_local.py:\n"
            "     DEEPSEEK_API_KEY = 'sk-90b9c21e412447b188162cab53fad814'\n\n"
            "  2. Variable de entorno:\n"
            "     export DEEPSEEK_API_KEY='sk-...'"
        )
    return build_llm_client(
        provider='deepseek',
        api_key=DEEPSEEK_API_KEY,
        model=DEEPSEEK_MODEL,
        base_url=DEEPSEEK_BASE_URL,
        timeout=LLM_TIMEOUT_SECONDS,
        temperature=LLM_TEMPERATURE
    )

# =========================================================
# 2) UTILIDADES DE NORMALIZACIÓN
# =========================================================
def normalize_column_name(col_name: str) -> str:
    col_name = col_name.lower()
    col_name = re.sub(r'[\s\.\-]+', '_', col_name)
    col_name = (col_name.replace('á', 'a').replace('é', 'e').replace('í', 'i')
                .replace('ó', 'o').replace('ú', 'u')
                .replace('ñ', 'n').replace('√≠', 'i'))
    return col_name


def strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', s) if not unicodedata.combining(c))


def clean_text(x) -> str:
    if pd.isna(x):
        return 'desconocido'
    s = str(x).strip().lower()
    s = strip_accents(s)
    s = re.sub(r'\s+', ' ', s)
    return s if s else 'desconocido'


def classify_substance_regex(nom_pro_text: str) -> List[str]:
    """Clasificación usando patrones regex (importados de patterns.py)"""
    if not isinstance(nom_pro_text, str):
        return ['desconocido']
    text = clean_text(nom_pro_text)
    found_groups = [group for group, pat in compiled_patterns.items() if pat.search(text)]
    return found_groups if found_groups else ['otros']

def parse_route_value(v: Any) -> Optional[int]:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if s == '':
        return None
    try:
        n = int(float(s))
        return n
    except:
        pass
    s_norm = clean_text(s)
    if s_norm.startswith("resp"): return 1
    if s_norm.startswith("oral") or "boca" in s_norm: return 2
    if s_norm.startswith("derm") or "mucosa" in s_norm: return 3
    if s_norm.startswith("ocu"): return 4
    if "desconoc" in s_norm: return 5
    if (s_norm.startswith("parent") or "intraven" in s_norm or "intramus" in s_norm or
            "subcut" in s_norm or "intraperit" in s_norm): return 6
    if "transplacen" in s_norm: return 7
    return None


def unify_route_columns(df: pd.DataFrame) -> pd.DataFrame:
    route_col = None
    if 'via_exp' in df.columns:
        route_col = 'via_exp'
    elif 'via_exposi' in df.columns:
        route_col = 'via_exposi'
    df['via_exposicion_col'] = route_col if route_col else None

    def map_code(val, colname):
        code = parse_route_value(val)
        if code is None: return None, None
        if colname == 'via_exp':
            text = VIA_EXP_MAP.get(code)
        elif colname == 'via_exposi':
            text = VIA_EXPOSI_MAP.get(code)
        else:
            text = VIA_EXP_MAP.get(code) or VIA_EXPOSI_MAP.get(code)
        return code, text

    if route_col:
        codes_texts = df[route_col].apply(lambda v: map_code(v, route_col))
        df['via_exposicion_codigo'] = codes_texts.apply(lambda x: x[0])
        df['via_exposicion_texto']  = codes_texts.apply(lambda x: x[1])
    else:
        df['via_exposicion_codigo'] = None
        df['via_exposicion_texto']  = None
    return df


def is_inhaled_route(code: Optional[int]) -> bool:
    return code == 1  # respiratoria


def is_oral_route(code: Optional[int]) -> bool:
    return code == 2  # oral

# =========================================================
# 3) PROMPT COMPACTO Y CACHE-FRIENDLY (v2.0)
# =========================================================
def build_llm_prompt_compact(nombres_pro_lista: List[str]) -> Tuple[str, Dict[str, str]]:
    """
    Construye prompt COMPACTO (reduce ~50% output tokens):
    - Items SIEMPRE al final (para prefix caching)
    - Respuesta JSON compacta: [{"id":"1","c":["cocaina_y_derivados"]}]
    - Sin prosa, solo reglas críticas y falsos positivos conocidos
    - Temperature=0.0 para máxima consistencia
    """
    id_to_nom_clean: Dict[str, str] = {str(i): clean_text(item) for i, item in enumerate(nombres_pro_lista)}
    
    prompt_txt = """Experto en SPA. Clasifica en UNA O MÁS categorías SOLAMENTE si hay evidencia explícita.
Respuesta SOLO JSON compacto: [{"id":"0","c":["cocaina_y_derivados"]}]

CATEGORÍAS: alucinogenos, cocaina_y_derivados, opioides, estimulantes, inhalantes, 
tranquilizantes_y_sedantes, alcohol_etanol, cannabinoides, escopolamina, PSA_no_clasificado_lista, otros

FALSOS POSITIVOS CRÍTICOS (EXCLUIR → "otros"):
- Hioscina/butilbromuro de hioscina → NUNCA escopolamina ni tranquilizantes → "otros"
- Difenhidramina/dimenhidrinato/dramamine → "otros" (NO tranquilizantes)
- Melatonina/valeriana/pasiflora → "otros" (NO tranquilizantes)
- Tizanidina/hidroxizina/hidroxicina → "otros" (NO tranquilizantes)
- Loperamida/naloxona/naltrexone → "otros" (NO opioides)
- Cafeína SOLA o en analgésicos (aspirina+cafeína, acetaminofén+cafeína) → "otros" (NO estimulantes)
- Únicamente "amina" genérica → "otros" (NO estimulantes; excepción: anfetamina/metanfetamina)
- Gas genérico/propano/butano/helio/dióxido/sulfuro → "otros" (NO inhalantes; excepción: thinner/sacol/poppers)
- Plaguicidas/herbicidas/productos agrícolas (rafaga, sicario, arriero, awake 500, etc.) → "otros"
- Productos limpieza/corrosivos/ácidos industriales → "otros"

REGLAS POSITIVAS (DEBEN ir a categoría si presente):
- Cocaína/crack/bazuco/perico → cocaina_y_derivados
- Marihuana/cannabis/THC/bareto/cripa → cannabinoides
- Heroína/fentanilo/morfina/tramadol/oxicontin → opioides (excepto: loperamida, naloxona)
- Anfetamina/metanfetamina/metilfenidato/ritalin/adderall/crystal → estimulantes
- Cerveza/vino/aguardiente/ron/whisky/vodka/etanol → alcohol_etanol
- Benzodiacepinas (clonazepam/alprazolam/diazepam/lorazepam) → tranquilizantes_y_sedantes
- LSD/DMT/psilocibina/MDMA/2CB/tusi/mescalina → alucinogenos
- Thinner/sacol/pegante/varsol/poppers (inhalables) → inhalantes
- Escopolamina/burundanga (SIN hioscina) → escopolamina

REGLA FINAL: Si NO hay trigger explícito de SPA → "otros". Preferir "otros" ante duda.

Items:"""
    
    for item_id, nom_clean in id_to_nom_clean.items():
        prompt_txt += f'\n{item_id}:{nom_clean}'
    
    return prompt_txt, id_to_nom_clean


def build_llm_prompt(nombres_pro_lista: List[str]) -> Tuple[str, Dict[str, str]]:
    """Alias para compatibilidad."""
    return build_llm_prompt_compact(nombres_pro_lista)

# 4) PARSEO DE JSON COMPACTO DEL LLM (ROBUSTO)
# =========================================================
def parse_llm_json_compact(texto_respuesta: str) -> List[Dict[str, Any]]:
    """
    Parsea respuesta compacta O antigua:
    - Compacta: [{"id":"1","c":["cocaina_y_derivados"]}]
    - Antigua: {"resultados":[{"id":"1","entrada":"...","categorias_clasificadas":[...]}]}
    
    Robusto ante:
    - Fences (```)
    - Espacios/newlines
    - Categorías inválidas (valida contra CATEGORIAS_VALIDAS)
    - IDs faltantes (fallback regex)
    """
    raw = texto_respuesta.strip() if texto_respuesta else ""
    
    # Elimina fences ``` si existen
    if raw.startswith("```"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            raw = raw[first_nl+1:]
        if raw.endswith("```"):
            raw = raw[:-3]
    
    # Elimina "json" prefix si aparece
    raw = re.sub(r'^\s*json\s*', '', raw, flags=re.IGNORECASE).strip()
    
    try:
        data = json.loads(raw)
        
        if isinstance(data, dict) and "resultados" in data:
            # Modo antiguo: {"resultados": [...]}
            resultados = data["resultados"]
        elif isinstance(data, list):
            # Modo compacto: [...]
            resultados = data
        else:
            raise ValueError(f"Formato inesperado: {type(data)}")
        
        # Normaliza resultado compacto a formato interno consistente
        normalized = []
        for item in resultados:
            if isinstance(item, dict):
                item_id = str(item.get("id", "")).strip()
                
                # Detecta si es compacto (clave "c") o antiguo (clave "categorias_clasificadas")
                cats = item.get("c", item.get("categorias_clasificadas", []))
                if isinstance(cats, str):
                    cats = [cats]
                
                # Valida categorías contra CATEGORIAS_VALIDAS
                valid_cats = [cat for cat in cats if cat in CATEGORIAS_VALIDAS]
                if not valid_cats:
                    valid_cats = ["otros"]
                
                normalized.append({
                    "id": item_id,
                    "c": valid_cats  # Usa siempre "c" internamente
                })
        
        return normalized if normalized else []
        
    except Exception as e:
        print(f"⚠️  Error parsing JSON compacto: {e}")
        print(f"   Raw (primeros 200 chars): {raw[:200]}")
        return []


def parse_llm_json(texto_respuesta: str) -> List[Dict[str, Any]]:
    """Alias para compatibilidad."""
    return parse_llm_json_compact(texto_respuesta)

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

# =========================================================
# 6) PIPELINE MODULAR
# =========================================================
class DataLoader:
    def __init__(self, sheets_map: Dict[str, Dict[str, str]]):
        self.sheets_map = sheets_map

    def load(self) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
        individual_dfs: Dict[str, pd.DataFrame] = {}
        all_processed_dfs: List[pd.DataFrame] = []

        print("--- Iniciando carga y pre-procesamiento de todos los datasets ---")
        for file_path, sheets_info in self.sheets_map.items():
            for sheet_name, _ in sheets_info.items():
                df_name_key = f"df_{sheet_name}"
                print(f"\nCargando y normalizando hoja: '{sheet_name}' del archivo '{file_path}'")
                temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
                temp_df['origen_hoja'] = sheet_name
                temp_df.columns = [normalize_column_name(col) for col in temp_df.columns]

                if 'nom_pro' in temp_df.columns:
                    temp_df['nom_pro'] = temp_df['nom_pro'].fillna('desconocido').apply(clean_text)
                    temp_df.loc[temp_df['nom_pro'].isin(TERMINOS_A_FILTRAR), 'nom_pro'] = 'otros'
                    temp_df = unify_route_columns(temp_df)

                    individual_dfs[df_name_key] = temp_df
                    all_processed_dfs.append(temp_df)
                else:
                    print(f"Advertencia: La columna 'nom_pro' no existe en la hoja '{sheet_name}'. Se omite.")

        if not all_processed_dfs:
            raise ValueError("No se encontraron DataFrames para procesar.")

        print("\n--- Consolidando todos los DataFrames ---")
        df_consolidado = pd.concat(all_processed_dfs, ignore_index=True, sort=False)
        return df_consolidado, individual_dfs


class Profiler:
    def profile(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_rows = len(df)
        unique_nom = df['nom_pro'].nunique() if 'nom_pro' in df.columns else 0
        stats = {
            'total_rows': total_rows,
            'unique_nom_pro': unique_nom
        }
        print(f"\n[Profiler] total_rows={total_rows}, unique_nom_pro={unique_nom}")
        return stats


class PreFilter:
    def apply(self, nombres_unicos: List[str]) -> Tuple[List[str], List[str]]:
        nombres_para_llm = []
        nombres_otros_directos = []
        for nombre in nombres_unicos:
            if is_in_general_blacklist(nombre):
                nombres_otros_directos.append(nombre)
            else:
                nombres_para_llm.append(nombre)
        return nombres_para_llm, nombres_otros_directos


class PostFilter:
    def apply(self, nom_pro: str, cats: List[str]) -> List[str]:
        return filter_categories_with_blacklist(nom_pro, cats)


class Validator:
    def apply(self, row: pd.Series) -> List[str]:
        cats = row['grupos_sustancia_final']
        code = row.get('via_exposicion_codigo', None)
        final_cats = list(cats)

        if 'inhalantes' in final_cats and code is not None and not is_inhaled_route(code):
            final_cats.remove('inhalantes')
        if 'alcohol_etanol' in final_cats and code is not None and not is_oral_route(code):
            final_cats.remove('alcohol_etanol')

        return final_cats if final_cats else ['otros']


class Exporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def save_blacklist(self, nombres_otros_directos: List[str], df_consolidado: pd.DataFrame) -> None:
        if not nombres_otros_directos:
            return
        df_blacklist = pd.DataFrame({
            'nombre_producto': nombres_otros_directos,
            'razon': 'Filtrado por blacklist general (plaguicidas/limpieza/corrosivos)'
        })
        conteos = df_consolidado[df_consolidado['nom_pro'].isin(nombres_otros_directos)]['nom_pro'].value_counts()
        df_blacklist['frecuencia'] = df_blacklist['nombre_producto'].map(conteos)
        df_blacklist = df_blacklist.sort_values('frecuencia', ascending=False)

        blacklist_output_path = os.path.join(self.output_dir, 'productos_filtrados_blacklist.xlsx')
        os.makedirs(os.path.dirname(blacklist_output_path), exist_ok=True)
        df_blacklist.to_excel(blacklist_output_path, index=False)
        print("  → Lista de productos filtrados guardada en: productos_filtrados_blacklist.xlsx")

    def save_outputs(self, df_consolidado: pd.DataFrame) -> None:
        columnas_base = [
            'origen_hoja', 'fec_not', 'cod_depto_o', 'cod_mun_o', 'sexo', 'edad', 'cod_pais',
            'nom_pro', 'via_exposicion_col', 'via_exposicion_codigo', 'via_exposicion_texto',
            'grupos_sustancia_final', 'grupos_sustancia_filtrado'
        ]
        columnas_existentes = [c for c in columnas_base if c in df_consolidado.columns]
        df_filtrado = df_consolidado[columnas_existentes]

        os.makedirs(self.output_dir, exist_ok=True)
        output_path_principal = os.path.join(self.output_dir, 'resultados_clasificacion_llm_avanzada.xlsx')
        output_path_resumen = os.path.join(self.output_dir, 'resumen_clasificacion_avanzada.xlsx')

        try:
            df_filtrado.to_excel(output_path_principal, index=False)
            print(f"\nDataFrame principal guardado exitosamente en: {output_path_principal}")
        except Exception as e:
            print(f"\nError al guardar el archivo Excel principal: {e}")

        print("\n--- Generando y guardando el archivo de resumen ---")
        all_filtered_categories = set(cat for sublist in df_consolidado['grupos_sustancia_filtrado'] for cat in sublist)
        resumen_data = []
        for sheet in df_consolidado['origen_hoja'].unique():
            df_sheet = df_consolidado[df_consolidado['origen_hoja'] == sheet]
            for cat in all_filtered_categories:
                conteo = df_sheet['grupos_sustancia_filtrado'].apply(lambda x: cat in x).sum()
                resumen_data.append({
                    'origen_hoja': sheet,
                    'grupo_sustancia_final': cat,
                    'conteo': conteo
                })

        df_resumen = pd.DataFrame(resumen_data)
        df_resumen = df_resumen.sort_values(by=['origen_hoja', 'conteo'], ascending=[True, False])

        try:
            df_resumen.to_excel(output_path_resumen, index=False)
            print(f"Archivo de resumen guardado exitosamente en: {output_path_resumen}")
        except Exception as e:
            print(f"Error al guardar el archivo de resumen: {e}")


def run_pipeline() -> None:
    """Pipeline optimizado con caché, deterministic, y métricas."""
    try:
        print("\n" + "="*70)
        print("PIPELINE OPTIMIZADO v2.0 - REDUCCIÓN DE COSTOS LLM")
        print("="*70)
        print(f"Caché: {ENABLE_CACHE} | Deterministic: {ENABLE_DETERMINISTIC} | Métricas: {ENABLE_METRICS}")
        
        metrics = PipelineMetrics() if ENABLE_METRICS else None
        
        # Inicializar componentes
        llm_client = build_llm_client_from_config()
        llm_classifier = DynamicBatchLLMClassifier(
            llm_client,
            delay_seconds=LLM_DELAY_SECONDS,
            budget_chars=LLM_BATCH_BUDGET_CHARS
        )
        
        cache_mgr = None
        if ENABLE_CACHE:
            cache_mgr = CacheManager(CACHE_DB_PATH, PROMPT_VERSION)
        
        deterministic_clf = None
        if ENABLE_DETERMINISTIC:
            deterministic_clf = DeterministicClassifier(use_strong_confidence_only=True)
        
        data_loader = DataLoader(file_sheets_map)
        profiler = Profiler()
        pre_filter = PreFilter()
        post_filter = PostFilter()
        validator = Validator()
        exporter = Exporter(OUTPUT_DIR)

        # Cargar datos
        df_consolidado, _ = data_loader.load()
        profiler.profile(df_consolidado)

        nombres_unicos_a_clasificar = df_consolidado['nom_pro'].unique().tolist()
        nombres_unicos_a_clasificar = [n for n in nombres_unicos_a_clasificar if n not in ['otros', 'desconocido']]
        
        if metrics:
            metrics.total_nombres = len(nombres_unicos_a_clasificar)

        # ETAPA 1: Pre-filtro
        nombres_para_llm, nombres_otros_directos = pre_filter.apply(nombres_unicos_a_clasificar)
        if metrics:
            metrics.filtrados_pre_blacklist = len(nombres_otros_directos)
        
        print(f"\n[ETAPA 1] Pre-filtro (blacklist general):")
        print(f"  Total: {len(nombres_unicos_a_clasificar)}")
        print(f"  → Filtrados: {len(nombres_otros_directos)}")
        print(f"  → Continúan: {len(nombres_para_llm)}")

        exporter.save_blacklist(nombres_otros_directos, df_consolidado)
        mapeo_llm: Dict[str, List[str]] = {nombre: ['otros'] for nombre in nombres_otros_directos}

        # ETAPA 2: Deterministic
        nombres_ambiguos = nombres_para_llm
        if ENABLE_DETERMINISTIC and deterministic_clf:
            print(f"\n[ETAPA 2] Deterministic classifier (regex alta confianza):")
            deterministic_results = deterministic_clf.classify_batch(nombres_para_llm)
            nombres_ambiguos = deterministic_clf.get_unclassified(nombres_para_llm)
            
            if metrics:
                metrics.clasificados_deterministic = len(deterministic_results)
            
            mapeo_llm.update(deterministic_results)
            print(f"  → Clasificados: {len(deterministic_results)}")
            print(f"  → Quedan ambiguos: {len(nombres_ambiguos)}")

        # ETAPA 3: Cache
        nombres_sin_cache = nombres_ambiguos
        if ENABLE_CACHE and cache_mgr:
            print(f"\n[ETAPA 3] Caché persistente (v={PROMPT_VERSION}):")
            cache_hits, nombres_sin_cache = cache_mgr.get_batch(nombres_ambiguos)
            
            if metrics:
                metrics.recuperados_cache = len(cache_hits)
            
            mapeo_llm.update(cache_hits)
            print(f"  → Cache hits: {len(cache_hits)}")
            print(f"  → Sin caché: {len(nombres_sin_cache)}")

        # ETAPA 4: LLM
        if nombres_sin_cache:
            print(f"\n[ETAPA 4] Clasificación LLM (DeepSeek):")
            if metrics:
                metrics.enviados_llm = len(nombres_sin_cache)
            
            mapeo_llm_nuevo = llm_classifier.classify_batch(nombres_sin_cache)
            mapeo_llm.update(mapeo_llm_nuevo)
            
            if ENABLE_CACHE and cache_mgr:
                cache_mgr.set_batch(mapeo_llm_nuevo)
                print(f"  → Guardados en caché: {len(mapeo_llm_nuevo)}")
            
            if llm_classifier.incidencias:
                print(f"\n  Incidencias:")
                for inc_type, count in llm_classifier.incidencias.items():
                    print(f"    - {inc_type}: {count}")
        else:
            print(f"\n[ETAPA 4] LLM: OMITIDO (todos en caché/deterministic)")

        if metrics:
            metrics.llm_calls_saved = (
                len(nombres_otros_directos) +
                (len(deterministic_results) if ENABLE_DETERMINISTIC else 0) +
                (len(cache_hits) if ENABLE_CACHE else 0)
            )

        # ETAPA 5: Post-filtro y validación
        print(f"\n[ETAPA 5] Post-filtro y validación...")

        def get_final_classification(nom_pro: str) -> List[str]:
            if nom_pro in ['otros', 'desconocido']:
                return ['otros']
            if is_in_general_blacklist(nom_pro):
                return ['otros']

            llm_cats = mapeo_llm.get(nom_pro, ['otros'])
            if llm_cats == ['otros'] or not llm_cats:
                cats = classify_substance_regex(nom_pro)
            else:
                cats = llm_cats

            cats = post_filter.apply(nom_pro, cats)
            return cats if cats else ['otros']

        df_consolidado['grupos_sustancia_final'] = df_consolidado['nom_pro'].apply(get_final_classification)

        all_final_categories = set(cat for sublist in df_consolidado['grupos_sustancia_final'] for cat in sublist)
        for cat in all_final_categories:
            df_consolidado[f'es_{cat}'] = df_consolidado['grupos_sustancia_final'].apply(
                lambda x: 1 if cat in x else 0
            )

        df_consolidado['grupos_sustancia_filtrado'] = df_consolidado.apply(validator.apply, axis=1)

        # ETAPA 6: Exportar
        print(f"\n[ETAPA 6] Exportando resultados...")
        exporter.save_outputs(df_consolidado)

        # Métricas finales
        if ENABLE_METRICS and metrics:
            total_rows = len(df_consolidado)
            otros_count = df_consolidado['grupos_sustancia_final'].apply(lambda x: 'otros' in x).sum()
            metrics.tasa_otros_final = otros_count / total_rows if total_rows > 0 else 0
            metrics.report()

        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETADO")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        raise


# =========================================================
# 7) PRUEBAS DE VALIDACIÓN - FALSOS POSITIVOS CONOCIDOS
# =========================================================
def test_cases():
    """
    Pruebas mínimas para validar que NO hay falsos positivos críticos.
    Corre deterministic classifier + post-filter logic.
    """
    print("\n" + "="*70)
    print("PRUEBAS DE VALIDACIÓN - FALSOS POSITIVOS")
    print("="*70)
    
    det_clf = DeterministicClassifier(use_strong_confidence_only=True)
    
    test_cases_negative = [
        ("hioscina", ["otros"], "Hioscina NO debe ser escopolamina ni tranquilizantes"),
        ("butilbromuro de hioscina", ["otros"], "Butilbromuro de hioscina NO debe ser tranquilizantes"),
        ("difenhidramina", ["otros"], "Difenhidramina NO debe ser tranquilizantes"),
        ("dimenhidrinato", ["otros"], "Dimenhidrinato NO debe ser tranquilizantes"),
        ("dramamine", ["otros"], "Dramamine NO debe ser tranquilizantes"),
        ("melatonina", ["otros"], "Melatonina NO debe ser tranquilizantes"),
        ("valeriana", ["otros"], "Valeriana NO debe ser tranquilizantes"),
        ("pasiflora", ["otros"], "Pasiflora NO debe ser tranquilizantes"),
        ("tizanidina", ["otros"], "Tizanidina NO debe ser tranquilizantes"),
        ("hidroxizina", ["otros"], "Hidroxizina NO debe ser tranquilizantes"),
        ("loperamida", ["otros"], "Loperamida NO debe ser opioides"),
        ("naloxona", ["otros"], "Naloxona NO debe ser opioides"),
        ("naltrexone", ["otros"], "Naltrexone NO debe ser opioides"),
        ("cafeina", ["otros"], "Cafeína sola NO debe ser estimulantes"),
        ("aspirina cafeina", ["otros"], "Aspirina+cafeína NO debe ser estimulantes"),
        ("acetaminofen cafeina", ["otros"], "Acetaminofén+cafeína NO debe ser estimulantes"),
        ("gas butano", ["otros"], "Gas butano NO debe ser inhalantes"),
        ("gas propano", ["otros"], "Gas propano NO debe ser inhalantes"),
        ("dióxido de carbono", ["otros"], "CO2 NO debe ser inhalantes"),
        ("helio", ["otros"], "Helio NO debe ser inhalantes"),
    ]
    
    test_cases_positive = [
        ("cocaina", ["cocaina_y_derivados"], "Cocaína DEBE ser cocaína"),
        ("crack", ["cocaina_y_derivados"], "Crack DEBE ser cocaína"),
        ("marihuana", ["cannabinoides"], "Marihuana DEBE ser cannabinoides"),
        ("cannabis", ["cannabinoides"], "Cannabis DEBE ser cannabinoides"),
        ("thc", ["cannabinoides"], "THC DEBE ser cannabinoides"),
        ("heroína", ["opioides"], "Heroína DEBE ser opioides"),
        ("fentanilo", ["opioides"], "Fentanilo DEBE ser opioides"),
        ("clonazepam", ["tranquilizantes_y_sedantes"], "Clonazepam DEBE ser tranquilizantes"),
        ("alprazolam", ["tranquilizantes_y_sedantes"], "Alprazolam DEBE ser tranquilizantes"),
        ("cerveza", ["alcohol_etanol"], "Cerveza DEBE ser alcohol"),
        ("thinner", ["inhalantes"], "Thinner DEBE ser inhalantes"),
        ("sacol", ["inhalantes"], "Sacol DEBE ser inhalantes"),
    ]
    
    passed = 0
    failed = 0
    
    print("\n1. PRUEBAS NEGATIVAS (NO deben ser SPA o estar en otras categorías):")
    for nom, expected_cats, description in test_cases_negative:
        # Deterministic
        det_result = det_clf.classify(nom)
        if det_result is None:
            det_result = ['otros']
        
        # Post-filter
        final_cats = filter_categories_with_blacklist(nom, det_result)
        
        # Validación
        if final_cats == expected_cats or (expected_cats == ["otros"] and final_cats == ["otros"]):
            print(f"   ✅ {nom}: {final_cats} - {description}")
            passed += 1
        else:
            print(f"   ❌ {nom}: ESPERADO {expected_cats}, GOT {final_cats} - {description}")
            failed += 1
    
    print("\n2. PRUEBAS POSITIVAS (DEBEN ser SPA en categoría específica):")
    for nom, expected_cats, description in test_cases_positive:
        # Deterministic (si está disponible)
        det_result = det_clf.classify(nom)
        
        if det_result is not None:
            final_cats = det_result
        else:
            final_cats = ["otros"]  # Si deterministic no lo detenta, iría al LLM en producción
        
        # Validación: al menos una categoría correcta
        has_correct = any(cat in expected_cats for cat in final_cats)
        
        if has_correct:
            print(f"   ✅ {nom}: {final_cats} - {description}")
            passed += 1
        else:
            print(f"   ❌ {nom}: ESPERADO {expected_cats}, GOT {final_cats} - {description}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTADOS: {passed} pasadas, {failed} fallidas")
    print("="*70)
    
    if failed > 0:
        print(f"\n⚠️  {failed} pruebas fallaron. Revisar blacklists o deterministic patterns.")
        return False
    else:
        print(f"\n✅ Todas las pruebas pasaron.")
        return True


if __name__ == '__main__':
    # Descomentar para ejecutar pruebas de validación
    # test_cases()
    
    # Ejecutar pipeline principal
    run_pipeline()
