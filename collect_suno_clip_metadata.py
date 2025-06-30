import os
import json
import requests
from time import sleep

# CONFIGURATION
AUTH_PATH = "auth.json"
DUMP_DIR = "suno_api_dump"
PAGE_LIMIT = 20

# Ensure the dump directory exists
os.makedirs(DUMP_DIR, exist_ok=True)

def load_auth():
    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def api_get(path, **params):
    """Perform an authenticated GET request to the Suno API."""
    auth = load_auth()
    headers = {
        "authorization": auth["auth_bearer"],
        "browser-token": auth["browser_token"],
        "device-id": auth["device_id"],
        "user-agent": auth["user_agent"],
        "accept": "*/*",
        "referer": "https://suno.com/",
    }
    url = f"https://studio-api.prod.suno.com/api/{path}"
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 401:
        print("[!] Unauthorized. Refresh token!")
        exit(1)
    if resp.status_code != 200:
        print(f"[!] HTTP {resp.status_code}: {resp.text}")
        exit(1)
    return resp.json()

def get_project_clips(pid, pname, clip_count):
    """
    Downloads all clips for a given project (by pid).
    For 'default', uses /api/default?page=N, for others uses /api/project/{pid}?page=N.
    Returns a list of all clip dicts.
    """
    all_clips = []
    seen_ids = set()
    page = 1
    while True:
        if pid == "default":
            api_path = "default"
        else:
            api_path = f"project/{pid}"
        params = {
            "hide_disliked": "true",
            "hide_studio_clips": "true",
            "page": page,
        }
        blob = api_get(api_path, **params)
        clips = blob.get("clips", [])
        if not clips:
            print(f"  • page {page:<3} empty – stopping")
            break
        unique = [c for c in clips if c.get("id") not in seen_ids]
        for c in unique:
            if "id" in c:
                seen_ids.add(c["id"])
        all_clips.extend(unique)
        print(f"  • page {page:<3}   {len(clips):<3} total   {len(unique):<3} new  unique {len(all_clips)}")
        if len(unique) == 0 or len(clips) < PAGE_LIMIT:
            break
        page += 1
        sleep(0.3)  # Be nice to the server!
    return all_clips

def main():
    # Load list of projects from your "me" endpoint (should be pre-crawled)
    with open("project_me.json", "r", encoding="utf-8") as f:
        me = json.load(f)
    projects = me["projects"]
    for prj in projects:
        pid = prj["id"]
        pname = prj["name"].replace(" ", "_").replace("/", "")
        clip_count = prj.get("clip_count", 0)
        print(f"\n=== {pname} ({clip_count} clips) ===")
        clips = get_project_clips(pid, pname, clip_count)
        json_path = os.path.join(DUMP_DIR, f"{pname}_clips.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(clips, f, indent=2, ensure_ascii=False)
        print(f"  → merged {len(clips)} clips → {os.path.basename(json_path)}")
    print(f"\n✅  All project clip data stored in {os.path.abspath(DUMP_DIR)}")

if __name__ == "__main__":
    main()
import os
import json
import requests
from time import sleep

# CONFIGURATION
AUTH_PATH = "auth.json"
DUMP_DIR = "suno_api_dump"
PAGE_LIMIT = 20

# Ensure the dump directory exists
os.makedirs(DUMP_DIR, exist_ok=True)

def load_auth():
    with open(AUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def api_get(path, **params):
    """Perform an authenticated GET request to the Suno API."""
    auth = load_auth()
    headers = {
        "authorization": auth["auth_bearer"],
        "browser-token": auth["browser_token"],
        "device-id": auth["device_id"],
        "user-agent": auth["user_agent"],
        "accept": "*/*",
        "referer": "https://suno.com/",
    }
    url = f"https://studio-api.prod.suno.com/api/{path}"
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code == 401:
        print("[!] Unauthorized. Refresh token!")
        exit(1)
    if resp.status_code != 200:
        print(f"[!] HTTP {resp.status_code}: {resp.text}")
        exit(1)
    return resp.json()

def get_project_clips(pid, pname, clip_count):
    """
    Downloads all clips for a given project (by pid).
    For 'default', uses /api/default?page=N, for others uses /api/project/{pid}?page=N.
    Returns a list of all clip dicts.
    """
    all_clips = []
    seen_ids = set()
    page = 1
    while True:
        if pid == "default":
            api_path = "default"
        else:
            api_path = f"project/{pid}"
        params = {
            "hide_disliked": "true",
            "hide_studio_clips": "true",
            "page": page,
        }
        blob = api_get(api_path, **params)
        clips = blob.get("clips", [])
        if not clips:
            print(f"  • page {page:<3} empty – stopping")
            break
        unique = [c for c in clips if c.get("id") not in seen_ids]
        for c in unique:
            if "id" in c:
                seen_ids.add(c["id"])
        all_clips.extend(unique)
        print(f"  • page {page:<3}   {len(clips):<3} total   {len(unique):<3} new  unique {len(all_clips)}")
        if len(unique) == 0 or len(clips) < PAGE_LIMIT:
            break
        page += 1
        sleep(0.3)  # Be nice to the server!
    return all_clips

def main():
    # Load list of projects from your "me" endpoint (should be pre-crawled)
    with open("project_me.json", "r", encoding="utf-8") as f:
        me = json.load(f)
    projects = me["projects"]
    for prj in projects:
        pid = prj["id"]
        pname = prj["name"].replace(" ", "_").replace("/", "")
        clip_count = prj.get("clip_count", 0)
        print(f"\n=== {pname} ({clip_count} clips) ===")
        clips = get_project_clips(pid, pname, clip_count)
        json_path = os.path.join(DUMP_DIR, f"{pname}_clips.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(clips, f, indent=2, ensure_ascii=False)
        print(f"  → merged {len(clips)} clips → {os.path.basename(json_path)}")
    print(f"\n✅  All project clip data stored in {os.path.abspath(DUMP_DIR)}")

if __name__ == "__main__":
    main()
