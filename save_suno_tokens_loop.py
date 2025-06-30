#!/usr/bin/env python3
"""
save_suno_tokens_loop.py
────────────────────────
Continuously watches the clipboard for a new “Copy as cURL (bash)” command,
extracts authorization / browser-token / device-id headers, and writes them to
auth.json.  Stops with Ctrl-C.

Requires: pip install pyperclip
"""

import json, re, sys, time, pathlib
import pyperclip             # pip install pyperclip

AUTH_OUT = pathlib.Path("auth.json")

PATTERNS = {
    "bearer":  re.compile(r"-H\s+'authorization:\s*Bearer\s+([^']+)'", re.I),
    "browser": re.compile(r"-H\s+'browser-token:\s*([^']+)'",         re.I),
    "device":  re.compile(r"-H\s+'device-id:\s*([^']+)'",             re.I),
}

def extract(curl_text: str):
    m = {k: rx.search(curl_text) for k, rx in PATTERNS.items()}
    if not all(m.values()):
        return None             # not a full Suno cURL
    return {k: s.group(1) for k, s in m.items()}

def save(tokens: dict):
    AUTH_OUT.write_text(json.dumps(tokens, indent=2), encoding="utf-8")
    when = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{when}]  ✔ auth.json updated")

def main():
    print("Watching clipboard — copy a fresh 'Copy as cURL (bash)' anytime.")
    last = ""
    try:
        while True:
            text = pyperclip.paste()
            if text.startswith("curl") and text != last:
                toks = extract(text)
                if toks:
                    last = text
                    save(toks)
                else:
                    print("⚠️  Detected cURL but missing required headers.")
            time.sleep(2)       # poll every 2 s
    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    if not pyperclip.paste():
        print("Tip: copy a cURL command first, then start the watcher.\n")
    main()
