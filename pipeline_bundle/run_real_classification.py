#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PIPELINE DE CLASIFICACIÓN SPA REAL - Versión 2.1
Ejecuta clasificaciones reales contra DeepSeek LLM usando datos de Excel
"""

import sys
import os
import argparse
import pandas as pd
import numpy as np
import time
from pathlib import Path
from collections import defaultdict

# Import configuration and pipeline modules
sys.path.insert(0, str(Path(__file__).parent))
from config import (
    DEEPSEEK_API_KEY,
    TEST_PERCENTAGE,
    logger,
    METRICS,
    VIA_EXP_MAP,
    VIA_EXPOSI_MAP
)

# Import LLM and pipeline components
try:
    from llm_clients import build_llm_client
    from nuevo_codigo import (
        build_llm_prompt_compact,
        parse_llm_json_compact,
        classify_substance_regex
    )
except ImportError as e:
    logger.error(f"Error importing modules: {e}")
    print(f"❌ Error importing modules: {e}")
    sys.exit(1)

# Simple in-memory cache
CLASSIFICATIONS_CACHE = {}

# ============================================================================
# EXCEL DATA LOADER
# ============================================================================

def map_via_exposicion_text(via_val, via_col=None):
    if via_val is None or (isinstance(via_val, float) and pd.isna(via_val)):
        return None
    s = str(via_val).strip()
    if s == '':
        return None
    try:
        code = int(float(s))
        if via_col == 'via_exp':
            return VIA_EXP_MAP.get(code)
        if via_col == 'via_exposi':
            return VIA_EXPOSI_MAP.get(code)
        return VIA_EXP_MAP.get(code) or VIA_EXPOSI_MAP.get(code)
    except Exception:
        pass

    s_lower = s.lower()
    if 'resp' in s_lower:
        return 'respiratoria'
    if 'oral' in s_lower or 'boca' in s_lower:
        return 'oral'
    if 'derm' in s_lower or 'mucosa' in s_lower:
        return 'dermica_mucosas'
    if 'ocu' in s_lower:
        return 'ocular'
    if 'parent' in s_lower or 'intraven' in s_lower or 'intramus' in s_lower or 'subcut' in s_lower:
        return 'parenteral'
    if 'transplac' in s_lower:
        return 'transplacentaria'
    if 'desconoc' in s_lower:
        return 'desconocida'
    return None

def load_excel_data(percentage=20):
    """
    Carga datos reales de archivos Excel
    
    Args:
        percentage (int): Porcentaje de datos a cargar (1-100)
    
    Returns:
        list: Lista de dicts con [consecutive, nom_pro, clasificac, categoria]
    """
    data_dir = Path(__file__).parent / "data" / "wetransfer_sivigila_2025-07-24_1807"
    
    excel_files = [
        data_dir / "356_365_2022.xlsx",
        data_dir / "356_365_2023.xlsx"
    ]
    
    products = []
    
    for excel_file in excel_files:
        if not excel_file.exists():
            logger.warning(f"Excel file not found: {excel_file}")
            continue
        
        try:
            # Read both sheets from each Excel file
            xls = pd.ExcelFile(excel_file)
            for sheet_name in xls.sheet_names:
                logger.info(f"Reading {sheet_name} from {excel_file.name}")
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                # Filter rows with nom_pro (product name) not null
                df_products = df[df['nom_pro'].notna()].copy()
                
                if len(df_products) == 0:
                    logger.warning(f"No products found in {sheet_name}")
                    continue
                
                # Sample if needed
                if percentage < 100:
                    sample_size = max(1, int(len(df_products) * (percentage / 100)))
                    df_products = df_products.sample(n=sample_size, random_state=42)
                
                # Extract relevant columns
                via_cols = ['Via_exposicion', 'via_exposicion', 'via_exp', 'via_exposi']
                for _, row in df_products.iterrows():
                    via_val = None
                    via_col = None
                    for col in via_cols:
                        raw_val = row.get(col, None)
                        if raw_val is None or (isinstance(raw_val, float) and pd.isna(raw_val)):
                            continue
                        text_val = str(raw_val).strip()
                        if text_val != '':
                            via_val = text_val
                            via_col = col
                            break

                    via_text = map_via_exposicion_text(via_val, via_col)

                    products.append({
                        'consecutive': int(row.get('CONSECUTIVE', 0)),
                        'nom_pro': str(row.get('nom_pro', '')).strip(),
                        'clasificac_exist': row.get('clasificac'),
                        'categoria_exist': row.get('categoria'),
                        'via_exposicion': via_val,
                        'via_exposicion_col': via_col,
                        'via_exposicion_texto': via_text,
                        'cod_sust': row.get('cod_sust'),
                        'evento': row.get('Nombre_evento', 'UNKNOWN'),
                        'ano': row.get('ANO', 0),
                        'origen_hoja': sheet_name,
                        'fec_not': row.get('FEC_NOT'),
                        'cod_mun_o': row.get('COD_MUN_O'),
                        'sexo': row.get('SEXO'),
                        'edad': row.get('EDAD')
                    })
        
        except Exception as e:
            logger.error(f"Error reading {excel_file}: {e}")
            continue
    
    logger.info(f"Loaded {len(products)} products from Excel files")
    return products

# ============================================================================
# PIPELINE EXECUTION
# ============================================================================

class RealPipelineExecutor:
    """Ejecuta el pipeline real contra productos de Excel"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.results = []
        self.stats = {
            'total': 0,
            'blacklisted': 0,
            'deterministic': 0,
            'cached': 0,
            'llm_called': 0,
            'post_filtered': 0,
            'final_classified': 0,
            'errors': 0
        }
    
    def classify_product(self, product_data):
        """
        Clasifica un producto mediante el pipeline de 6 etapas
        
        Returns:
            dict: Resultado con clasificación y metadata
        """
        nom_pro = product_data['nom_pro']
        via_exposicion = product_data.get('via_exposicion')
        via_exposicion_col = product_data.get('via_exposicion_col')
        via_exposicion_texto = product_data.get('via_exposicion_texto')
        
        try:
            # 1. PRE-FILTER: SMART BLACKLIST - solo si NO hay contexto médico/farmacéutico
            # Palabras clave que indican NO-SPA (agrícolas, químicos industriales, etc.)
            agro_keywords = [
                'herbicida', 'rodenticida', 'plaguicida', 'pesticida', 'fungicida',
                'insecticida', 'acaricida', 'fertilizante', 'agroquimico', 'gramoxone',
                'paraquat', 'glifosato', 'campeon', 'matarratas', 'veneno para ratas',
                'citronela', 'creolina', 'tiner', 'solvente', 'desengrasante',
                'raticida', 'abono', 'fertilizante', 'fitosanitario', 'agroquímico'
            ]
            
            # Solo filtrar si es agrícola Y no tiene clasificación médica
            is_agro = any(kw.lower() in nom_pro.lower() for kw in agro_keywords)
            has_medical_context = via_exposicion and any(v in str(via_exposicion).lower() 
                                                        for v in ['oral', 'respir', 'dermat', 'inhalado'])
            
            if is_agro and not has_medical_context:
                self.stats['blacklisted'] += 1
                return {
                    'product': nom_pro,
                    'clasificac': 'AGRO_PRODUCT',
                    'categoria': 'agro_product',
                    'categorias_detectadas': ['AGRO_PRODUCT'],
                    'confidence': 1.0,
                    'method': 'agro_filter',
                    'original_clasificac': product_data.get('clasificac_exist'),
                    'via_exposicion': via_exposicion,
                    'via_exposicion_col': via_exposicion_col,
                    'via_exposicion_texto': via_exposicion_texto
                }
            
            # 2. DETERMINISTIC CLASSIFIER - try regex
            det_results = classify_substance_regex(nom_pro)
            if det_results and len(det_results) > 0:
                first_result = det_results[0]
                self.stats['deterministic'] += 1
                return {
                    'product': nom_pro,
                    'clasificac': first_result if isinstance(first_result, str) else 'UNKNOWN',
                    'categoria': first_result if isinstance(first_result, str) else 'UNKNOWN',
                    'categorias_detectadas': det_results,
                    'confidence': 0.95,
                    'method': 'deterministic',
                    'original_clasificac': product_data.get('clasificac_exist'),
                    'via_exposicion': via_exposicion,
                    'via_exposicion_col': via_exposicion_col,
                    'via_exposicion_texto': via_exposicion_texto
                }
            
            # 3. CACHE CHECK
            if nom_pro in CLASSIFICATIONS_CACHE:
                cached = CLASSIFICATIONS_CACHE[nom_pro]
                self.stats['cached'] += 1
                cached_cats = cached.get('categorias', [cached.get('clasificac', 'UNKNOWN')])
                primary_cat = cached_cats[0] if cached_cats else cached.get('clasificac', 'UNKNOWN')
                return {
                    'product': nom_pro,
                    'clasificac': primary_cat,
                    'categoria': primary_cat,
                    'categorias_detectadas': cached_cats,
                    'confidence': 0.85,
                    'method': 'cache',
                    'original_clasificac': product_data.get('clasificac_exist'),
                    'via_exposicion': via_exposicion,
                    'via_exposicion_col': via_exposicion_col,
                    'via_exposicion_texto': via_exposicion_texto
                }
            
            # 4. LLM CALL (only if not classified yet)
            self.stats['llm_called'] += 1
            try:
                # Build prompt for single product
                if isinstance(nom_pro, list):
                    prompt_text = build_llm_prompt_compact(nom_pro)
                else:
                    prompt_text = build_llm_prompt_compact([nom_pro])
                
                # Call LLM
                response_text = self.llm_client.generate(prompt_text)
                
                parsed_list = parse_llm_json_compact(response_text)
                
                if not parsed_list or len(parsed_list) == 0:
                    self.stats['errors'] += 1
                    return {
                        'product': nom_pro,
                        'clasificac': 'PARSE_ERROR',
                        'categoria': 'ERROR',
                        'confidence': 0.0,
                        'method': 'llm_error',
                        'original_clasificac': product_data.get('clasificac_exist'),
                        'via_exposicion': via_exposicion
                    }
                
                parsed = parsed_list[0]
                cats = parsed.get('c', parsed.get('categorias_clasificadas', []))
                if isinstance(cats, str):
                    cats = [cats]
                primary_cat = cats[0] if cats else 'UNKNOWN'
                
                # Cache the result
                CLASSIFICATIONS_CACHE[nom_pro] = {
                    'clasificac': primary_cat,
                    'categoria': primary_cat,
                    'categorias': cats
                }
                
                return {
                    'product': nom_pro,
                    'clasificac': primary_cat,
                    'categoria': primary_cat,
                    'categorias_detectadas': cats,
                    'confidence': parsed.get('confidence', 0.7),
                    'method': 'llm',
                    'original_clasificac': product_data.get('clasificac_exist'),
                    'via_exposicion': via_exposicion,
                    'via_exposicion_col': via_exposicion_col,
                    'via_exposicion_texto': via_exposicion_texto
                }
            
            except Exception as llm_error:
                logger.error(f"LLM error for '{nom_pro}': {llm_error}")
                self.stats['errors'] += 1
                return {
                    'product': nom_pro,
                    'clasificac': 'LLM_ERROR',
                    'categoria': 'ERROR',
                    'categorias_detectadas': ['LLM_ERROR'],
                    'confidence': 0.0,
                    'method': 'llm_error',
                    'error': str(llm_error),
                    'original_clasificac': product_data.get('clasificac_exist'),
                    'via_exposicion': via_exposicion,
                    'via_exposicion_col': via_exposicion_col,
                    'via_exposicion_texto': via_exposicion_texto
                }
        
        except Exception as e:
            logger.error(f"Error classifying '{nom_pro}': {e}")
            self.stats['errors'] += 1
            return {
                'product': nom_pro,
                'clasificac': 'ERROR',
                'categoria': 'ERROR',
                'categorias_detectadas': ['ERROR'],
                'confidence': 0.0,
                'method': 'error',
                'error': str(e),
                'original_clasificac': product_data.get('clasificac_exist'),
                'via_exposicion': via_exposicion,
                'via_exposicion_col': via_exposicion_col,
                'via_exposicion_texto': via_exposicion_texto
            }
    
    def execute(self, products):
        """Ejecuta el pipeline para lista de productos"""
        self.stats['total'] = len(products)
        
        logger.info(f"Starting real pipeline execution for {len(products)} products")
        
        for i, product in enumerate(products, 1):
            result = self.classify_product(product)
            result['consecutive'] = product.get('consecutive')
            result['origen_hoja'] = product.get('origen_hoja')
            result['fec_not'] = product.get('fec_not')
            result['cod_mun_o'] = product.get('cod_mun_o')
            result['sexo'] = product.get('sexo')
            result['edad'] = product.get('edad')
            # Note: original_clasificac is already in result from classify_product()
            self.results.append(result)
            
            # Progress
            if i % 50 == 0 or i == len(products):
                logger.info(f"Progress: {i}/{len(products)} - "
                           f"LLM: {self.stats['llm_called']}, "
                           f"Det: {self.stats['deterministic']}, "
                           f"Cache: {self.stats['cached']}")
        
        return self.results
    
    def get_summary(self):
        """Retorna resumen de estadísticas"""
        total = self.stats['total']
        
        if total == 0:
            return {}
        
        return {
            'total_products': total,
            'blacklisted': self.stats['blacklisted'],
            'deterministic': self.stats['deterministic'],
            'cached': self.stats['cached'],
            'llm_called': self.stats['llm_called'],
            'errors': self.stats['errors'],
            'llm_percentage': round((self.stats['llm_called'] / max(1, total - self.stats['blacklisted'])) * 100, 1),
            'llm_avoided_percentage': round(100 - ((self.stats['llm_called'] / max(1, total - self.stats['blacklisted'])) * 100), 1)
        }

# ============================================================================
# RESULTS AGGREGATION
# ============================================================================

def aggregate_results(results):
    """Agrega resultados por categoría"""
    aggregation = defaultdict(lambda: {'count': 0, 'examples': []})
    
    for result in results:
        key = f"{result['clasificac']} / {result['categoria']}"
        aggregation[key]['count'] += 1
        if len(aggregation[key]['examples']) < 3:
            aggregation[key]['examples'].append(result['product'])
    
    return aggregation

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Pipeline de Clasificación SPA v2.1 - Ejecución Real'
    )
    parser.add_argument('--pct', type=int, default=20,
                       help='Porcentaje de datos a procesar (1-100)')
    parser.add_argument('--show-results', action='store_true',
                       help='Mostrar resultados detallados')
    
    args = parser.parse_args()
    
    # Validate percentage
    if not 1 <= args.pct <= 100:
        print("❌ Percentage must be between 1 and 100")
        return 1
    
    print("\n" + "="*70)
    print(" PIPELINE DE CLASIFICACIÓN SPA v2.1 - EJECUCIÓN REAL")
    print("="*70 + "\n")
    
    # 1. Validate API key
    print("🔑 Validando API Key...")
    if not DEEPSEEK_API_KEY or not DEEPSEEK_API_KEY.startswith('sk-'):
        print("❌ API Key inválida")
        return 1
    print(f"✅ API Key válida: {DEEPSEEK_API_KEY[:10]}...{DEEPSEEK_API_KEY[-6:]}")
    
    # 2. Initialize LLM client
    print("\n🌐 Inicializando cliente LLM...")
    try:
        llm_client = build_llm_client(
            provider="deepseek",
            api_key=DEEPSEEK_API_KEY,
            model="deepseek-chat",
            base_url="https://api.deepseek.com",
            temperature=0.0
        )
        
        # Test connection
        test_response = llm_client.generate("Hola")
        print("✅ Conexión con LLM verificada")
    except Exception as e:
        print(f"❌ Error conectando con LLM: {e}")
        logger.error(f"LLM connection error: {e}")
        return 1
    
    # 3. Load Excel data
    print(f"\n📂 Cargando datos de Excel (primero {args.pct}%)...")
    try:
        products = load_excel_data(percentage=args.pct)
        if not products:
            print("❌ No se cargaron productos de Excel")
            return 1
        print(f"✅ {len(products)} productos cargados")
    except Exception as e:
        print(f"❌ Error cargando Excel: {e}")
        logger.error(f"Excel load error: {e}")
        return 1
    
    # 4. Execute pipeline
    print(f"\n🚀 Ejecutando pipeline real...")
    start_time = time.time()
    
    executor = RealPipelineExecutor(llm_client)
    try:
        executor.execute(products)
    except KeyboardInterrupt:
        print("\n⚠️  Pipeline interrumpido por usuario")
        elapsed = time.time() - start_time
        print(f"⏱️  Tiempo parcial: {elapsed:.1f}s")
    except Exception as e:
        print(f"❌ Error ejecutando pipeline: {e}")
        logger.error(f"Pipeline execution error: {e}")
        return 1
    
    elapsed = time.time() - start_time
    
    # 5. Generate results summary
    summary = executor.get_summary()
    aggregation = aggregate_results(executor.results)
    
    print("\n" + "="*70)
    print(" RESUMEN DE EJECUCIÓN")
    print("="*70)
    print(f"\n⏱️  Tiempo total: {elapsed:.1f}s")
    print(f"📊 Productos procesados: {summary.get('total_products', 0)}")
    print(f"  • Blacklist: {summary.get('blacklisted', 0)}")
    print(f"  • Deterministic: {summary.get('deterministic', 0)}")
    print(f"  • Cache: {summary.get('cached', 0)}")
    print(f"  • LLM: {summary.get('llm_called', 0)} ({summary.get('llm_percentage', 0)}%)")
    print(f"  • Errores: {summary.get('errors', 0)}")
    print(f"\n💡 Ahorro LLM: {summary.get('llm_avoided_percentage', 0)}%")
    
    print("\n" + "="*70)
    print(" TOP CLASIFICACIONES (Agregadas)")
    print("="*70)
    
    sorted_agg = sorted(
        aggregation.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:20]  # Top 20
    
    for classification, data in sorted_agg:
        examples = ", ".join([f"'{ex}'" for ex in data['examples']])
        print(f"\n  {classification}")
        print(f"    Count: {data['count']}")
        print(f"    Examples: {examples}")
    
    # 6. Save results to CSV and XLSX
    print("\n📁 Guardando resultados...")
    output_dir = Path(__file__).parent / "outputs" / "salidas_llm" / "resultados_reales"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CSV
    results_df = pd.DataFrame(executor.results)
    results_file = output_dir / f"clasificaciones_{int(time.time())}.csv"
    results_df.to_csv(results_file, index=False)
    print(f"✅ CSV guardado en: {results_file}")
    
    # XLSX FILES
    # Create output dir for XLSX
    xlsx_output_dir = Path(__file__).parent.parent / "resultados_v5"
    xlsx_output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. resultados_clasificacion_llm_avanzada.xlsx - Full detailed results
    xlsx_file1 = xlsx_output_dir / "resultados_clasificacion_llm_avanzada.xlsx"
    results_df.to_excel(xlsx_file1, sheet_name='Resultados', index=False)
    print(f"✅ XLSX #1 guardado: {xlsx_file1}")
    
    # 2. resumen_clasificacion_avanzada.xlsx - Summary by classification
    summary_df = results_df.groupby('clasificac').agg({
        'product': 'count',
        'confidence': 'mean'
    }).reset_index()
    summary_df.columns = ['Clasificación', 'Total', 'Confianza Promedio']
    summary_df = summary_df.sort_values('Total', ascending=False)
    
    xlsx_file2 = xlsx_output_dir / "resumen_clasificacion_avanzada.xlsx"
    with pd.ExcelWriter(xlsx_file2) as writer:
        summary_df.to_excel(writer, sheet_name='Resumen', index=False)
    print(f"✅ XLSX #2 guardado: {xlsx_file2}")
    
    # 3. resumen_conteo_clasificacion_final.xlsx - Detailed count by product
    # Group by classification and product
    detailed_count = results_df.groupby(['clasificac', 'product']).size().reset_index(name='Conteo')
    detailed_count = detailed_count.sort_values(['clasificac', 'Conteo'], ascending=[True, False])
    
    # Also summary by category
    category_summary = results_df.groupby('clasificac').size().reset_index(name='Conteo')
    category_summary.columns = ['Clasificación Final', 'Conteo']
    category_summary = category_summary.sort_values('Conteo', ascending=False)
    
    product_summary = detailed_count.copy()
    product_summary.columns = ['Clasificación Final', 'Nombre de Producto', 'Conteo']
    
    xlsx_file3 = xlsx_output_dir / "resumen_conteo_clasificacion_final.xlsx"
    with pd.ExcelWriter(xlsx_file3) as writer:
        category_summary.to_excel(writer, sheet_name='Resumen por Categoría', index=False)
        product_summary.to_excel(writer, sheet_name='Detalle por Producto', index=False)
    print(f"✅ XLSX #3 guardado: {xlsx_file3}")
    
    # 4. productos_por_categoria.xlsx - One sheet per category (usando categorias_detectadas)
    xlsx_file4 = xlsx_output_dir / "productos_por_categoria.xlsx"
    
    # Expandir cada fila a todas sus categorías detectadas
    expanded_rows = []
    for _, row in results_df.iterrows():
        cats = row.get('categorias_detectadas', [row['clasificac']])
        if isinstance(cats, str):
            cats = [cats]
        for cat in cats:
            row_copy = row.copy()
            row_copy['categoria_asignada'] = cat
            expanded_rows.append(row_copy)
    
    expanded_df = pd.DataFrame(expanded_rows)
    all_categories = expanded_df['categoria_asignada'].unique()
    
    with pd.ExcelWriter(xlsx_file4) as writer:
        for category in sorted(all_categories):
            # Filter data for this category
            category_data = expanded_df[expanded_df['categoria_asignada'] == category].copy()
            # Sort by product name for readability
            category_data = category_data.sort_values('product')
            # Write to sheet (truncate sheet name if too long - Excel limit is 31 chars)
            sheet_name = str(category)[:31]
            category_data.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"✅ XLSX #4 guardado: {xlsx_file4}")
    print(f"   → Contiene {len(all_categories)} hojas (una por categoría, usando categorias_detectadas)")
    
    # 5. productos_por_categoria_conteo.xlsx - One sheet per category with product counts (usando categorias_detectadas)
    xlsx_file5 = xlsx_output_dir / "productos_por_categoria_conteo.xlsx"
    
    with pd.ExcelWriter(xlsx_file5) as writer:
        for category in sorted(all_categories):
            # Filter data for this category (from expanded_df)
            category_data = expanded_df[expanded_df['categoria_asignada'] == category].copy()
            # Group by product name to get counts
            product_counts = category_data.groupby('product').agg({
                'categoria_asignada': 'count',  # Count occurrences
                'confidence': 'mean',    # Average confidence
                'method': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'unknown'  # Most common method
            }).reset_index()
            product_counts.columns = ['Producto', 'Conteo', 'Confianza Promedio', 'Método Principal']
            # Sort by count descending
            product_counts = product_counts.sort_values('Conteo', ascending=False)
            # Write to sheet
            sheet_name = str(category)[:31]
            product_counts.to_excel(writer, sheet_name=sheet_name, index=False)
    print(f"✅ XLSX #5 guardado: {xlsx_file5}")
    print(f"   → Contiene {len(all_categories)} hojas (conteo por producto, usando categorias_detectadas)")
    
    # 7. Log summary
    logger.info(f"Real pipeline execution completed")
    logger.info(f"Summary: {summary}")
    
    print("\n" + "="*70)
    print("✅ Ejecución completada exitosamente")
    print("="*70 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
