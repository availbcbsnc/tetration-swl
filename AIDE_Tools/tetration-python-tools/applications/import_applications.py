import json
import csv
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description="import application workspaces from csv")
    parser.add_argument('-f', dest='file', help='csv file w/name and scope', required=True)
    args = parser.parse_args()
    return args


def main():
    rc = RestClient(json.loads(open('../endpoint.json', 'r').read())["api_endpoint"], credentials_file='../credentials.json', verify=False)

    args = get_args()
    with open(args.file) as file:
        rows = csv.reader(file, delimiter=',')
        #rows = sorted(rows, key=lambda x: x[1])
        for row in rows:
            resp = rc.get('/app_scopes/')
            app_scopes = json.loads(resp.content)
            scope_id = ''
            for app_scope in app_scopes:
                if app_scope['name'] == row[1]:
                    scope_id = app_scope['id']
                    break

            req_payload = {
                "app_scope_id": scope_id,
                "name": row[0],
            }

            print("create application: " + row[1] + " > " + row[0])
            resp = rc.post('/openapi/v1/applications', json_body=json.dumps(req_payload))
            print(str(resp.status_code) + " " + resp.reason)
            if resp.status_code is not 200:
                print(resp.text)


if __name__ == '__main__':
    main()
