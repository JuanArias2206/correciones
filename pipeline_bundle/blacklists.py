# -*- coding: utf-8 -*-
"""
BLACKLISTS Y FILTROS DE EXCLUSIÓN
=================================
Este módulo contiene todas las listas de exclusión para filtrar productos
que NO deben clasificarse como SPA (Sustancias Psicoactivas).

Estos productos serán automáticamente asignados a "otros" sin pasar por el LLM,
lo que ahorra cuota de API y evita clasificaciones erróneas.

Estructura:
- BLACKLIST_GENERAL: Productos que siempre van a "otros" sin importar contexto
- AGRO_KEYWORDS: Palabras clave de productos agrícolas/plaguicidas
- AGRO_ACTIVE_INGREDIENTS: Ingredientes activos de plaguicidas
- HOUSEHOLD_CORROSIVE_KEYWORDS: Productos de limpieza/corrosivos
- Blacklists por categoría: Para post-filtrar resultados del LLM
"""

import re
from typing import Set

# =========================================================
# BLACKLIST GENERAL - Productos que SIEMPRE van a "otros"
# =========================================================
# Estos productos se excluyen ANTES de enviar al LLM
BLACKLIST_GENERAL: Set[str] = {
    "gas natural", "dioxido de carbono", "dióxido de carbono", "productos de limpieza",
    "monoxido de carbono", "monóxido de carbono", "dioxido de nitrogeno"
    # Agregar aquí productos específicos que siempre deben ir a "otros"
    # Ejemplo: "producto_especifico", "otro_producto",
}

# =========================================================
# PRODUCTOS AGRÍCOLAS / PLAGUICIDAS
# =========================================================

# Palabras que indican claramente plaguicidas / productos agrícolas
AGRO_KEYWORDS: Set[str] = {
    "herbicida", "herbicidas",
    "plaguicida", "plaguicidas",
    "pesticida", "pesticidas",
    "insecticida", "insecticidas",
    "fungicida", "fungicidas",
    "rodenticida", "rodenticidas",
    "raticida", "raticidas",
    "acaricida", "acaricidas",
    "nematicida", "nematicidas",
    "fertilizante", "fertilizantes",
    "abono", "abonos", "abono foliar",
    "agroquimico", "agroquimicos", "baygon",
    "producto agricola", "productos agricolas",
    "uso agricola", "usos agricolas",
    "fitosanitario", "fitosanitarios",
}

# Ingredientes activos típicos de plaguicidas (OF, carbamatos, herbicidas, rodenticidas, etc.)
AGRO_ACTIVE_INGREDIENTS: Set[str] = {
    "paraquat", "gramoxone",
    "glifosato", "glyphosate",
    "2,4-d", "24d", "2 4 d",
    "atrazina",
    "imidacloprid",
    "clorpirifos", "chlorpyrifos",
    "malation", "malathion",
    "paration", "parathion",
    "diazinon",
    "dimetoato", "dimethoate",
    "endosulfan", "endosulfam",
    "lindano",
    "aldrin", "dieldrin", "heptacloro",
    "carbaril", "carbaryl",
    "aldicarb",
    "carbofuran", "furadan",
    "fosfuro de aluminio", "fosfuro de zinc", "fosfina",
    "bromadiolona", "brodifacoum",
    "warfarina", "coumatetralyl", "difenacoum",
    # Productos agrícolas colombianos específicos
    "rafaga", "el sicario", "sicario", "el arriero", "arriero","campero", 
    "diablo rojo", "awake 500", "methavin 90", "methomyl",
    "bright 90", "alto 100", "lorsban", "metsulfuron",
}

# =========================================================
# PRODUCTOS DE LIMPIEZA / CORROSIVOS
# =========================================================

HOUSEHOLD_CORROSIVE_KEYWORDS: Set[str] = {
    "soda caustica",
    "hidroxido de sodio", "hidroxido sodico",
    "acido muriatico",
    "acido clorhidrico",
    "acido sulfurico",
    "acido nitrico",
    "destapa canerias", "destapacanerias", "destapador de canerias",
    "detergente", "detergentes",
    "jabon en polvo", "jabones en polvo",
    "limpiador", "limpiadores",
    "limpiavidrios",
    "limpiador de pisos",
    "limpia hornos",
    "desengrasante", "desengrasantes",
    "limpido",
    "hipoclorito",
    "cloro", "cloro gaseoso",
    "lejia",
    "amonio cuaternario", "amonios cuaternarios",
    "amoniaco",
}

# =========================================================
# GASES / HUMO / EMISIONES INDUSTRIALES (PRE-FILTRO)
# =========================================================
# Estos términos nunca son SPA recreativos. Se envían directo a "otros".
INDUSTRIAL_GASES_KEYWORDS: Set[str] = {
    # Términos generales
    "humo", "humo de extintor", "humo de motor", "humo de gasolina",
    "vapor de gasolina", "mezcla de gases", "gases de combustion",
    "gas desconocido", "gas irritante",
    # Gases comunes e industriales
    "gas metano", "metano",
    "gas natural", "propano", "gas licuado", "gas liquido",
    "gas industrial", "gas de uso industrial",
    # Minería / entornos
    "gas de mina", "gas de mina de carbon",
    # Halógenos y otros
    "cloro gaseoso", "dioxido de nitrogeno", "oxido de etileno",
    "cloroformo", "diclorometano", "cloruro de metileno",
    # Refrigerantes y similares
    "gas refrigerante", "freon", "freaon", "clorodifluorometano",
    # Protección / control
    "gas lacrimogeno", "gas pimienta",
}

# =========================================================
# BLACKLISTS POR CATEGORÍA - Post-filtrado de LLM
# =========================================================
# Estos se aplican DESPUÉS del LLM para corregir clasificaciones erróneas

# Alucinógenos: sin patrón genérico para "ácidos"
ALUCINOGENOS_BLACKLIST: Set[str] = {
    # Ácidos químicos/médicos (NO son LSD)
    "acido folico", "ácido fólico",
    "acido acetilsalicilico", "ácido acetilsalicílico",
    "acido citrico", "ácido cítrico",
    "acido sulfurico", "ácido sulfúrico",
    "acido muriatico", "ácido muriático",
    "acido clorhidrico", "ácido clorhídrico",
    "acido nitrico", "ácido nítrico",
    "acido borico", "ácido bórico",
    "acido fosforico", "ácido fosfórico",
    "acido valproico", "ácido valproico",
    "acido tranexamico", "ácido tranexámico",
    "aminoacidos", "aminoácidos",
    "acidos grasos", "ácidos grasos",
    "acidos inorganicos", "ácidos inorgánicos",
    "acidos organicos", "ácidos orgánicos",
    "omega 3", "omega 6", "omega-3", "omega-6",
    "acidos grasos poliinsaturados",
    # Hongos no alucinógenos
    "hongofenol", "hongo ganoderma", "removedor de hongos",
    "hongosin", "hongosan",
    "trazadona hongos alcohol",
}

# Regex para alucinógenos (patrón de exclusión)
ALUCINOGENOS_BLACKLIST_REGEX = re.compile(
    r'\bacido\s+folico\b'
    r'|\bacido\s+acetilsalicilico\b'
    r'|\bacido\s+citrico\b'
    r'|\bacido\s+sulfurico\b'
    r'|\bacido\s+muriatico\b'
    r'|\bacido\s+clorhidrico\b'
    r'|\bacido\s+nitrico\b'
    r'|\bacido\s+borico\b'
    r'|\bacido\s+fosforico\b'
    r'|\bacido\s+valproico\b'
    r'|\bacido\s+tranexamico\b'
    r'|\baminoacidos?\b'
    r'|\bacidos?\s+grasos?\b'
    r'|\bomega\s*[36]\b'
    r'|\bhongofenol\b'
    r'|\bhongo\s+ganoderma\b'
    r'|\bremovedor\s+de\s+hongos\b'
    r'|\bhongosin\b'
    r'|\bhongosan\b'
    r'|\btrazadona\s+hongos\s+alcohol\b'
    r'|\brobitussin\b(?!.*tusi)',  # Robitussin NO es tusi (antitusivo)
    flags=re.IGNORECASE
)

# --- ESTIMULANTES ---
# Productos que el LLM erróneamente clasifica como estimulantes
ESTIMULANTES_BLACKLIST: Set[str] = {
    # Medicamentos con cafeína (no son estimulantes recreativos)
    "acetaminofen cafeina", "acetaminofén cafeína",
    "aspirina cafeina", "aspirina más cafeína",
    "ergotamina cafeina", "ergotamina/cafeína",
    "sevedol",
    "cafiaspirina",
    "dipirona cafeina",
    "axcedrin", "excedrin",
    "cafeina", "cafeína",  # Solo cafeina sin contexto SPA
    # Bebidas energéticas (contexto colombiano - no SPA)
    "vive 100", "vive100",
    "awake 500", "awake", # También es plaguicida
    "red bull", "monster",
    "bebida energetica", "bebida energética",
    "energizante",
    # Productos para adelgazar (no SPA)
    "sibutramina",
    "clenbuterol",
    "fentermina",
    "pastilla para adelgazar", "pastillas para adelgazar",
    "pastilla adelgazar", "tabletas para adelgazar",
    "adelgazante", "adelgazantes",
    # Nicotina (no es SPA en este proyecto)
    "nicotina", "cigarro", "cigarrillo",
    # Productos agrícolas mal clasificados
    "methavin", "methergyn", "methylcarbamoyloxy",
    "methamex", "methomyl", "methox", "metsulfuron methyl",
    # Medicamentos mal escritos o que contienen "amina" sin ser SPA
    "amina",  # Solo "amina" sin anfetamina/metanfetamina
    "exalt",
    "cupex",
    "adrenalina",
    "epi-mek",
    "full mina",
    "profiamina",
    "campeon",
    "dulofetina",
    "actformina",
    "ally",
    "anabolicos",
    "benademina",
    "berifen",
    "brillaking",
    "concerta",  # A menos que tenga metilfenidato explícito
    "dantepamina",
    "dientiamina",
    "dotamina",
    "fastfen",
    "hawker",
    "hetaformina",
    "metforimina", "metformina",
    "tdi 180",
    "atomik",
    "daconi",
    "bupirop",
    "metandienone",
    "panzer amina",
    "pep pills",
    "roodup",
    "tenamfetamina",
}

# Regex para estimulantes (patrón de exclusión)
ESTIMULANTES_BLACKLIST_REGEX = re.compile(
    r'\bacetaminofen\s*(con\s*)?cafeina\b'
    r'|\baspirina\s*(mas\s*|con\s*)?cafeina\b'
    r'|\bergotamina\s*/?\s*cafeina\b'
    r'|\bsevedol\b'
    r'|\bcafiaspirina\b'
    r'|\bdipirona\s*cafeina\b'
    r'|\baxcedrin\b'
    r'|\bexcedrin\b'
    r'|\bvive\s*100\b'
    r'|\bawake\s*500\b'
    r'|\bred\s*bull\b'
    r'|\bmonster\b'
    r'|\bbebida\s+energetica\b'
    r'|\benergizante\b'
    r'|\bsibutramina\b'
    r'|\bclenbuterol\b'
    r'|\bfentermina\b'
    r'|\bpastilla(s)?\s+(para\s+)?adelgazar\b'
    r'|\btabletas\s+para\s+adelgazar\b'
    r'|\badelgazante\b'
    r'|\bnicotina\b'
    r'|\bcigarrillo?\b'
    r'|\bmethavin\b'
    r'|\bmethergyn\b'
    r'|\bmethomyl\b'
    r'|\bmetsulfuron\b'
    r'|\bcafeina\b(?!.*anfetamin)(?!.*metanfetamin)'
    r'|\bamina\b(?!.*anfetamin)(?!.*metanfetamin)'
    r'|\bexalt\b'
    r'|\bcupex\b'
    r'|\badrenalina\b'
    r'|\bepi-mek\b'
    r'|\bfull\s+mina\b'
    r'|\bprofiamina\b'
    r'|\bcampeon\b'
    r'|\bdulofetina\b'
    r'|\bactformina\b'
    r'|\bally\b'
    r'|\banabolico\b'
    r'|\bbenademina\b'
    r'|\bberifen\b'
    r'|\bbrillaking\b'
    r'|\bdantepamina\b'
    r'|\bdientiamina\b'
    r'|\bdotamina\b'
    r'|\bfastfen\b'
    r'|\bhawker\b'
    r'|\bhetaformina\b'
    r'|\bmetforimina\b|\bmetformina\b'
    r'|\btdi\s+180\b'
    r'|\batomik\b'
    r'|\bdaconi\b'
    r'|\bbupirop\b'
    r'|\bmetandienone\b'
    r'|\bpanzer\s+amina\b'
    r'|\bpep\s+pills\b'
    r'|\broodup\b'
    r'|\btenamfetamina\b',
    flags=re.IGNORECASE
)

# --- COCAÍNA Y DERIVADOS ---
# Productos que el LLM erróneamente clasifica como cocaína
COCAINA_BLACKLIST: Set[str] = {
    # Anestésicos locales (terminan en -caína pero NO son cocaína)
    "lidocaina", "lidocaína",
    "benzocaina", "benzocaína",
    "xilocaina", "xilocaína",
    "oxibuprocaina", "oxibuprocaína",
    "melocaina", "melocaína",
    "procaina", "procaína",
    "tetracaina", "tetracaína",
    "bupivacaina", "bupivacaína",
    "ropivacaina", "ropivacaína",
    "mepivacaina", "mepivacaína",
    "articaina", "articaína",
    "prilocaina", "prilocaína",
    # Productos con "coca" que no son cocaína
    "agua de coca",
    "acido de coca", "ácido de coca",
    "coca cola", "coca-cola", "cocacola",
    "alcohol de cocina",
    "cocadil",
    "veneno para el cultivo de coca",
    "azuco",  # azufre coloidal
    "folicocarbonatode",
    # Palabras similares que NO son cocaína
    "coquan",
    "cocaetileno",
    "coscina",
}

# Regex para cocaína (patrón de exclusión)
COCAINA_BLACKLIST_REGEX = re.compile(
    r'\blidocaina\b'
    r'|\bbenzocaina\b'
    r'|\bxilocaina\b'
    r'|\boxibuprocaina\b'
    r'|\bmelocaina\b'
    r'|\bprocaina\b'
    r'|\btetracaina\b'
    r'|\bbupivacaina\b'
    r'|\bropivacaina\b'
    r'|\bmepivacaina\b'
    r'|\barticaina\b'
    r'|\bprilocaina\b'
    r'|\bagua\s+de\s+coca\b'
    r'|\bacido\s+de\s+coca\b'
    r'|\bcoca[\s\-]?cola\b'
    r'|\balcohol\s+de\s+cocina\b'
    r'|\bcocadil\b'
    r'|\bcoquan\b'
    r'|\bcocaetileno\b'
    r'|\bcoscina\b',
    flags=re.IGNORECASE
)

# --- INHALANTES ---
# Productos que el LLM erróneamente clasifica como inhalantes
INHALANTES_BLACKLIST_REGEX = re.compile(
    r'\bfuga de gas\b'
    r'|\bfuga de gas \+ gas natural\b'
    r'|\bgas metano\b'
    r'|\bgas de mina de carbon\b'
    r'|\bcloro gaseoso\b'
    r'|\bdioxido de nitrogeno\b'
    r'|\bspray raid\b'
    r'|\braid\b'
    r'|\bacetileno\b'
    r'|\bgas liquido\b'
    r'|\blimpido\b'
    r'|\bestufa\b'
    r'|\bgas vehicular\b'
    r'|\bpropano\b'
    r'|\bgas industrial\b'
    r'|\bgas de uso industrial\b'
    r'|\binhalacion por sustancia desconocida por aire acondicionado\b'
    r'|\bvalvulina\b'
    r'|\boxido de etileno\b'
    r'|\bpolvo de extintor\b'
    r'|\baldehyde c 12\b'
    r'|\bcloruro de metileno\b'
    r'|\bgas refrigerante\b'
    r'|\bmezcla de gases\b'
    r'|\bgases de combustion\b'
    r'|\bcloroformo\b'
    r'|\bdesechos de la explotacion petrolifera\b'
    r'|\bdiclorometano\b'
    r'|\bfortage madera liquido\b'
    r'|\bgas desconocido\b'
    r'|\bgas natural - propano\b'
    r'|\bisocianatos\b'
    r'|\bbombona\b'
    r'|\bcloroeteno\b'
    r'|\bformol \+ lorsban\b'
    r'|\bgas casero\b'
    r'|\bgas extintor\b'
    r'|\bgas[- ]freaon 22 clorodifluorometano\b'
    r'|\bgases fluorados\b'
    r'|\bgases no especificados\b'
    r'|\bhipoclorito y desengrasante\b'
    r'|\bhumo\b'
    r'|\bhumo de extintor\b'
    r'|\bhumo de motor de gasolina\b'
    r'|\bhumo de motro de gasolina\b'
    r'|\binhalacion de cloro\b'
    r'|\binhalao humo extintor\b'
    r'|\blimpiador de ladrillos\b'
    r'|\bniquilamina- diuron- terbutre- oxacionana- pegante\b'
    r'|\bolor de quimico\b'
    r'|\bplagakill_ aerosol\b'
    r'|\bpvc\b'
    r'|\btiza china\b'
    r'|\bvapor de gasolina -humo\b'
    r'|\bgas irritante\b'
    r'|\bgas lacrimogeno\b'
    r'|\bgas pimienta\b'
    r'|\bsulfuro de hidrogeno\b'
    r'|\bsulfuro\b'
    r'|\bdioxido de azufre\b'
    r'|\bhelio\b'
    r'|\bbutano\b'
    r'|\bpentoxido de fosforo\b'
    r'|\balcohol industrial\b',
    flags=re.IGNORECASE
)

INHALANTES_BLACKLIST: Set[str] = {
    # Gases industriales / domésticos (NO son inhalantes SPA)
    "alcohol industrial",
    "aceite combustible para motores",
    "aceite de motor",
    "dioxido de azufre", "dióxido de azufre",
    "sulfuro de hidrogeno", "sulfuro de hidrógeno",
    "sulfuro de carbono",
    "sulfuro",
    "ambientador",
    "gas",  # Solo "gas" genérico
    "gas butano",
    "gas de carbono",
    "gas domiciliario",
    "gas natural",
    "pentoxido de fosforo", "pentóxido de fósforo",
    "rayol liquido",
    "fosgas ec",
    "easy off",
    "helio",
    "hexano",
    "intoxicacion con dioxido de carbono",
    "lubricantes",
    "mezcla de productos quimicos desconocidos",
    "mono de carbono", "monoxide de carbano",
    "monoxido de carbon", "monóxido de carbono",
    "pegatina",
    "randall",
    "resina de vidrio",
    "vap",
    "glufosinato de amonio",
}

# --- OPIOIDES ---
# Productos que el LLM erróneamente clasifica como opioides
OPIOIDES_BLACKLIST: Set[str] = {
    "bupropion", "bupropión",
    "tiotropio bromuro",
    "topiramato",
    # Medicamentos antidiarreicos que NO son SPA
    "loperamida", "loperamida hcl",
    "lomotil",
    # Antagonistas opioides (NO son opioides SPA)
    "naloxona", "naloxon",
    "naltrexone", "naltrexona", "naltrexon",
    # Amapola y derivados que NO son SPA
    "amapola", "ketum",
    # Variaciones mal escritas que NO son opioides
    "fentopen",
    "paracetadona",
    "tramina",
    "tranadona",
    "metmorfina",
    "fentoato",
    "tizodinametrazadona",
    "tragadolinavelafexina",
}

OPIOIDES_BLACKLIST_REGEX = re.compile(
    r'\bbupropion\b'
    r'|\btiotropio\s*bromuro\b'
    r'|\btopiramato\b'
    r'|\bloperamid\w*\b'
    r'|\blomotil\b'
    r'|\bnaloxon\w*\b'
    r'|\bnaltrexon\w*\b'
    r'|\bamapola\b'
    r'|\bketum\b'
    r'|\bfentopen\b'
    r'|\bparacetadona\b'
    r'|\btramina\b(?!dol)'
    r'|\btranadona\b'
    r'|\bmetmorfina\b'
    r'|\bfentoato\b'
    r'|\btizodinametrazadona\b'
    r'|\btragadolinavelafexina\b',
    flags=re.IGNORECASE
)

# --- TRANQUILIZANTES Y SEDANTES ---
# IMPORTANTE: Estos productos NO deben clasificarse como tranquilizantes en ESTE proyecto
TRANQUILIZANTES_BLACKLIST: Set[str] = {
    # Antihistamínicos (NO son tranquilizantes en este proyecto)
    "difenhidramina", "difenhidramina hcl",
    "dimenhidrinato", "dramamine",
    # Suplementos naturales (NO son tranquilizantes)
    "melatonina", "goma de melatonina", "gomitas de melatonina",
    "valeriana", "valeriano",
    "pasiflora", "passiflora", "pasionaria",
    # Relajantes musculares (NO son tranquilizantes en este proyecto)
    "tizanidina",
    # Antihistamínicos de segunda generación
    "hidroxizina", "hidroxicina", "atarax",
    # Escopolamina y análogos (NO son tranquilizantes, son anticolinérgicos)
    "hioscina", "hiocina", "hiosina",
    "butilbromuro de hioscina", "n-butilbromuro de hioscina",
    "hioscina butilbromuro",
    # Otros medicamentos que NO son tranquilizantes SPA
    "litio", "carbonato de litio",
}

# Regex para tranquilizantes (patrón de exclusión)
TRANQUILIZANTES_BLACKLIST_REGEX = re.compile(
    r'\bdifenhidra\w*\b'
    r'|\bdimenhidri\w*\b'
    r'|\bdramamine\b'
    r'|\bmelatonin\w*\b'
    r'|\bgoma\s+de\s+melatonin\w*\b'
    r'|\bvalerian\w*\b'
    r'|\bpasiflor\w*\b'
    r'|\bpassiflor\w*\b'
    r'|\bpasionaria\b'
    r'|\btizanidin\w*\b'
    r'|\bhidroxiz\w+\b'
    r'|\bhidroxicin\w+\b'
    r'|\batarax\b'
    r'|\bhioscin\w+\b'
    r'|\bhiocin\w+\b'
    r'|\bhiosin\w+\b'
    r'|\bbutilbromuro\s+de\s+hioscin\w*\b'
    r'|\bn[\s\-]?butilbromuro\s+de\s+hioscin\w*\b'
    r'|\blitio\b'
    r'|\bcarbonato\s+de\s+litio\b',
    flags=re.IGNORECASE
)

# --- ALCOHOL/ETANOL ---
ALCOHOL_BLACKLIST: Set[str] = {
    "colicort",
    "mirtapax",
    "azul de metileno",
    "cloroetano",
}

ALCOHOL_BLACKLIST_REGEX = re.compile(
    r'\bcolicort\b'
    r'|\bmirtapax\b'
    r'|\bazul\s+de\s+metileno\b'
    r'|\bcloroetano\b',
    flags=re.IGNORECASE
)

# --- CANNABINOIDES ---
# Patrón de SPA FUERTE para cannabinoides (para validar si hay trigger real)
CANNABINOIDES_STRONG_TRIGGERS = re.compile(
    r'\bmarihuana\b|\bmariguana\b|\bcannabis\b|\bthc\b|\bbareto\b'
    r'|\bcripa\b|\bcripy\b|\bvareta\b|\bhashish\b|\bweed\b|\bporro\b'
    r'|\bhuana\b',
    flags=re.IGNORECASE
)

CANNABINOIDES_BLACKLIST: Set[str] = {
    # Falsos positivos que contienen "can" pero NO son cannabis
    "ganabano", "guanabano",
    "rambler",
    "gruya", "grulla",
    "guayaguil", "guayaquil",
    "guayapal",
    "kalach green",
    "vaper", "vaporizador",
    "aqui si can",
}

CANNABINOIDES_BLACKLIST_REGEX = re.compile(
    r'\bganabano\b|\bguanabano\b'
    r'|\brambler\b'
    r'|\bgru[ly]a\b'
    r'|\bguaya(guil|pal)\b'
    r'|\bkalach\s+green\b'
    r'|\bvap(er|orizador)\b'
    r'|\baqui\s+si\s+can\b'
    r'|\bsustancia\s+verde\b',
    flags=re.IGNORECASE
)

# --- ESCOPOLAMINA ---
# IMPORTANTE: Escopolamina NO debe dispararse por hioscina/butilbromuro de hioscina
ESCOPOLAMINA_BLACKLIST: Set[str] = {
    # Agregar productos específicos aquí si es necesario
}

# Patrón para detectar hioscina (que NO debe ir a escopolamina)
HIOSCINA_PATTERN = re.compile(
    r'\bhioscin\w+\b'
    r'|\bhiocin\w+\b'
    r'|\bhiosin\w+\b'
    r'|\bbutilbromuro\s+de\s+hioscin\w*\b'
    r'|\bn[\s\-]?butilbromuro\s+de\s+hioscin\w*\b',
    flags=re.IGNORECASE
)

ESCOPOLAMINA_BLACKLIST_REGEX = re.compile(
    r'$^',  # Regex vacío (no coincide con nada)
    flags=re.IGNORECASE
)


# =========================================================
# FUNCIONES DE VERIFICACIÓN
# =========================================================

def is_in_general_blacklist(texto: str) -> bool:
    """
    Verifica si un texto está en la blacklist general o en las listas
    de productos agrícolas/limpieza que siempre van a 'otros'.
    """
    texto_lower = texto.lower().strip()
    
    # Verificar blacklist general
    if texto_lower in BLACKLIST_GENERAL:
        return True
    
    # Verificar keywords agrícolas
    for keyword in AGRO_KEYWORDS:
        if keyword in texto_lower:
            return True
    
    # Verificar ingredientes activos agrícolas
    for ingredient in AGRO_ACTIVE_INGREDIENTS:
        if ingredient in texto_lower:
            return True
    
    # Verificar productos de limpieza/corrosivos
    for keyword in HOUSEHOLD_CORROSIVE_KEYWORDS:
        if keyword in texto_lower:
            return True

    # Verificar gases/humo/emisiones industriales
    for keyword in INDUSTRIAL_GASES_KEYWORDS:
        if keyword in texto_lower:
            return True
    
    return False


def apply_category_blacklist(texto: str, categoria: str) -> bool:
    """
    Verifica si un texto debe ser EXCLUIDO de una categoría específica.
    Retorna True si el texto está en la blacklist de esa categoría.
    
    IMPORTANTE: Incluye lógica condicional para evitar falsos positivos:
    - Escopolamina: NO si hay hioscina
    - Cannabinoides: NO si NO hay trigger fuerte
    - Cocaína: NO si NO hay trigger fuerte
    """
    texto_lower = texto.lower().strip()
    
    if categoria == 'alucinogenos':
        if texto_lower in ALUCINOGENOS_BLACKLIST:
            return True
        if ALUCINOGENOS_BLACKLIST_REGEX.search(texto_lower):
            return True
            
    elif categoria == 'estimulantes':
        if texto_lower in ESTIMULANTES_BLACKLIST:
            return True
        if ESTIMULANTES_BLACKLIST_REGEX.search(texto_lower):
            return True
        
        # Lógica condicional: si solo tiene "cafeina" o "amina" sin SPA fuerte
        # NO la clasifiques como estimulante
        if re.search(r'\bcafein\w*\b', texto_lower):
            # Si tiene "cafeina" pero NO tiene anfetamina/metanfetamina/metilfenidato/etc
            if not re.search(
                r'\banfetamina\b|\bmetanfetamina\b|\bmetilfenidato\b'
                r'|\britalin\b|\bconcerta\b|\badderall\b|\bcrystal\b|\bcrystal meth\b'
                r'|\bspeed\b|\bcapilot\b|\bcriptonita\b',
                texto_lower
            ):
                return True  # Excluir (solo cafeína, no es SPA)
        
        if re.search(r'\bamina\b', texto_lower):
            # Si tiene "amina" pero NO tiene anfetamina/metanfetamina
            if not re.search(r'\banfetamina\b|\bmetanfetamina\b', texto_lower):
                return True  # Excluir
            
    elif categoria == 'cocaina_y_derivados':
        if texto_lower in COCAINA_BLACKLIST:
            return True
        if COCAINA_BLACKLIST_REGEX.search(texto_lower):
            return True
        
        # Lógica condicional: si NO hay trigger fuerte, excluir
        if not re.search(
            r'\bcocain\w*\b|\bcrack\b|\bbazuco\b|\bperico\b'
            r'|\bbase de coca\b|\bbenzoylmethylecgonine\b',
            texto_lower
        ):
            # No tiene trigger fuerte para cocaína
            return False  # Permitir si el LLM lo clasificó (solo hará si muy seguro)
        
    elif categoria == 'inhalantes':
        if texto_lower in INHALANTES_BLACKLIST:
            return True
        if INHALANTES_BLACKLIST_REGEX.search(texto_lower):
            return True
            
    elif categoria == 'opioides':
        if texto_lower in OPIOIDES_BLACKLIST:
            return True
        if OPIOIDES_BLACKLIST_REGEX.search(texto_lower):
            return True
            
    elif categoria == 'tranquilizantes_y_sedantes':
        if texto_lower in TRANQUILIZANTES_BLACKLIST:
            return True
        if TRANQUILIZANTES_BLACKLIST_REGEX.search(texto_lower):
            return True
            
    elif categoria == 'alcohol_etanol':
        if texto_lower in ALCOHOL_BLACKLIST:
            return True
        if ALCOHOL_BLACKLIST_REGEX.search(texto_lower):
            return True
            
    elif categoria == 'cannabinoides':
        if texto_lower in CANNABINOIDES_BLACKLIST:
            return True
        if CANNABINOIDES_BLACKLIST_REGEX.search(texto_lower):
            return True
        
        # Lógica condicional: si NO hay trigger fuerte, excluir
        if not CANNABINOIDES_STRONG_TRIGGERS.search(texto_lower):
            return True  # Excluir si no hay trigger fuerte
            
    elif categoria == 'escopolamina':
        # CRÍTICO: Escopolamina NO debe asignarse si hay hioscina/butilbromuro de hioscina
        if HIOSCINA_PATTERN.search(texto_lower):
            return True  # Excluir escopolamina si hay hioscina
        
        if texto_lower in ESCOPOLAMINA_BLACKLIST:
            return True
        if ESCOPOLAMINA_BLACKLIST_REGEX.search(texto_lower):
            return True
    
    return False


def filter_categories_with_blacklist(texto: str, categorias: list) -> list:
    """
    Filtra una lista de categorías eliminando aquellas que están en blacklist
    para el texto dado.
    
    Args:
        texto: El nombre del producto
        categorias: Lista de categorías asignadas por el LLM
        
    Returns:
        Lista de categorías filtradas (sin las que están en blacklist)
    """
    if not categorias:
        return ['otros']
    
    categorias_filtradas = []
    for cat in categorias:
        if not apply_category_blacklist(texto, cat):
            categorias_filtradas.append(cat)
    
    # Si todas las categorías fueron filtradas, devolver 'otros'
    return categorias_filtradas if categorias_filtradas else ['otros']
