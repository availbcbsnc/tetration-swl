import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description="update inventory filters for scope to make public")
    parser.add_argument('-s', dest='scope', help='name of scope filter is tied to', required=True)
    args = parser.parse_args()
    return args


def main():
    rc = RestClient(json.loads(open('endpoint.json', 'r').read())["api_endpoint"], credentials_file='./credentials.json', verify=False)
    args = get_args()

    resp = rc.get('/app_scopes/')
    app_scopes = json.loads(resp.content)

    for app_scope in app_scopes:
        if app_scope['name'] == args.scope:
            scope_id = app_scope['id']
            break

    resp = rc.get('/filters/inventories/')
    filters = json.loads(resp.content)

    for ifilter in filters:
        if ifilter['app_scope_id'] == scope_id:
            req_payload = {
                "public": "true"
            }

            print("update " + ifilter['name'])
            resp = rc.put('/filters/inventories/' + ifilter['id'], json_body=json.dumps(req_payload))
            print(str(resp.status_code) + " " + resp.reason)
            if resp.status_code is not 200:
                print(resp.text)


if __name__ == '__main__':
    main()
