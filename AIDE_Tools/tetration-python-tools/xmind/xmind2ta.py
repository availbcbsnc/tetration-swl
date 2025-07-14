import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import zipfile
from xml.etree import ElementTree
import datetime


def get_args():
    parser = argparse.ArgumentParser(description='create scopes from xmind')
    parser.add_argument('-f', dest='file', help='xmind file (exmample.xmind) REQUIRED', required=True)
    parser.add_argument('-s', dest='id', help='parent scope id (add in UI first) REQUIRED', required=True)
    args = parser.parse_args()
    return args


def add_scope(parent_id, child, ns, rc):
    query = {'type': 'eq', 'field': 'ip', 'value': '10.0.0.1'}
    if child.find('ns0:notes', ns) is not None:
        query = json.loads(child.find('ns0:notes/ns0:plain', ns).text.split('\n')[0].replace('\'', '\"'))
    req_payload = {
        'short_name': child.find('ns0:title', ns).text,
        'short_query': query,
        'parent_app_scope_id': parent_id
    }

    print('create scope ' + child.find('ns0:title', ns).text + ' pareent_id: ' + parent_id)
    resp = rc.post('/app_scopes', json_body=json.dumps(req_payload))
    print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)

    if resp.status_code == 200:
        print('        ' + json.loads(resp.content)['name'] + '\n')
        parent_app_scope_id = json.loads(resp.content)['id']
        if child.find('ns0:children', ns) is not None:
            for topic in child.findall('./ns0:children/ns0:topics[@type="attached"]/ns0:topic', ns):
                add_scope(parent_app_scope_id, topic, ns, rc)

            for topic in child.findall('./ns0:children/ns0:topics[@type="detached"]/ns0:topic', ns):
                if topic.find('ns0:title', ns).text == 'Filters':
                    for filter_topic in topic.findall('./ns0:children/ns0:topics[@type="attached"]/ns0:topic', ns):
                        add_filter(parent_app_scope_id, filter_topic, ns, rc)
                if topic.find('ns0:title', ns).text == 'Segmentation':
                    for application_topic in topic.findall('./ns0:children/ns0:topics[@type="attached"]/ns0:topic', ns):
                        add_application(parent_app_scope_id, application_topic, ns, rc)

    else:
        raise Exception(resp.text)
    return None


def add_filter(parent_id, child, ns, rc):
    query = {'type': 'eq', 'field': 'ip', 'value': '10.0.0.1'}
    if child.find('ns0:notes', ns) is not None:
        query = json.loads(child.find('ns0:notes/ns0:plain', ns).text.split('\n')[0].replace('\'', '\"'))

    req_payload = {
        'app_scope_id': parent_id,
        'name': child.find('ns0:title', ns).text,
        'query': query,
        'primary': 'true',
        'public': 'true'
    }

    print('create filter ' + child.find('ns0:title', ns).text + ' pareent_id: ' + parent_id)
    resp = resp = rc.post('/filters/inventories', json_body=json.dumps(req_payload))
    print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)

    if resp.status_code == 200:
        print('        ' + json.loads(resp.content)['name'] + '\n')
    else:
        raise Exception(resp.text)
    return None


def add_application(parent_id, child, ns, rc):
    req_payload = {
        "app_scope_id": parent_id,
        "name": child.find('ns0:title', ns).text
    }

    print('create application ' + child.find('ns0:title', ns).text + ' pareent_id: ' + parent_id)
    resp = resp = rc.post('/applications', json_body=json.dumps(req_payload))
    print('    ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(resp.status_code) + ' ' + resp.reason)

    if resp.status_code == 200:
        print('        ' + json.loads(resp.content)['name'] + '\n')
    else:
        raise Exception(resp.text)
    return None


def main():
    args = get_args()

    with zipfile.ZipFile(args.file) as file:
        file.extractall()

    with open('content.xml', 'r') as file:
        doc = ElementTree.parse(file)

    ns = {'ns0': doc.getroot().tag[1:doc.getroot().tag.index('}')]}
    rc = RestClient(json.loads(open('endpoint.json', 'r').read())['api_endpoint'], credentials_file='./credentials.json', verify=False)

    for topic in doc.getroot().findall('./ns0:sheet/ns0:topic/ns0:children/ns0:topics/ns0:topic', ns):
        add_scope(args.id, topic, ns, rc)


if __name__ == '__main__':
    main()
