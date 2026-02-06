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
        r'\bacetaminofen\b|\bparacetamol\b|\bibuprofeno\b|\bibuprofen\b|\bnaproxeno\b|\bnaproxseno\b'
        r'|\bdiclofenaco\b|\bdifenaco\b|\bmeloxicam\b|\bmoloxicam\b|\bpiroxicam\b|\bketoprofeno\b'
        r'|\baines\b|\baspirina\b(?!.*psicoactiv)|\basa\b|\bácido acetilsalicílico\b'
        r'|\bácido salicílico\b|\bsalicílico\b|\bsacac\b'
        # Antibióticos (principales)
        r'|\bamoxicilina\b|\bamoxacilina\b|\bcefalexina\b|\bcetalexina\b|\bcefalo\b'
        r'|\bmetronidazol\b|\bmetrodinazol\b|\bciprofloxacina\b|\bofloxacina\b'
        r'|\bazitromicina\b|\bclaritromicina\b|\bclindamicina\b|\baciclovir\b'
        r'|\bnitrofurantoina\b|\bampicilina\b|\bdoxiciclina\b|\boxitetraciclina\b'
        r'|\bdicloxacilina\b|\bfluconazol\b|\bketoconazol\b|\beritromicina\b'
        r'|\bcefradina\b|\bcefazolina\b|\bgentamicina\b|\btetraciclina\b'
        r'|\pantibiotico\b|\bcefalo\b|\bcefalosporina\b|\bpenisilina\b'
        # Antiácidos y gastrointestinales
        r'|\bomeprazol\b|\bomeprasol\b|\besomeprazol\b|\bpantoprazol\b'
        r'|\blansoprazol\b|\branitidina\b|\bdomperidona\b|\bmetoclopramida\b'
        r'|\bmetroclopramida\b|\bmetroclopicida\b|\btrimebutina\b|\bbisacodilo\b'
        r'|\bsucralfate\b|\bsimeticona\b|\bmisoprostol\b|\bcarbon activado\b'
        r'|\bmucinex\b'
        # Antihipertensivos y cardiovasculares
        r'|\blosartan\b|\blozartan\b|\bamlodipino\b|\benalapril\b|\bcaptopril\b'
        r'|\bvalsartan\b|\bmetoprolol\b|\bmetroprolol\b|\bcarvedilol\b|\bpropanolol\b'
        r'|\bbisoprolol\b|\bnebivolol\b|\bhidroclorotiazida\b|\bfurosemida\b'
        r'|\bnifedipino\b|\bverapamilo\b|\bprazosin\b|\bespironolactona\b'
        r'|\blisinopril\b|\bperindopril\b|\btamsulosina\b|\brosuvastatina\b'
        r'|\batorvastatina\b|\blovastatina\b|\bgemfibrozilo\b|\btelemisartan\b'
        r'|\bperoxido de hidrogeno\b|\bhidrogeno peroxido\b'
        # Antihistamínicos y respiratorios
        r'|\bloratadina\b|\bcetirizina\b|\bdesloratadina\b|\bclorfeniramina\b'
        r'|\bclorfenamina\b|\bclorofenamina\b|\bfexofenadina\b|\blevocetirizina\b'
        r'|\bmontelukast\b|\bsalbutamol\b|\bsalbutanol\b|\bbudesonida\b'
        r'|\bsumriptam\b|\bsumatriptam\b'
        # Vitaminas y suplementos
        r'|\btiamina\b|\bacido folico\b|\bácido fólico\b|\bsulfato ferroso\b'
        r'|\bvitaminas\b|\bmultivitaminicos\b|\bcomplejo b\b|\bcalcio\b'
        r'|\bcarbonat[eo] de calcio\b|\bzinc\b|\bhierro\b|\bcentrum\b'
        r'|\bomega 3\b|\bginkgo biloba\b|\bginkobiloba\b|\bbiotina\b'
        r'|\bgluconato de calcio\b|\bpeditrace\b'
        # Anticonvulsivantes (no sedantes)
        r'|\bcarbamazepina\b|\bcarbamacepina\b|\blevetiracetam\b|\bgabapentina\b'
        r'|\boxcarbazepina\b|\boxcarbazepia\b|\bfenitoina\b|\blacosamida\b'
        r'|\bpregabalina\b|\blamotrigina\b|\btamotrigina\b|\bribaviricetam\b'
        # Antidiabéticos
        r'|\bmetformina\b|\bglibenclamida\b|\binsulina\b|\bdeglutec\b'
        r'|\bsitagliptina\b|\bempagliflozina\b|\bjardiance\b'
        # Psiquiátricos/neurológicos
        r'|\bfluoxetina\b|\bparoxetina\b|\bsertalina\b|\bsertralina\b|\bsentralina\b'
        r'|\bescitalopram\b|\bcitalopram\b|\bvenlafaxina\b|\bvelafaxina\b'
        r'|\bduloxetina\b|\bfluvoxamina\b|\bclomipramina\b|\bamitriptilina\b'
        r'|\bamitriptilina\b|\binmipramina\b|\bimipramine\b|\bimipramina\b'
        r'|\bmirtazapina\b|\bmirtazopina\b|\btrazodon\b|\btrazadona\b'
        r'|\btrazodone\b|\bbupropion\b|\bbrupopion\b|\bdolutegravir\b'
        r'|\bpramipexol\b|\bapiprazol\b|\brisperidona\b|\bollanzapina\b'
        r'|\bquetiapina\b|\bclozapina\b|\bhaloperidol\b|\bclorpromazina\b'
        r'|\bamisulprida\b|\bpipotiazina\b|\blevomepromazina\b'
        # Otros medicamentos comunes
        r'|\blevotiroxina\b|\bsildenafil\b|\bviagra\b|\bflunarizina\b'
        r'|\bminoxidil\b|\bivermectina\b|\balbendazol\b|\bmareol\b'
        r'|\bnitazoxianida\b|\bpamoato de pirantel\b|\bpiperazina\b'
        r'|\bciclosporina\b|\bmemantina\b|\brivastigmina\b|\bdonepezilo\b'
        r'|\btinidazol\b|\bcalcitriol\b|\bclonidina\b|\bbiperideno\b'
        r'|\bmetotrexate\b|\bcabergolina\b|\bmetimazol\b|\bbetahistina\b'
        r'|\boximetazolina\b|\bnafazolina\b|\bpantoprazol\b|\bpantrozol\b'
        r'|\bdicloxacilina\b|\bcefradina\b|\britonavir\b|\bdolutegravir\b'
        r'|\btenofovir\b|\bemtricitabina\b|\bnevirapina\b|\bnevirapina\b'
        r'|\bpentoxifilina\b|\bteofilina\b|\bciproheptadina\b|\bciproeptadina\b'
        r'|\bclobazam\b|\bciclobenzapina\b|\bcyclobenzaprine\b|\bmebendazol\b'
        r'|\bpirimetamina\b|\bcarbendazim\b|\bticarcilina\b|\btazobactam\b'
        r'|\bdiclorvos\b|\btacrolimus\b|\bmedroxiprogesterona\b'
        r'|\btrimetoprim\b|\bsulfametoxazol\b|\bsulfametazol\b'
        r'|\bmercaptopurina\b|\bmetildopa\b|\bmetildigoxina\b'
        r'|\bmedicamentos\b|\bmultiples medicamentos\b|\bmezcla de medicamentos\b'
        r'|\bpolifarmacia\b|\bpolimedicamentosa\b|\bmedicinas\b'
        r'|\bdolex\b|\btylenol\b|\badvil\b|\bexcedrin\b|\bneosaldina\b'
        r'|\bsampsic\b|\bpanatox\b|\bsevedol\b|\bdolofen\b|\bbuprion\b'
    ),

    'productos_limpieza': (
        # Cloros y blanqueadores
        r'\bclorox\b|\bhipoclorito\b(?!.*sodi[uo]m)'
        r'|\bhipoclorito de sodio\b|\bblanqueador\b|\bcloro\b(?!.*pirifo)'
        r'|\bcloro granulado\b|\blimpido\b|\blímpido\b'
        r'|\bdioxido de cloro\b|\bdióxido de cloro\b|\bcloro activo\b|\bcloruro de cal\b'
        # Detergentes y limpiadores
        r'|\bdetergente\b|\bfabuloso\b|\bdesinfectante\b|\bproductos de limpieza\b'
        r'|\bvanish\b|\bsuavitel\b|\bsoflan\b|\bjabon\b(?!.*bactericid)'
        r'|\bambientador\b|\bcolonia\b|\bshampoo\b|\bchampú\b|\btalco\b|\bcrema alisadora\b'
        r'|\besmalte de uñas\b|\bdilusor de esmalte\b|\bremovedor de esmalte\b'
        r'|\blociones?\b|\bjabon antibacterial\b|\bgel antibacterial\b'
        r'|\barsall\b|\bador\b|\bpagasol\b|\blija\b|\bablana\b|\bpinol\b'
        r'|\blavarropa\b|\blavarropes\b|\blavaplatos\b|\bacondicionador\b'
        r'|\bsapone\b|\bdesmaquillante\b|\bdemaquillante\b|\bdilusor\b'
        r'|\bscan\b|\bwindex\b|\blimpiacristales\b|\btorpol\b|\blimpia\b'
        r'|\blimpiadera\b|\blimpiadoras\b|\bpiso\b|\bpisos\b'
        # Ácidos industriales/limpieza
        r'|\bsoda caustica\b|\bsoda caústica\b|\bhidroxido de sodio\b|\bhidróxido de sodio\b'
        r'|\bacido muriatico\b|\bácido muriático\b|\bacido clorhidrico\b|\bácido clorhídrico\b'
        r'|\bacido nitrico\b|\bácido nítrico\b|\bamoniaco\b|\bamonio\b|\bagua oxigenada\b'
        r'|\bperoxido de aluminio\b|\bformol\b|\bformaldehido\b|\bvinagre\b'
        r'|\bborax\b|\bbórax\b|\btriclosan\b|\btricloroetano\b|\btricloroetileno\b'
        r'|\bpercloro etileno\b|\bpercloroetileno\b|\boxido de etileno\b|\bóxido de etileno\b'
        r'|\bfenol\b|\bfenoles\b|\bcarbonato de sodio\b|\bbicarbonato de sodio\b'
        r'|\bsoda carbonato\b|\bsodio carbonato\b|\bsodio bicarb\b'
        r'|\bacido sulfurico\b|\bácido sulfúrico\b|\bacido fosforico\b|\bácido fosfórico\b'
        r'|\bsol amoniaco\b|\bsolución amoniacal\b|\bperóxido\b|\bperoxido\b'
        r'|\bperóxido de hidrogeno\b|\bperoxido de hidrógeno\b'
        # Productos de limpieza especiales
        r'|\bdeshollinador\b|\bdeshollinante\b|\bdesodorante\b|\bdesodor\b'
        r'|\baroma\b|\baromaritmo\b|\baromatizante\b'
        r'|\bbrasso\b|\bpronto\b|\bvapol\b|\bmusol\b|\blisol\b|\blysol\b'
        r'|\brevo\b|\bflipazo\b|\bsplash\b|\bsoftlan\b'
        r'|\balbayalde\b|\btrementina\b|\btrementine\b|\btiner\b|\bthinner\b'
        r'|\bdiluyente\b|\bsolvente\b|\bsolventes\b'
        r'|\bcosmeticos\b|\bcrema\b(?!.*medic)|\blocion de bebe\b'
        r'|\bpapel higienico\b|\bpapel higiénico\b|\btoalla\b|\btoallitas\b'
        r'|\btoallitas humedas\b|\btoallitas húmedas\b|\btoallitas desinfectantes\b'
        r'|\btissue\b|\bpañales\b|\bpantys\b|\bcompresas\b'
        r'|\bsellador\b|\bprotector\b|\bpolicarbonato\b|\bsuavisante\b|\bsuavizante\b'
        r'|\bsimil clorox\b|\btolquén\b|\btolquen\b'
    ),

    'gases_combustibles': (
        # Gases industriales (NO inhalantes SPA)
        r'\bgas natural\b|\bgas propano\b|\bpropano\b|\bgas butano\b|\bbutano\b'
        r'|\bgas metano\b|\bmetano\b|\bgas liquido\b|\bfuga de gas\b'
        r'|\bgas de mina\b|\bdioxido de carbono\b|\bdióxido de carbono\b'
        r'|\bmonoxido de carbono\b|\bmonóxido de carbono\b|\bdioxido de nitrogeno\b'
        r'|\bdióxido de nitrogeno\b|\bhelio\b'
        r'|\bmezcla de gases\b|\bcloro\b(?!.*activ)|\bcloro gaseoso\b|\bgas cloro\b'
        # Combustibles
        r'|\bacpm\b|\baceite combustible\b|\baceite de motor\b|\baceite de moto\b'
        r'|\baceite\b(?!.*esenci)|\bkerosene\b|\bgasolina\b(?!.*inhala)'
        r'|\bethanol\b(?!.*alcohol)|\betanol industrial\b|\bpropanol\b'
        r'|\baceite hidraulico\b|\baceite hidráulico\b|\bpetroleo\b|\bpetróleo\b'
        r'|\bGLP\b|\bgas licuado\b|\bfuel oil\b|\bfuel\b'
        # Otros gases no-SPA
        r'|\bgas pimienta\b|\bgas lacrimogeno\b|\bgas irritante\b'
        r'|\bfosfuro de aluminio\b|\bhumo\b|\bmercurio\b(?!.*termometro)'
        r'|\bazufre\b|\bóxido de etileno\b|\boxido de etileno\b'
        r'|\bpentoxido de fosforo\b|\bpentóxido de fósforo\b'
    ),
}

# =========================================================
# PATRONES COMPILADOS (para mejor rendimiento)
# =========================================================

compiled_patterns: Dict[str, Pattern] = {
    k: re.compile(v, flags=re.IGNORECASE) 
    for k, v in substance_patterns.items()
}
