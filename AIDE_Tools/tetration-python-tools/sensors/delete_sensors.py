from datetime import datetime, timedelta
import json
import csv
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from prettytable import PrettyTable


def get_args():
    parser = argparse.ArgumentParser(description='delete sensors in seed file')
    parser.add_argument('-f', dest='file', help='list of sensor ips REQUIRED', required=True)
    parser.add_argument('-i', dest='inactive', help='(true/false) only delete if no check-in in 24 hours OPTIONAL default false', required=False)

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
    args = get_args()

    rc = RestClient(json.loads(open('../endpoint.json', 'r').read())["api_endpoint"], credentials_file='../credentials.json', verify=False)

    with open(args.file, encoding='ascii', errors='ignore') as file:
        delete_ips = list(file.read().split('\n'))

    # get sensors
    print('\ngetting sensors')
    resp = rc.get('/sensors', timeout=30.0)

    if 'offset' in json.loads(resp.content).keys():
        sensors = offset(rc, resp)
    else:
        sensors = json.loads(resp.content)['results']

    table = PrettyTable()

    table.field_names = ['IP', 'UUID', 'HOST', 'PLATFORM', 'TYPE', 'VERSION', 'LAST CHECK-IN']

    delete_ids = []

    for sensor in sensors:
        for interface in sensor['interfaces']:
            if interface['ip'] in delete_ips:
                if 'deleted_at' not in sensor.keys():
                    if args.inactive is None or args.inactive.lower() == 'false':
                        delete_ids.append(interface['ip'] + ' ' + sensor['uuid'])
                        table.add_row([interface['ip'], sensor['uuid'], sensor['host_name'], sensor['platform'], sensor['agent_type'], sensor['current_sw_version'], str(datetime.fromtimestamp(sensor['last_config_fetch_at']))])
                    elif args.inactive.lower() == 'true':
                        if datetime.fromtimestamp(sensor['last_config_fetch_at']) < (datetime.now() - timedelta(days=1)):
                            delete_ids.append(interface['ip'] + ' ' + sensor['uuid'])
                            table.add_row([interface['ip'], sensor['uuid'], sensor['host_name'], sensor['platform'], sensor['agent_type'], sensor['current_sw_version'], str(datetime.fromtimestamp(sensor['last_config_fetch_at']))])

    if len(delete_ids) > 0:
        print(table.get_string(sortby='LAST CHECK-IN'))

        # prompt to delete first
        response = input("\ndelete " + str(len(delete_ids)) + " sensors (yes/no)? ")

        count = 0
        if response == 'yes':
            for delete_id in delete_ids:
                count += 1
                print(str(count) + '/' + str(len(delete_ids)) + ' delete ' + delete_id)
                resp = rc.delete('/sensors/' + delete_id.split(' ')[1])
                print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)
        else:
            print('\nskipped!\n')

    else:
        print('\nnothing to delete\n')

    # count=0
    # active_count=0
    # report=[['client_ip', 'host_name', 'platform', 'health', 'agent_type_name', 'current_sw_version', 'last_registration_req_at', 'uuid', 'has_active']]

    # # gather acitve ips
    # for sensor in sensors:
    #     if sensor['health'] == 'active':
    #         active.append(sensor['client_ip'])
    #         for interface in sensor['interfaces']:
    #             if interface['name'] != 'lo' and interface['family_type'] == 'IPV4':
    #                 active.append('ip')

    # # gather inactive, check if has_active
    # for sensor in sensors:
    #     if sensor['health'] == 'inactive':
    #         has_active=False
    #         if sensor['client_ip'] in active:
    #             has_active=True
    #         for interface in sensor['interfaces']:
    #             if interface['name'] != 'lo' and interface['family_type'] == 'IPV4' and interface['ip'] in active:
    #                 has_active=True

    #         if has_active:
    #             active_count += 1

    #         report.append([sensor['client_ip'], sensor['host_name'], sensor['platform'], sensor['health'], sensor['agent_type_name'], sensor['current_sw_version'], datetime.datetime.fromtimestamp(sensor['last_registration_req_at']), sensor['uuid'], has_active])

    # writer=csv.writer(open(args.file.split('.')[0] + '_delete_inactive.csv', 'w', newline=''))
    # writer.writerows(report)

    # print('\ncreated ' + args.file.split('.')[0] + '_delete_inactive.csv')
    # print('inactive: ' + str(len(report) - 1))
    # print('has_active: ' + str(active_count))

    # # prompt to delete first
    # response=input("\ndelete first of " + str(len(report) - 1) + " inactive sensors (yes/no)? ")

    # if response == 'yes':
    #     for inactive in report:
    #         count += 1
    #         print('delete ' + inactive[0] + ' ' + inactive[1] + ' ' + inactive[5] + ' ' + inactive[2])
    #         resp=rc.delete('sensors/' + inactive[7])
    #         print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)
    #         # prompt to delete rest
    #         if count == 1:
    #             response=input("\ncontintue to delete " + str(len(report) - 2) + " inactive sensors (yes/no)? ")
    #             if response == 'yes':
    #                 print('\ndeleting inactive\n')
    #             else:
    #                 print('\nskipping!\n')
    #                 quit()
    #     print('done')
    # else:
    #     print('\nskipped!\n')


if __name__ == '__main__':
    main()
