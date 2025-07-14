import json
import csv
import argparse
from ipwhois import IPWhois
import pandas
import ipaddress


def get_args():
    parser = argparse.ArgumentParser(description='summarize list of IPs into CIDR blocks')
    parser.add_argument('-f', dest='file', help='file with IPs to summarize', required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()
    with open(args.file, encoding='ascii', errors='ignore') as file:
        ips = [x[0] for x in list(csv.reader(file, delimiter=','))]

    #ips = ['10.0.0.0', '10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.5']

    count = 0

    nets = [ipaddress.ip_network(ip) for ip in ips]
    cidrs = []
    network_adresses = []

    [cidrs.append([x.with_prefixlen]) for x in list(ipaddress.collapse_addresses(nets))]
    [network_adresses.append([x.with_prefixlen.split('/')[0]]) for x in list(ipaddress.collapse_addresses(nets))]

    print(cidrs)
    #Out[6]: [IPv4Network('10.0.0.0/30'), IPv4Network('10.0.0.5/32')]

    file = args.file.split('.')[0]
    writer = csv.writer(open(file + '_cidrs.csv', 'w', newline=''))
    writer.writerows(cidrs)
    writer = csv.writer(open(file + '_network_addresses.csv', 'w', newline=''))
    writer.writerows(network_adresses)


if __name__ == '__main__':
    main()
