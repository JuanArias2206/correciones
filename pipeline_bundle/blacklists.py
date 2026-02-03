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

# --- ALUCINÓGENOS ---
# Productos que el LLM erróneamente clasifica como alucinógenos
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
    # Antitusivos
    "antitusivo", "antitusivos", "robitusin", "robitussin",
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
    r'|\bantitusivo\b'
    r'|\brobitusin\b',
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
    # Bebidas energéticas (contexto colombiano - no SPA)
    "vive 100", "vive100",
    "awake 500", "awake", # También es plaguicida
    "red bull", "monster",
    "bebida energetica", "bebida energética",
    "energizante",
    # Productos agrícolas mal clasificados
    "methavin", "methergyn", "methylcarbamoyloxy",
    "methamex", "methomyl", "methox", "metsulfuron methyl",
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
    r'|\bmethavin\b'
    r'|\bmethergyn\b'
    r'|\bmethomyl\b'
    r'|\bmetsulfuron\b',
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
    r'|\bcocadil\b',
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
    r'|\bgas pimienta\b',
    flags=re.IGNORECASE
)

INHALANTES_BLACKLIST: Set[str] = {
    # Agregar productos específicos aquí
}

# --- OPIOIDES ---
# Productos que el LLM erróneamente clasifica como opioides
OPIOIDES_BLACKLIST: Set[str] = {
    "bupropion", "bupropión",
    "tiotropio bromuro",
    "topiramato",
}

OPIOIDES_BLACKLIST_REGEX = re.compile(
    r'\bbupropion\b'
    r'|\btiotropio\s*bromuro\b'
    r'|\btopiramato\b',
    flags=re.IGNORECASE
)

# --- TRANQUILIZANTES Y SEDANTES ---
TRANQUILIZANTES_BLACKLIST: Set[str] = {
    # Agregar productos específicos aquí si es necesario
}

TRANQUILIZANTES_BLACKLIST_REGEX = re.compile(
    r'$^',  # Regex vacío (no coincide con nada)
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
CANNABINOIDES_BLACKLIST: Set[str] = {
    # Agregar productos específicos aquí si es necesario
}

CANNABINOIDES_BLACKLIST_REGEX = re.compile(
    r'$^',  # Regex vacío (no coincide con nada)
    flags=re.IGNORECASE
)

# --- ESCOPOLAMINA ---
ESCOPOLAMINA_BLACKLIST: Set[str] = {
    # Agregar productos específicos aquí si es necesario
}

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
            
    elif categoria == 'cocaina_y_derivados':
        if texto_lower in COCAINA_BLACKLIST:
            return True
        if COCAINA_BLACKLIST_REGEX.search(texto_lower):
            return True
            
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
            
    elif categoria == 'escopolamina':
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
