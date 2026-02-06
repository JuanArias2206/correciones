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

    # =========================================================
    # NUEVAS CATEGORÍAS - MEDICAMENTOS, LIMPIEZA, GASES
    # =========================================================
    
    'medicamentos_no_SPA': (
        # Analgésicos comunes
        r'\bacetaminofen\b|\bparacetamol\b|\bibuprofeno\b|\bnaproxeno\b|\bdiclofenaco\b|\bmeloxicam\b'
        r'|\bpiroxicam\b|\bketoprofeno\b|\baines\b|\baspirina\b(?!.*psicoactiv)'
        # Antibióticos
        r'|\bamoxicilina\b|\bamoxacilina\b|\bcefalexina\b|\bmetronidazol\b|\bciprofloxacina\b'
        r'|\bazitromicina\b|\bclaritromicina\b|\bclindamicina\b|\baciclovir\b|\bnitrofurantoina\b'
        r'|\bampicilina\b|\bdoxiciclina\b|\bdicloxacilina\b|\bfluconazol\b|\bketoconazol\b'
        r'|\beritromicina\b|\bcefradina\b|\bcefazolina\b|\bgentamicina\b|\btetraciclina\b'
        r'|\bantibiotico\b'
        # Antiácidos y gastrointestinales
        r'|\bomeprazol\b|\bomeprasol\b|\besomeprazol\b|\blansoprazol\b|\bmetoclopramida\b'
        r'|\btrimebutina\b|\bbisacodilo\b|\bsucralfate\b|\bsimeticona\b'
        # Antihipertensivos y cardiovasculares
        r'|\blosartan\b|\blozartan\b|\bamlodipino\b|\benalapril\b|\bcaptopril\b|\bvalsartan\b'
        r'|\bmetoprolol\b|\bcarvedilol\b|\bpropanolol\b|\bbisoprolol\b|\bhidroclorotiazida\b'
        r'|\bfurosemida\b|\bnifedipino\b|\bverapamilo\b|\bprazosin\b|\bespironolactona\b'
        r'|\blisinopril\b|\btamsulosina\b|\brosuvastatina\b|\batorvastatina\b|\blovastatina\b'
        r'|\bgemfibrozilo\b|\bantihipertensivos\b'
        # Antihistamínicos y respiratorios
        r'|\bloratadina\b|\bcetirizina\b|\bdesloratadina\b|\bclorfeniramina\b|\bclorfenamina\b'
        r'|\bfexofenadina\b|\blevocetirizina\b|\bmontelukast\b|\bsalbutamol\b'
        # Vitaminas y suplementos
        r'|\btiamina\b|\bacido folico\b|\bsulfato ferroso\b|\bvitaminas\b|\bmultivitaminicos\b'
        r'|\bcomplejo b\b|\bcalcio\b|\bcarbonat[eo] de calcio\b|\bzinc\b|\bhierro\b|\bcentrum\b'
        r'|\bomega 3\b|\bginkgo biloba\b|\bginkobiloba\b|\bbiotina\b'
        # Anticonvulsivantes (no sedantes)
        r'|\bcarbamazepina\b|\bcarbamacepina\b|\blevetiracetam\b|\bgabapentina\b|\boxcarbazepina\b'
        r'|\bfenitoina\b|\blacosamida\b|\bpregabalina\b|\blamotrigina\b'
        # Antidiabéticos
        r'|\bmetformina\b|\bglibenclamida\b|\binsulina\b|\bdeglutec\b|\bsitagliptina\b|\bempagliflozina\b'
        r'|\bjardiance\b'
        # Otros medicamentos comunes
        r'|\blevotiroxina\b|\bsildenafil\b|\bviagra\b|\bflunarizina\b|\bminoxidil\b|\bivermectina\b'
        r'|\balbendazol\b|\bmareol\b|\bnitazoxianida\b|\bpamoato de pirantel\b|\bciclosporina\b'
        r'|\bmemantina\b|\brivastigmina\b|\bdonepezilo\b|\btinidazol\b|\bcalcitriol\b'
        r'|\blevopromazina\b|\bhaloperidol\b|\bclonidina\b|\bbiperideno\b|\bamisulprida\b'
        r'|\bmetotrexate\b|\bcabergolina\b|\bmetimazol\b|\bbetahistina\b|\boximetazolina\b'
        r'|\bmedicamentos\b|\bmultiples medicamentos\b|\bmezcla de medicamentos\b'
        r'|\bdolex\b|\btylenol\b|\badvil\b|\bexcedrin\b|\bneosaldina\b|\bmigrañon\b'
    ),

    'productos_limpieza': (
        # Cloros y blanqueadores
        r'\bclorox\b|\bhipoclorito\b(?!.*sodi[uo]m)'
        r'|\bhipoclorito de sodio\b|\bblanqueador\b|\bcloro\b(?!.*pirifo)'
        r'|\bcloro granulado\b|\blimpido\b|\blímpido\b'
        # Detergentes y limpiadores
        r'|\bdetergente\b|\bfabuloso\b|\bdesinfectante\b|\bproductos de limpieza\b'
        r'|\bvanish\b|\bsuavitel\b|\bsoflan\b|\bjabon\b(?!.*bactericid)'
        r'|\bambientador\b|\bcolonia\b|\bshampoo\b|\btalco\b|\bcrema alisadora\b'
        r'|\besmalte de uñas\b|\bdilusor de esmalte\b|\bremovedor de esmalte\b'
        r'|\blociones?\b|\bjabon antibacterial\b|\bgel antibacterial\b'
        # Ácidos industriales/limpieza
        r'|\bsoda caustica\b|\bsoda caústica\b|\bhidroxido de sodio\b|\bhidróxido de sodio\b'
        r'|\bacido muriatico\b|\bácido muriático\b|\bacido clorhidrico\b|\bácido clorhídrico\b'
        r'|\bacido nitrico\b|\bácido nítrico\b|\bamoniaco\b|\bamonio\b|\bagua oxigenada\b'
        r'|\bperoxido de aluminio\b|\bformol\b|\bformaldehido\b|\bvinagre\b'
        r'|\bcosmeticos\b|\bcrema\b(?!.*medic)|\blocion de bebe\b'
    ),

    'gases_combustibles': (
        # Gases industriales (NO inhalantes SPA)
        r'\bgas natural\b|\bgas propano\b|\bpropano\b|\bgas butano\b|\bbutano\b'
        r'|\bgas metano\b|\bmetano\b|\bgas liquido\b|\bfuga de gas\b'
        r'|\bgas de mina\b|\bdioxido de carbono\b|\bdióxido de carbono\b'
        r'|\bmonoxido de carbono\b|\bmonóxido de carbono\b|\bdioxido de nitrogeno\b'
        r'|\bdióxido de nitrogeno\b|\bhelio\b'
        # Combustibles
        r'|\bacpm\b|\baceite combustible\b|\baceite de motor\b|\baceite de moto\b'
        r'|\baceite\b(?!.*esenci)|\bkerosene\b|\bgasolina\b(?!.*inhala)'
        r'|\bethanol\b(?!.*alcohol)|\betanol industrial\b|\bpropanol\b'
        # Otros gases no-SPA
        r'|\bgas pimienta\b|\bgas lacrimogeno\b|\bgas irritante\b|\bcloro gaseoso\b'
        r'|\bfosfuro de aluminio\b|\bhumo\b|\bmercurio\b(?!.*termometro)'
    ),
}

# =========================================================
# PATRONES COMPILADOS (para mejor rendimiento)
# =========================================================

compiled_patterns: Dict[str, Pattern] = {
    k: re.compile(v, flags=re.IGNORECASE) 
    for k, v in substance_patterns.items()
}
