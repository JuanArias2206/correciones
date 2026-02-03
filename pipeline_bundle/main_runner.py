#!/usr/bin/env python3
"""Main Python runner for the pipeline bundle.
Usage:
  python3 main_runner.py [--input /path/to/wetransfer_folder]

This script:
 - optionally copies Excel files from an external wetransfer folder into ./data/...
 - creates a versioned run via manage_versions.py
 - runs nuevo_codigo.py and captures logs
 - moves outputs into the versioned run folder and creates a symlink to the latest
 - runs verification scripts and captures logs
 - writes metadata.json in the run folder
"""
import argparse
import os
import shutil
import time
import subprocess
import sys
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'wetransfer_sivigila_2025-07-24_1807')
OUTPUTS_DIR = os.path.join(BASE_DIR, 'outputs', 'clasificaciones_conteo')
VERSIONS_DIR = os.path.join(BASE_DIR, 'outputs_versions')
MANAGE_VERSIONS = os.path.join(BASE_DIR, 'manage_versions.py')

os.makedirs(VERSIONS_DIR, exist_ok=True)


def copy_input_folder(src_folder: str):
    os.makedirs(DATA_DIR, exist_ok=True)
    for name in os.listdir(src_folder):
        src = os.path.join(src_folder, name)
        dst = os.path.join(DATA_DIR, name)
        try:
            if os.path.isdir(src):
                # copytree without error if dst exists
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        except Exception as e:
            print(f"Warning copying {src} -> {dst}: {e}")


def run_manage_versions() -> (int, str):
    # run manage_versions.py --create and parse stdout
    try:
        out = subprocess.check_output([sys.executable, MANAGE_VERSIONS, '--create'], cwd=BASE_DIR, stderr=subprocess.STDOUT, text=True)
        out = out.strip()
        parts = out.split()
        if len(parts) >= 2:
            ver = int(parts[0])
            ts = parts[1]
            timestamped_print(f"Created version {ver} {ts}")
            return ver, ts
    except subprocess.CalledProcessError as e:
        print(f"Error running manage_versions.py: {e.output}")
    except Exception as e:
        print(f"Unexpected error running manage_versions.py: {e}")
    # fallback
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    return 0, now


def timestamped_print(msg: str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{ts}] {msg}")


def run_script(script_relpath: str, log_path: str) -> int:
    """Run a script and stream output to both console (with timestamps) and a log file."""
    script_path = os.path.join(BASE_DIR, script_relpath)
    timestamped_print(f"Starting {script_relpath}")
    with open(log_path, 'w', encoding='utf-8') as lf:
        lf.write(f"=== Running {script_relpath} at {datetime.now().isoformat()} ===\n")
        lf.flush()
        proc = subprocess.Popen([sys.executable, script_path], cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # stream output
        try:
            for line in proc.stdout:
                if line is None:
                    continue
                line = line.rstrip('\n')
                lf.write(line + '\n')
                lf.flush()
                timestamped_print(f"{script_relpath}: {line}")
        except Exception as e:
            lf.write(f"Error streaming output: {e}\n")
            timestamped_print(f"Error streaming output from {script_relpath}: {e}")
        ret = proc.wait()
        lf.write(f"=== Finished {script_relpath} at {datetime.now().isoformat()} returncode={ret} ===\n")
    timestamped_print(f"Finished {script_relpath} returncode={ret}")
    return ret


def safe_move(src: str, dst: str):
    # operate on paths that may be directories, files or symlinks
    if not os.path.lexists(src):
        return False

    # If src is a symlink, try to resolve and move the real target directory
    if os.path.islink(src):
        try:
            target = os.readlink(src)
            if not os.path.isabs(target):
                target = os.path.join(os.path.dirname(src), target)
            target = os.path.abspath(target)
        except Exception:
            target = None

        if target and os.path.exists(target) and os.path.isdir(target):
            # remove dst if exists
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            shutil.move(target, dst)
            try:
                os.unlink(src)
            except Exception:
                pass
            return True
        else:
            # broken symlink or points to non-directory: remove the symlink
            try:
                os.unlink(src)
            except Exception:
                pass
            return False

    # Normal file/directory
    if os.path.exists(dst):
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        else:
            os.remove(dst)
    shutil.move(src, dst)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', help='Optional path to wetransfer folder to copy into bundle data')
    args = parser.parse_args()

    if args.input:
        if os.path.isdir(args.input):
            timestamped_print(f"Copying input files from: {args.input} -> {DATA_DIR}")
            copy_input_folder(args.input)
        else:
            timestamped_print(f"Provided input path is not a directory: {args.input}")

    ver, ts = run_manage_versions()
    run_name = f"run_v{ver}_{ts}"
    run_dir = os.path.join(VERSIONS_DIR, run_name)
    os.makedirs(run_dir, exist_ok=True)

    # backup existing outputs if present
    if os.path.exists(OUTPUTS_DIR):
        backup_name = f"previous_outputs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dst = os.path.join(run_dir, backup_name)
        timestamped_print(f"Moving existing outputs to backup: {backup_dst}")
        safe_move(OUTPUTS_DIR, backup_dst)

    # ensure outputs parent dir exists
    os.makedirs(os.path.dirname(OUTPUTS_DIR), exist_ok=True)

    # Run main pipeline
    timestamped_print("Running main pipeline: nuevo_codigo.py")
    run_script('nuevo_codigo.py', os.path.join(run_dir, 'nuevo_codigo.log'))

    # After run, move outputs into run folder if present. Be tolerant to
    # different ways the pipeline may have written files (direct folder,
    # files in parent dir, or symlinks).
    result_dst = os.path.join(run_dir, 'clasificaciones_conteo')
    # small pause to let any file handles flush
    time.sleep(0.5)

    parent_dir = os.path.dirname(OUTPUTS_DIR)
    moved = False

    # Case A: pipeline created the EXPECTED directory
    if os.path.isdir(OUTPUTS_DIR):
        timestamped_print(f"Archiving outputs directory to: {result_dst}")
        moved = safe_move(OUTPUTS_DIR, result_dst)

    # Case B: pipeline left files in the parent outputs folder (common mismatch).
    if (not moved) and os.path.isdir(parent_dir):
        expected_files = [
            'resultados_clasificacion_llm_avanzada.xlsx',
            'resumen_clasificacion_avanzada.xlsx'
        ]
        found_any = False
        for fname in expected_files:
            if os.path.exists(os.path.join(parent_dir, fname)):
                found_any = True
                break
        if found_any:
            timestamped_print(f"Found expected output files in parent dir; moving into {result_dst}")
            os.makedirs(result_dst, exist_ok=True)
            for fname in expected_files:
                srcf = os.path.join(parent_dir, fname)
                if os.path.exists(srcf):
                    try:
                        shutil.move(srcf, os.path.join(result_dst, fname))
                    except Exception as e:
                        timestamped_print(f"Warning moving file {srcf} -> {result_dst}: {e}")
            moved = True

    # Case C: pipeline may have created a directory with the same name under parent
    alt_dir = os.path.join(parent_dir, 'clasificaciones_conteo')
    if (not moved) and os.path.isdir(alt_dir):
        timestamped_print(f"Archiving alternate outputs dir to: {result_dst}")
        moved = safe_move(alt_dir, result_dst)

    if not moved:
        timestamped_print(f"No outputs found to archive into {result_dst}")

    # Create/refresh symlink to latest
    link_path = OUTPUTS_DIR
    # Only create symlink if we actually have archived outputs
    if os.path.exists(result_dst):
        # remove existing link or dir at link_path
        try:
            if os.path.islink(link_path):
                os.unlink(link_path)
            elif os.path.isdir(link_path):
                shutil.rmtree(link_path)
            elif os.path.exists(link_path):
                os.remove(link_path)
        except Exception:
            pass
        try:
            os.symlink(result_dst, link_path)
        except Exception as e:
            timestamped_print(f"Warning creating symlink {link_path} -> {result_dst}: {e}")
    else:
        timestamped_print(f"Skipping symlink creation because {result_dst} does not exist")

    # Run verification scripts
    # Run verification scripts only if archived outputs exist and contain expected files
    expected_check = os.path.join(result_dst, 'resultados_clasificacion_llm_avanzada.xlsx')
    if os.path.exists(result_dst) and os.path.exists(expected_check):
        timestamped_print("Running verification: conteo_clasificaciones.py")
        run_script('conteo_clasificaciones.py', os.path.join(run_dir, 'conteo_clasificaciones.log'))

        timestamped_print("Running verification: graficas_sexo.py")
        run_script('graficas_sexo.py', os.path.join(run_dir, 'graficas_sexo.log'))
    else:
        timestamped_print(f"Skipping verification: expected file missing: {expected_check}")

    # Write metadata
    meta = {'version': ver, 'timestamp': ts, 'run_dir': run_dir}
    with open(os.path.join(run_dir, 'metadata.json'), 'w', encoding='utf-8') as mf:
        json.dump(meta, mf, indent=2, ensure_ascii=False)

    timestamped_print(f"Run completed. Version: {ver}, stored at: {run_dir}")


if __name__ == '__main__':
    main()
