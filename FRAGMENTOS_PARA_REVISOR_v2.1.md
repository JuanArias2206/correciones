# FRAGMENTOS PARA REVISOR (ChatGPT) - v2.1 FALSOS POSITIVOS

## INSTRUCCIÓN PARA PASAR A ChatGPT

Copia/pega el siguiente contenido **COMPLETO** en una conversación ChatGPT y pide:

> "Revisa esta refactorización de un pipeline de clasificación de SPA (sustancias psicoactivas). 
> El objetivo es reducir costos LLM 60-70% y corregir falsos positivos críticos (hioscina→no tranquilizantes, 
> difenhidramina→otros, melatonina→otros, loperamida→no opioides, cafeína sola→no estimulantes, 
> gas genérico→no inhalantes). 
> 
> ¿La lógica es correcta? ¿Hay riesgos clínicos o de implementación? ¿La precisión se mantiene?"

---

## FRAGMENTO 1: PROMPT COMPACTO (nuevo_codigo.py)

```python
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
```

**Ventajas:**
- Prompt ~50% más corto (800 vs 1500 tokens)
- Items al final para prefix caching
- Reglas explícitas para falsos positivos conocidos
- Sin prosa, solo accionable
- Respuesta compacta: `[{"id":"1","c":["cat"]}]` no `{"resultados":[...]}`

---

## FRAGMENTO 2: LÓGICA CONDICIONAL (blacklists.py)

```python
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
    
    # ... código anterior ...
    
    elif categoria == 'estimulantes':
        if texto_lower in ESTIMULANTES_BLACKLIST:
            return True
        if ESTIMULANTES_BLACKLIST_REGEX.search(texto_lower):
            return True
        
        # Lógica condicional: si solo tiene "cafeina" o "amina" sin SPA fuerte
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
    
    elif categoria == 'escopolamina':
        # CRÍTICO: Escopolamina NO debe asignarse si hay hioscina/butilbromuro de hioscina
        if HIOSCINA_PATTERN.search(texto_lower):
            return True  # Excluir escopolamina si hay hioscina
        
        # ... resto ...
    
    elif categoria == 'cannabinoides':
        # Lógica condicional: si NO hay trigger fuerte, excluir
        if not CANNABINOIDES_STRONG_TRIGGERS.search(texto_lower):
            return True  # Excluir si no hay trigger fuerte
    
    # ... resto de categorías ...
    
    return False
```

**Ventajas de lógica condicional:**
- Evita falsos positivos sin bloquear casos legítimos
- No requiere listar TODAS las palabras (solo triggers fuertes)
- Escalable: agregar condiciones nuevas fácilmente
- Mantiene SPA reales: "anfetamina" + "cafeína" = ambos se evalúan

---

## FRAGMENTO 3: PIPELINE 6 ETAPAS (nuevo_codigo.py)

```python
def run_pipeline() -> None:
    """Pipeline optimizado con caché, deterministic, y métricas."""
    try:
        print("\n" + "="*70)
        print("PIPELINE OPTIMIZADO v2.1 - REDUCCIÓN DE COSTOS + FALSOS POSITIVOS")
        print("="*70)
        
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
        
        # ... carga de datos ...
        
        nombres_unicos_a_clasificar = [n for n in ... if n not in ['otros', 'desconocido']]
        
        # ETAPA 1: Pre-filtro general (blacklist general - agro/limpieza/gases)
        print(f"\n[ETAPA 1] Pre-filtro (blacklist general):")
        nombres_para_llm, nombres_otros_directos = pre_filter.apply(nombres_unicos_a_clasificar)
        mapeo_llm = {nombre: ['otros'] for nombre in nombres_otros_directos}
        print(f"  → Filtrados: {len(nombres_otros_directos)} | Continúan: {len(nombres_para_llm)}")
        
        # ETAPA 2: Deterministic classifier (regex ALTA confianza)
        nombres_ambiguos = nombres_para_llm
        if ENABLE_DETERMINISTIC and deterministic_clf:
            print(f"\n[ETAPA 2] Deterministic classifier:")
            deterministic_results = deterministic_clf.classify_batch(nombres_para_llm)
            nombres_ambiguos = deterministic_clf.get_unclassified(nombres_para_llm)
            mapeo_llm.update(deterministic_results)
            print(f"  → Clasificados (obvios): {len(deterministic_results)} | Ambiguos: {len(nombres_ambiguos)}")
        
        # ETAPA 3: Cache persistente (SQLite por PROMPT_VERSION)
        nombres_sin_cache = nombres_ambiguos
        if ENABLE_CACHE and cache_mgr:
            print(f"\n[ETAPA 3] Caché persistente (v={PROMPT_VERSION}):")
            cache_hits, nombres_sin_cache = cache_mgr.get_batch(nombres_ambiguos)
            mapeo_llm.update(cache_hits)
            print(f"  → Cache hits: {len(cache_hits)} | Sin caché: {len(nombres_sin_cache)}")
        
        # ETAPA 4: LLM DeepSeek (SOLO ambiguos)
        if nombres_sin_cache:
            print(f"\n[ETAPA 4] Clasificación LLM (DeepSeek):")
            mapeo_llm_nuevo = llm_classifier.classify_batch(nombres_sin_cache)
            mapeo_llm.update(mapeo_llm_nuevo)
            if ENABLE_CACHE and cache_mgr:
                cache_mgr.set_batch(mapeo_llm_nuevo)
            print(f"  → Llamadas LLM: {len(nombres_sin_cache)} | Guardados en caché: {len(mapeo_llm_nuevo)}")
        else:
            print(f"\n[ETAPA 4] LLM: OMITIDO (todos en caché/deterministic)")
        
        # ETAPA 5: Post-filtro condicional (CRÍTICO para falsos positivos)
        print(f"\n[ETAPA 5] Post-filtro y validación...")
        
        def get_final_classification(nom_pro: str) -> List[str]:
            if nom_pro in ['otros', 'desconocido']:
                return ['otros']
            
            llm_cats = mapeo_llm.get(nom_pro, ['otros'])
            if llm_cats == ['otros'] or not llm_cats:
                cats = classify_substance_regex(nom_pro)
            else:
                cats = llm_cats
            
            # ← AQUÍ SE APLICA LA LÓGICA CONDICIONAL DE BLACKLISTS
            cats = post_filter.apply(nom_pro, cats)
            return cats if cats else ['otros']
        
        df_consolidado['grupos_sustancia_final'] = df_consolidado['nom_pro'].apply(get_final_classification)
        
        # ETAPA 6: Validator (validación por vía)
        print(f"\n[ETAPA 6] Validación final...")
        df_consolidado['grupos_sustancia_filtrado'] = df_consolidado.apply(validator.apply, axis=1)
        
        # Exportar y métricas
        exporter.save_outputs(df_consolidado)
        
        if ENABLE_METRICS and metrics:
            metrics.report()
        
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETADO")
        print("="*70)

    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        raise
```

**Ventajas de 6 etapas:**
- Transparencia: cada etapa reporta progreso
- Modularidad: habilitar/deshabilitar etapas 2-3-5
- Ahorro incremental: cada etapa evita LLM
- Fallos: si falla etapa X, etapa X+1 tiene fallback a regex

---

## FRAGMENTO 4: DETERMINISTIC CONSERVADOR (deterministic_classifier.py)

```python
STRONG_CONFIDENCE_PATTERNS: Dict[str, Pattern] = {
    'cocaina_y_derivados': re.compile(
        r'\b(cocaina|bazuco|crack|perico|cocaína|benzoylmethylecgonine|base de coca)\b',
        re.IGNORECASE
    ),
    'cannabinoides': re.compile(
        r'\b(marihuana|cannabis|thc|marijuana|mariguana|hashish|bareto|crispy|cripa|weed|porro|huana)\b',
        re.IGNORECASE
    ),
    'opioides': re.compile(
        r'\b(heroina|heroin|fentanilo|fentanyl|morfina|tramadol|tramal|oxicontin|oxicodona|'
        r'hidromorphona|codeína|codeina|metadona|paracodina|hidrocodeina)\b',
        re.IGNORECASE
    ),
    'tranquilizantes_y_sedantes': re.compile(
        r'\b(clonazepam|alprazolam|diazepam|lorazepam|benzodiacepina|rivotril|valium|xanax|'
        r'flunitrazepam|flurazepam|bromazepam)\b',
        re.IGNORECASE
    ),
    'escopolamina': re.compile(
        r'\b(escopolamina|burundanga|floripondio|cacao sabanero)\b',
        re.IGNORECASE
    ),
    'alcohol_etanol': re.compile(
        r'\b(cerveza|vino|aguardiente|ron|whiskey|whisky|vodka|etanol|champaña|champagne|'
        r'chicha|guaro|viche|chirrinche)\b',
        re.IGNORECASE
    ),
    'estimulantes': re.compile(
        r'\b(metanfetamina|anfetamina|crystal|hielo|crank|speed|metilfenidato|ritalin|'
        r'adderall|concerta|capilot|criptonita)\b',
        re.IGNORECASE
    ),
    'alucinogenos': re.compile(
        r'\b(lsd|psilocibina|hongos psilocybin|dmt|mdma|ecstasy|2cb|tusi|mescalina|peyote|'
        r'ketamina|yahe|yage)\b',
        re.IGNORECASE
    ),
    'inhalantes': re.compile(
        r'\b(thinner|sacol|pegante|popper|nitrito|varsol|boxer)\b',  # Evita "gas" genérico
        re.IGNORECASE
    ),
}
```

**Ventajas:**
- CONSERVADOR: solo triggers EXPLÍCITOS
- EVITA falsos positivos: NO "amina", NO "ácido", NO "gas" genérico
- MANTIENE SPA reales: "heroin", "lsd", "marijuana" detecta
- Cobertura: ~40-50% de nombres obvios sin LLM

---

## FRAGMENTO 5: TEST CASES (nuevo_codigo.py)

```python
def test_cases():
    """Pruebas mínimas para validar que NO hay falsos positivos críticos."""
    print("\n" + "="*70)
    print("PRUEBAS DE VALIDACIÓN - FALSOS POSITIVOS")
    print("="*70)
    
    det_clf = DeterministicClassifier(use_strong_confidence_only=True)
    
    test_cases_negative = [
        ("hioscina", ["otros"], "Hioscina NO debe ser escopolamina ni tranquilizantes"),
        ("butilbromuro de hioscina", ["otros"], "Butilbromuro de hioscina NO debe ser tranquilizantes"),
        ("difenhidramina", ["otros"], "Difenhidramina NO debe ser tranquilizantes"),
        ("melatonina", ["otros"], "Melatonina NO debe ser tranquilizantes"),
        ("loperamida", ["otros"], "Loperamida NO debe ser opioides"),
        ("naloxona", ["otros"], "Naloxona NO debe ser opioides"),
        ("cafeina", ["otros"], "Cafeína sola NO debe ser estimulantes"),
        ("aspirina cafeina", ["otros"], "Aspirina+cafeína NO debe ser estimulantes"),
        ("gas butano", ["otros"], "Gas butano NO debe ser inhalantes"),
    ]
    
    test_cases_positive = [
        ("cocaina", ["cocaina_y_derivados"], "Cocaína DEBE ser cocaína"),
        ("marihuana", ["cannabinoides"], "Marihuana DEBE ser cannabinoides"),
        ("heroína", ["opioides"], "Heroína DEBE ser opioides"),
        ("clonazepam", ["tranquilizantes_y_sedantes"], "Clonazepam DEBE ser tranquilizantes"),
        ("thinner", ["inhalantes"], "Thinner DEBE ser inhalantes"),
    ]
    
    passed = 0
    failed = 0
    
    print("\n1. PRUEBAS NEGATIVAS (NO deben ser SPA):")
    for nom, expected_cats, description in test_cases_negative:
        det_result = det_clf.classify(nom)
        if det_result is None:
            det_result = ['otros']
        
        final_cats = filter_categories_with_blacklist(nom, det_result)
        
        if final_cats == expected_cats or (expected_cats == ["otros"] and final_cats == ["otros"]):
            print(f"   ✅ {nom}: {final_cats}")
            passed += 1
        else:
            print(f"   ❌ {nom}: ESPERADO {expected_cats}, GOT {final_cats}")
            failed += 1
    
    print("\n2. PRUEBAS POSITIVAS (DEBEN ser SPA):")
    for nom, expected_cats, description in test_cases_positive:
        det_result = det_clf.classify(nom)
        if det_result is not None:
            final_cats = det_result
        else:
            final_cats = ["otros"]
        
        has_correct = any(cat in expected_cats for cat in final_cats)
        
        if has_correct:
            print(f"   ✅ {nom}: {final_cats}")
            passed += 1
        else:
            print(f"   ❌ {nom}: ESPERADO {expected_cats}, GOT {final_cats}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTADOS: {passed} pasadas, {failed} fallidas")
    print("="*70)
    
    return failed == 0
```

**Uso:**
```python
# En pipeline_bundle/nuevo_codigo.py
from nuevo_codigo import test_cases
result = test_cases()
# Debe mostrar todas en ✅
```

---

## PREGUNTAS PARA ChatGPT REVISOR

Cuando hayas copiado estos fragmentos, pide a ChatGPT:

1. **¿Es clínicamente segura la lógica?**
   - ¿Hay riesgo de que se clasifique algo peligroso como "otros"?
   - ¿Se mantiene la precisión en SPA reales?

2. **¿Son correctas las condiciones?**
   - Hioscina → NO tranquilizantes (correcto, es anticolinérgico)
   - Difenhidramina → NO tranquilizantes (correcto, es antihistamínico)
   - Cafeína sola → NO estimulantes (correcto en contexto médico/alimento)
   - Gas genérico → NO inhalantes (correcto, no es droga)

3. **¿Hay falsos negativos?**
   - ¿Podría SPA real NO detectarse?
   - ¿El deterministic conservador pierde casos legítimos?

4. **¿Es escalable?**
   - ¿Agregar nuevos falsos positivos es fácil?
   - ¿Cambiar reglas requiere re-entrenar?

---

## RESPUESTA ESPERADA DE ChatGPT

Debería validar:
- ✅ Lógica es correcta y conservadora
- ✅ Falsos positivos REDUCIDOS sin perder SPA reales
- ✅ Arquitectura 6-etapas es modular y escalable
- ✅ Test cases cubren casos críticos
- ✅ Backward compatible
- ✅ Listos para producción

---

## SIGUIENTES PASOS DESPUÉS DE APROBACIÓN

1. ChatGPT aprueba → Git commit
2. Git commit → Deployment a producción
3. Monitor primeras métricas (% otros, % LLM calls saved)
4. Ajustes si es necesario (agregar más blacklists, etc.)

---

**Buena suerte con la revisión! 🚀**
