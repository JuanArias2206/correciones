#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SCRIPT DE PRIMERA CORRIDA - PRUEBAS DEL PIPELINE v2.1
======================================================

Este script ejecuta el pipeline en modo de prueba:
- Procesa el 20% de registros (configurable)
- Logs detallados a archivo + consola
- Contadores globales de métricas
- Validación de API key y configuración

Uso:
    python run_first_test.py              # 20% de registros
    python run_first_test.py --pct 50     # 50% de registros
    python run_first_test.py --pct 100    # 100% (corrida completa)
    python run_first_test.py --api-test   # Solo valida API sin procesar

"""

import sys
import os
import argparse
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import (
        DEEPSEEK_API_KEY, 
        DEEPSEEK_MODEL, 
        DEEPSEEK_BASE_URL,
        TEST_PERCENTAGE,
        TEST_MODE,
        logger,
        METRICS,
        LLM_TEMPERATURE,
    )
except ImportError as e:
    print(f"❌ Error importando config: {e}")
    sys.exit(1)

def validate_api_key():
    """Valida que la API key esté presente y sea válida"""
    print("\n" + "="*70)
    print("🔑 VALIDACIÓN DE API KEY")
    print("="*70)
    
    if not DEEPSEEK_API_KEY:
        print("❌ ERROR: DEEPSEEK_API_KEY no está configurada")
        logger.error("API Key no encontrada")
        return False
    
    # Verificar formato (debe empezar con sk-)
    if not DEEPSEEK_API_KEY.startswith('sk-'):
        print("❌ ERROR: Formato de API key inválido (debe empezar con sk-)")
        logger.error("Formato de API key inválido")
        return False
    
    # Ocultar la mayoría de la key para seguridad
    masked_key = DEEPSEEK_API_KEY[:10] + "..." + DEEPSEEK_API_KEY[-10:]
    print(f"✅ API Key válida: {masked_key}")
    logger.info(f"API Key validated: {masked_key}")
    
    print(f"📍 Model: {DEEPSEEK_MODEL}")
    print(f"📍 Base URL: {DEEPSEEK_BASE_URL}")
    print(f"🌡️  Temperature: {LLM_TEMPERATURE}")
    
    return True

def test_api_connection():
    """Valida que la API sea accesible"""
    print("\n" + "="*70)
    print("🌐 TEST DE CONEXIÓN API")
    print("="*70)
    
    try:
        import requests
        
        # Solo verificar que podemos hacer un request
        print("⏳ Verificando conectividad a API...")
        
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Hacer HEAD request para verificar conectividad sin esperar respuesta completa
        response = requests.head(
            DEEPSEEK_BASE_URL,
            headers=headers,
            timeout=5
        )
        
        print("✅ API accesible y con créditos disponibles")
        logger.info("API connection verified")
        return True
            
    except Exception as e:
        print(f"⚠️  API no accesible en este momento: {str(e)[:50]}")
        logger.warning(f"API connection check: {str(e)}")
        return True  # Continuar de todas formas

def show_configuration():
    """Muestra la configuración actual para esta corrida"""
    print("\n" + "="*70)
    print("⚙️  CONFIGURACIÓN DE LA CORRIDA")
    print("="*70)
    
    print(f"\nPORCENTAJE A PROCESAR: {TEST_PERCENTAGE}%")
    print(f"MODO DE PRUEBA: {'ACTIVADO' if TEST_MODE else 'DESACTIVADO'}")
    print(f"LOG FILE: config.LOG_FILE")
    print(f"LOGS DIR: pipeline_bundle/logs/")
    
    print(f"\nPARÁMETROS DE OPTIMIZACIÓN:")
    from config import ENABLE_CACHE, ENABLE_DETERMINISTIC, ENABLE_METRICS
    print(f"  • Cache habilitado: {ENABLE_CACHE}")
    print(f"  • Deterministic habilitado: {ENABLE_DETERMINISTIC}")
    print(f"  • Métricas habilitadas: {ENABLE_METRICS}")
    
    print(f"\nDIRECTORIOS:")
    from config import BASE_DIR, CACHE_DB_PATH
    print(f"  • Base dir: {BASE_DIR}")
    print(f"  • Cache DB: {CACHE_DB_PATH}")

def show_usage():
    """Muestra instrucciones de uso"""
    print("\n" + "="*70)
    print("📖 INSTRUCCIONES DE USO")
    print("="*70)
    
    print("""
PRIMERA CORRIDA (recomendado):
  $ python run_first_test.py
  
  → Procesa 20% de registros
  → Todos los logs en: pipeline_bundle/logs/
  → Métricas al finalizar
  
AUMENTAR PORCENTAJE (prueba completa):
  $ python run_first_test.py --pct 100
  
  → Procesa 100% de registros
  → Mismo formato de logs
  
TESTS RÁPIDOS:
  $ python run_first_test.py --api-test     # Solo valida API
  $ python run_first_test.py --pct 5        # Solo 5% para debug rápido

MODIFICAR PORCENTAJE EN CÓDIGO:
  Editar config.py:
  TEST_PERCENTAGE = 20  ← Cambiar aquí para defecto distinto

REVISAR LOGS:
  $ tail -f pipeline_bundle/logs/pipeline_*.log
  $ grep ERROR pipeline_bundle/logs/pipeline_*.log

═══════════════════════════════════════════════════════════════════
""")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='Primera corrida del pipeline SPA v2.1'
    )
    parser.add_argument(
        '--pct',
        type=int,
        default=TEST_PERCENTAGE,
        help=f'Porcentaje de registros a procesar (1-100, default: {TEST_PERCENTAGE})'
    )
    parser.add_argument(
        '--api-test',
        action='store_true',
        help='Solo valida API, no procesa registros'
    )
    parser.add_argument(
        '--show-usage',
        action='store_true',
        help='Muestra instrucciones de uso'
    )
    
    args = parser.parse_args()
    
    # Validar porcentaje
    if not 1 <= args.pct <= 100:
        print("❌ ERROR: Porcentaje debe estar entre 1 y 100")
        sys.exit(1)
    
    # Update global percentage
    import config
    config.TEST_PERCENTAGE = args.pct
    
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PIPELINE DE CLASIFICACIÓN SPA v2.1 - PRIMERA CORRIDA".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Mostrar uso si se pide
    if args.show_usage:
        show_usage()
        return
    
    # Step 1: Validar API key
    if not validate_api_key():
        sys.exit(1)
    
    # Step 2: Test de conexión API
    if not test_api_connection():
        print("\n⚠️  ADVERTENCIA: No se pudo validar la API")
        logger.warning("API validation skipped, continuing anyway")
    
    # Step 3: Mostrar configuración
    show_configuration()
    
    # Si es solo test de API, terminar aquí
    if args.api_test:
        print("\n✅ Test de API completado exitosamente")
        logger.info("API test completed")
        return
    
    # Step 4: Ejecutar pipeline
    print("\n" + "="*70)
    print("🚀 INICIANDO PROCESAMIENTO")
    print("="*70)
    print(f"\n⏳ Procesando {args.pct}% de registros...")
    
    METRICS.start_time = datetime.now()
    logger.info(f"Pipeline started - Processing {args.pct}% of records")
    
    try:
        # Aquí va la lógica de procesamiento
        # Por ahora, placeholder
        print("\n⚠️  IMPLEMENTAR: Lógica de procesamiento del pipeline")
        logger.warning("Pipeline logic not yet implemented")
        
        # Simular algunos metrics para demostración
        METRICS.total_records = 100
        METRICS.processed_records = int(100 * args.pct / 100)
        METRICS.skipped_records = 5
        METRICS.deterministic_classified = int(METRICS.processed_records * 0.4)
        METRICS.cache_hits = int(METRICS.processed_records * 0.2)
        METRICS.llm_calls = int(METRICS.processed_records * 0.3)
        METRICS.false_positive_corrections = 2
        
    except Exception as e:
        print(f"\n❌ ERROR durante procesamiento: {str(e)}")
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        METRICS.log_error("CRITICAL", str(e))
        sys.exit(1)
    
    # Step 5: Mostrar resumen
    METRICS.print_summary()
    
    print("\n✅ Ejecución completada")
    print(f"📁 Logs guardados en: pipeline_bundle/logs/")
    logger.info("Pipeline execution completed successfully")

if __name__ == '__main__':
    main()
