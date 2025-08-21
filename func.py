import json
import requests
import sys
import urllib3
import os
from urllib.parse import urlparse, urljoin
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON file: {e}")
        sys.exit(1)

def extract_fields(obj, field_names):
    results = []
    def recursive(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in field_names:
                    results.append(f"{k}: {v}")
                recursive(v)
        elif isinstance(o, list):
            for item in o:
                recursive(item)
    recursive(obj)
    return results

def extract_fields_with_paths(obj, field_names, show_path=False):
    results = []
    def recursive(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                new_path = f"{path}/{k}" if path else k
                if k in field_names:
                    if show_path:
                        results.append(f"{k}: {v} (Path: /{new_path})")
                    else:
                        results.append(f"{k}: {v}")
                recursive(v, new_path)
        elif isinstance(o, list):
            for idx, item in enumerate(o):
                new_path = f"{path}/{idx}" if path else str(idx)
                recursive(item, new_path)
    recursive(obj)
    return results

def handle_save_response(resp, save_path):
    if save_path:
        try:
            content = resp.json()
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, indent=4, ensure_ascii=False)
        except ValueError:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(resp.text)
        print(f"💾 Response saved to {save_path}")

def sanitize_filename(url):
    path = urlparse(url).path.strip('/')
    return path.replace('/', os.sep) or 'root'

def recursive_fetch(url, auth, headers, base_path, visited, depth=0, max_depth=10):
    if url in visited or depth > max_depth:
        return
    visited.add(url)
    try:
        resp = requests.get(url, headers=headers, auth=auth, verify=False, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️ Failed to fetch {url} (status: {resp.status_code})")
            return
        try:
            data = resp.json()
        except ValueError:
            print(f"⚠️ Non-JSON response at {url}")
            return
        path = os.path.join(base_path, sanitize_filename(url))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path + '.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"💾 Saved: {path}.json")
        # Recursively fetch inner odata.id
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) and '@odata.id' in v:
                    full_url = urljoin(url, v['@odata.id'])
                    recursive_fetch(full_url, auth, headers, base_path, visited, depth + 1, max_depth)
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, dict) and '@odata.id' in item:
                            full_url = urljoin(url, item['@odata.id'])
                            recursive_fetch(full_url, auth, headers, base_path, visited, depth + 1, max_depth)
    except Exception as e:
        print(f"❌ Error fetching {url}: {e}")

def deep_find_path(url, auth, headers, field_names, visited=None, counter=None):
    if visited is None:
        visited = set()
    if counter is None:
        counter = [1]
    if url in visited:
        return
    visited.add(url)
    try:
        resp = requests.get(url, auth=auth, headers=headers, verify=False, timeout=10)
        data = resp.json()
    except Exception:
        return
    matches = extract_fields_with_paths(data, field_names, show_path=False)
    api_path = urlparse(url).path
    for match in matches:
        print(f"[{counter[0]}] {match} (API Path: {api_path})")
        counter[0] += 1
    links = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and '@odata.id' in v:
                links.append(urljoin(url, v['@odata.id']))
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict) and '@odata.id' in item:
                        links.append(urljoin(url, item['@odata.id']))
    for link in links:
        deep_find_path(link, auth, headers, field_names, visited, counter)