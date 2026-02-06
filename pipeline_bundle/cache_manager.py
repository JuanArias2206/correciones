# -*- coding: utf-8 -*-
"""
GESTOR DE CACHÉ PERSISTENTE (SQLite)
====================================
Cache local para evitar múltiples llamadas al LLM con los mismos nombres.
Soporta versionado: cuando cambia el prompt/reglas, la cache se invalida.
"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class CacheManager:
    """
    Cache persistente con SQLite para resultados de clasificación.
    - Mapea: (nom_clean, prompt_version) -> list de categorías
    - Soporta invalidación por versión de prompt
    """
    
    def __init__(self, db_path: str, prompt_version: str):
        """
        Args:
            db_path: Ruta a archivo SQLite (ej: /path/cache.db)
            prompt_version: String de versión del prompt (ej: "v1.0"). 
                           Cambiar esto invalida cache anterior.
        """
        self.db_path = db_path
        self.prompt_version = prompt_version
        self._init_db()
    
    def _init_db(self):
        """Inicializa tablas si no existen."""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS classifications (
                    nom_clean TEXT NOT NULL,
                    prompt_version TEXT NOT NULL,
                    categorias TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (nom_clean, prompt_version)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_nom_version 
                ON classifications(nom_clean, prompt_version)
            ''')
            conn.commit()
    
    def get(self, nom_clean: str) -> Optional[List[str]]:
        """
        Obtiene categorías en caché para un nombre normalizado.
        Retorna None si no existe o si versión de prompt no coincide.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT categorias FROM classifications WHERE nom_clean = ? AND prompt_version = ?',
                (nom_clean, self.prompt_version)
            )
            row = cursor.fetchone()
        
        if row:
            try:
                return json.loads(row[0])
            except:
                return None
        return None
    
    def get_batch(self, noms_clean: List[str]) -> Tuple[Dict[str, List[str]], List[str]]:
        """
        Obtiene múltiples nombres en caché de una vez.
        Retorna: (dict de hits en caché, lista de nombres NO en caché)
        """
        cached = {}
        not_cached = []
        
        with sqlite3.connect(self.db_path) as conn:
            for nom_clean in noms_clean:
                cursor = conn.execute(
                    'SELECT categorias FROM classifications WHERE nom_clean = ? AND prompt_version = ?',
                    (nom_clean, self.prompt_version)
                )
                row = cursor.fetchone()
                
                if row:
                    try:
                        cached[nom_clean] = json.loads(row[0])
                    except:
                        not_cached.append(nom_clean)
                else:
                    not_cached.append(nom_clean)
        
        return cached, not_cached
    
    def set(self, nom_clean: str, categorias: List[str]):
        """Almacena un resultado en caché."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO classifications 
                   (nom_clean, prompt_version, categorias, created_at)
                   VALUES (?, ?, ?, ?)''',
                (nom_clean, self.prompt_version, json.dumps(categorias), 
                 datetime.utcnow().isoformat())
            )
            conn.commit()
    
    def set_batch(self, results: Dict[str, List[str]]):
        """Almacena múltiples resultados en caché."""
        with sqlite3.connect(self.db_path) as conn:
            for nom_clean, categorias in results.items():
                conn.execute(
                    '''INSERT OR REPLACE INTO classifications 
                       (nom_clean, prompt_version, categorias, created_at)
                       VALUES (?, ?, ?, ?)''',
                    (nom_clean, self.prompt_version, json.dumps(categorias), 
                     datetime.utcnow().isoformat())
                )
            conn.commit()
    
    def clear_old_versions(self, keep_version: Optional[str] = None):
        """
        Borra resultados de versiones antiguas de prompt.
        Si keep_version=None, mantiene solo la versión actual.
        """
        keep = keep_version or self.prompt_version
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                'DELETE FROM classifications WHERE prompt_version != ?',
                (keep,)
            )
            conn.commit()
    
    def stats(self) -> Dict[str, int]:
        """Retorna estadísticas del caché."""
        with sqlite3.connect(self.db_path) as conn:
            total = conn.execute(
                'SELECT COUNT(*) FROM classifications'
            ).fetchone()[0]
            
            current = conn.execute(
                'SELECT COUNT(*) FROM classifications WHERE prompt_version = ?',
                (self.prompt_version,)
            ).fetchone()[0]
            
            versions = conn.execute(
                'SELECT COUNT(DISTINCT prompt_version) FROM classifications'
            ).fetchone()[0]
        
        return {
            'total_entries': total,
            'current_version_entries': current,
            'distinct_versions': versions
        }
