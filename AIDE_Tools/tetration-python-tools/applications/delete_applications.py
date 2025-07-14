import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_args():
    parser = argparse.ArgumentParser(description="Delete applications under specified scope")
    parser.add_argument('-r', dest='root', help='root scope name to delete applications', required=True)
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    rc = RestClient(json.loads(open('../endpoint.json', 'r').read())["api_endpoint"], credentials_file='../credentials.json', verify=False)

    resp = rc.get('/applications/')
    applications = json.loads(resp.content)

    resp = rc.get('/app_scopes/')
    scopes = json.loads(resp.content)

    delete_ids = []
    for scope in scopes:
        if scope['name'].split(":")[0] == args.root.split(":")[0]:
            delete_ids.append(scope['id'])

    for application in applications:
        if application['app_scope_id'] in delete_ids:
            resp = rc.get('/openapi/v1/applications/' + application['id'] + '/policies')
            policies = json.loads(resp.content)

            for absolute_policy in policies['absolute_policies']:
                print("delete absolute policy: " + application['name'] + " > " + absolute_policy['id'])
                resp = rc.delete('/openapi/v1/policies/' + absolute_policy['id'])
                print(str(resp.status_code) + " " + resp.reason)
                if resp.status_code is not 200:
                    print(resp.text)

            for default_policy in policies['default_policies']:
                print("delete default policy: " + application['name'] + " > " + default_policy['id'])
                resp = rc.delete('/openapi/v1/policies/' + default_policy['id'])
                print(str(resp.status_code) + " " + resp.reason)
                if resp.status_code is not 200:
                    print(resp.text)

            print("delete application: " + scope['name'] + " > " + application['name'])
            resp = rc.delete('/applications/' + application['id'])
            print(str(resp.status_code) + " " + resp.reason)
            if resp.status_code is not 200:
                print(resp.text)


if __name__ == '__main__':
    main()
