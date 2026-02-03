# -*- coding: utf-8 -*-
import os
import re
import json
import time
import unicodedata
import warnings
from typing import List, Dict, Any, Optional

import pandas as pd
from tqdm import tqdm
import google.generativeai as genai
import requests

warnings.filterwarnings('ignore')

# =========================================================
# 1) CONFIGURACIÓN DE LAS APIS
# =========================================================
# API de Gemini (se mantiene)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyB7BLl_abUktiP-aitJ4o-pw3gFqO26XvE")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# API de Búsqueda Web (Google Custom Search API)
# ¡REEMPLAZA ESTAS CLAVES CON LAS QUE ACABAS DE OBTENER!
GOOGLE_SEARCH_API_KEY = "AIzaSyDCS8_rpxnvtaKu7N2Nr0T3be85VN52xak"
GOOGLE_CSE_ID = "f31dbbbb7d1444927"

# =========================================================
# 2) RUTAS DE ARCHIVOS Y HOJAS
# =========================================================
file_sheets_map = {
    '/Users/mac/Documents/trabajo/javeriana/sivigila/wetransfer_sivigila_2025-07-24_1807/356_365_2022.xlsx': {
        '356_2022': 'NA',
        '365_2022': 'NA'
    },
    '/Users/mac/Documents/trabajo/javeriana/sivigila/wetransfer_sivigila_2025-07-24_1807/356_365_2023.xlsx': {
        '356_2023': 'NA',
        '365_2023': 'NA'
    }
}

# =========================================================
# 3) DICCIONARIO DE PATRONES (INTACTO)
# =========================================================
substance_patterns = {
    'alucinogenos': r'\blsd\b|\btusi\b|\b2cb\b|\bcandy fly\b|\btrip\b|\blucy\b|\bpapel\b|\bdietilamida\b|\bacidos?\b|\bácido lisérgico\b|\bpcp\b|\bfenciclidina\b|\bpeace pill\b|\bangel dust\b|\bpeyote\b|\bmescalina\b|\bhongos? psilocybin\b|\becstasis\b|\bextasis\b|\badam\b|\bmdma\b|\btacha\b|\bmolly\b|\bketamina\b|\bdmt\b|\bamt\b|\bfoxy\b|\bsalvia\b|\bjahe\b|\brueda\b|\byaje\b|\byage\b|\bhongo alucinógeno\b',
    'cocaina_y_derivados': r'\bbazuco\b|\bcocaína\b|\bcocaina\b|\bcrack\b|\bmetilecnonina\b|\bperico\b|\bbenzoilmetilecgonina\b|\bpatraciado\b|\bbase de coca\b',
    'opioides': r'\bopioides?\b|\bheroína\b|\bheroina\b|\bfentanil\b|\bamapola\b|\bmetadona\b|\bbrown\b|\bmorfina\b|\btramadol\b|\btramal\b|\boxicontin\b|\boxicodona\b|\bcodeína\b|\bcodeina\b|\bpercocet\b|\bhidroxicina\b|\bhidrocodeina\b|\bhidromorfona\b|\bparacodina\b|\bopiaceos\b|\btramadol y acetaminofen\b|\bacetaminofen tramadol\b|\bwinadeine\b|\bdihidrocodeina\b',
    'estimulantes': r'\bmetanfetaminas?\b|\bbenzedrine\b|\bcriptonita\b|\bcristal\b|\bhielo\b|\bcrank\b|\banfetaminas?\b|\bmethylfenidato\b|\bmetilfenidato\b|\britalin\b|\badderall\b|\bconcerta\b|\bcapilots\b|\bpep pills\b|\bspeed\b|\bcateina\b|\bawake\b',
    'inhalantes': r'\boxido nítrico\b|\bpopper\b|\blíquidos? solventes?\b|\bspray de pintura\b|\blimpiadores? de computadores?\b|\baerosoles? en spray\b|\bpegantes?\b|\bboxer\b|\bmarcadores?\b|\bsacol\b|\bdesengrasante\b|\bdisolventes?\b|\bsolución\b|\bidrocarburo\b|\bgasolina\b|\bdik\b|\bdick\b|\blady\b|\bnitrito\b|\bnitrato de amilo\b|\bformaldehido\b|\bvarsol\b|\bthinner\b|\bgas propano\b|\bgas natural\b|\bhumo\b|\bmonoxido de carbono\b|\bmonóxido de carbono\b|\bacpm\b|\baceite combustible\b|\bgas metano\b|\bdioxido de carbono\b|\bgas de mina de carbon\b|\bshampoo\b|\bremovedor de esmalte\b|\bgas pimienta\b|\bgas lacrimogeno\b|\bacetona\b|\bamonio\b|\bamoniaco\b|\bpinturas\b|\bambientador\b|\bcolonia\b|\bacido clorhidrico acido nitrico\b|\bsolvente de pintura\b|\bcloro gaseoso\b',
    'tranquilizantes_y_sedantes': r'\bquetapina\b|\bquetiapina\b|\bquietiapina\b|\bclonazepam\b|\bclonazepan\b|\bclonazepina\b|\bclorazepan\b|\bamitriptilina\b|\bsertralina\b|\bfluoxetina\b|\bzopiclona\b|\bzopilcona\b|\bzolpicona\b|\bsopiclona\b|\bescitalopram\b|\btrazodona\b|\btrazadona\b|\bvalproico\b|\bansioliticos?\b|\bantidepresivos?\b|\bsedantes?\b|\btranquilizantes?\b|\bbenzodiazepinas?\b|\balprazolam\b|\blorazepam\b|\bdiazepam\b|\bbenzocleozapinas?\b|\bcitalopram\b|\bclozapin\b|\bclozarpina\b|\bclozapina\b|\bzolpidem\b|\beszopiclone\b|\beszopiclona\b|\bzaleplon\b|\bflurazepam\b|\btemazepam\b|\btriazolam\b|\bbarbituricos?\b|\bbutalbital\b|\bsecobarbital\b|\bpentobarbital\b|\bpropofol\b|\bbutabarbital\b|\bbupropion\b|\bcymbalta\b|\bduloxetina\b|\bfluvoxamina\b|\bclomipramina\b|\bmirtazapina\b|\bpaxan\b|\bprozac\b|\bparoxetina\b|\btrittico\b|\bvenlafaxina\b|\bimipramina\b|\blevamepromacina\b|\bxanax\b|\bdormicum\b|\bhipnoticos?\b|\bmidazolam\b|\bzolof\b|\bdivalproato sodico\b|\blevopramazina\b|\bpregabalina\b|\brivotril\b|\bpsicótico(s)?\b|\bneurolepticos?\b|\bpam\b|\bzepam\b|\bmelatonina\b|\bcarbonato de litio\b|\bfenobarbital\b|\bolanzapina\b|\brisperidona\b|\blevomepromazina\b|\blamotrigina\b|\blitio\b|\bvalcote\b|\bhaliperidol\b|\bhioscina\b|\bciclobenzaprina\b|\bfenitoina\b|\blacosamida\b|\btopiramato\b|\bsomnifero desconocido\b|\bsinogan\b|\baripiprazol\b|\bzoplicona\b|\bbenzodiacepinas\b|\blyrica\b|\bvaleriana\b|\bsinogan\b|\brespirodona\b',
    'alcohol_etanol': r'\bcervezas?\b|\baguardiente\b|\bbebidas alcoholicas\b|\bron\b|\betanol\b|\bvino\b|\bbebidas? alcohólicas?\b|\bwhiskey\b|\bwhisky\b|\balcohol\b|\balcohol etilico\b|\balcohol antiseptico\b|\bguaro\b|\b(aguardiente de caña)\b|\balcohol industrial\b|\baperitivo\b|\blicor adulterado con metanol\b|\bvodka\b',
    'cannabinoides': r'\bmarihuana\b|\bcrippy\b|\bthc\b|\btetrahidrocanabinol\b|\bcriptonita\b|\bmarimba\b|\bcannabis\b|\bcanabis\b|\bcripa\b|\bcrispi\b|\bvareto\b|\bbareto\b|\byerba\b|\bsativa\b|\bhashish\b',
    'escopolamina': r'\bescopolamina\b|\bcacao sabanero\b|\bborrachera\b|\bburundanga\b|\bfloripondio\b',
}

# =========================================================
# 4) UTILIDADES DE NORMALIZACIÓN (INTACTO)
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

compiled_patterns = {k: re.compile(v, flags=re.IGNORECASE) for k, v in substance_patterns.items()}

def classify_substance_regex(nom_pro_text: str) -> List[str]:
    if not isinstance(nom_pro_text, str):
        return ['desconocido']
    text = clean_text(nom_pro_text)
    found_groups = [group for group, pat in compiled_patterns.items() if pat.search(text)]
    return found_groups if found_groups else ['otros']

# =========================================================
# 5) VÍAS DE EXPOSICIÓN (INTACTO)
# =========================================================
VIA_EXP_MAP = {
    1: "respiratoria", 2: "oral", 3: "dermica_mucosas", 4: "ocular",
    5: "desconocida", 6: "parenteral", 8: "transplacentaria"
}
VIA_EXPOSI_MAP = {
    1: "respiratoria", 2: "oral", 3: "dermica_mucosas", 4: "ocular",
    5: "desconocida", 6: "parenteral", 7: "transplacentaria"
}

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
    if s_norm.startswith("parent") or "intraven" in s_norm or "intramus" in s_norm or "subcut" in s_norm or "intraperit" in s_norm: return 6
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
# 6) PROMPT REFINADO (ahora pide una lista de categorías)
# =========================================================
def build_llm_prompt(nombres_pro_lista: List[str]) -> str:
    categorias_validas = [
        'alucinogenos', 'cocaina_y_derivados', 'opioides', 'estimulantes',
        'inhalantes', 'tranquilizantes_y_sedantes', 'alcohol_etanol',
        'cannabinoides', 'escopolamina', 'PSA_no_clasificado_lista', 'otros'
    ]
    prompt_txt = f"""
Eres experto en toxicología y vigilancia de SPA, con total conocimiento del uso de las sustancias, tanto en nombres tecnicos, como de jergas o contextos socioculturales y distingues y entiendes lo que es un PSA y nos centraremos en los 
cuales se usan para drogarseo su principal uso es el recreativo. Clasifica cada ítem en una o más de estas categorías validas:
{json.dumps(categorias_validas, ensure_ascii=False)}
Reglas:
1) **Foco en SPA de uso recreativo/misuso/que causen adicciones**. Si un ítem es una combinación, clasifícalo en todas las categorías relevantes (ej: "opio cafeína" -> ["opioides", "estimulantes"]).
2) Si es SPA pero no encaja en las categorías: "PSA_no_clasificado_lista". Por ejemplo: **"mefedrona"**.
3) Si es un **medicamento terapéutico común (antibióticos, antihipertensivos, analgésicos OTC, etc.) o productos de limpieza/plaguicidas/alimentos sin uso recreativo**, clasifica como "otros".
4) Normaliza ortografía y diacríticos, acepta jerga callejera y marcas (perico, bareto, tusi, molly, xanax, etc.), tolera errores fonéticos/leet/espacios/guiones/de escritura/gramaticales.
5) Si un ítem no tiene un uso claro, clasifica como "otros".
Formato de salida:
- La respuesta debe ser **únicamente un objeto JSON**. No incluyas ningún texto explicativo, código markdown (```json), ni comentarios.
- El objeto JSON debe tener una clave "resultados" con una lista de objetos. Cada objeto debe contener las claves "entrada", "nombre_normalizado" y "categorias_clasificadas" (una lista).
- La salida es una **lista JSON de objetos**, donde cada objeto tiene la categoría clasificada como una lista.
Salida:
{{ "resultados": [
    {{"entrada": "opio cafeina", "nombre_normalizado": "opio cafeina", "categorias_clasificadas": ["opioides", "estimulantes"]}},
    {{"entrada": "acetaminofen", "nombre_normalizado": "acetaminofen", "categorias_clasificadas": ["otros"]}},
    {{"entrada": "mefedrona", "nombre_normalizado": "mefedrona", "categorias_clasificadas": ["PSA_no_clasificado_lista"]}}
    ...
]}}
Entrada:
{json.dumps(nombres_pro_lista, ensure_ascii=False)}
""".strip()
    return prompt_txt

# =========================================================
# 7) LIMPIEZA DEL JSON DEVUELTO POR EL LLM
# =========================================================
def strip_code_fences(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl+1:]
        if s.endswith("```"):
            s = s[:-3]
    s = re.sub(r'^\s*json\s*', '', s, flags=re.IGNORECASE)
    return s.strip()

def parse_llm_json(texto_respuesta: str) -> List[Dict[str, Any]]:
    raw = strip_code_fences(texto_respuesta or "")
    try:
        data = json.loads(raw)
        if not isinstance(data.get("resultados"), list):
            raise ValueError("La respuesta no es una lista JSON válida.")
        return data["resultados"]
    except Exception as e:
        print(f"Error al parsear JSON: {e}")
        return []

# =========================================================
# 8) VALIDACIÓN Y CLASIFICACIÓN CON LLM Y BÚSQUEDA WEB
# (Optimizada con caché)
# =========================================================

VALIDATION_CACHE_PATH = '/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/outputs/salidas_llm/validacion_cache.json'
validation_cache = {}

def load_validation_cache():
    global validation_cache
    if os.path.exists(VALIDATION_CACHE_PATH):
        try:
            with open(VALIDATION_CACHE_PATH, 'r', encoding='utf-8') as f:
                validation_cache = json.load(f)
            print(f"Caché de validación cargado con {len(validation_cache)} entradas.")
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error al cargar el caché de validación, se iniciará uno nuevo: {e}")
            validation_cache = {}
    else:
        print("No se encontró caché de validación, se creará uno nuevo.")

def save_validation_cache():
    try:
        os.makedirs(os.path.dirname(VALIDATION_CACHE_PATH), exist_ok=True)
        with open(VALIDATION_CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(validation_cache, f, ensure_ascii=False, indent=4)
        print("Caché de validación guardado.")
    except IOError as e:
        print(f"Error al guardar el caché de validación: {e}")


def search_web(query: str) -> str:
    search_url = "[https://www.googleapis.com/customsearch/v1](https://www.googleapis.com/customsearch/v1)"
    params = {
        'key': GOOGLE_SEARCH_API_KEY,
        'cx': GOOGLE_CSE_ID,
        'q': query
    }
    try:
        response = requests.get(search_url, params=params, timeout=5)
        response.raise_for_status()
        results = response.json().get('items', [])
        snippets = [item.get('snippet', '') for item in results]
        return ' '.join(snippets)
    except requests.RequestException as e:
        print(f"Error en la búsqueda web para '{query}': {e}")
        return ""

def validate_llm_classification(substance_name: str, llm_categories: List[str]) -> List[str]:
    # Primero, revisa si la sustancia ya está en el caché
    if substance_name in validation_cache:
        # print(f"Usando caché para '{substance_name}'.")
        return validation_cache[substance_name]

    recreational_categories = {'tranquilizantes_y_sedantes', 'opioides', 'estimulantes'}
    
    if not any(cat in recreational_categories for cat in llm_categories):
        validation_cache[substance_name] = llm_categories
        return llm_categories

    search_query = f"{substance_name} uso recreativo o terapeutico"
    search_results = search_web(search_query)

    if not search_results:
        validation_cache[substance_name] = llm_categories
        return llm_categories

    prompt_validacion = f"""
    Basado en el siguiente texto de búsqueda web, ¿el compuesto '{substance_name}' es conocido principalmente por su uso terapéutico (ej. medicamento) o tiene un uso recreativo/abusivo significativo?
    Texto de búsqueda: "{search_results[:1500]}..."
    Responde ÚNICAMENTE con "terapeutico" si es principalmente terapéutico o "recreativo" si tiene un uso recreativo significativo. Si no hay evidencia clara, responde "desconocido".
    """
    
    try:
        response = model.generate_content(prompt_validacion)
        validation_result = response.text.strip().lower()
        
        final_cats = llm_categories
        if validation_result == "terapeutico":
            print(f"Validación: '{substance_name}' clasificado como 'terapeutico'. Reclasificando a 'otros'.")
            final_cats = ['otros']
        
        validation_cache[substance_name] = final_cats
        return final_cats
        
    except Exception as e:
        print(f"Error durante la validación del LLM para '{substance_name}': {e}")
    
    validation_cache[substance_name] = llm_categories
    return llm_categories

def clasificar_sustancias_con_llm_batch(nombres_pro_lista: List[str]) -> Dict[str, List[str]]:
    llm_prompt = build_llm_prompt(nombres_pro_lista)
    for attempt in range(3):
        try:
            resp = model.generate_content(llm_prompt)
            resultados = parse_llm_json(getattr(resp, "text", ""))
            
            mapeo_llm = {}
            for r in resultados:
                entrada_clean = clean_text(r.get('entrada', ''))
                cats = r.get('categorias_clasificadas', ['otros'])
                
                final_cats = validate_llm_classification(r.get('entrada', ''), cats)
                
                if entrada_clean:
                    mapeo_llm[entrada_clean] = final_cats
            
            save_validation_cache()
            return mapeo_llm
            
        except Exception as e:
            print(f"Error en el LLM (intento {attempt+1}): {e}")
            time.sleep(2 ** attempt)
    
    return {clean_text(n): ['otros'] for n in nombres_pro_lista}

# =========================================================
# 9) PIPELINE
# =========================================================
individual_dfs: Dict[str, pd.DataFrame] = {}
all_processed_dfs: List[pd.DataFrame] = []

print("--- Iniciando carga y pre-procesamiento de todos los datasets ---")

# Cargar el caché de validación al inicio del proceso
load_validation_cache()

terminos_a_filtrar = {
    'sin nombre', 'sin dato', 'sin informacion', 'desconocido', 'desconocida',
    'desconocidos', 'desconocidas', 'no sabe', 'no recuerda'
}

try:
    for file_path, sheets_info in file_sheets_map.items():
        for sheet_name, _ in sheets_info.items():
            df_name_key = f"df_{sheet_name}"
            print(f"\nCargando y normalizando hoja: '{sheet_name}' del archivo '{file_path}'")
            temp_df = pd.read_excel(file_path, sheet_name=sheet_name)
            temp_df['origen_hoja'] = sheet_name
            temp_df.columns = [normalize_column_name(col) for col in temp_df.columns]

            if 'nom_pro' in temp_df.columns:
                temp_df['nom_pro'] = temp_df['nom_pro'].fillna('desconocido').apply(clean_text)
                temp_df.loc[temp_df['nom_pro'].isin(terminos_a_filtrar), 'nom_pro'] = 'otros'

                temp_df = unify_route_columns(temp_df)

                individual_dfs[df_name_key] = temp_df
                all_processed_dfs.append(temp_df)
            else:
                print(f"Advertencia: La columna 'nom_pro' no existe en la hoja '{sheet_name}'. Se omite.")

    if not all_processed_dfs:
        raise ValueError("No se encontraron DataFrames para procesar.")

    print("\n--- Consolidando todos los DataFrames ---")
    df_consolidado = pd.concat(all_processed_dfs, ignore_index=True, sort=False)

    # Identificar nombres únicos a clasificar
    nombres_unicos_a_clasificar = df_consolidado['nom_pro'].unique().tolist()
    nombres_unicos_a_clasificar = [n for n in nombres_unicos_a_clasificar if n not in ['otros', 'desconocido']]

    print(f"\nTotal de nombres únicos a clasificar: {len(nombres_unicos_a_clasificar)}")

    # Clasificación por lotes con LLM y validación
    mapeo_llm = {}
    if nombres_unicos_a_clasificar:
        batch_size = 50
        for i in tqdm(range(0, len(nombres_unicos_a_clasificar), batch_size), desc="Clasificando y validando con Gemini"):
            lote_nombres = nombres_unicos_a_clasificar[i:i + batch_size]
            mapeo_llm_lote = clasificar_sustancias_con_llm_batch(lote_nombres)
            mapeo_llm.update(mapeo_llm_lote)
            # No es necesario un sleep adicional aquí, ya que la función lo maneja
    
    # Aquí puedes opcionalmente guardar el caché una última vez si quieres.
    # Ya se hace dentro de la función, pero es un buen paso de seguridad.
    save_validation_cache()


    print("\n--- Aplicando clasificaciones (LLM + validación) ---")

    def get_final_classification(nom_pro):
        # Primero, la clasificación LLM
        llm_cats = mapeo_llm.get(nom_pro, ['otros'])
        # Si el LLM no encontró nada, usa regex
        if llm_cats == ['otros'] or not llm_cats:
            return classify_substance_regex(nom_pro)
        return llm_cats

    df_consolidado['grupos_sustancia_final'] = df_consolidado['nom_pro'].apply(get_final_classification)

    # Generar columnas de categorías binarias para el análisis
    all_final_categories = set(cat for sublist in df_consolidado['grupos_sustancia_final'] for cat in sublist)
    for cat in all_final_categories:
        df_consolidado[f'es_{cat}'] = df_consolidado['grupos_sustancia_final'].apply(lambda x: 1 if cat in x else 0)

    # Validaciones adicionales (via)
    def aplicar_filtros_via(row):
        cats = row['grupos_sustancia_final']
        code = row.get('via_exposicion_codigo', None)
        final_cats = list(cats)
        if 'inhalantes' in final_cats and code is not None and not is_inhaled_route(code):
            final_cats.remove('inhalantes')
        if 'alcohol_etanol' in final_cats and code is not None and not is_oral_route(code):
            final_cats.remove('alcohol_etanol')
        
        return final_cats if final_cats else ['otros']

    df_consolidado['grupos_sustancia_filtrado'] = df_consolidado.apply(aplicar_filtros_via, axis=1)

    print("Clasificación final completada. Preparando para guardar...")

    # Columnas de salida
    columnas_base = ['origen_hoja', 'fec_not', 'cod_depto_o', 'cod_mun_o', 'sexo', 'edad', 'cod_pais',
                      'nom_pro', 'via_exposicion_col', 'via_exposicion_codigo', 'via_exposicion_texto',
                      'grupos_sustancia_final', 'grupos_sustancia_filtrado']
    
    columnas_existentes = [c for c in columnas_base if c in df_consolidado.columns]
    df_filtrado = df_consolidado[columnas_existentes]

    # Salidas
    base_out = '/Users/mac/Documents/trabajo/javeriana/sivigila/py_sivigila/outputs/salidas_llm'
    os.makedirs(base_out, exist_ok=True)
    output_path_principal = os.path.join(base_out, 'resultados_clasificacion_llm_avanzada.xlsx')
    output_path_resumen  = os.path.join(base_out, 'resumen_clasificacion_avanzada.xlsx')

    try:
        df_filtrado.to_excel(output_path_principal, index=False)
        print(f"\nDataFrame principal guardado exitosamente en: {output_path_principal}")
    except Exception as e:
        print(f"\nError al guardar el archivo Excel principal: {e}")

    print("\n--- Generando y guardando el archivo de resumen ---")
    
    # Nuevo resumen por categorías filtradas
    all_filtered_categories = set(cat for sublist in df_consolidado['grupos_sustancia_filtrado'] for cat in sublist)
    resumen_data = []
    for sheet in df_consolidado['origen_hoja'].unique():
        df_sheet = df_consolidado[df_consolidado['origen_hoja'] == sheet]
        for cat in all_filtered_categories:
            conteo = df_sheet['grupos_sustancia_filtrado'].apply(lambda x: cat in x).sum()
            resumen_data.append({'origen_hoja': sheet, 'grupo_sustancia_final': cat, 'conteo': conteo})
    
    df_resumen = pd.DataFrame(resumen_data)
    df_resumen = df_resumen.sort_values(by=['origen_hoja', 'conteo'], ascending=[True, False])
    
    try:
        df_resumen.to_excel(output_path_resumen, index=False)
        print(f"Archivo de resumen guardado exitosamente en: {output_path_resumen}")
    except Exception as e:
        print(f"Error al guardar el archivo de resumen: {e}")

except Exception as e:
    print(f"\nProceso finalizado con un error crítico: {e}")

print("\nProceso finalizado.")