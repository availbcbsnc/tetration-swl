import json
import csv
import argparse
from tetpyclient import RestClient
import urllib3
from datetime import datetime, timedelta
import ipaddress
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description='For selected scopes, query convos for number of hours with specified dimensions. Output CSV per scope.')
    parser.add_argument('-s', dest='scopes', help='comma-separated scope names OPTIONAL', required=False)
    parser.add_argument('-D', dest='days', help='number of days back to query OPTIONAL', required=False)
    # parser.add_argument('-H', dest='hours', help='number of hours back to query OPTIONAL', required=False)
    # parser.add_argument('-m', dest='minutes', help='number of minutes back to query OPTIONAL', required=False)
    parser.add_argument('-d', dest='dimensions', help='comma-separated fields to retain OPTIONAL default src_address,dst_address,proto,dst_port)', required=False)
    parser.add_argument('-E', dest='endpoint', help='API endpoint (Tetration IP or hostname) OPTIONAL defualt: "api_endpoint" from ./endpoint.json')
    parser.add_argument('-C', dest='credentials', help='api_credentials.json (download at Settings > API Key > Creat API Key) OPTIONAL', required=False)
    parser.add_argument('-O', dest='or_filters', help='file containing or filters (first row field name)', required=False)

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    # get or filters
    if args.or_filters is not None:
        with open(args.or_filters, encoding='ascii', errors='ignore') as or_filters:
            rows = list(csv.reader(or_filters, delimiter=','))

        field = rows.pop(0)[0]

        filters = []
        for row in rows:
            filters.append({"type": "eq", "field": field, "value": row[0].strip()})

        filter = {"type": "or", "filters": filters}
    else:
        filter = {}

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

    # get scopes
    if args.scopes is not None:
        scopes = [x.strip() for x in args.scopes.split(',')]
    else:
        print('\nscopes:')
        resp = rc.get('/app_scopes/')
        if resp.status_code == 200:
            parsed_resp = json.loads(resp.content)
            for i in range(len(parsed_resp)):
                print(' ' + str(i) + '\t' + parsed_resp[i]['name'])
        else:
            raise Exception(resp.text)

        response = input('\nenter scopes (comma-separated value or range): ').split(',')

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

        scopes = [parsed_resp[int(x)]['name'] for x in choices.split(',')]

    # # get hours
    # if args.hours is not None:
    #     hours = int(args.hours)
    # else:
    #     hours = int(input('\nenter number of hours: '))

    # # get minutes
    # if args.minutes is not None:
    #     minutes = int(args.minutes)
    # else:
    #     minutes = int(input('\nenter number of minutes: '))
    # if hours is not None:
    #     minutes += hours * 60

    # get days
    if args.days is not None:
        days = int(args.days)
    else:
        days = int(input('\nenter number of days: '))

    # get metrics
    metrics = ['fwd_bytes', 'fwd_pkts', 'rev_bytes', 'rev_pkts']

    # get dimensions
    dimensions = ['src_address', 'dst_address', 'proto', 'dst_port']

    if args.dimensions is not None:
        dimensions = list(set([x.strip() for x in args.dimensions.split(',')] + dimensions))

    else:
        print('\ndimensions:')
        resp = rc.get('/flowsearch/dimensions', timeout=90.0)

        if resp.status_code == 200:
            parsed_resp = sorted(json.loads(resp.content))
        else:
            raise Exception(resp.text)

        for i in range(len(parsed_resp)):
            print(' ' + str(i) + '\t' + parsed_resp[i])

        print('\ndefault: ' + ','.join(dimensions))
        response = input('\nenter dimensions (comma-separated value or range): ').split(',')

        if response != ['']:
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

            dimensions = list(set(dimensions + [parsed_resp[int(x)] for x in choices.split(',')]))

    print('\nscopes: ' + ','.join(scopes))
    #  print('hours: ' + str(hours))
    print('days: ' + str(days))
    print('dimensions: ' + ','.join(dimensions))

    for scope in scopes:
        print('\n' + scope)

        headers = sorted(dimensions)
        rows = []
        results = []
        grand_total = 0
        now = datetime.now()

        for day in range(days):
            count = 0
            total = 0

            # get time
            t0 = (now - timedelta(days=day + 1)).strftime('%Y-%m-%dT%H:%M:%S-00:00')
            t1 = (now - timedelta(days=day)).strftime('%Y-%m-%dT%H:%M:%S-00:00')

            print(' -' + str(day + 1) + ' days, from ' + t0 + ' to ' + t1)

        # count = 0
        # total = 0

        # # get time
        # t1 = now.strftime('%Y-%m-%dT%H:%M:%S-00:00')
        # t0 = (now - timedelta(minutes=minutes)).strftime('%Y-%m-%dT%H:%M:%S-00:00')

        # print(' -' + str(minutes) + ' minutes, from ' + t0 + ' to ' + t1)

            offset = ''

            # get count
            req_payload = {
                'scopeName': scope,
                'filter': filter,
                't0': t0,
                't1': t1,
            }

            resp = rc.post('/flowsearch/count', json_body=json.dumps(req_payload), timeout=90.0)
            if resp.status_code == 200:
                count = json.loads(resp.content)['count']
                grand_total += count
            else:
                print('  unable to get count')
                raise Exception(resp.text)

            if count > 0:

                while offset is not None:
                    req_payload = {
                        'filter': filter,
                        'metrics': metrics,
                        'dimensions': dimensions,
                        'offset': offset,
                        'scopeName': scope,

                        't0': t0,
                        't1': t1,
                    }
                    resp = rc.post('/flowsearch', json_body=json.dumps(req_payload), timeout=90.0)
                    if resp.status_code == 200:
                        parsed_resp = json.loads(resp.content)
                        total += len(parsed_resp['results'])
                        print('  getting flows... %d%%' % (total / count * 100) + ' %d' % total + '/' + str(count), end='\r')
                    else:
                        print('  unable to query flows')
                        raise Exception(resp.text)
                    if 'offset' in parsed_resp:
                        offset = parsed_resp['offset']
                    else:
                        print('')
                        offset = None
                    results += parsed_resp['results']
            else:
                print('  no flows\n')

        total = 0
        # for hour in range(hours):
        #     count = 0
        #     total = 0

        #     # get time
        #     t0 = (now - timedelta(hours=hour + 1)).strftime('%Y-%m-%dT%H:%M:%S-00:00')
        #     t1 = (now - timedelta(hours=hour)).strftime('%Y-%m-%dT%H:%M:%S-00:00')

        #     print(' -' + str(hour + 1) + ' hours, from ' + t0 + ' to ' + t1)

        #     offset = ''

        #     # get count
        #     req_payload = {
        #         'scopeName': scope,
        #         'filter': {},
        #         't0': t0,
        #         't1': t1,
        #     }
        #     resp = rc.post('/flowsearch/count', json_body=json.dumps(req_payload), timeout=90.0)
        #     if resp.status_code == 200:
        #         count = json.loads(resp.content)['count']
        #         grand_total += count
        #     else:
        #         print('  unable to get count')
        #         raise Exception(resp.text)

        #     while offset is not None:
        #         req_payload = {
        #             'filter': {},
        #             'metrics': metrics,
        #             'dimensions': dimensions,
        #             'offset': offset,
        #             'scopeName': scope,

        #             't0': t0,
        #             't1': t1,
        #         }
        #         resp = rc.post('/flowsearch', json_body=json.dumps(req_payload), timeout=90.0)
        #         if resp.status_code == 200:
        #             parsed_resp = json.loads(resp.content)
        #             total += len(parsed_resp['results'])
        #             print('  getting flows... %d%%' % (total / count * 100) + ' %d' % total + '/' + str(count), end='\r')
        #         else:
        #             print('  unable to query flows')
        #             raise Exception(resp.text)
        #         if 'offset' in parsed_resp:
        #             offset = parsed_resp['offset']
        #         else:
        #             print('')
        #             offset = None
        #         results += parsed_resp['results']

        #     total = 0

        for result in results:
            total += 1
            print(' processing %d%%' % (total / grand_total * 100) + ' %d' % total + '/' + str(grand_total), end='\r')
            row = []
            for header in headers:
                row.append(result[header])

            multicast = False

            if ':' in result['dst_address']:
                multicast = ipaddress.IPv6Address(result['dst_address']).is_multicast
            else:
                multicast = ipaddress.IPv4Address(result['dst_address']).is_multicast

            if not multicast and (result['rev_bytes'] > 0 or result['proto'] == 'UDP'):
                if row not in [x[0:len(x) - 3] for x in rows]:
                    row.append(1)
                    row.append(result['fwd_pkts'] + result['rev_pkts'])
                    row.append(result['fwd_bytes'] + result['rev_bytes'])
                    rows.append(row)
                else:
                    rows[[x[0:len(x) - 3] for x in rows].index(row)][len(row)] += 1
                    rows[[x[0:len(x) - 3] for x in rows].index(row)][len(row) + 1] += (result['fwd_pkts'] + result['rev_pkts'])
                    rows[[x[0:len(x) - 3] for x in rows].index(row)][len(row) + 2] += (result['fwd_bytes'] + result['rev_bytes'])

        print('')
        print(' ' + str(grand_total) + ' total flows')

        headers.append('flow_count')
        headers.append('packet_count')
        headers.append('byte_count')
        rows.insert(0, headers)

        writer = csv.writer(open(scope.replace(':', '_') + '_convos.csv', 'w', newline=''))
        writer.writerows(rows)

        print(' ' + str(len(rows) - 1) + ' convos, created ' + scope.replace(':', '_') + '_convos.csv')

    #print('\nDone!\n\nPATH$ python miniadm.py -s "' + ','.join(scopes) + '" -H ' + str(hours) + ' -d "' + ','.join(dimensions) + '" -C ' + credentials + ' -E ' + endpoint.split('/')[2] + '\n\n')

    path = '\nDone!\n\nPATH$ python miniadm.py -s "' + ','.join(scopes) + '" -D ' + str(days) + ' -d "' + ','.join(dimensions) + '" -C ' + credentials + ' -E ' + endpoint.split('/')[2]

    if args.or_filters is not None:
        path += ' -O ' + args.or_filters + '\n\n'
    else:
        path += '\n\n'

    print(path)


if __name__ == '__main__':
    main()
