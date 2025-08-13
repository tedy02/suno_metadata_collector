#!/usr/bin/env python3
"""
Suno Metatag Collector v2.0.1

All-in-one Suno metatag/metadata collector (Python 3.9+)

What's new in v2.0.1
- Excel auto-named as suno_clips_YYYY-MM-DD.xlsx with _1, _2 suffixes if needed
- Version info logged at start of each run
- README documents current 94 extracted metadata fields

Security
- On successful completion, automatically deletes token files: auth.json and auto.json (if present).

Credits
- Code written by tedy02, 2025
- Coding assistance by Chat-GPT
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Set

__version__ = "2.0.1"
__version_notes__ = """- Excel auto-named as suno_clips_YYYY-MM-DD.xlsx with _1, _2 suffixes if needed
- Version info logged at start of each run
- README documents current 94 extracted metadata fields
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    import pyperclip  # optional but recommended for automatic clipboard watching
except ImportError:
    pyperclip = None

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Suno Metatag Collector")
    p.add_argument("--out-dir", default="suno_api_dump", help="Output directory (default: suno_api_dump)")
    p.add_argument("--workspace", action="append", default=None,
                   help="Filter to specific workspace name(s). Case-insensitive. Repeat for multiple.")
    p.add_argument("--open-excel", default="true", choices=["true", "false"],
                   help="Open the Excel file on completion (default: true)")
    p.add_argument("--no-watcher", action="store_true", help="Disable watcher subprocess (manual pasting only)")
    p.add_argument("--write-parquet", action="store_true", help="Also write suno_clips.parquet if pyarrow available")
    p.add_argument("--log-dir", default="logs", help="Directory for logs (default: logs)")
    p.add_argument("--watcher", action="store_true", help=argparse.SUPPRESS)
    return p.parse_args()

ARGS = parse_args()

ORIGIN: str = "https://studio-api.prod.suno.com"
PAGE_LIMIT: int = 250

ROOT = pathlib.Path(".").resolve()
AUTH_FILE = ROOT / "auth.json"
AUTO_FILE = ROOT / "auto.json"   # extra safeguard: delete on success if present
OUT_DIR   = ROOT / ARGS.out_dir
PAGE_DIR  = OUT_DIR / "pages"
PARQUET_OUT = ROOT / "suno_clips.parquet"

OUT_DIR.mkdir(parents=True, exist_ok=True)
PAGE_DIR.mkdir(parents=True, exist_ok=True)

LOG_DIR = ROOT / ARGS.log_dir
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"run_{time.strftime('%Y%m%d_%H%M%S')}.log"
os.environ["SUNO_LOG_FILE"] = str(LOG_FILE)

def _append_log(line: str) -> None:
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass

def log(msg: str) -> None:
    print(msg)
    _append_log(msg)

def _redact(s: str) -> str:
    return re.sub(r"([A-Za-z0-9_\-]{12,})", lambda m: (m.group(1)[:6] + "…" + m.group(1)[-4:]), s)

def log_http_error(prefix: str, status: int, body: str) -> None:
    safe = _redact(body[:500])
    log(f"{prefix} HTTP {status}: {safe}")

def _bell() -> None:
    try:
        import winsound  # type: ignore
        try:
            winsound.MessageBeep(-1)
        except Exception:
            winsound.Beep(1000, 160)
        return
    except Exception:
        pass
    try:
        print("\a", end="", flush=True)
    except Exception:
        pass

def _print_header_workspace(name: str, expected: int) -> None:
    log(f"\n=== {name} ({expected} rows) ===")

def _print_page_line(page: int, new_rows: int, total: int) -> None:
    log(f"  • page {page:<4} adding {new_rows:<3} new rows   total # of rows {total}")

COMMON_QS: Dict[str, Any] = dict(
    hide_disliked="true",
    hide_studio_clips="true",
    hide_gen_stems="true",
    limit=PAGE_LIMIT,
)

def _build_session() -> requests.Session:
    retry = Retry(
        total=8, connect=5, read=5, status=8,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        respect_retry_after_header=True,
    )
    s = requests.Session()
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://",  HTTPAdapter(max_retries=retry))
    return s

SESSION = _build_session()

HDR_RX = {
    "bearer":  re.compile(r"-H\s+['\"]authorization:\s*Bearer\s+([^'\"]+)['\"]", re.I),
    "browser": re.compile(r"-H\s+['\"]browser-token:\s*([^'\"]+)['\"]",          re.I),
    "device":  re.compile(r"-H\s+['\"]device-id:\s*([^'\"]+)['\"]",              re.I),
}

def _extract_tokens_from_curl(curl: str) -> Optional[Dict[str, str]]:
    out: Dict[str, str] = {}
    for key, rx in HDR_RX.items():
        m = rx.search(curl)
        if not m:
            return None
        out[key] = m.group(1)
    return out

def _write_auth(tokens: Dict[str, str]) -> None:
    AUTH_FILE.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    when = time.strftime("%Y-%m-%d %H:%M:%S")
    log(f"[{when}] auth.json updated")

def _load_tokens() -> Dict[str, str]:
    d = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    return {"bearer": d["bearer"], "browser": d["browser"], "device": d["device"]}

def _headers() -> Dict[str, str]:
    t = _load_tokens()
    return {
        "Authorization": f"Bearer {t['bearer']}",
        "browser-token": t['browser'],
        "device-id": t['device'],
        "Accept": "*/*",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": "https://suno.com",
        "Referer": "https://suno.com/"
    }

def _stdin_watcher_loop() -> None:
    log("Watcher (stdin mode): paste a 'Copy as cURL (bash)'; blank line to submit. Ctrl+C to stop.")
    while True:
        _bell()
        log("Paste cURL now:")
        lines: List[str] = []
        while True:
            try:
                ln = input()
            except EOFError:
                return
            if not ln.strip():
                break
            lines.append(ln.rstrip())
        text = "\n".join(lines)
        if text.startswith("curl"):
            toks = _extract_tokens_from_curl(text)
            if toks:
                _write_auth(toks)
            else:
                log("Watcher: cURL missing required headers. Ensure you used 'Copy as cURL (bash)'.")
        else:
            log("Watcher: Input did not start with 'curl'. Try again.")

def _run_watcher_loop(poll_interval: float = 2.0) -> None:
    log("Watcher: listening for 'Copy as cURL (bash)'. Close this window to stop.")
    if pyperclip is None:
        log("Watcher: 'pyperclip' not installed. Falling back to manual paste mode.")
        _stdin_watcher_loop()
        return
    last = ""
    while True:
        try:
            txt = pyperclip.paste()
        except Exception:
            txt = ""
        if txt.startswith("curl") and txt != last:
            toks = _extract_tokens_from_curl(txt)
            if toks:
                last = txt
                _write_auth(toks)
            else:
                log("Watcher: detected cURL but missing required headers.")
        time.sleep(poll_interval)

def _spawn_watcher_subprocess() -> Optional[subprocess.Popen]:
    args = [sys.executable, str(pathlib.Path(__file__).resolve()), "--watcher"]
    env = os.environ.copy()
    env["SUNO_LOG_FILE"] = str(LOG_FILE)
    try:
        if os.name == "nt":
            return subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0), env=env)
        return subprocess.Popen(args, start_new_session=True, env=env)
    except Exception as e:
        log(f"Warning: could not start watcher subprocess: {e}")
        return None

def _wait_for_auth_refresh(old_mtime: float) -> None:
    log("Waiting for auth.json refresh …")
    _bell()
    while True:
        try:
            if AUTH_FILE.stat().st_mtime != old_mtime:
                break
        except FileNotFoundError:
            pass
        time.sleep(2)
    log("auth.json updated")

def api_get(path: str, **qs) -> Dict[str, Any]:
    url = f"{ORIGIN}/api/{path.lstrip('/')}"
    while True:
        try:
            r = SESSION.get(url, headers=_headers(), params={**COMMON_QS, **qs}, timeout=45)
        except Exception as e:
            log(f"Request failed: {e}. Retrying in 10s…")
            time.sleep(10)
            continue

        if r.status_code == 401:
            log("[!] 401 Unauthorized. Waiting for new token.")
            try:
                old_m = AUTH_FILE.stat().st_mtime
            except FileNotFoundError:
                old_m = 0.0
            _wait_for_auth_refresh(old_m)
            continue

        if r.status_code == 429:
            retry_after = int(r.headers.get("Retry-After", "0") or 0)
            wait = max(retry_after, 30)
            log(f"[!] 429 Too Many Requests. Waiting {wait}s before retrying…")
            time.sleep(wait)
            continue

        if r.status_code >= 400:
            log_http_error("[!]", r.status_code, r.text)
            time.sleep(10)
            continue

        try:
            return r.json()
        except ValueError:
            log("[!] Non-JSON response; retrying in 10s…")
            time.sleep(10)

def _clean_ws_name(name: Optional[str], fb: str) -> str:
    return re.sub(r"[^\w\- ]+", "", name or "").strip().replace(" ", "_")[:60] or fb

def _name_matches_filter(raw_name: Optional[str], cleaned: str) -> bool:
    if not ARGS.workspace:
        return True
    targets = [w.lower() for w in ARGS.workspace]
    return (raw_name or "").lower() in targets or cleaned.lower() in targets

def crawl_all_projects() -> Dict[str, int]:
    projects_blob = api_get("project/me")
    (OUT_DIR / "project_me.json").write_text(json.dumps(projects_blob, indent=2), encoding="utf-8")

    stats: Dict[str, int] = {}
    for pr in projects_blob.get("projects", []):
        pid: str = pr["id"]
        pname_raw: str = pr.get("name")
        pname_clean: str = _clean_ws_name(pname_raw, pr["id"][:8])
        if not _name_matches_filter(pname_raw, pname_clean):
            continue
        clip_goal: int = pr.get("clip_count") or 0

        _print_header_workspace(pname_clean, clip_goal)
        merged_rows: List[Dict[str, Any]] = []
        total_unique: Set[str] = set()
        page = 1

        while True:
            if pid == "default":
                blob = api_get("feed/v2", page=page, workspace="default")
            else:
                blob = api_get("feed/v2", page=page, project_id=pid)

            clips = blob.get("clips") or []
            if not clips:
                break

            (PAGE_DIR / f"{pname_clean}_page{page}.json").write_text(json.dumps(clips, indent=2), encoding="utf-8")

            new = 0
            for c in clips:
                unique_id = c.get("id") or c.get("clip_id")
                if unique_id and unique_id not in total_unique:
                    merged_rows.append(c)
                    total_unique.add(unique_id)
                    new += 1

            _print_page_line(page, new, len(total_unique))

            if new == 0 or (clip_goal and len(total_unique) >= clip_goal):
                break
            page += 1

        out = OUT_DIR / f"{pname_clean}_clips.json"
        json.dump(dict(
            project_id=pid,
            name=pname_raw,
            clip_count=len(merged_rows),
            project_clips=merged_rows
        ), out.open("w", encoding="utf-8"), indent=2)
        log(f"  → merged {len(merged_rows)} rows → {out.name}")
        stats[pname_clean] = len(merged_rows)

    log("\nAll project clip data stored in " + str(OUT_DIR))
    log("\nCLIP COUNTS PER PROJECT:")
    for pname, count in stats.items():
        log(f" - {pname}: {count}")
    return stats

def _flatten(obj: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
    flat: Dict[str, Any] = {}
    for k, v in obj.items():
        key = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            flat.update(_flatten(v, key))
        else:
            flat[key] = v
    return flat

def _excel_legal_sheetname(name: str) -> str:
    cleaned = re.sub(r"[\[\]:*?/\\]", "_", name or "")
    return (cleaned or "Sheet")[:31]

def _unique_sheetname(base: str, taken: set[str]) -> str:
    name = _excel_legal_sheetname(base)
    if name not in taken:
        return name
    root = name[:28]
    i = 2
    while True:
        candidate = f"{root}_{i}"
        if candidate not in taken:
            return candidate
        i += 1

def _make_excel_path() -> pathlib.Path:
    base = f"suno_clips_{time.strftime('%Y-%m-%d')}"
    path = ROOT / f"{base}.xlsx"
    i = 1
    while path.exists():
        path = ROOT / f"{base}_{i}.xlsx"
        i += 1
    return path

def build_excel(write_parquet: bool = False) -> pathlib.Path:
    clip_files = list(OUT_DIR.glob("*_clips.json"))
    if not clip_files:
        log("No *_clips.json files found or they contain no clips. Skipping Excel.")
        return _make_excel_path()

    project_dfs: Dict[str, pd.DataFrame] = {}
    all_rows: List[Dict[str, Any]] = []
    taken: set[str] = set()

    for jf in clip_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        project_name = data.get("name") or jf.stem.replace("_clips", "")
        project_id   = data.get("project_id")
        clips = data.get("project_clips", [])
        if not clips:
            continue

        rows = []
        for clip in clips:
            row = _flatten(clip)
            row["project_name"] = project_name
            row["project_id"]   = project_id
            rows.append(row)

        df = pd.DataFrame(rows)
        front = ["project_name", "project_id"]
        cols  = front + sorted([c for c in df.columns if c not in front])
        df = df[cols]

        sheetname = _unique_sheetname(str(project_name), taken)
        taken.add(sheetname)
        project_dfs[sheetname] = df
        all_rows.extend(rows)

    excel_out = _make_excel_path()
    with pd.ExcelWriter(excel_out, engine="xlsxwriter") as writer:
        all_df = pd.DataFrame(all_rows) if all_rows else pd.DataFrame(columns=["project_name","project_id"])
        front = ["project_name", "project_id"]
        cols  = front + sorted([c for c in all_df.columns if c not in front])
        all_df = all_df[cols]
        all_df.to_excel(writer, sheet_name="ALL", index=False)

        for name, df in project_dfs.items():
            df.to_excel(writer, sheet_name=name, index=False)

    log(f"Excel written to {excel_out.resolve()}")

    if write_parquet and not all_df.empty:
        try:
            all_df.to_parquet(PARQUET_OUT, index=False)
            log(f"Parquet written to {PARQUET_OUT.resolve()}")
        except Exception as e:
            log(f"Parquet not written (install 'pyarrow' to enable): {e}")

    return excel_out

def ask_for_initial_curl() -> str:
    _bell()
    if pyperclip is not None:
        try:
            txt = pyperclip.paste()
            if isinstance(txt, str) and txt.startswith("curl"):
                log("Copied cURL from clipboard.")
                return txt
        except Exception:
            pass
    log("Paste cURL (end with empty line):")
    lines: List[str] = []
    while True:
        ln = input().strip()
        if not ln:
            break
        lines.append(ln)
    return "\n".join(lines)

def _open_excel_file(path: pathlib.Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as e:
        log(f"Could not auto-open Excel file: {e}")

def _cleanup_tokens_on_success() -> None:
    """Security cleanup on successful completion: remove auth.json and auto.json if present."""
    for p in (AUTH_FILE, AUTO_FILE):
        try:
            if p.exists():
                p.unlink()
                log(f"Deleted token file: {p.name}")
        except Exception as e:
            log(f"Warning: could not delete {p.name}: {e}")

def _main() -> int:
    log(f"Suno Metatag Collector v{__version__} starting")
    log("Version notes:\n" + __version_notes__.strip())

    watcher = None
    if not ARGS.no_watcher:
        watcher = _spawn_watcher_subprocess()
        if watcher:
            log(f"Watcher PID: {watcher.pid}")
        else:
            log("Note: watcher could not be started. You can still paste tokens manually if needed.")
    else:
        log("Watcher disabled via --no-watcher")

    curl = ask_for_initial_curl()
    toks = _extract_tokens_from_curl(curl)
    if not toks:
        log("Missing header(s). Copy as cURL (bash) and try again.")
        return 2
    _write_auth(toks)

    ok = False
    excel_path = None
    try:
        crawl_all_projects()
        log("\nCrawling finished, building Excel …")
        excel_path = build_excel(write_parquet=ARGS.write_parquet)
        ok = True
    finally:
        if watcher and watcher.poll() is None:
            try:
                watcher.terminate()
                watcher.wait(timeout=3)
            except Exception:
                try:
                    watcher.kill()
                except Exception:
                    pass

    if ok:
        log("All done.")
        _bell()
        if ARGS.open_excel.lower() == "true" and excel_path:
            _open_excel_file(excel_path)
        _cleanup_tokens_on_success()
        return 0
    return 1

def _watcher_entry() -> int:
    try:
        _run_watcher_loop()
    except KeyboardInterrupt:
        pass
    return 0

if __name__ == "__main__":
    if sys.version_info < (3, 9):
        sys.exit("Python 3.9+ is required.")
    if ARGS.watcher:
        lf = os.environ.get("SUNO_LOG_FILE")
        if lf:
            LOG_FILE = pathlib.Path(lf)
        sys.exit(_watcher_entry())
    sys.exit(_main())
