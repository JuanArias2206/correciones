#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar estructura de archivos Excel
"""
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import file_sheets_map

print("=" * 70)
print("VERIFICANDO ESTRUCTURA DE ARCHIVOS EXCEL")
print("=" * 70)

for filepath, sheets_config in file_sheets_map.items():
    if os.path.exists(filepath):
        print(f"\n✅ Archivo encontrado: {os.path.basename(filepath)}")
        print(f"   Ruta: {filepath}")
        
        try:
            xls = pd.ExcelFile(filepath)
            print(f"   Hojas disponibles: {xls.sheet_names}")
            
            for sheet_name in sheets_config.keys():
                if sheet_name in xls.sheet_names:
                    df = pd.read_excel(filepath, sheet_name=sheet_name)
                    print(f"\n   📊 Hoja: {sheet_name}")
                    print(f"      Total registros: {len(df)}")
                    print(f"      Columnas: {list(df.columns)}")
                    print(f"      Primeras 3 registros:")
                    for idx, row in df.head(3).iterrows():
                        print(f"        {idx}: {dict(row)}")
                else:
                    print(f"   ❌ Hoja '{sheet_name}' no encontrada")
        except Exception as e:
            print(f"   ❌ Error leyendo archivo: {e}")
    else:
        print(f"\n❌ Archivo NO encontrado: {filepath}")

print("\n" + "=" * 70)
