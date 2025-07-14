import csv
import json
import argparse
from tetpyclient import RestClient
import tetpyclient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description='Duplicate tags to all sensor interfaces if interface ip is unique and tags do not exist. Link-local, loopback and duplicates ignored.\n')
    parser.add_argument('-s', dest='scope', help='root scope name REQUIRED', required=True)
    parser.add_argument('-v', dest='version', help='(ipv4/ipv6) OPTIONAL default ipv4', required=False)
    parser.add_argument('-f', dest='file', help='sensors.json file OPTIONAL', required=False)

    args = parser.parse_args()
    return args


def offset(rc, resp):
    results = json.loads(resp.content)['results']
    resp = rc.get('/sensors', params={'limit': 1000, 'offset': json.loads(resp.content)['offset']}, timeout=30.0)

    if 'offset' in json.loads(resp.content).keys():
        return results + offset(rc, resp)
    else:
        return results + json.loads(resp.content)['results']


def main():
    rc = RestClient(json.loads(open('../endpoint.json', 'r').read())["api_endpoint"], credentials_file='../credentials.json', verify=False)
    args = get_args()

    # get version
    if args.version is None:
        version = 'ipv4'
    elif args.version in ['ipv4', 'ipv6']:
        version = args.version
    else:
        print('invalid version (ipv4/ipv6)')
        quit()

    # get app scopes
    print('\ngetting scopes')
    resp = rc.get('/app_scopes/', timeout=30.0)
    app_scopes = json.loads(resp.content)

    print('\ngetting vrf')
    vrf_id = None
    for app_scope in app_scopes:
        if app_scope['name'].split(':')[0] == args.scope:
            vrf_id = app_scope['vrf_id']
            break
    if vrf_id is None:
        print('invalid scope name')
        quit()

    # get sensors
    print('\ngetting sensors')
    if args.file is not None:
        sensors = json.loads(open(args.file, 'r').read())
    else:
        resp = rc.get('/sensors', timeout=30.0)

        if 'offset' in json.loads(resp.content).keys():
            sensors = offset(rc, resp)
        else:
            sensors = json.loads(resp.content)['results']

    print('found ' + str(len(sensors)) + ' sensors')

    sensor_ips = []

    for sensor in sensors:
        for interface in sensor['interfaces']:
            if interface['vrf_id'] == vrf_id:
                if version == 'ipv4':
                    if ':' not in interface['ip']:
                        sensor_ips.append(interface['ip'])
                else:
                    sensor_ips.append(interface['ip'])

    groups = []
    for sensor in sensors:
        ips = []
        for interface in sensor['interfaces']:
            if sensor_ips.count(interface['ip']) == 1 and interface['ip'] not in ips and '169.254.' != interface['ip'][0:8]:
                ips.append(interface['ip'])
        if len(ips) > 1:
            groups.append(ips)

    # get annotations
    print('\ngetting annotations, saving as undo.csv')
    filename = 'undo.csv'
    rc.download(filename, '/assets/cmdb/download/' + args.scope)
    with open(filename, encoding='ascii', errors='ignore') as file:
        annotations = list(csv.reader(file, delimiter=','))

    if len(annotations) > 0:

        headers = annotations.pop(0)

        # duplicate tags
        print('\nduplicating tags')
        copies = []
        annotation_ips = []

        for annotation in annotations:
            if '/' not in annotation[0]:
                annotation_ips.append(annotation[0])

        for group in groups:
            template = None
            for annotation in annotations:
                if '/' not in annotation[0] and annotation[0] in group:
                    template = annotation
                    break
            if template is not None:
                for ip in group:
                    if ip not in annotation_ips:
                        copy = template.copy()
                        copy[0] = ip
                        copies.append(copy)

        if len(copies) > 0:
            copies.insert(0, headers)

            for copy in copies:
                print(','.join(copy))

            with open('output.csv', 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(copies)
                print("\noutput.csv created")
                print(str(len(copies) - 1) + " updates")

            response = input("\nupload annotations (yes/no)? ")

            if response == 'yes':
                body = [tetpyclient.MultiPartOption(key='X-Tetration-Oper', val='add')]
                resp = rc.upload("output.csv", '/assets/cmdb/upload/' + args.scope, body)
                if resp.status_code == 200:
                    print('\ndone\n')
                else:
                    print(str(resp.status_code) + " " + resp.reason + " " + resp.text)
            else:
                print('\nskipped!\n')
        else:
            print('\nnothing to update\n')
    else:
        print('\nno annotations\n')


if __name__ == '__main__':
    main()
