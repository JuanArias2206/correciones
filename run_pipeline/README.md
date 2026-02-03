Pipeline runner for `correciones` folder

Overview
- `run_all.sh`: main runner to execute `nuevo_codigo.py` and verification scripts. Creates versioned archives of outputs under `correciones/outputs_versions` and keeps a symlink at `outputs/salidas_llm/resultados_v5` pointing to the latest run.
- `manage_versions.py`: tiny helper to increment and record run versions in `correciones/versions.json`.

Usage
1) Make the runner executable:

```bash
cd correciones/run_pipeline
chmod +x run_all.sh
```

2) (Optional) Activate your Python environment (if you have a venv in `env_python3.11`):

```bash
source ../env_python3.11/bin/activate
```

3) Run the full pipeline with a single command:

```bash
./run_all.sh
```

What it does
- Backs up any existing `outputs/salidas_llm/resultados_v5` into a versioned folder under `correciones/outputs_versions/run_v{N}_{TIMESTAMP}`.
- Runs `correciones/nuevo_codigo.py` and logs output into the run folder.
- Moves the newly created results to the run folder and creates a symlink so verification scripts can find data where they expect it.
- Runs `correciones/resultados_v5/conteo_clasificaciones.py` and `graficas_sexo.py`, saving logs into the run folder.

Notes and next steps
- The runner assumes Python 3 is available as `python3`.
- It avoids editing your existing scripts; instead it archives current outputs and stores each run separately.
- If you want the pipeline to use a different outputs location, edit `run_all.sh` to modify `OUTPUTS_DIR`.
