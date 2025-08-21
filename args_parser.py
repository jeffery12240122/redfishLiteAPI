import argparse
def parse_args():
    parser = argparse.ArgumentParser(description='Redfish Lite API Tool')
    exclusive = parser.add_mutually_exclusive_group()
    exclusive.add_argument('--version', action='store_true', help='Show tool version and exit')
    parser.add_argument('--url', help='Target Redfish API endpoint')
    parser.add_argument('--method', choices=['get', 'post', 'patch'], help='HTTP method')
    parser.add_argument('-U', '--username', help='Username for authentication')
    parser.add_argument('-P', '--password', help='Password for authentication')
    parser.add_argument('--json_file', help='Path to JSON file for request body (only for POST or PATCH)')
    parser.add_argument('--find', nargs='+', help='Find and display value(s) of specific field(s) in JSON response (only for GET)')
    parser.add_argument('--find_path', nargs='+', help='Show path of each matched field recursively (GET only)')
    parser.add_argument('--save', help='Save response output to specified file')
    parser.add_argument('--header', action='append', help='Custom header(s), format: Key:Value')
    parser.add_argument('--all', action='store_true', help='Recursively follow @odata.id and save all data into folders')
    parser.add_argument('--file_name', default='redfish_dump', help='Folder name to save files when using --all')
    parser.add_argument('--session_token', help='Use existing Redfish session token')
    parser.add_argument('--login_session', action='store_true', help='Automatically login to get Redfish session token')
    args = parser.parse_args()
    if not args.version and (not args.url or not args.method):
        parser.error("the following arguments are required: --url, --method")
    return args
