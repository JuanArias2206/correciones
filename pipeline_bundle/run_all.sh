#!/usr/bin/env zsh

# Portable runner for the pipeline bundle.
# Usage: ./run_all.sh /path/to/wetransfer_sivigila_2025-07-24_1807
# If no argument is provided, place the wetransfer folder inside `data/`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$SCRIPT_DIR"
DATA_DIR="$BASE_DIR/data/wetransfer_sivigila_2025-07-24_1807"
OUTPUTS_DIR="$BASE_DIR/outputs/salidas_llm/resultados_v5"
VERSIONS_DIR="$BASE_DIR/outputs_versions"

# Allow passing the input folder as first arg
if [ "$#" -ge 1 ] && [ -d "$1" ]; then
  echo "Using provided input folder: $1"
  # copy contents into local data dir (do not overwrite existing copy unless confirmed)
  mkdir -p "$DATA_DIR"
  cp -a "$1"/* "$DATA_DIR/" || true
else
  echo "No external input folder provided. Expecting Excel files under: $DATA_DIR"
fi

mkdir -p "$VERSIONS_DIR"

# Create next version
read VER_NUM VER_TS < <(python3 "$BASE_DIR/manage_versions.py" --create)
RUN_NAME="run_v${VER_NUM}_${VER_TS}"
RUN_DIR="$VERSIONS_DIR/$RUN_NAME"
mkdir -p "$RUN_DIR"

# Backup existing outputs if any
if [ -e "$OUTPUTS_DIR" ]; then
  mv "$OUTPUTS_DIR" "$RUN_DIR/previous_outputs_$(date +%Y%m%d_%H%M%S)"
fi

# Ensure fresh outputs dir exists for scripts
mkdir -p "$OUTPUTS_DIR"

# Run main pipeline
echo "Running main pipeline: nuevo_codigo.py"
python3 "$BASE_DIR/nuevo_codigo.py" 2>&1 | tee "$RUN_DIR/nuevo_codigo.log"

# Move results into run folder
if [ -e "$OUTPUTS_DIR" ]; then
  mv "$OUTPUTS_DIR" "$RUN_DIR/resultados_v5"
fi

# Create symlink to latest
ln -sfn "$RUN_DIR/resultados_v5" "$OUTPUTS_DIR"

# Run verifications
echo "Running verification: conteo_clasificaciones.py"
python3 "$BASE_DIR/conteo_clasificaciones.py" 2>&1 | tee "$RUN_DIR/conteo_clasificaciones.log"

echo "Running verification: graficas_sexo.py"
python3 "$BASE_DIR/graficas_sexo.py" 2>&1 | tee "$RUN_DIR/graficas_sexo.log"

# Save run metadata
echo "{\"version\": $VER_NUM, \"timestamp\": \"$VER_TS\", \"run_dir\": \"$RUN_DIR\"}" > "$RUN_DIR/metadata.json"

echo "Run completed. Version: $VER_NUM, stored at: $RUN_DIR"
