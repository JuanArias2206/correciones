# -*- coding: utf-8 -*-
"""
CLASIFICADOR DETERMINÍSTICO (REGEX DE ALTA CONFIANZA)
======================================================
Detecta sustancias obviamente psicoactivas sin pasar por el LLM.
Evita ~40-50% de las llamadas al LLM para casos claros.

Sistema de "Strong Confidence" patterns para cada categoría.
"""

import re
from typing import List, Dict, Optional, Pattern
from patterns import compiled_patterns


class DeterministicClassifier:
    """
    Usa regex compilados de patterns.py pero con reglas de "alta confianza".
    Si detecta claramente una sustancia SPA (sin ambigüedad), devuelve
    la categoría sin pasar por el LLM.
    """
    
    # Patrones de ALTA CONFIANZA: si se detectan, NO hay ambigüedad
    # Estos son los nombres "obvios" de SPA
    # IMPORTANTE: CONSERVADOR - solo triggers fuertes, evita falsos positivos
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
            r'\b(heroina|heroin|fentanilo|fentanyl|morfina|tramadol|tramal|oxicontin|oxicodona|hidromorphona|codeína|codeina|metadona|paracodina|hidrocodeina)\b',
            re.IGNORECASE
        ),
        'tranquilizantes_y_sedantes': re.compile(
            r'\b(clonazepam|clonacepam|clonazepan|clonacepan|clonacepa|alprazolam|diazepam|lorazepam|benzodiacepina|rivotril|valium|xanax|flunitrazepam|flurazepam|bromazepam)\b',
            re.IGNORECASE
        ),
        'escopolamina': re.compile(
            r'\b(escopolamina|burundanga|floripondio|cacao sabanero)\b',
            re.IGNORECASE
        ),
        'alcohol_etanol': re.compile(
            r'\b(cerveza|vino|aguardiente|ron|whiskey|whisky|vodka|etanol|champaña|champagne|cerveza|chicha|guaro|viche|chirrinche)\b',
            re.IGNORECASE
        ),
        'estimulantes': re.compile(
            r'\b(metanfetamina|anfetamina|crystal|hielo|crank|speed|metilfenidato|ritalin|adderall|concerta|capilot|criptonita)\b',
            re.IGNORECASE
        ),
        'alucinogenos': re.compile(
            r'\b(lsd|psilocibina|hongos psilocybin|dmt|mdma|ecstasy|2cb|tusi|tussi|tusy|tussy|tussyl|tusivet|mescalina|peyote|ketamina|yahe|yage)\b',
            re.IGNORECASE
        ),
        'inhalantes': re.compile(
            r'\b(thinner|sacol|pegante|popper|nitrito|varsol|boxer)\b',  # Evita "gas" genérico
            re.IGNORECASE
        ),
    }
    
    def __init__(self, use_strong_confidence_only: bool = True):
        """
        Args:
            use_strong_confidence_only: Si True, solo usa STRONG_CONFIDENCE_PATTERNS.
                                        Si False, usa todos los patrones compilados.
        """
        self.use_strong_confidence_only = use_strong_confidence_only
    
    def classify(self, nom_clean: str) -> Optional[List[str]]:
        """
        Intenta clasificar usando patrones determinísticos.
        Retorna lista de categorías SI se detecta con alta confianza,
        None SI hay ambigüedad o no se detecta.
        """
        if not isinstance(nom_clean, str) or not nom_clean.strip():
            return None
        
        text = nom_clean.lower().strip()
        
        # Usa STRONG_CONFIDENCE si está activado
        if self.use_strong_confidence_only:
            found_categories = []
            for cat, pattern in self.STRONG_CONFIDENCE_PATTERNS.items():
                if pattern.search(text):
                    found_categories.append(cat)
            
            # Si encontró exactamente una categoría, es clara
            if len(found_categories) == 1:
                return found_categories
            # Si encontró múltiples, es ambiguo -> pasar al LLM
            if len(found_categories) > 1:
                return None
            # Si no encontró nada con strong confidence
            return None
        
        # Modo fallback: usa todos los patrones compilados
        found_categories = [
            cat for cat, pat in compiled_patterns.items() 
            if pat.search(text)
        ]
        
        if len(found_categories) == 1:
            return found_categories
        
        return None
    
    def classify_batch(self, noms_clean: List[str]) -> Dict[str, List[str]]:
        """
        Clasifica múltiples nombres determinísticamente.
        Retorna dict: nom_clean -> categorías (solo para los que se pudieron clasificar).
        """
        results = {}
        for nom_clean in noms_clean:
            cats = self.classify(nom_clean)
            if cats is not None:
                results[nom_clean] = cats
        return results
    
    def get_unclassified(self, noms_clean: List[str]) -> List[str]:
        """
        Retorna los nombres que NO se pudieron clasificar determinísticamente.
        Estos irán al LLM.
        """
        return [nom for nom in noms_clean if self.classify(nom) is None]
