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
        r'\bdietilamida\b|\bacido liser\b|\bacido lisergico\b|\bpcp\b|\bfenciclidina\b|\bpeace pill\b|'
        r'\bangel dust\b|\bpeyote\b|\bmescalina\b|\bhongos? psilocybin\b|\becstasis\b|'
        r'\bextasis\b|\badam\b|\bmdma\b|\btacha\b|\bmolly\b|\bketamina\b|\bdmt\b|'
        r'\bamt\b|\bfoxy\b|\bsalvia\b|\bjahe\b|\brueda\b|\byaje\b|\byage\b|'
        r'\bhongo alucinogeno\b'
    ),

    'cocaina_y_derivados': (
        r'\bbazuco\b|\bcocaina\b|\bcrack\b|\bmetilecnonina\b|\bperico\b|'
        r'\bbenzoilmetilecgonina\b|\bpatraciado\b|\bbase de coca\b|\bpasta de coca\b'
    ),

    'opioides': (
        r'\bopioides?\b|\bopiodes\b|\bheroina\b|\bfentanil\b|\bamapola\b|\bmetadona\b|\bbrown\b|'
        r'\bmorfina\b|\btramadol\b|\btramal\b|\boxicontin\b|\boxicodona\b|\bcodeina\b|'
        r'\bpercocet\b|\bhidroxicina\b|\bhidrocodeina\b|\bhidromorfona\b|\bparacodina\b|'
        r'\bopiaceos\b|\btramadol y acetaminofen\b|\bacetaminofen tramadol\b|'
        r'\bwinadeine\b|\bdihidrocodeina\b'
    ),

    'estimulantes': (
        r'\bmetanfetaminas?\b|\bbenzedrine\b|\bcriptonita\b|\bcristal\b|\bhielo\b|'
        r'\bcrank\b|\banfetaminas?\b|\bmethylfenidato\b|\bmetilfenidato\b|\britalin\b|\britalina\b|'
        r'\badderall\b|\bconcerta\b|\bcapilots\b|\bpep pills\b|\bspeed\b|\bcateina\b|'
        r'\bawake\b|\bpower max\b|\batomoxetina\b'
    ),

    # Inhalantes: solo SPA inhaladas típicas (pegantes/solventes/poppers/etc.)
    'inhalantes': (
        r'\boxido nitrico\b|\bpopper\b|\bliquidos? solventes?\b|\bspray de pintura\b|'
        r'\blimpiadores? de computadores?\b|\baerosoles? en spray\b|\bpegantes?\b|'
        r'\bboxer\b|\bmarcadores?\b|\bsacol\b|\bdesengrasante\b|\bdisolventes?\b|'
        r'\bsolucion\b|\bhidrocarburo\b|\bihidrocarburo\b|\bhidrocarburos\b|\bgasolina\b|\bdik\b|\bdick\b|'
        r'\blady\b|\bnitrito\b|\bnitrato de amilo\b|\bvarsol\b|\bthinner\b|\bacetona\b|'
        r'\bremovedor de esmalte\b|\bsolvente de pintura\b'
        r'|\bformol\b|\bformaldehido\b|\btetrahidrofurano\b|\btetrahidrofurano disolvente\b'
        r'|\bdisolvente desconocido\b|\bsolvente desconocido\b|\bisoflurano\b'
        r'|\bnitromax\b|\btolueno\b|\balcohol isopropilico\b'
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
        r'\bmarihuana\b|\bcrippy\b|\bcripy\b|\bthc\b|\btetrahidrocanabinol\b|\bcriptonita\b|'
        r'\bmarimba\b|\bcannabis\b|\bcanabis\b|\bcripa\b|\bcrispi\b|\bvareto\b|\bbareto\b|'
        r'\byerba\b|\bsativa\b|\bhashish\b'
    ),

    'escopolamina': (
        r'\bescopolamina\b|\bescopilina\b|\bcacao sabanero\b|\bborrachera\b|\bburundanga\b|\bfloripondio\b|\bfloripondia\b|\bborrachero\b'
    ),

    # =========================================================
    # NUEVAS CATEGORÍAS - MEDICAMENTOS, LIMPIEZA, GASES
    # =========================================================
    
    'medicamentos_no_SPA': (
        # Analgesicos comunes - ENRIQUECIDO
        r'\bacetaminofen\b|\bparacetamol\b|\bibuprofeno\b|\bibuprofen\b|\bnaproxeno\b|\bnaproxseno\b'
        r'|\bdiclofenaco\b|\bdifenaco\b|\bmeloxicam\b|\bmoloxicam\b|\bpiroxicam\b|\bketoprofeno\b'
        r'|\baines\b|\baspirina\b(?!.*psicoactiv)|\basa\b|\bacido acetilsalicilico\b'
        r'|\bacido salicilico\b|\bsalicilico\b|\bsacac\b|\bpanatox\b|\bsampsic\b|\bdolofen\b'
        r'|\btramadol\b|\btramal\b|\bnaproxeno sodico\b|\bnaproxeno 500 mg\b|\bnaproxeno gr\b'
        # Antibioticos - ENRIQUECIDO
        r'|\bamoxicilina\b|\bamoxacilina\b|\bcefalexina\b|\bcetalexina\b|\bcefalo\b'
        r'|\bmetronidazol\b|\bmetrodinazol\b|\bciprofloxacina\b|\bofloxacina\b|\bnorfloxacina\b'
        r'|\bazitromicina\b|\bclaritromicina\b|\bclindamicina\b|\baciclovir\b|\bnitrofurantoina\b'
        r'|\bampicilina\b|\bdoxiciclina\b|\boxitetraciclina\b|\bdicloxacilina\b|\bfluconazol\b'
        r'|\bketoconazol\b|\beritromicina\b|\bcefradina\b|\bcefazolina\b|\bgentamicina\b'
        r'|\btetraciclina\b|\bcefalosporina\b|\bpenisilina\b|\bticarcilina\b|\btazobactam\b'
        r'|\bterbinafina\b|\btiabendazol\b|\btriclabendazol\b|\btrimetoprim sulfametoxazol\b'
        # Antivirales - NUEVO/ENRIQUECIDO
        r'|\britonavir\b|\bdolutegravir\b|\btenofovir\b|\bemtricitabina\b|\bnevirapina\b'
        r'|\bzidovudina\b|\bzanamivir\b|\blamivudina\b|\btenofovir alafenamida\b'
            r'|\btrimebatina\b|\bbisacodilo\b'
        # Antiacidos y gastrointestinales - ENRIQUECIDO
        r'|\bomeprazol\b|\bomeprasol\b|\besomeprazol\b|\bpantoprazol\b|\bpantrozol\b'
        r'|\blansoprazol\b|\branitidina\b|\bdomperidona\b|\bmetoclopramida\b'
        r'|\bmetroclopramida\b|\bmetroclopicida\b|\btrimebutina\b|\bbisacodilo\b'
        r'|\bsucralfate\b|\bsimeticona\b|\bmisoprostol\b|\bcarbon activado\b|\bmucinex\b'
        # Antihipertensivos y cardiovasculares - ENRIQUECIDO
        r'|\blosartan\b|\blozartan\b|\bamlodipino\b|\benalapril\b|\bcaptopril\b|\bvalsartan\b'
        r'|\bmetoprolol\b|\bmetroprolol\b|\bcarvedilol\b|\bpropanolol\b|\bbisoprolol\b'
        r'|\bnebivolol\b|\bhidroclorotiazida\b|\bfurosemida\b|\bnifedipino\b|\bverapamilo\b'
        r'|\bprazosin\b|\bespironolactona\b|\blisinopril\b|\bperindopril\b|\btamsulosina\b'
        r'|\brosuvastatina\b|\batorvastatina\b|\blovastatina\b|\bgemfibrozilo\b|\btelemisartan\b'
            r'|\bramipril\b|\bticagrelor\b|\braltegravir\b'
            r'|\bloratadina pseudoefedrina\b'
        # Antialergicos y respiratorios - ENRIQUECIDO
        r'|\bloratadina\b|\bcetirizina\b|\bdesloratadina\b|\bclorfeniramina\b|\bclorfenamina\b'
        r'|\bclorofenamina\b|\bfexofenadina\b|\blevocetirizina\b|\bmontelukast\b'
        r'|\bsalbutamol\b|\bsalbutanol\b|\bbudesonida\b|\bsumriptam\b|\bsumatriptam\b'
        # Vitaminas y suplementos - ENRIQUECIDO
        r'|\btiamina\b|\bacido folico\b|\bsulfato ferroso\b|\bvitaminas\b|\bmultivitaminicos\b'
        r'|\btiamina hcl\b|\bacido folico\b|\bsulfato ferroso\b|\bvitaminas\b'
        r'|\bvitamina a\b|\bvitamina c\b|\bvitamina d\b|\bvitamina d2\b|\bvitamina d3\b'
        r'|\bvitamina e\b|\bvitamina k\b|\bvitamina b6\b|\bpiridoxina\b|\bvitamina b12\b'
        r'|\bcianocobalamina\b|\bmultivitaminicos\b|\bcomplejo b\b|\bselenio\b|\bbiotina\b'
        r'|\bcalcio\b|\bcarbonat[eo] de calcio\b|\bzinc\b|\bhierro\b'
        r'|\bcentrum\b|\bomega 3\b|\bginkgo biloba\b|\bginkobiloba\b'
        r'|\bgluconato de calcio\b|\bpeditrace\b|\bvoglibose\b|\bvildagliptina\b'
        # Anticonvulsivantes - ENRIQUECIDO
        r'|\bcarbamazepina\b|\bcarbamacepina\b|\blevetiracetam\b|\bgabapentina\b'
        r'|\boxcarbazepina\b|\boxcarbazepia\b|\bfenitoina\b|\blacosamida\b'
        r'|\bpregabalina\b|\bpregabalina xl\b|\bpregabalina er\b|\blamotrigina\b'
        r'|\btamotrigina\b|\bribaviricetam\b|\bclobazam\b|\btopiramato\b'
        r'|\btiagabina\b|\bvalproato de magnesio\b|\bvalproato sodico\b|\bvalproato\b'
        r'|\byoduro de sodio\b'
            r'|\bziprasidona\b|\btrimepazina\b'
            # Hormonas y terapias biologicas - NUEVO
            r'|\btestosterona\b|\btestosterona gel\b|\bteriparatide\b|\btetracosactida\b'
            r'|\binfliximab\b|\bremicade\b|\bmedroxiprogesterona\b|\btofacitinib\b'
            r'|\btolcapona\b|\btrastuzumab\b|\btafenoquina\b'
        # Antidiabeticos - ENRIQUECIDO
        r'|\bmetformina\b|\bglibenclamida\b|\binsulina\b|\bdeglutec\b|\bsitagliptina\b'
        r'|\bempagliflozina\b|\bjardiance\b'
        # Psiquiatricos y neurologicos - NUEVO/ENRIQUECIDO
        r'|\bfluoxetina\b|\bparoxetina\b|\bsertalina\b|\bsertralina\b|\bsentralina\b'
        r'|\bescitalopram\b|\bcitalopram\b|\bvenlafaxina\b|\bvelafaxina\b|\bduloxetina\b'
        r'|\bfluvoxamina\b|\bclomipramina\b|\bamitriptilina\b|\binmipramina\b|\bimipramine\b'
        r'|\bimipramina\b|\bmirtazapina\b|\bmirtazopina\b|\btrazodon\b|\btrazadona\b'
        r'|\btrazodone\b|\bbupropion\b|\bbrupopion\b|\bpramipexol\b|\bapiprazol\b'
        r'|\brisperidona\b|\bollanzapina\b|\bquetiapina\b|\bclozapina\b|\bhaloperidol\b'
        r'|\bclorpromazina\b|\bamisulprida\b|\bpipotiazina\b|\blevomepromazina\b'
        # Otros medicamentos comunes - ENRIQUECIDO
        r'|\blevotiroxina\b|\bsildenafil\b|\bviagra\b|\bflunarizina\b|\bminoxidil\b'
        r'|\bivermectina\b|\balbendazol\b|\bmareol\b|\bnitazoxianida\b|\bpamoato de pirantel\b'
        r'|\bpiperazina\b|\bciclosporina\b|\bmemantina\b|\brivastigmina\b|\bdonepezilo\b'
        r'|\btinidazol\b|\bcalcitriol\b|\bclonidina\b|\bbiperideno\b|\bmetotrexate\b'
        r'|\bcabergolina\b|\bmetimazol\b|\bbetahistina\b|\boximetazolina\b|\bnafazolina\b'
        r'|\bpentoxifilina\b|\bteofilina\b|\bciproheptadina\b|\bciproeptadina\b'
        r'|\bciclobenzapina\b|\bcyclobenzaprine\b|\bmebendazol\b|\bpirimetamina\b'
        r'|\bcarbendazim\b|\bdiclorvos\b|\btacrolimus\b|\bmedroxiprogesterona\b'
        r'|\btrimetoprim\b|\bsulfametoxazol\b|\bsulfametazol\b|\bmercaptopurina\b'
        r'|\bmetildopa\b|\bmetildigoxina\b'
            r'|\bsulfametazol\b|\bmercaptopurina\b|\bmetildopa\b|\bmetildigoxina\b'
        # Palabras genericas
        r'|\bmedicamentos\b|\bmultiples medicamentos\b|\bmezcla de medicamentos\b'
        r'|\bpolifarmacia\b|\bpolimedicamentosa\b|\bmedicinas\b'
        r'|\bdolex\b|\btylenol\b|\badvil\b|\bexcedrin\b|\bneosaldina\b|\bsevedol\b'
    ),

    'productos_limpieza': (
        # Cloros y blanqueadores - ENRIQUECIDO
        r'\bclorox\b|\bhipoclorito\b(?!.*sodi[uo]m)'
        r'|\bhipoclorito de sodio\b|\bblanqueador\b|\bcloro\b(?!.*pirifo)'
        r'|\bcloro granulado\b|\blimpido\b'
            r'|\bjabon clorado\b|\bjabon cloradolimpido\b'
        r'|\bdioxido de cloro\b|\bcloro activo\b|\bcloruro de cal\b'
        # Detergentes y limpiadores - ENRIQUECIDO
        r'|\bdetergente\b|\bdetergente liquido\b|\bdetergente polvo\b|\bdetergente concentrado\b'
        r'|\bdetergente universal\b|\bdetergente especializado\b'
        r'|\bfabuloso\b|\bdesinfectante\b|\bproductos de limpieza\b'
        r'|\bvanish\b|\bsuavitel\b|\bsoflan\b|\bjabon\b(?!.*bactericid)'
        r'|\bjabon blanco\b|\bjabon glicerina\b|\bjabon barra\b|\bjabon liquido\b'
        r'|\bjabon neutro\b|\bjabon antibacterial\b|\bjabon desinfectante\b'
        r'|\bsapindus saponaria\b|\bsaponaria\b'
        r'|\bambientador\b|\bcolonia\b|\bshampoo\b|\bchampu\b|\btalco\b|\bcrema alisadora\b'
        r'|\bacondicionador\b'
        r'|\besmalte de unas\b|\bdilusor de esmalte\b|\bremovedor de esmalte\b'
        r'|\blociones?\b|\bgel antibacterial\b'
        r'|\barsall\b|\bador\b|\bpagasol\b|\blija\b|\bablana\b|\bpinol\b'
        r'|\blavarropa\b|\blavarropes\b|\blavaplatos\b|\bacondicionador\b'
        r'|\blavarropa\b|\blavarropes\b|\blavaplatos\b'
        r'|\bdesmaquillante\b|\bdemaquillante\b|\bremovedor de maquillaje\b'
        r'|\bremovedor\b|\bremovedor de pintura\b|\bremovedor de cuticulas\b'
        r'|\bremovedor esmalte\b|\bdisolvente\b|\bdisolvente universal\b'
        r'|\bdiluyente\b|\bdiluyente de pintura\b|\bdiluyente universal\b|\bdiluyente trementina\b'
        r'|\bdesemparador\b|\bdesempapelador\b'
        r'|\bdesengrasante\b|\bdesengrasante fuerte\b|\bdesengrasante cocina\b|\bdesengrasante ropa\b'
        r'|\bdecolorante para cabello\b|\bdecolorante en polvo\b|\bdecolorante crema\b'
        r'|\bcrema depilatoria\b|\bdepilatoria\b|\bdepilador liquido\b|\bdepilador en crema\b'
        r'|\bvello stop\b'
        r'|\bcorrector liquido\b|\bcorrector cinta\b|\bcorrector pen\b|\btinta correctora\b'
        r'|\bscan\b|\bwindex\b|\blimpiacristales\b|\btorpol\b|\blimpia\b'
        r'|\blimpiadera\b|\blimpiadoras\b|\bpiso\b|\bpisos\b|\blimpiador de pisos\b'
        r'|\blimpiador de ventanas\b|\blimpiador de banos\b|\blimpiador multiusos\b'
        # Acidos industriales/limpieza - ENRIQUECIDO
        r'|\bsoda caustica\b|\bhidroxido de sodio\b'
        r'|\bacido muriatico\b|\bacido clorhidrico\b'
        r'|\bacido salicilico\b|\bacido oxalico\b|\bacido formico\b|\bacido fluorhidrico\b'
        r'|\bacido borico\b|\bacido acetico\b|\bacido de bateria\b'
        r'|\bacido nitrico\b|\bacido sulfurico\b|\bacido fosforico\b'
        r'|\bamoniaco\b|\bamonio\b|\bagua oxigenada\b'
        r'|\bperoxido de aluminio\b|\bformol\b|\bformaldehido\b|\bvinagre\b'
        r'|\bborax\b|\btriclosan\b|\btricloroetano\b|\btricloroetileno\b'
        r'|\bpercloro etileno\b|\bpercloroetileno\b|\boxido de etileno\b'
        r'|\bfenol\b|\bfenoles\b|\bcarbonato de sodio\b|\bbicarbonato de sodio\b'
        r'|\bsoda carbonato\b|\bsodio carbonato\b|\bsodio bicarb\b'
        r'|\bacido sulfurico\b|\bacido fosforico\b'
        r'|\bsol amoniaco\b|\bsolucion amoniacal\b|\bperoxido\b'
        r'|\bperoxido de hidrogeno\b'
        # Disolventes y productos industriales - NUEVO
        r'|\bxilol\b|\bxileno\b|\btolueno\b|\bbenceno\b|\bmek\b|\bmetiletilcetona\b'
        r'|\bdimetilformamida\b|\btetracloroetileno\b'
        r'|\bdicloroetano\b|\bdiclorodifeniltricloroetano\b|\bddt\b'
        r'|\bacetona\b'
        # Productos especiales - NUEVO
        r'|\bsoldadura\b|\bflux para soldadura\b|\bsoldadura blanda\b|\bsoldadura fuerte\b'
        r'|\bslime\b|\bplastilina industrial\b|\bpegamento industrial\b'
        r'|\bdeshumecedor\b|\bdeshumecedor para audifonos\b|\bdeshumecedor silica gel\b'
        r'|\bhumidificador\b'
        r'|\bsolkaflam\b'
        # Productos para higiene - ENRIQUECIDO
        r'|\bcosmeticos\b|\bcrema\b(?!.*medic)|\\blocion de bebe\b'
        r'|\bpapel higienico\b|\btoalla\b|\btoallitas\b'
        r'|\btoallitas humedas\b|\btoallitas desinfectantes\b'
        r'|\btissue\b|\bpanales\b|\bpantys\b|\bcompresas\b'
        r'|\bsellador\b|\bprotector\b|\bpolicarbonato\b|\bsuavisante\b|\bsuavizante\b'
        r'|\bsimil clorox\b|\btolquen\b'
    ),

    'gases_combustibles': (
        # Gases industriales (NO inhalantes SPA) - ENRIQUECIDO
        r'\bgas natural\b|\bgas propano\b|\bpropano\b|\bgas butano\b|\bbutano\b'
        r'|\bgas metano\b|\bmetano\b|\bgas liquido\b|\bfuga de gas\b'
        r'|\bgas de mina\b|\bdioxido de carbono\b'
            r'|\bco2\b'
        r'|\bmonoxido de carbono\b|\bdioxido de nitrogeno\b'
            r'|\bco\b|\bdioxido de nitrogeno\b'
        r'|\bhelio\b'
        r'|\bmezcla de gases\b|\bcloro\b(?!.*activ)|\bcloro gaseoso\b|\bgas cloro\b'
        r'|\bfosgeno\b|\bgas clorina\b'
        # Combustibles y aceites - ENRIQUECIDO
        r'|\bacpm\b|\baceite combustible\b|\baceite de motor\b|\baceite de moto\b'
        r'|\baceite\b(?!.*esenci)|\bkerosene\b|\bgasolina\b(?!.*inhala)'
        r'|\bethanol\b(?!.*alcohol)|\betanol industrial\b|\bpropanol\b'
        r'|\baceite hidraulico\b|\bpetroleo\b'
        r'|\bGLP\b|\bgas licuado\b|\bfuel oil\b|\bfuel\b'
            # Solventes para frenos y anticongelantes - NUEVO
            r'|\bethylenglycol liquido para frenos\b|\bethylenglycol\b|\betilenglicol\b'
            r'|\bglicol automotriz\b|\bpropilenglicol\b|\bglicol monopropileno\b'
            # Eteres industriales - NUEVO
            r'|\beter monometil de etilenglicol\b|\bmetileter etilenglicol\b'
            # Gases y vapores toxicos - NUEVO
            r'|\bdioxido de azufre\b|\bdisulfuro de carbono y azufre\b'
            r'|\bdisulfuro de carbono\b|\bcloruro de hidrogeno\b'
            r'|\bcloruro de butirilo\b|\bcloruro tionio\b|\bcloruro vinilo\b'
            # Derivados del petroleo - NUEVO
            r'|\bderivado del petroleo\b|\bderivados petroquimicos\b|\bdestilado de petroleo\b'
            # Disolventes de pintura - NUEVO
            r'|\bdiluente de pintura trementina\b|\btrementina\b|\baguarras\b'
            r'|\btrementina rectificada\b|\besencia de trementina\b'
            # Fosfatos y compuestos - NUEVO
            r'|\bpentoxido de fosforo\b|\btrifosfato\b|\bpirofosfato\b'
            # Oxidos y compuestos - NUEVO
            r'|\boxido de etileno\b|\boxido de propileno\b'
            # Insecticidas y fumigantes - NUEVO
            r'|\bromadiolona\b|\bcloropirifos\b|\bmalation\b|\bparathion\b|\bpermetrina\b'
        # Otros gases no-SPA - ENRIQUECIDO
        r'|\bgas pimienta\b|\bgas lacrimogeno\b|\bgas irritante\b'
        r'|\bfosfuro de aluminio\b|\bhumo\b|\bmercurio\b(?!.*termometro)'
        r'|\bazufre\b'
    ),
}

# =========================================================
# PATRONES COMPILADOS (para mejor rendimiento)
# =========================================================

compiled_patterns: Dict[str, Pattern] = {
    k: re.compile(v, flags=re.IGNORECASE) 
    for k, v in substance_patterns.items()
}
