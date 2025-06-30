#!/usr/bin/env python3
"""
refresh_and_collect.py
──────────────────────
Launch watcher  →  run crawler  →  (on success) build Excel
"""

import json, os, pathlib, re, subprocess, sys, time
try:
    import pyperclip
except ImportError:
    pyperclip = None                   # clipboard optional

AUTH_FILE      = pathlib.Path("auth.json")
WATCHER_SCRIPT = "save_suno_tokens_loop.py"
CRAWLER_SCRIPT = "collect_suno_clip_metadata.py"
EXCEL_SCRIPT   = "make_suno_excel.py"

HDR_RX = {
    "bearer":  re.compile(r"-H\s+'authorization:\s*Bearer\s+([^']+)'", re.I),
    "browser": re.compile(r"-H\s+'browser-token:\s*([^']+)'",          re.I),
    "device":  re.compile(r"-H\s+'device-id:\s*([^']+)'",              re.I),
}

def grab_curl():
    if pyperclip:
        txt = pyperclip.paste()
        if txt.startswith("curl"):
            print("✔ Copied cURL from clipboard.")
            return txt
    print("Paste cURL (end with empty line):")
    lines = []
    while (ln := input().strip()):
        lines.append(ln)
    return "\n".join(lines)

def tokens(curl):
    miss = [k for k, rx in HDR_RX.items() if not rx.search(curl)]
    if miss:
        sys.exit(f"Missing header(s): {', '.join(miss)}")
    return {k: rx.search(curl).group(1) for k, rx in HDR_RX.items()}

def write_auth(tok):
    AUTH_FILE.write_text(json.dumps(tok, indent=2), "utf-8")
    print("✅  auth.json written")

def spawn_watcher():
    if os.name == "nt":  # Windows new console
        return subprocess.Popen(
            ["python", WATCHER_SCRIPT],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
    # macOS / Linux
    for term in (("gnome-terminal","--"),
                 ("x-terminal-emulator","-e")):
        exe = pathlib.Path("/usr/bin")/term[0]
        if exe.exists():
            return subprocess.Popen([*term, "python", WATCHER_SCRIPT])
    # fallback: same window, background
    return subprocess.Popen(["python", WATCHER_SCRIPT])

def main():
    write_auth(tokens(grab_curl()))
    watcher = spawn_watcher()
    print("🖥  watcher PID:", watcher.pid)

    try:
        # run crawler
        res = subprocess.run(["python", CRAWLER_SCRIPT])
        ok  = res.returncode == 0
        if ok:
            print("\n🗂  Crawling finished – building Excel …")
            subprocess.run(["python", EXCEL_SCRIPT], check=True)
    finally:
        # always close watcher
        if watcher.poll() is None:
            print("⏹  Closing watcher …")
            try:
                watcher.terminate()
                watcher.wait(3)
            except Exception:
                watcher.kill()

    if ok:
        print("✅  All done – suno_clips.xlsx created.")
    else:
        sys.exit("Crawler failed – Excel not generated.")

if __name__ == "__main__":
    main()
