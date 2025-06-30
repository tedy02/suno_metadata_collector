#!/usr/bin/env python3
"""
make_suno_excel.py
──────────────────
• Scans suno_api_dump/*_clips.json
• Flattens every clip dict (nested keys become dotted paths)
• Adds columns: project_name, project_id
• Combines ALL projects into one worksheet
• Writes suno_clips.xlsx
"""

import json, pathlib, sys
from typing import Any, Dict
import pandas as pd

OUT_DIR   = pathlib.Path("suno_api_dump")
OUT_FILE  = pathlib.Path("suno_clips.xlsx")
CLIP_GLOB = "*_clips.json"

# ── flatten helper ────────────────────────────────────────────
def flatten(obj: Dict[str, Any], prefix="") -> Dict[str, Any]:
    """Recursively flattens nested dictionaries using dotted keys."""
    flat: Dict[str, Any] = {}
    for k, v in obj.items():
        key = f"{prefix}{k}" if prefix == "" else f"{prefix}.{k}"
        if isinstance(v, dict):
            flat.update(flatten(v, key))
        else:
            flat[key] = v
    return flat

# ── gather all clips ──────────────────────────────────────────
rows = []

for jf in OUT_DIR.glob(CLIP_GLOB):
    data = json.loads(jf.read_text())
    project_name = data.get("name") or jf.stem.replace("_clips", "")
    project_id   = data.get("project_id")

    for clip in data.get("project_clips", []):
        row = flatten(clip)
        row["project_name"] = project_name
        row["project_id"]   = project_id
        rows.append(row)

if not rows:
    sys.exit("No *_clips.json files found or they contain no clips.")

# Build DataFrame with **all** keys (missing values become NaN)
df = pd.DataFrame(rows)

# Optional: sort columns – place project columns first, then the rest alpha
front = ["project_name", "project_id"]
cols  = front + sorted(c for c in df.columns if c not in front)
df = df[cols]

# Write Excel (single sheet)
df.to_excel(OUT_FILE, index=False)
print(f"✓ Excel written to {OUT_FILE.resolve()}")
