#!/usr/bin/env zsh

# Runner script for the corrections pipeline.
# - Backs up any existing outputs at `outputs/salidas_llm/resultados_v5`
# - Runs `nuevo_codigo.py` (main pipeline)
# - Moves the newly created results into a versioned folder under `correciones/outputs_versions`
# - Creates a symlink so verification scripts still reference the expected path
# - Runs verification scripts: `conteo_clasificaciones.py` and `graficas_sexo.py`

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CORRECTIONS_DIR="$REPO_ROOT/correciones"

# Paths used by the original scripts (they use absolute paths inside the repo)
OUTPUTS_DIR="$REPO_ROOT/outputs/salidas_llm/resultados_v5"
VERSIONS_DIR="$CORRECTIONS_DIR/outputs_versions"
VERSIONS_META="$CORRECTIONS_DIR/versions.json"

# Ensure versions dir exists
mkdir -p "$VERSIONS_DIR"

# Get next version and timestamp from the small manager
read VER_NUM VER_TS < <(python3 "$SCRIPT_DIR/manage_versions.py" --create)
RUN_NAME="run_v${VER_NUM}_${VER_TS}"
RUN_DIR="$VERSIONS_DIR/$RUN_NAME"
mkdir -p "$RUN_DIR"

# If there is an existing outputs dir, move it to an archival folder (avoid overwriting)
if [ -e "$OUTPUTS_DIR" ]; then
  EXISTING_BACKUP="$RUN_DIR/previous_outputs_$(date +%Y%m%d_%H%M%S)"
  mv "$OUTPUTS_DIR" "$EXISTING_BACKUP"
fi

# Create a fresh outputs dir that the scripts expect
mkdir -p "$OUTPUTS_DIR"

# Run the main corrected code
echo "Running main pipeline: nuevo_codigo.py"
python3 "$CORRECTIONS_DIR/nuevo_codigo.py" 2>&1 | tee "$RUN_DIR/nuevo_codigo.log"

# After run, move the produced outputs into the versioned run folder
if [ -e "$OUTPUTS_DIR" ]; then
  mv "$OUTPUTS_DIR" "$RUN_DIR/resultados_v5"
fi

# Create a symlink at the original location pointing to the versioned results
ln -sfn "$RUN_DIR/resultados_v5" "$OUTPUTS_DIR"

# Run verification scripts (they assume the same expected paths)
# Conteo
echo "Running verification: conteo_clasificaciones.py"
python3 "$CORRECTIONS_DIR/resultados_v5/conteo_clasificaciones.py" 2>&1 | tee "$RUN_DIR/conteo_clasificaciones.log"

# Graficas
echo "Running verification: graficas_sexo.py"
python3 "$CORRECTIONS_DIR/resultados_v5/graficas_sexo.py" 2>&1 | tee "$RUN_DIR/graficas_sexo.log"

# Save a small summary
echo "{\"version\": $VER_NUM, \"timestamp\": \"$VER_TS\", \"run_dir\": \"$RUN_DIR\"}" > "$RUN_DIR/metadata.json"

echo "Run completed. Version: $VER_NUM, stored at: $RUN_DIR"
