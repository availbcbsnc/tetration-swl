import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import datetime


def get_args():
    parser = argparse.ArgumentParser(description="Delete filters under specified root scope")
    parser.add_argument('-s', dest='scope', help='parent scope of inventory fileters REQUIRED', required=True)
    parser.add_argument('-f', dest='file', help='delete filters in file only OPTIONAL default delete all for scope', required=False)
    parser.add_argument('-r', dest='recursive', help='(true/false) recursively delete dependendts OPTIONAL default false', required=False)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    rc = RestClient(json.loads(open('endpoint.json', 'r').read())["api_endpoint"], credentials_file='./credentials.json', verify=False)

    resp = rc.get('/filters/inventories/')
    inventory_filters = json.loads(resp.content)

    # get filters to delete
    delete_filters = []

    print('\ngetting scopes')
    resp = rc.get('/app_scopes/', timeout=30.0)
    scopes = json.loads(resp.content)
    app_scope_id = ''
    for scope in scopes:
        if scope['name'] == args.scope:
            app_scope_id = scope['id']

    if args.file is None:
        for inventory_filter in inventory_filters:
            if inventory_filter['app_scope_id'] == app_scope_id:
                delete_filters.append(inventory_filter['id'])
    else:
        with open(args.file, encoding='ascii', errors='ignore') as file:
            rows = list(file)
        for row in rows:
            for inventory_filter in inventory_filters:
                if inventory_filter['name'] == row.strip() and inventory_filter['app_scope_id'] == app_scope_id:
                    delete_filters.append([inventory_filter['id'], inventory_filter['name']])

    print('\ndeleting filters')
    count = 0
    for delete_filter in delete_filters:
        count += 1
        print(str(count) + '/' + str(len(delete_filters)) + ' delete ' + args.scope + ' > ' + delete_filter[1])
        resp = rc.delete('/filters/inventories/' + delete_filter[0])
        if resp.status_code == 200:
            print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)
        # elif resp.status_code == 422 and args.recursive == 'true':
        #     delete_dependents(rc, resp, delete_filter
        else:
            print('    ' + str(resp.status_code) + ' ' + resp.text)


if __name__ == '__main__':
    main()
