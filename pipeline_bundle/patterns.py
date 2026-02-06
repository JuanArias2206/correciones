# -*- coding: utf-8 -*-
"""
PATRONES REGEX PARA CLASIFICACIÓN DE SUSTANCIAS
================================================
Este módulo contiene todos los patrones regex utilizados para clasificar
sustancias como respaldo cuando el LLM falla o no está disponible.

Los patrones se compilan una sola vez para mejor rendimiento.
"""

import re
from typing import Dict, Pattern

# =========================================================
# DICCIONARIO DE PATRONES REGEX POR CATEGORÍA
# =========================================================

substance_patterns: Dict[str, str] = {
    # Alucinógenos: sin patrón genérico para "ácidos"
    'alucinogenos': (
        r'\blsd\b|\btusi\b|\btussi\b|\btusy\b|\btussy\b|\btussyl\b|\btusivet\b'
        r'|\b2cb\b|\bcandy fly\b|\btrip\b|\blucy\b|\bpapel\b|\bacidos\b|\bácidos\b'
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
        r'\bclonacepam\b|\bclonacepan\b|\bclonacepa\b'
        r'|\bclonazepina\b|\bclorazepan\b|\bamitriptilina\b|\bsertralina\b|\bfluoxetina\b|'
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
# PATRONES COMPILADOS (para mejor rendimiento)
# =========================================================

compiled_patterns: Dict[str, Pattern] = {
    k: re.compile(v, flags=re.IGNORECASE) 
    for k, v in substance_patterns.items()
}
