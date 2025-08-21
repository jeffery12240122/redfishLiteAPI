from args_parser import parse_args
from func import (
    extract_fields, extract_fields_with_paths, handle_save_response,
    recursive_fetch, deep_find_path, load_json, sanitize_filename
)
import sys
import requests
from urllib.parse import urlparse, urljoin
from requests.auth import HTTPBasicAuth
import os
import json
def main(VERSION):
    args = parse_args()
    if args.version:
        print(f"redfishLiteApi version: {VERSION}")
        return

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    # Add custom headers
    if args.header:
        for header in args.header:
            try:
                key, value = header.split(':', 1)
                headers[key.strip()] = value.strip()
            except ValueError:
                print(f"❌ Invalid header format: {header}. Use Key:Value")
                sys.exit(1)

    # Handle session token or login session
    session_token = None
    if args.session_token:
        session_token = args.session_token
        headers['X-Auth-Token'] = session_token
    elif args.login_session and args.username and args.password:
        login_url = urljoin(args.url, '/redfish/v1/SessionService/Sessions')
        login_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        login_body = {
            'UserName': args.username,
            'Password': args.password
        }
        try:
            login_resp = requests.post(login_url, headers=login_headers, json=login_body, verify=False, timeout=10)
            if login_resp.status_code in [200, 201]:
                session_token = login_resp.headers.get('X-Auth-Token')
                if not session_token:
                    print("❌ Login succeeded but no token returned.")
                    sys.exit(1)
                headers['X-Auth-Token'] = session_token
                print("🔑 Redfish session login successful.")
            else:
                print(f"❌ Login failed (HTTP {login_resp.status_code})")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Login error: {e}")
            sys.exit(1)

    # Fallback to Basic Auth if no token
    auth = None
    if not session_token and args.username and args.password:
        auth = HTTPBasicAuth(args.username, args.password)

    payload = load_json(args.json_file) if args.json_file else None

    try:
        timeout = 10
        if args.method == 'get':
            resp = requests.get(args.url, auth=auth, headers=headers, verify=False, timeout=timeout)
        elif args.method == 'post':
            resp = requests.post(args.url, auth=auth, headers=headers, json=payload, verify=False, timeout=timeout)
        elif args.method == 'patch':
            resp = requests.patch(args.url, auth=auth, headers=headers, json=payload, verify=False, timeout=timeout)

        print(f"🔁 HTTP Status: {resp.status_code}")

        # Handle --all for recursive crawl
        if args.all:
            base_path = args.file_name
            print(f"🌐 Recursively fetching data from {args.url} into folder: {base_path}")
            os.makedirs(base_path, exist_ok=True)
            visited = set()
            recursive_fetch(args.url, auth, headers, base_path, visited)
            return

        # Handle response output
        try:
            data = resp.json()
            if args.method == 'get' and args.find_path:
                deep_find_path(args.url, auth, headers, args.find_path)
                return
            elif args.method == 'get' and args.find:
                matches = extract_fields_with_paths(data, args.find, show_path=False)
                if matches:
                    for i, match in enumerate(matches, 1):
                        print(f"[{i}] {match}")
                else:
                    print("⚠️  No matching fields found.")
            else:
                print(json.dumps(data, indent=4))
            handle_save_response(resp, args.save)
        except ValueError:
            print("⚠️  Response is not JSON:")
            print(resp.text)
            handle_save_response(resp, args.save)

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        sys.exit(1)