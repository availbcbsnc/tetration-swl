import json
import csv
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import datetime
#from treelib import Node, Tree


def get_args():
    parser = argparse.ArgumentParser(description='Import scopes from specified csv file. Add root scope in UI first.')
    parser.add_argument('-f', dest='file', help='csv file w/short name, parent name and query', required=True)
    parser.add_argument('-r', dest='root', help='root scope', required=True)
    args = parser.parse_args()
    return args


def main():
    rc = RestClient(json.loads(open('../endpoint.json', 'r').read())['api_endpoint'], credentials_file='../credentials.json', verify=False)

    args = get_args()

    print('getting scopes')
    resp = rc.get('/app_scopes/', timeout=30)
    app_scopes = json.loads(resp.content)
    app_scopes = sorted(app_scopes, key=lambda x: x['created_at'])
    #tree = Tree()
    scope_ids = []
    add = []

    print("=============================== CURRENT ===============================")
    for app_scope in app_scopes:
        name = app_scope['name']
        if name.split(':')[0] == args.root:
            scope_ids.append([name, app_scope['id']])
            print(name)
    #         L = name.split(':')
    #         if len(L) == 1:
    #             tree.create_node(name, name)
    #         else:
    #             short = L.pop()
    #             parent = ":".join(L)
    #             tree.create_node(short, name, parent)
    # print()
    # tree.show()

    with open(args.file, encoding='ascii', errors='ignore') as file:
        rows = list(csv.reader(file, delimiter=','))

    rows = sorted(rows, key=lambda x: len(x[1].split(':')))

    print("================================= NEW =================================")
    for row in rows:
        name = row[1] + ':' + row[0]
        if name.split(':')[0] == args.root:
            scope_ids.append([name, app_scope['id']])
            print(name)
    #         L = name.split(':')
    #         if len(L) == 1:
    #             tree.create_node(name, name)
    #         else:
    #             short = L.pop()
    #             parent = ":".join(L)
    #             tree.create_node(short, name, parent)
    # print()
    # tree.show()

    response = input('\nimport ' + str(len(rows)) + ' scopes (yes/no)? ')
    count = 0
    if response == 'yes':
        for row in rows:
            parent_id = ''
            for scope_id in scope_ids:
                if row[1] == scope_id[0]:
                    parent_id = scope_id[1]
                    break

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
                req_payload = {
                    'short_name': row[0],
                    'short_query': {
                        'type': 'or',
                        'filters': filters
                    },
                    'parent_app_scope_id': parent_id
                }
            elif ' and ' in row[2]:
                filters = []
                for equation in row[2].split(' and '):
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
                    req_payload = {
                        'short_name': row[0],
                        'short_query': {
                            'type': 'and',
                            'filters': filters
                        },
                        'parent_app_scope_id': parent_id
                    }

            else:
                if '!=' in row[2]:
                    req_payload = {
                        'short_name': row[0],
                        'short_query': {
                            'type': 'not',
                            'filter': {
                                'type': 'eq',
                                'field': row[2].split('!=')[0].strip(),
                                'value': row[2].split('!=')[1].strip()
                            }
                        },
                        'parent_app_scope_id': parent_id
                    }

                elif '=' in row[2]:
                    req_payload = {
                        'short_name': row[0],
                        'short_query': {
                            'type': 'eq',
                            'field': row[2].split('=')[0].strip(),
                            'value': row[2].split('=')[1].strip()
                        },
                        'parent_app_scope_id': parent_id
                    }

            count += 1
            print(str(count) + '/' + str(len(rows)) + ' create ' + row[1] + ':' + row[0])
            resp = rc.post('/app_scopes', json_body=json.dumps(req_payload))
            print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)

            if resp.status_code == 200:
                scope_ids.append([json.loads(resp.content)['name'], json.loads(resp.content)['id']])
                scope_ids.sort(reverse=True)
            else:
                print('    ' + str(resp.status_code) + ' ' + resp.text)

        root_scope_id = ''

        for scope_id in scope_ids:
            if scope_id[0] == args.root:
                root_scope_id = scope_id[1]

        req_payload = {
            "root_app_scope_id": root_scope_id,
            "sync": True
        }

        print("commit scope changes")
        resp = rc.post('/app_scopes/commit_dirty', json_body=json.dumps(req_payload), timeout=30.0)
        if resp.status_code == 200:
            print('    ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " " + str(resp.status_code) + " " + resp.reason)
        else:
            print(resp.text)
    else:
        print('\nskipped!\n')


if __name__ == '__main__':
    main()
