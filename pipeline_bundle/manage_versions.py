#!/usr/bin/env python3
"""Version manager for the portable pipeline bundle.
Creates/updates `versions.json` and prints the new version id and timestamp.
Usage: python manage_versions.py --create
Output (stdout): <version_number> <timestamp>
"""
import json
import os
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSIONS_FILE = os.path.join(BASE_DIR, 'versions.json')


def load_versions():
    if os.path.exists(VERSIONS_FILE):
        try:
            with open(VERSIONS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"last_version": 0, "runs": []}
    return {"last_version": 0, "runs": []}


def save_versions(versions_data):
    with open(VERSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(versions_data, f, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != '--create':
        print("Usage: python manage_versions.py --create", file=sys.stderr)
        sys.exit(2)

    data = load_versions()
    last = data.get('last_version', 0) or 0
    new_ver = last + 1
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    entry = {"version": new_ver, "timestamp": ts}
    data.setdefault('runs', []).append(entry)
    data['last_version'] = new_ver
    save_versions(data)
    # Print to stdout: version timestamp
    print(f"{new_ver} {ts}")
