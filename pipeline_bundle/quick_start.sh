#!/bin/bash
# 🚀 Quick Start Script - Primera Corrida del Pipeline

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   PIPELINE SPA v2.1 - PRIMERA CORRIDA                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Detectar si estamos en el directorio correcto
if [ ! -f "config.py" ]; then
    echo "❌ Error: Debe ejecutarse desde pipeline_bundle/"
    echo ""
    echo "Uso correcto:"
    echo "  cd pipeline_bundle"
    echo "  bash ../quick_start.sh"
    exit 1
fi

echo "✅ Directorio: $(pwd)"
echo ""

# 1. Validar Python
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no encontrado"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python: $PYTHON_VERSION"
echo ""

# 2. Crear directorio de logs
echo "📁 Creando directorio de logs..."
mkdir -p logs
echo "✅ logs/ listo"
echo ""

# 3. Validar dependencias
echo "📦 Verificando dependencias..."
python3 -c "import pandas, tqdm, requests" 2>/dev/null || {
    echo "⚠️  Instalando dependencias..."
    pip3 install pandas tqdm requests -q
}
echo "✅ Dependencias OK"
echo ""

# 4. Validar configuración
echo "⚙️  Validando configuración..."
python3 -c "
from config import DEEPSEEK_API_KEY, TEST_PERCENTAGE
print(f'✅ API Key: {DEEPSEEK_API_KEY[:10]}...{DEEPSEEK_API_KEY[-10:]}')
print(f'✅ Porcentaje: {TEST_PERCENTAGE}%')
" || {
    echo "❌ Error en configuración"
    exit 1
}
echo ""

# 5. Resumen
echo "════════════════════════════════════════════════════════════"
echo "📋 CONFIGURACIÓN LISTA:"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  • API Key:      ✅ Configurada"
echo "  • Porcentaje:   ✅ 20% (editar config.py para cambiar)"
echo "  • Logs:         ✅ logs/"
echo "  • Python:       ✅ $PYTHON_VERSION"
echo ""

# 6. Opción de ejecutar
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Para iniciar la primera corrida, ejecuta:"
echo ""
echo "  python run_first_test.py"
echo ""
echo "Opciones:"
echo "  python run_first_test.py                 # 20% de registros"
echo "  python run_first_test.py --pct 100      # 100% de registros"
echo "  python run_first_test.py --pct 50 -v    # 50% con verbose"
echo "  python run_first_test.py --api-test     # Solo testa API"
echo ""
echo "════════════════════════════════════════════════════════════"
