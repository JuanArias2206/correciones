# -*- coding: utf-8 -*-
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

warnings.filterwarnings('ignore')

# Base dir for the portable bundle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =========================================================
# 1) CONFIGURACIÓN DE LA API DE GEMINI (SOLO LLM)
# =========================================================
# Hardcoded API key requested by user

GEMINI_API_KEY = "AIzaSyB7BLl_abUktiP-aitJ4o-pw3gFqO26XvE"    # USADA

#GEMINI_API_KEY = "AIzaSyC65dXNYxzlKJG5Wko3AttsXXCPwA3Ogys"    USADA

#GEMINI_API_KEY = "AIzaSyD7jxtM9MkdBQU6Z3bvKXB_HDquUfzx8dw"    USADA

#GEMINI_API_KEY = "AIzaSyC-kC8Ms9lY_w13U3JTvMmU6xXqmKuy9nY"     USADA

if not GEMINI_API_KEY:
    raise ValueError("Debes definir la variable de entorno GEMINI_API_KEY con tu clave de Gemini.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite')

# =========================================================
# 2) RUTAS DE ARCHIVOS Y HOJAS (AHORA RELATIVAS DENTRO DEL BUNDLE)
# =========================================================
file_sheets_map = {
    os.path.join(BASE_DIR, 'data', 'wetransfer_sivigila_2025-07-24_1807', '356_365_2022.xlsx'): {
        '356_2022': 'NA',
        '365_2022': 'NA'
    },
    os.path.join(BASE_DIR, 'data', 'wetransfer_sivigila_2025-07-24_1807', '356_365_2023.xlsx'): {
        '356_2023': 'NA',
        '365_2023': 'NA'
    }
}

# =========================================================
# 3) DICCIONARIO DE PATRONES (AJUSTADO → SIN “acidos?” GENÉRICO
#    Y CON “inhalantes” SOLO COMO SPA INHALADAS)
# =========================================================
substance_patterns = {
    # Alucinógenos: sin patrón genérico para "ácidos"
    'alucinogenos': (
        r'\blsd\b|\btusi\b|\b2cb\b|\bcandy fly\b|\btrip\b|\blucy\b|\bpapel\b|\bacidos\b|\bácidos\b'
        r'\bdietilamida\b|\bacido liser\b|\bpcp\b|\bfenciclidina\b|\bpeace pill\b|'
        r'\bangel dust\b|\bpeyote\b|\bmescalina\b|\bhongos? psilocybin\b|\becstasis\b|'
        r'\bextasis\b|\badam\b|\bmdma\b|\btacha\b|\bmolly\b|\bketamina\b|\bdmt\b|'
        r'\bamt\b|\bfoxy\b|\bsalvia\b|\bjahe\b|\brueda\b|\byaje\b|\byage\b|'
        r'\bhongo alucinogeno\b'
    ),

    'cocaina_y_derivados': (
        r'\bbazuco\b|\bcocaina\b|\bcrack\b|\bmetilecnonina\b|\bperico\b|'
        r'\bbenzoilmetilecgonina\b|\bpatraciado\b|\bbase de coca\b'
    ),

    'opioides': (
        r'\bopioides?\b|\bheroina\b|\bfentanil\b|\bamapola\b|\bmetadona\b|\bbrown\b|'
        r'\bmorfina\b|\btramadol\b|\btramal\b|\boxicontin\b|\boxicodona\b|\bcodeina\b|'
        r'\bpercocet\b|\bhidroxicina\b|\bhidrocodeina\b|\bhidromorfona\b|\bparacodina\b|'
        r'\bopiaceos\b|\btramadol y acetaminofen\b|\bacetaminofen tramadol\b|'
        r'\bwinadeine\b|\bdihidrocodeina\b'
    ),

    'estimulantes': (
        r'\bmetanfetaminas?\b|\bbenzedrine\b|\bcriptonita\b|\bcristal\b|\bhielo\b|'
        r'\bcrank\b|\banfetaminas?\b|\bmethylfenidato\b|\bmetilfenidato\b|\britalin\b|'
        r'\badderall\b|\bconcerta\b|\bcapilots\b|\bpep pills\b|\bspeed\b|\bcateina\b|'
        r'\bawake\b'
    ),

    # Inhalantes: solo SPA inhaladas típicas (pegantes/solventes/poppers/etc.)
    'inhalantes': (
        r'\boxido nitrico\b|\bpopper\b|\bliquidos? solventes?\b|\bspray de pintura\b|'
        r'\blimpiadores? de computadores?\b|\baerosoles? en spray\b|\bpegantes?\b|'
        r'\bboxer\b|\bmarcadores?\b|\bsacol\b|\bdesengrasante\b|\bdisolventes?\b|'
        r'\bsolucion\b|\bhidrocarburo\b|\bidrocarburo\b|\bgasolina\b|\bdik\b|\bdick\b|'
        r'\blady\b|\bnitrito\b|\bnitrato de amilo\b|\bvarsol\b|\bthinner\b|\bacetona\b|'
        r'\bremovedor de esmalte\b|\bsolvente de pintura\b'
    ),

    'tranquilizantes_y_sedantes': (
        r'\bquetapina\b|\bquetiapina\b|\bquietiapina\b|\bclonazepam\b|\bclonazepan\b|'
        r'\bclonazepina\b|\bclorazepan\b|\bamitriptilina\b|\bsertralina\b|\bfluoxetina\b|'
        r'\bzopiclona\b|\bzopilcona\b|\bzolpicona\b|\bsopiclona\b|\bescitalopram\b|'
        r'\btrazodona\b|\btrazadona\b|\bvalproico\b|\bansioliticos?\b|\bantidepresivos?\b|'
        r'\bsedantes?\b|\btranquilizantes?\b|\bbenzodiazepinas?\b|\balprazolam\b|\b'
        r'lorazepam\b|\bdiazepam\b|\bbenzocleozapinas?\b|\bcitalopram\b|\bclozapin\b|'
        r'\bclozarpina\b|\bclozapina\b|\bzolpidem\b|\beszopiclone\b|\beszopiclona\b|'
        r'\bzaleplon\b|\bflurazepam\b|\btemazepam\b|\btriazolam\b|\bbarbituricos?\b|'
        r'\bbutalbital\b|\bsecobarbital\b|\bpentobarbital\b|\bpropofol\b|\bbutabarbital\b|'
        r'\bbupropion\b|\bcymbalta\b|\bduloxetina\b|\bfluvoxamina\b|\bclomipramina\b|'
        r'\bmirtazapina\b|\bpaxan\b|\bprozac\b|\bparoxetina\b|\btrittico\b|\bvenlafaxina\b|'
        r'\bimipramina\b|\blevamepromacina\b|\bxanax\b|\bdormicum\b|\bhipnoticos?\b|'
        r'\bmidazolam\b|\bzolof\b|\bdivalproato sodico\b|\blevopramazina\b|\bpregabalina\b|'
        r'\brivotril\b|\bpsicotico(s)?\b|\bneurolepticos?\b|\bpam\b|\bzepam\b|\bmelatonina\b|'
        r'\bcarbonato de litio\b|\bfenobarbital\b|\bolanzapina\b|\brisperidona\b|'
        r'\blevomepromazina\b|\blamotrigina\b|\blitio\b|\bvalcote\b|\bhaliperidol\b|'
        r'\bhioscina\b|\bciclobenzaprina\b|\bfenitoina\b|\blacosamida\b|\btopiramato\b|'
        r'\bsomnifero desconocido\b|\bsinogan\b|\baripiprazol\b|\bzoplicona\b|'
        r'\bbenzodiacepinas\b|\blyrica\b|\bvaleriana\b|\brespirodona\b'
    ),

    'alcohol_etanol': (
        r'\bcervezas?\b|\baguardiente\b|\bbebidas alcoholicas\b|\bron\b|\betanol\b|'
        r'\bvino\b|\bbebidas? alcoholicas?\b|\bwhiskey\b|\bwhisky\b|\balcohol\b|'
        r'\balcohol etilico\b|\balcohol antiseptico\b|\bguaro\b|\baguardiente de cana\b|'
        r'\balcohol industrial\b|\baperitivo\b|\blicor adulterado con metanol\b|\bvodka\b'
    ),

    'cannabinoides': (
        r'\bmarihuana\b|\bcrippy\b|\bthc\b|\btetrahidrocanabinol\b|\bcriptonita\b|'
        r'\bmarimba\b|\bcannabis\b|\bcanabis\b|\bcripa\b|\bcrispi\b|\bvareto\b|\bbareto\b|'
        r'\byerba\b|\bsativa\b|\bhashish\b'
    ),

    'escopolamina': (
        r'\bescopolamina\b|\bcacao sabanero\b|\bborrachera\b|\bburundanga\b|\bfloripondio\b'
    ),
}

# =========================================================
# 4) UTILIDADES DE NORMALIZACIÓN
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
# 5) VÍAS DE EXPOSICIÓN
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
# 6) PROMPT REFINADO (LLM → LISTA DE CATEGORÍAS, CON IDs)
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
            raise ValueError("La respuesta no tiene la clave 'resultados' como lista.")
        return data["resultados"]
    except Exception as e:
        print(f"Error al parsear JSON desde LLM: {e}")
        return []

# =========================================================
# 8) CLASIFICACIÓN CON LLM (MANEJO DE LOTES + IDs)
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
# 9) PIPELINE COMPLETO
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

    print(f"\nTotal de nombres únicos a clasificar con LLM: {len(nombres_unicos_a_clasificar)}")

    # ------------------------------
    # Clasificación por lotes con LLM
    # ------------------------------
    mapeo_llm: Dict[str, List[str]] = {}
    if nombres_unicos_a_clasificar:
        batch_size = 10  # lotes pequeños para mayor robustez
        for i in tqdm(range(0, len(nombres_unicos_a_clasificar), batch_size),
                      desc="Clasificando con Gemini (lotes pequeños)"):
            lote_nombres = nombres_unicos_a_clasificar[i:i + batch_size]
            mapeo_llm_lote = clasificar_sustancias_con_llm_batch(lote_nombres)
            mapeo_llm.update(mapeo_llm_lote)

    print("\n--- Aplicando clasificaciones (LLM + regex fallback) ---")

    def get_final_classification(nom_pro: str) -> List[str]:
        """
        Mezcla LLM + regex.
        - Si nom_pro es 'otros' o 'desconocido' -> devolver directamente ['otros'].
        - Si el LLM devolvió categorías distintas de ['otros'] -> usar esas.
        - Si el LLM devolvió ['otros'] o no tiene entrada -> usar regex.
        """
        if nom_pro in ['otros', 'desconocido']:
            return ['otros']

        llm_cats = mapeo_llm.get(nom_pro, ['otros'])
        if llm_cats == ['otros'] or not llm_cats:
            return classify_substance_regex(nom_pro)
        return llm_cats

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
