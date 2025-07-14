import json
import csv
import argparse
from ipwhois import IPWhois
import pandas
import ipaddress
from datetime import datetime


def get_args():
    parser = argparse.ArgumentParser(description='query rdap for IP address info')
    parser.add_argument('-f', dest='file', help='file with IPs to query', required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    with open(args.file, encoding='ascii', errors='ignore') as file:
        ips = list(set(filter(None, file.read().split('\n'))))

    print(ips)
    start = datetime.now()

    asns = []
    cidrs = []
    filters = []
    failures = []
    filter_names = set()
    unique = set()
    count = 0
    lookup_count = 0
    for ip in ips:
        count += 1
        lookup = True

        if ipaddress.ip_network(ip).is_global:
            for cidr in unique:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(cidr):
                    lookup = False

            if lookup and ipaddress.ip_address(ip) in ipaddress.ip_network('192.0.0.0/24'):
                print(' 192.0.0.0/24 Internet Assigned Numbers Authority (IANA)')
                unique.add('192.0.0.0/24')
                cidrs.append(['192.0.0.0/24', 'Internet Assigned Numbers Authority (IANA)'])
                filter_names.add('Internet Assigned Numbers Authority (IANA)')
                lookup = False

            if lookup:
                lookup_count += 1
                print(str(count) + '/' + str(len(ips)) + ' ' + str(lookup_count) + ' ' + ip)

                try:
                    obj = IPWhois(ip)
                    asn = obj.lookup_rdap()
                    asns.append(asn)

                    for cidr in [x.strip() for x in asn['network']['cidr'].split(',')]:

                        if cidr not in unique and cidr != '0.0.0.0/0':

                            name = ''
                            for entity in asn['entities']:
                                if asn['objects'][entity]['contact']['kind'] == 'org':
                                    name = asn['objects'][entity]['contact']['name'].replace(',', '')
                                    break
                                elif asn['objects'][entity]['contact']['kind'] == 'individual':
                                    if asn['objects'][entity]['contact']['email'] is not None:
                                        name = asn['objects'][entity]['contact']['email'][0]['value'].split('@')[1]
                                        break
                                elif asn['objects'][entity]['contact']['kind'] == 'group':
                                    if asn['objects'][entity]['contact']['email'] is not None:
                                        name = asn['objects'][entity]['contact']['email'][0]['value'].split('@')[1]
                                        break
                            if name != '':
                                print(' ' + cidr + ' ' + name)
                                unique.add(cidr)
                                cidrs.append([cidr, name])
                                filter_names.add(name)
                            else:
                                print(' org name lookup failed for cidr ' + cidr)

                except Exception as e:
                    print(' rdap lookup failed for ------->' + ip)
                    print(e)
                    failures.append([ip, str(e)])

    for filter_name in filter_names:
        filters.append([filter_name, 'Default', 'user_rdap_org=' + filter_name])

    file = args.file.split('.')[0]

    pandas.read_json(json.dumps(asns)).to_csv(file + '_asn.csv')

    cidrs.insert(0, ['IP', 'rdap_org'])
    writer = csv.writer(open(file + '_annotations.csv', 'w', newline=''))
    writer.writerows(cidrs)

    writer = csv.writer(open(file + '_filters.csv', 'w', newline=''))
    writer.writerows(filters)

    writer = csv.writer(open(file + '_failures.csv', 'w', newline=''))
    writer.writerows(failures)

    print(datetime.now() - start)


if __name__ == '__main__':
    main()
