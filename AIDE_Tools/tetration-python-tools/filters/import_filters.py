import json
import csv
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description='import inventory filters from csv')
    parser.add_argument('-f', dest='file', help='csv file w/name, scope and query', required=True)
    args = parser.parse_args()
    return args


def main():
    rc = RestClient(json.loads(open('endpoint.json', 'r').read())['api_endpoint'], credentials_file='./credentials.json', verify=False)

    args = get_args()
    with open(args.file, encoding='ascii', errors='ignore') as file:
        rows = list(csv.reader(file, delimiter=','))

    rows = sorted(rows, key=lambda x: x[1])

    print('\ngetting scopes')
    resp = rc.get('/app_scopes/', timeout=30.0)
    app_scopes = json.loads(resp.content)
    scope_ids = []
    for app_scope in app_scopes:
        scope_ids.append([app_scope['id'], app_scope['name']])

    count = 0
    print('\nimporting filters')
    for row in rows:
        app_scope_id = ''
        for scope_id in scope_ids:
            if scope_id[1] == row[1]:
                app_scope_id = scope_id[0]

        filters = []
        if ' or ' in row[2]:
            filters = []
            for equation in row[2].split(' or '):
                if '!=' in equation:
                    filters.append({
                        'type': 'not',
                        'filter': {
                            'type': 'eq',
                            'field': equation.split('!=')[0].strip(),
                            'value': equation.split('!=')[1].strip()
                        }
                    })
                elif '=' in equation:
                    filters.append({
                        'type': 'eq',
                        'field': equation.split('=')[0].strip(),
                        'value': equation.split('=')[1].strip()
                    })
            query = {
                'type': 'or',
                'filters': filters
            }
        else:
            query = {
                'type': 'eq',
                'field': row[2].split('=')[0].strip(),
                'value': row[2].split('=')[1].strip()
            }
            #         req_payload = {
            #             'short_name': row[0],
            #             'short_query': {
            #                 'type': 'or',
            #                 'filters': filters
            #             },
            #             'parent_app_scope_id': parent_id
            #         }
            # for expression in row[2].split('[AND]'):
            #     filters.append({'type': 'eq', 'field': expression.split('=')[0], 'value': expression.split('=')[1]})

        req_payload = {
            'app_scope_id': app_scope_id,
            'name': row[0],
            'query': query,
            'primary': 'true',
            'public': 'true'
        }

        count += 1
        print(str(count) + '/' + str(len(rows)) + ' create ' + row[1] + ' > ' + row[0])
        resp = rc.post('/filters/inventories', json_body=json.dumps(req_payload))
        print('    ' + str(resp.status_code) + ' ' + resp.reason)
        if resp.status_code is not 200:
            print(resp.text)


if __name__ == '__main__':
    main()
