import json
import argparse
import pandas
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description='For selected applications, query convos with consumer/provider cluster/filter/scope. Output CSV per application.')
    parser.add_argument('-a', dest='applications', help='comma-separated adm workspaces OPTIONAL', required=False)
    parser.add_argument('-d', dest='dimensions', help='comma-separated dimensions OPTIONAL', required=False)
    parser.add_argument('-e', dest='external', help='external convos only (true/false) OPTIONAL', required=False)
    parser.add_argument('-x', dest='excluded', help='excluded convos only (true/false) OPTIONAL', required=False)
    parser.add_argument('-E', dest='endpoint', help='API endpoint (Tetration IP or hostname) OPTIONAL defualt: "api_endpoint" from ./endpoint.json')
    parser.add_argument('-C', dest='credentials', help='api_credentials.json (download at Settings > API Key > Creat API Key) OPTIONAL', required=False)
    parser.add_argument('-k', dest='keyword', help='filter convos by keyword in consumer_filter_name or provider_filter_name (e.g. "NONPROD") OPTIONAL', required=False)
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    # get endpoint
    if args.endpoint is not None:
        endpoint = 'https://' + args.endpoint + '/'
    else:
        endpoint = json.loads(open('../endpoint.json', 'r').read())['api_endpoint']

    # get credentials
    if args.credentials is not None:
        credentials = args.credentials
    else:
        credentials = '../credentials.json'

    rc = RestClient(endpoint, credentials_file='./' + credentials, verify=False)

    # get applications
    if args.applications is not None:
        app_names = [x.strip() for x in args.applications.split(',')]
    else:
        print('\napplications:')
        resp = rc.get('/applications/')
        if resp.status_code == 200:
            applications = json.loads(resp.content)
            for i in range(len(applications)):
                print(' ' + str(i) + '\t' + applications[i]['name'])

        else:
            raise Exception(resp.text)

    response = input('\nenter applications (comma-separated): ').split(',')

    choices = ''
    for x in response:
        if choices == '':
            if '-' in x:
                choices = ','.join([str(x) for x in list(range(int(x.split('-')[0]), int(x.split('-')[1]) + 1))])
            else:
                choices = x
        else:
            if '-' in x:
                choices += ',' + ','.join([str(x) for x in list(range(int(x.split('-')[0]), int(x.split('-')[1]) + 1))])
            else:
                choices += ',' + x

    app_names = [applications[int(x)]['name'] for x in choices.split(',')]

    # get dimensions
    dimensions = ['ip']
    if args.dimensions is not None:
        dimensions = list(set([x.strip() for x in args.dimensions.split(',')] + dimensions))

    else:
        print('\ndimensions:')
        resp = rc.get('/inventory/search/dimensions', timeout=90.0)

        if resp.status_code == 200:
            items = sorted(json.loads(resp.content))
        else:
            raise Exception(resp.text)

        for i in range(len(items)):
            print(' ' + str(i) + '\t' + items[i])

        print('\ndefault: ' + 'none')
        response = input('\nenter dimensions (comma-separated value, range or "all"): ').split(',')

        if response == ['']:
            dimensions = []
        elif response == ['all']:
            dimensions = dimensions + items
        else:
            choices = ''
            for x in response:
                if choices == '':
                    if '-' in x:
                        choices = ','.join([str(x) for x in list(range(int(x.split('-')[0]), int(x.split('-')[1]) + 1))])
                    else:
                        choices = x
                else:
                    if '-' in x:
                        choices += ',' + ','.join([str(x) for x in list(range(int(x.split('-')[0]), int(x.split('-')[1]) + 1))])
                    else:
                        choices += ',' + x

            dimensions = list(set(dimensions + [items[int(x)] for x in choices.split(',')]))

    for app_name in app_names:
        rows = []
        headers = []
        for application in applications:
            if application['name'] == app_name:
                # get convos
                offset = ''
                convos = []

                while offset is not None:
                    req_payload = {
                        'version': application['latest_adm_version'],
                        'offset': offset,
                        'dimensions': [],
                        'metrics': []
                    }
                    resp = rc.post('/conversations/' + application['id'], json_body=json.dumps(req_payload), timeout=90.0)
                    if resp.status_code == 200:
                        parsed_resp = json.loads(resp.content)
                    else:
                        print('  unable to query convos')
                        raise Exception(resp.text)
                    if 'offset' in parsed_resp:
                        offset = parsed_resp['offset']
                    else:
                        print('')
                        offset = None
                    convos += parsed_resp['results']

                if len(convos) > 0:

                    headers = list(convos[0].keys())
                    print(str(len(convos)) + ' convos')

                    root_scope = ''
                    # get application details
                    resp = rc.get('/applications/' + application['id'] + '/details', timeout=30.0)
                    if resp.status_code == 200:
                        application_details = json.loads(resp.content)
                        root_scope = application_details['app_scope']['name'].split(':')[0]

                    else:
                        raise Exception(resp.text)

                    internal_ids = []
                    internal_ids.append(application['app_scope_id'])

                    if 'inventory_filters' in application_details.keys():
                        inventory_filters = application_details['inventory_filters']
                        for inventory_filter in inventory_filters:
                            if inventory_filter['filter_type'] == 'UserInventoryFilter' and inventory_filter['parent_app_scope']['id'] == application['app_scope_id']:
                                internal_ids.append(inventory_filter['id'])

                    if 'clusters' in application_details.keys():
                        for cluster in application_details['clusters']:
                            internal_ids.append(cluster['id'])

                    ips = set()
                    for convo in convos:
                        ips.add(convo['src_ip'])
                        ips.add(convo['dst_ip'])

                        row = []
                        for key in convo.keys():
                            row.append(convo[key])

                        # get consumer filter name
                        consumer_filter_name = ''

                        if convo['consumer_filter_id'] in [x['id'] for x in inventory_filters]:
                            consumer_filter_name = inventory_filters[[x['id'] for x in inventory_filters].index(convo['consumer_filter_id'])]['name']
                        elif 'clusters' in application_details.keys():
                            clusters = application_details['clusters']
                            if convo['consumer_filter_id'] in [x['id'] for x in clusters]:
                                consumer_filter_name = clusters[[x['id'] for x in clusters].index(convo['consumer_filter_id'])]['name']

                        # get provider filter name
                        provider_filter_name = ''

                        if convo['provider_filter_id'] in [x['id'] for x in inventory_filters]:
                            provider_filter_name = inventory_filters[[x['id'] for x in inventory_filters].index(convo['provider_filter_id'])]['name']
                        elif 'clusters' in application_details.keys():
                            clusters = application_details['clusters']
                            if convo['provider_filter_id'] in [x['id'] for x in clusters]:
                                provider_filter_name = clusters[[x['id'] for x in clusters].index(convo['provider_filter_id'])]['name']

                        # check if in approved policy
                        approved = False
                        action = None
                        for policy in application_details['default_policies']:
                            if convo['consumer_filter_id'] == policy['consumer_filter_id'] and convo['provider_filter_id'] == policy['provider_filter_id']:
                                for param in policy['l4_params']:
                                    if param['approved'] is True:
                                        if param['proto'] == 1 and convo['protocol'] == 'ICMP':
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] == 6 and convo['protocol'] == 'TCP' and convo['port'] == str(param['port'][0]):
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] == 17 and convo['protocol'] == 'UDP' and convo['port'] == str(param['port'][0]):
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] is None:
                                            approved = True
                                            action = policy['action']
                        for policy in application_details['absolute_policies']:
                            if convo['consumer_filter_id'] == policy['consumer_filter_id'] and convo['provider_filter_id'] == policy['provider_filter_id']:
                                for param in policy['l4_params']:
                                    if param['approved'] is True:
                                        if param['proto'] == 1 and convo['protocol'] == 'ICMP':
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] == 6 and convo['protocol'] == 'TCP' and convo['port'] == str(param['port'][0]):
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] == 17 and convo['protocol'] == 'UDP' and convo['port'] == str(param['port'][0]):
                                            approved = True
                                            action = policy['action']
                                        elif param['proto'] is None:
                                            approved = True
                                            action = policy['action']

                        # check if external
                        external = True
                        if convo['consumer_filter_id'] in internal_ids and convo['provider_filter_id'] in internal_ids:
                            external = False

                        append = True

                        # filter by keyword
                        if args.keyword is not None:
                            if args.keyword not in consumer_filter_name and args.keyword not in provider_filter_name:
                                append = False

                        # filter by external
                        if args.external is not None:
                            if bool(args.external) != external:
                                append = False

                        # filter by excluded
                        if args.excluded is not None:
                            if bool(args.excluded) != bool(convo['excluded']):
                                append = False

                        if append:
                            row.append(consumer_filter_name)
                            row.append(provider_filter_name)
                            row.append(approved)
                            row.append(external)
                            row.append(action)
                            rows.append(row)

        headers.append('Consumer Filter')
        headers.append('Provider Filter')
        headers.append('Approved')
        headers.append('External')
        headers.append('Action')

        rows_df = pandas.DataFrame(rows)
        rows_df.columns = headers
        rows_df.rename(columns={'src_ip': 'Consumer Address', 'dst_ip': 'Provider Address', 'protocol': 'Protocol', 'port': 'Port', 'packet_count': 'Packet Count', 'byte_count': 'Byte Count', 'excluded': 'Excluded', 'confidence': 'Confidence'}, inplace=True)
        rows_df = rows_df[['Action', 'Consumer Filter', 'Consumer Address', 'Provider Filter', 'Provider Address', 'Protocol', 'Port', 'Approved', 'Packet Count', 'Byte Count', 'External', 'Excluded', 'Confidence', 'address_type', 'consumer_filter_id', 'consumer_filter_ids', 'count', 'exclusion_filter_type', 'exclusion_filter_uuid', 'provider_filter_id', 'provider_filter_ids']]

        if len(dimensions) > 0:
            inventory = []
            offset = ''

            while offset is not None:
                req_payload = {
                    'filter': {
                        "type": "in",
                        "field": "ip",
                        "values": list(ips)
                    },
                    'offset': offset,
                    'limit': 0,
                    'dimensions': dimensions,
                    'scopeName': root_scope
                }
                resp = rc.post('/inventory/search', json_body=json.dumps(req_payload), timeout=90.0)
                if resp.status_code == 200:
                    parsed_resp = json.loads(resp.content)
                else:
                    print('  unable to query inventory')
                    raise Exception(resp.text)
                if 'offset' in parsed_resp:
                    offset = parsed_resp['offset']
                else:
                    print('')
                    offset = None
                inventory += parsed_resp['results']

            inventory_df = pandas.DataFrame(inventory)
            inventory_df.rename(columns={'ip': 'Address'}, inplace=True)
            inventory_df = inventory_df.add_prefix('Consumer ')
            rows_df = pandas.merge(rows_df, inventory_df, on='Consumer Address', how='left')
            inventory_df.columns = inventory_df.columns.str.replace('Consumer ', 'Provider ')
            rows_df = pandas.merge(rows_df, inventory_df, on='Provider Address', how='left')

        rows_df.to_csv(app_name.replace(' ', '_').replace(':', '_') + '.csv', index=False)
        print(' ' + app_name.replace(' ', '_').replace(':', '_') + '.csv created')

    print('\nDone!\n')


if __name__ == '__main__':
    main()
