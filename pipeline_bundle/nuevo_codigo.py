# -*- coding: utf-8 -*-
"""
PIPELINE DE CLASIFICACIÓN DE SUSTANCIAS PSICOACTIVAS (SPA)
===========================================================
Este módulo ejecuta el pipeline completo de clasificación usando:
- Blacklists para filtrado previo (evita enviar al LLM productos no-SPA)
- LLM (Google Gemini) para clasificación principal
- Regex como respaldo cuando el LLM falla
- Post-filtrado con blacklists por categoría para corregir errores del LLM
"""

import os
import re
import json
import time
import unicodedata
import warnings
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from tqdm import tqdm
import google.generativeai as genai

# Importar módulos locales
from config import (
    BASE_DIR, GEMINI_API_KEY, GEMINI_MODEL, LLM_DELAY_SECONDS, LLM_BATCH_SIZE,
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
# 1) CONFIGURACIÓN DE LA API DE GEMINI
# =========================================================
if not GEMINI_API_KEY:
    raise ValueError("Debes definir GEMINI_API_KEY en config.py")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

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
# 3) PROMPT REFINADO (LLM → LISTA DE CATEGORÍAS, CON IDs)
# =========================================================
def build_llm_prompt(nombres_pro_lista: List[str]) -> Tuple[str, Dict[str, str]]:
    """
    Construye el prompt para el LLM y devuelve:
      - el texto del prompt
      - un mapa id -> nom_pro_normalizado (clean_text)
    """
    categorias_validas = [
        'alucinogenos', 'cocaina_y_derivados', 'opioides', 'estimulantes',
        'inhalantes', 'tranquilizantes_y_sedantes', 'alcohol_etanol',
        'cannabinoides', 'escopolamina', 'PSA_no_clasificado_lista', 'otros'
    ]

    items = []
    id_to_nom_clean: Dict[str, str] = {}
    for idx, nombre in enumerate(nombres_pro_lista, start=1):
        item_id = str(idx)
        items.append({"id": item_id, "nombre": nombre})
        id_to_nom_clean[item_id] = clean_text(nombre)

    prompt_txt = f"""
Eres experto en toxicología clínica y vigilancia de sustancias psicoactivas (SPA) en Latinoamérica.
Tu tarea es decidir, para cada NOMBRE DE PRODUCTO, si contiene una o más SPA de uso recreativo/misuso,
o si NO es una SPA y debe ir a "otros".

Clasifica cada ítem en una o más de estas categorías válidas:
{json.dumps(categorias_validas, ensure_ascii=False)}

DEFINICIÓN GENERAL
- SPA: sustancias cuyo uso principal o frecuente en la práctica es ALTERAR LA CONCIENCIA,
  el ánimo o el comportamiento (euforia, alucinaciones, “viaje”, excitación, sedación, etc.).
- No se consideran SPA: ácidos corrosivos, plaguicidas, productos de limpieza, cosméticos,
  vitaminas, suplementos nutricionales, medicamentos puramente terapéuticos sin uso recreativo típico.

REGLAS CLAVE (MUY ESTRICTAS):

1) ALUCINOGENOS
   Clasifica como "alucinogenos" SOLO si el producto contiene:
   - LSD / ácido lisérgico / “ácido” o 'ácidos' claramente relacionado con LSD o un uso recreativo
   - DMT, AMT, fenciclidina / PCP
   - hongos psilocibios / "hongos alucinogenos"
   - mescalina, peyote
   - tusi, 2CB, MDMA, "molly", "éxtasis"
   - ketamina usada como droga recreativa
   - Angel
   - Yahe, yage
   - metilendioximetanfetamina

   NO clasifiques como "alucinogenos":
   - Cualquier ácido químico o medicamento que solo se llama “acido":
     EJEMPLOS (deben ir a "otros" salvo que tengan además una SPA):
       "acido valproico"
       "acido folico"
       "acido acetilsalicilico"
       "acido tranexamico"
       "acido sulfurico"
       "acido muriatico"
       "acido clorhidrico"
       "acido nitrico"
       "acido borico"
       "acido fosforico"
       "acido citrico"
       Antiácidos
       "acidos inorganicos", "acidos organicos", aminoácidos, ácidos grasos,
   - Vitaminas y suplementos: ácido fólico, omega 3, multivitamínicos, calcio, hierro, etc.
   - hongofenol, hongo ganoderma, "removedor de hongos", hongosin, hongosan
   - antitusivos, robitusin
   - Productos agrícolas o plaguicidas que contengan "ácido" en su nombre. 
   -Productos agrícolas o plaguicidas como el sicario, el arriero, rafaga, campero, y diferentes.
   - acidos grasos, poli insaturados omega 3 y omega 6

2) ESTIMULANTES
   Incluye como "estimulantes":
   - anfetaminas, metanfetaminas, capilot, cristal, speed, criptonita
   - metilfenidato, Adderall, Concerta, ritalin, benzedrine, atomoxetina

   MUY IMPORTANTE:
   - La sola presencia de "cafeina" o "cafe" en un ANALGÉSICO O MEDICAMENTO
     NO es suficiente para clasificar como "estimulantes".
     EJEMPLOS que deben ir a "otros" (a menos que también contengan una SPA clara):
       "acetaminofen cafeina"
       "aspirina mas cafeina"
       "ergotamina/cafeina"
       "sevedol"
       "cafiaspirina"
       "dipirona cafeina"
       "axcedrin asa acetaminofen cafeina"
   - Antidepresivos y estabilizadores del ánimo como:
       "bupropion", "venlafaxina", "fluoxetina", "duloxetina",
       "sertralina", "lamotrigina", etc.
       
     NO deben ir a "estimulantes". Clasifícalos como:
       - "tranquilizantes_y_sedantes" si son psicotrópicos sedantes/ansiolíticos, o
       - "otros" si el contexto es claramente médico y no recreativo.
       - productos agricolas como Rafaga, el sicario, el arriero, campero, diablo rojo, awake 500, methavin 90
       bright 90, alto 100 y diferentes herbicidas y plaguicidas deben ir a "otros".
       - productos para adelgazar o energizantes sin una SPA clara no deben ir a "estimulantes".
       - bebidas energeticas como vive 100 y demás del contexto colombiano, deben ir a "otros".

   No incluir:
   - MDMA, methavin, methergyn, methylcarbamoyloxy, methamex, methomyl, methox, metsulfuron methyl
   - bebidas energéticas y preparados claramente estimulantes:
     "vive 100", "four loko", "energizante", "bebida energetica",
     "pastilla para adelgazar" o productos con sibutramina, fentermina,
     clenbuterol usados como adelgazantes o estimulantes.

3) INHALANTES: 
   Clasifica como "inhalantes" SOLO sustancias que se usan típicamente
   para drogarse inhalando vapores o gases, como:
   - pegantes / solventes volátiles: thinner, sacol, boxer, pegante,
     disolventes de pintura, varsol, gasolina inhalada, formaldehido etc.
   - aerosoles y sprays inhalados con fin recreativo: poppers (nitrito de amilo),
     aerosoles de pintura, limpiadores en spray usados para “patear”.

   NO clasifiques como "inhalantes" (van a "otros", salvo que explícitamente
   se indique un uso recreativo):
   - gases de uso doméstico o industrial:
       "gas propano", "gas natural", "fuga de gas", "gas metano",
       "gas domiciliario", "gases fluorados", "humo", "gas industrial",
       "dioxido de carbono", "monoxido de carbono",
       "gas de mina de carbon", "boxer", "pintura" etc.
   - productos de limpieza o domésticos:
       "shampoo", "colonia", "ambientador", "liquido de frenos",
       "kerosene", "alcohol isopropilico", "cloro",
       "glufosinato de amonio", "hexano", "percloroetileno",
       "amoniaco" como limpiador, etc.
    - productos agrícolas o plaguicidas que contengan "inhalantes" en su nombre o por ejemplo,
        Rafaga, el sicario, el arriero, campero, diablo rojo, awake 500, methavin 90, bright 90, alto 100.
    - gas irritante desconocido, gas lacrimogeno, gas pimienta --- IGNORE ---

4) TRANQUILIZANTES_Y_SEDANTES
   Incluye:
   - benzodiacepinas (clonazepam, alprazolam, diazepam, lorazepam, rivotril, valium, etc.)
   - antidepresivos (amitriptilina, bupoprion, paroxetina, fluoxetina, trittico, escitalopram, Imipramina, escitalopram)
   - hipnóticos tipo z (zopiclona, zolpidem)
   - antipsicóticos, antiepilépticos, antidepresivos y moduladores del ánimo
     con potencial de abuso sedante (quetiapina, olanzapina, haloperidol,
     lamotrigina, acido valproico, barbituricos, acido valproico, pregabalina etc.)
   - cuando haya duda y se trate de medicamentos psicotrópicos sedantes,
     es preferible asignar aquí antes que a "alucinogenos" o "estimulantes". 

5) ALCOHOL_ETANOL
   - Bebidas alcohólicas y preparaciones donde el alcohol etílico es
     claramente la sustancia: "cerveza", "vino", "aguardiente", "cocktail", "ron", "whisky", "vodka", "four loko", "viche", "guaro", "chirrinch", "bebidas alcoholicas", "bebidas embrigantes", "etanol", etc.

   Eliminar: "colicort", "mirtapax", "azul de metileno", cloroetano

6) CANNABINOIDES, COCAINA_Y_DERIVADOS, OPIOIDES, ESCOPOLAMINA
   - marihuana, mariguana, cannabis, bareto, cripa, cripy, vareta, THC, hashish, brownie con cannabis, happy brownie → "cannabinoides"

   - cocaína, perico, bazuco, crack, base de coca, benzoylmethylecgonine → "cocaina_y_derivados"

   - Estos van es cocaína y derivados: cocaína usada como estimulante (además de "cocaina_y_derivados") 
   Para cocaína y derivados no incluir: - lidocaína, alcohol de cocina, folicocarbonatode, "azuco (azufre coloidal", "veneno para el cultivo de coca", "cocadil", benzocaína, melocaina, xilocaína, oxibuprocaina, agua de coca, ácido de coca, cocacola
   - heroína, fentanilo, morfina, tramadol, oxicontin, hidromorphona, hidrocodeina, codeína, metadona, paracodina, fentanil, opioides en general → "opioides"
   Excluir de opioides: bupropion, tiotropio bromuro, topiamato

   - escopolamina, burundanga, floripondio, cacao sabanero → "escopolamina"


7) PSA_NO_CLASIFICADO_LISTA
   - Usa "PSA_no_clasificado_lista" SOLO cuando:
     - la sustancia sí es claramente una SPA con uso recreativo
       pero no encaja en ninguna de las otras categorías (por ejemplo "mefedrona").

8) OTROS
   - Todo producto que NO sea claramente una SPA de uso recreativo debe ir a "otros":
     medicamentos para dolor, fiebre, migraña, hipertensión, diabetes, antibióticos,
     vitaminas, suplementos, productos de cuidado personal, plaguicidas, corrosivos,
     combustibles, gases industriales, limpiadores, cosméticos, etc.
     - Si un nombre contiene una mezcla larga de muchos medicamentos sin una SPA obvia,
       clasifica como "otros" o, si incluye un psicotrópico sedante/ansiolítico,
       como "tranquilizantes_y_sedantes".
    - Recuerda que los herbicidas, plaguicidas, productos de limpieza, ácidos corrosivos,
      vitaminas, suplementos nutricionales y medicamentos puramente terapéuticos sin uso recreativo
      NO son SPA y deben ir a "otros". Productos agricolas como Rafaga, el sicario, el arriero,
      campero, y diferentes
      herbicidas y plaguicidas deben ir a "otros".


FORMATO DE RESPUESTA
- La respuesta debe ser únicamente un objeto JSON, sin texto adicional ni ``` .
- Debe tener una clave "resultados" que sea una lista de objetos.
- Cada objeto DEBE contener:
  - "id" (string, exactamente igual al id recibido)
  - "entrada" (texto original del nombre)
  - "nombre_normalizado"
  - "categorias_clasificadas" (lista de una o más categorías válidas)
- Si devuelves algo que no sea JSON válido exactamente como se indica, la respuesta se considerará inválida
Ejemplo de salida:
{{ "resultados": [
  {{"id": "1", "entrada": "opio cafeina", "nombre_normalizado": "opio cafeina", "categorias_clasificadas": ["opioides", "estimulantes"]}},
  {{"id": "2", "entrada": "acetaminofen cafeina", "nombre_normalizado": "acetaminofen cafeina", "categorias_clasificadas": ["otros"]}},
  {{"id": "3", "entrada": "mefedrona", "nombre_normalizado": "mefedrona", "categorias_clasificadas": ["PSA_no_clasificado_lista"]}}
]}}

Entrada (lista de ítems con id):
{json.dumps(items, ensure_ascii=False)}
""".strip()

    return prompt_txt, id_to_nom_clean

# =========================================================
# 4) LIMPIEZA DEL JSON DEVUELTO POR EL LLM
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
            raise ValueError("La respuesta no tiene la clave 'resultados' como lista.")
        return data["resultados"]
    except Exception as e:
        print(f"Error al parsear JSON desde LLM: {e}")
        return []

# =========================================================
# 5) CLASIFICACIÓN CON LLM (MANEJO DE LOTES + IDs)
# =========================================================
def clasificar_sustancias_con_llm_batch(nombres_pro_lista: List[str]) -> Dict[str, List[str]]:
    if not nombres_pro_lista:
        return {}

    llm_prompt, id_to_nom_clean = build_llm_prompt(nombres_pro_lista)
    input_ids = set(id_to_nom_clean.keys())

    for attempt in range(3):
        try:
            # Pausa de 5 segundos antes de cada llamada al LLM para respetar límites de cuota
            time.sleep(5)
            resp = model.generate_content(llm_prompt)
            texto_llm = getattr(resp, "text", "") if hasattr(resp, "text") else str(resp)
            resultados = parse_llm_json(texto_llm)

            mapeo_llm: Dict[str, List[str]] = {}
            ids_vistos: set = set()

            for r in resultados:
                item_id = str(r.get('id', '')).strip()
                if not item_id:
                    continue
                if item_id not in id_to_nom_clean:
                    print(f"[Advertencia LLM] Se recibió un id desconocido en la respuesta: {item_id}")
                    continue

                ids_vistos.add(item_id)
                nom_clean = id_to_nom_clean[item_id]
                cats = r.get('categorias_clasificadas', ['otros'])
                if not isinstance(cats, list) or not cats:
                    cats = ['otros']
                mapeo_llm[nom_clean] = cats

            ids_faltantes = input_ids - ids_vistos
            if ids_faltantes:
                nombres_faltantes = [id_to_nom_clean[i] for i in ids_faltantes]
                print(f"[Advertencia LLM] {len(ids_faltantes)} ítems del lote no fueron devueltos por el modelo.")
                print(f"Ejemplos de ítems faltantes (normalizados): {nombres_faltantes[:10]}")

            return mapeo_llm

        except Exception as e:
            print(f"Error en el LLM (intento {attempt+1}): {e}")
            time.sleep(2 ** attempt)

    print(f"[Fallo crítico LLM] No se pudo clasificar un lote de {len(nombres_pro_lista)} ítems tras 3 intentos.")
    print("Se asignará ['otros'] provisionalmente y luego se usará regex como respaldo para estos ítems.")
    return {clean_text(n): ['otros'] for n in nombres_pro_lista}

# =========================================================
# 6) PIPELINE COMPLETO
# =========================================================
individual_dfs: Dict[str, pd.DataFrame] = {}
all_processed_dfs: List[pd.DataFrame] = []

print("--- Iniciando carga y pre-procesamiento de todos los datasets ---")

terminos_a_filtrar = {
    'sin nombre', 'sin dato', 'sin informacion', 'desconocido', 'desconocida',
    'desconocidos', 'desconocidas', 'no sabe', 'no recuerda'
}

try:
    # ------------------------------
    # Carga y normalización de hojas
    # ------------------------------
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

    # ------------------------------
    # Consolidación
    # ------------------------------
    print("\n--- Consolidando todos los DataFrames ---")
    df_consolidado = pd.concat(all_processed_dfs, ignore_index=True, sort=False)

    # Identificar nombres únicos a clasificar
    nombres_unicos_a_clasificar = df_consolidado['nom_pro'].unique().tolist()
    nombres_unicos_a_clasificar = [n for n in nombres_unicos_a_clasificar if n not in ['otros', 'desconocido']]

    # PRE-FILTRADO: Separar productos que van directamente a "otros" usando blacklist general
    # Esto ahorra cuota del LLM al no enviar productos que sabemos que no son SPA
    nombres_para_llm = []
    nombres_otros_directos = []
    
    for nombre in nombres_unicos_a_clasificar:
        if is_in_general_blacklist(nombre):
            nombres_otros_directos.append(nombre)
        else:
            nombres_para_llm.append(nombre)
    
    print(f"\nTotal de nombres únicos encontrados: {len(nombres_unicos_a_clasificar)}")
    print(f"  → Filtrados a 'otros' por blacklist general: {len(nombres_otros_directos)}")
    print(f"  → Enviados al LLM para clasificación: {len(nombres_para_llm)}")

    # Guardar lista de productos filtrados por blacklist en Excel
    if nombres_otros_directos:
        df_blacklist = pd.DataFrame({
            'nombre_producto': nombres_otros_directos,
            'razon': 'Filtrado por blacklist general (plaguicidas/limpieza/corrosivos)'
        })
        # Contar cuántas veces aparece cada producto filtrado
        conteos = df_consolidado[df_consolidado['nom_pro'].isin(nombres_otros_directos)]['nom_pro'].value_counts()
        df_blacklist['frecuencia'] = df_blacklist['nombre_producto'].map(conteos)
        df_blacklist = df_blacklist.sort_values('frecuencia', ascending=False)
        
        # Guardar en la carpeta de salida
        blacklist_output_path = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo', 'productos_filtrados_blacklist.xlsx')
        os.makedirs(os.path.dirname(blacklist_output_path), exist_ok=True)
        df_blacklist.to_excel(blacklist_output_path, index=False)
        print(f"  → Lista de productos filtrados guardada en: productos_filtrados_blacklist.xlsx")

    # ------------------------------
    # Clasificación por lotes con LLM (solo para nombres que pasaron el pre-filtro)
    # ------------------------------
    mapeo_llm: Dict[str, List[str]] = {}
    
    # Agregar los productos blacklisteados directamente al mapeo
    for nombre in nombres_otros_directos:
        mapeo_llm[nombre] = ['otros']
    
    # Clasificar con LLM solo los que no están en blacklist
    if nombres_para_llm:
        batch_size = 10  # lotes pequeños para mayor robustez
        for i in tqdm(range(0, len(nombres_para_llm), batch_size),
                      desc="Clasificando con Gemini (lotes pequeños)"):
            lote_nombres = nombres_para_llm[i:i + batch_size]
            mapeo_llm_lote = clasificar_sustancias_con_llm_batch(lote_nombres)
            mapeo_llm.update(mapeo_llm_lote)

    print("\n--- Aplicando clasificaciones (LLM + regex fallback + post-filtro blacklist) ---")

    def get_final_classification(nom_pro: str) -> List[str]:
        """
        Pipeline de clasificación con múltiples etapas:
        1. Si nom_pro es 'otros' o 'desconocido' -> devolver ['otros']
        2. Si está en blacklist general -> devolver ['otros']
        3. Usar resultado del LLM si es válido
        4. Usar regex como fallback si LLM falló
        5. Aplicar post-filtro de blacklist por categoría
        """
        if nom_pro in ['otros', 'desconocido']:
            return ['otros']
        
        # Verificar blacklist general (por seguridad, aunque ya debería estar filtrado)
        if is_in_general_blacklist(nom_pro):
            return ['otros']

        # Obtener clasificación del LLM o regex
        llm_cats = mapeo_llm.get(nom_pro, ['otros'])
        if llm_cats == ['otros'] or not llm_cats:
            cats = classify_substance_regex(nom_pro)
        else:
            cats = llm_cats
        
        # POST-FILTRADO: Aplicar blacklists por categoría para corregir errores del LLM
        # Esto remueve categorías incorrectas (ej: lidocaína en cocaína, vitaminas en alucinógenos)
        cats = filter_categories_with_blacklist(nom_pro, cats)
        
        return cats if cats else ['otros']

    df_consolidado['grupos_sustancia_final'] = df_consolidado['nom_pro'].apply(get_final_classification)

    # ------------------------------
    # Columnas binarias para análisis
    # ------------------------------
    all_final_categories = set(cat for sublist in df_consolidado['grupos_sustancia_final'] for cat in sublist)
    for cat in all_final_categories:
        df_consolidado[f'es_{cat}'] = df_consolidado['grupos_sustancia_final'].apply(
            lambda x: 1 if cat in x else 0
        )

    # ------------------------------
    # Validaciones adicionales (via de exposición)
    # ------------------------------
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

    # ------------------------------
    # Columnas de salida y guardado
    # ------------------------------
    columnas_base = [
        'origen_hoja', 'fec_not', 'cod_depto_o', 'cod_mun_o', 'sexo', 'edad', 'cod_pais',
        'nom_pro', 'via_exposicion_col', 'via_exposicion_codigo', 'via_exposicion_texto',
        'grupos_sustancia_final', 'grupos_sustancia_filtrado'
    ]

    columnas_existentes = [c for c in columnas_base if c in df_consolidado.columns]
    df_filtrado = df_consolidado[columnas_existentes]

    base_out = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo')
    os.makedirs(base_out, exist_ok=True)
    output_path_principal = os.path.join(base_out, 'resultados_clasificacion_llm_avanzada.xlsx')
    output_path_resumen  = os.path.join(base_out, 'resumen_clasificacion_avanzada.xlsx')

    try:
        df_filtrado.to_excel(output_path_principal, index=False)
        print(f"\nDataFrame principal guardado exitosamente en: {output_path_principal}")
    except Exception as e:
        print(f"\nError al guardar el archivo Excel principal: {e}")

    print("\n--- Generando y guardando el archivo de resumen ---")

    # Resumen por categorías filtradas
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

except Exception as e:
    print(f"\nProceso finalizado con un error crítico: {e}")

print("\nProceso finalizado.")
