import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import zipfile
from xml.etree import ElementTree as ET
import time


def get_args():
    parser = argparse.ArgumentParser(description='create xmind from scopes')
    # parser.add_argument('-f', dest='file', help='app_scopes.json', required=False)
    parser.add_argument('-s', dest='scope', help='scope name', required=True)
    args = parser.parse_args()
    return args


def add_topic(relationships, scope, scopes, parent, rc, inventory_filters, applications):
    topic = ET.SubElement(parent, 'topic', id=scope['id'], branch='folded')
    topic.set('structure-class', 'org.xmind.ui.tree.right')

    # # root scope
    # if scope['short_name'] == scope['name']:
    #     topic.set('structure-class', 'org.xmind.ui.tree.right')
    #     # extensions = ET.SubElement(topic, 'extensions')
    #     # extension = ET.SubElement(extensions, 'extension', provider='org.xmind.ui.map.balanced')
    #     # content = ET.SubElement(extension, 'content')
    #     # ET.SubElement(content, 'right-number').text = '-1'

    # else:
    #     topic.set('structure-class', 'org.xmind.ui.tree.right')
    #     topic.set('branch', 'folded')

    print(scope['name'])
    ET.SubElement(topic, 'title').text = scope['short_name']
    notes = ET.SubElement(topic, 'notes')
    ET.SubElement(notes, 'plain').text = json.dumps(scope['short_query']) + '\n'
    children = ET.SubElement(topic, 'children')
    detached_topics = ET.SubElement(children, 'topics', type='detached')
    attached_topics = ET.SubElement(children, 'topics', type='attached')

    if scope['id'] in [x['app_scope_id'] for x in inventory_filters]:
        topic_id = str(time.time()).replace('.', '')
        filters_topic = ET.SubElement(detached_topics, 'topic', id=topic_id, branch='folded')
        # filters_topic.set('structure-class', 'org.xmind.ui.locic.right')
        ET.SubElement(filters_topic, 'title').text = 'Filters'
        ET.SubElement(relationships, 'relationship', id=str(time.time()).replace('.', ''), end1=scope['id'], end2=topic_id)
        # control_points = ET.SubElement(relationship, 'control-points')
        # ET.SubElement(control_points, 'control-point', amount='0.25', angle='0.25', index='0')
        # ET.SubElement(control_points, 'control-point', amount='0.25', angle='0.25', index='1')

        filters_children = ET.SubElement(filters_topic, 'children')
        filter_topics = ET.SubElement(filters_children, 'topics', type='attached')

        for inventory_filter in inventory_filters:
            if inventory_filter['app_scope_id'] == scope['id']:
                filter_topic = ET.SubElement(filter_topics, 'topic', id=inventory_filter['id'])
                ET.SubElement(filter_topic, 'title').text = inventory_filter['name']
                filter_notes = ET.SubElement(filter_topic, 'notes')
                ET.SubElement(filter_notes, 'plain').text = json.dumps(inventory_filter['short_query']) + '\n'

                resp = rc.post('/inventory/search', json_body=json.dumps({'filter': inventory_filter['short_query'], 'scopeName': scope['name']}), timeout=30.0)
                if resp.status_code == 200:
                    inventory = json.loads(resp.content)['results']
                    for host in inventory:
                        if host['host_name'] is not None:
                            filter_notes.find('plain').text += host['ip'] + ' ' + host['host_name'] + '\n'
                        else:
                            filter_notes.find('plain').text += host['ip'] + '\n'
                else:
                    raise Exception(resp.text)

    if scope['id'] in [x['app_scope_id'] for x in applications]:
        topic_id = str(time.time()).replace('.', '')
        applications_topic = ET.SubElement(detached_topics, 'topic', id=topic_id, branch='folded')
        # applications_topic.set('structure-class', 'org.xmind.ui.logic.right')
        ET.SubElement(applications_topic, 'title').text = 'Segmentation'
        ET.SubElement(relationships, 'relationship', id=str(time.time()).replace('.', ''), end1=scope['id'], end2=topic_id)
        # control_points = ET.SubElement(relationship, 'control-points')
        # ET.SubElement(control_points, 'control-point', amount='0.25', angle='0.25', index='0')
        # ET.SubElement(control_points, 'control-point', amount='0.25', angle='0.25', index='1')

        applications_children = ET.SubElement(applications_topic, 'children')
        applications_topics = ET.SubElement(applications_children, 'topics', type='attached')

        for application in applications:
            # absolute_policies = []
            # default_policies = []

            if application['app_scope_id'] == scope['id']:
                resp = rc.get('/applications/' + application['id'] + '/details', timeout=30.0)
                if resp.status_code == 200:

                    application_topic = ET.SubElement(applications_topics, 'topic', id=application['id'])
                    ET.SubElement(application_topic, 'title').text = application['name']
                    application_notes = ET.SubElement(application_topic, 'notes')
                    ET.SubElement(application_notes, 'plain').text = str(resp.content) + '\n'

                    # application_notes = ET.SubElement(absolute_topic, 'notes')
                    # ET.SubElement(application_notes, 'plain').text = resp.content + '\n'
                else:
                    raise Exception(resp.text)
                    # absolute_policies = json.loads(resp.content)['absolute_policies']
                #     default_policies = json.loads(resp.content)['default_policies']
                # else:
                #     raise Exception(resp.text)
                # application_topic = ET.SubElement(applications_topics, 'topic', id=application['id'])
                # ET.SubElement(application_topic, 'title').text = application['name']
                # application_notes = ET.SubElement(absolute_topic, 'notes')
                # ET.SubElement(application_notes, 'plain').text = resp.content + '\n'

                # application_children = ET.SubElement(application_topic, 'children')
                # application_topics = ET.SubElement(application_children, 'topics', type='attached')

                # if len(absolute_policies) > 0:
                #     absolute_topic = ET.SubElement(application_topics, 'topic', id=str(time.time()).replace('.', ''))
                #     ET.SubElement(absolute_topic, 'title').text = 'Absolute Policies'
                #     absolute_notes = ET.SubElement(absolute_topic, 'notes')
                #     ET.SubElement(absolute_notes, 'plain').text = str(absolute_policies) + '\n'
                # if len(default_policies) > 0:
                #     default_topic = ET.SubElement(application_topics, 'topic', id=str(time.time()).replace('.', ''))
                #     ET.SubElement(default_topic, 'title').text = 'Default Policies'
                #     absolute_notes = ET.SubElement(default_topic, 'notes')
                #     ET.SubElement(absolute_notes, 'plain').text = str(default_policies) + '\n'

    if len(scope['child_app_scope_ids']) == 0:
        resp = rc.post('/inventory/search', json_body=json.dumps({'filter': {}, 'scopeName': scope['name']}), timeout=30.0)
        if resp.status_code == 200:
            inventory = json.loads(resp.content)['results']
            for host in inventory:
                if host['host_name'] is not None:
                    notes.find('plain').text += host['ip'] + ' ' + host['host_name'] + '\n'
                else:
                    notes.find('plain').text += host['ip'] + '\n'
        else:
            raise Exception(resp.text)

    for child_id in scope['child_app_scope_ids']:
        for app_scope in scopes:
            if app_scope['id'] == child_id:
                add_topic(relationships, app_scope, scopes, attached_topics, rc, inventory_filters, applications)
    return None


def main():
    args = get_args()
    rc = RestClient(json.loads(open('endpoint.json', 'r').read())['api_endpoint'], credentials_file='./credentials.json', verify=False)

    # get scopes
    resp = rc.get('/app_scopes', timeout=30.0)
    if resp.status_code == 200:
        scopes = json.loads(resp.content)
    else:
        raise Exception(resp.text)
    scopes = sorted(scopes, key=lambda x: x['created_at'])

    # get filters
    resp = rc.get('/filters/inventories/')
    if resp.status_code == 200:
        inventory_filters = json.loads(resp.content)
    else:
        raise Exception(resp.text)

    # get applications
    resp = rc.get('/applications/')
    if resp.status_code == 200:
        applications = json.loads(resp.content)
    else:
        raise Exception(resp.text)

    content = ET.Element('xmap-content', xmlns='urn:xmind:xmap:xmlns:content:2.0')
    sheet = ET.SubElement(content, 'sheet', id=str(time.time()).replace('.', ''))
    relationships = ET.SubElement(sheet, 'relationships')
    ET.SubElement(sheet, 'title').text = 'Sheet 1'

    for scope in scopes:
        if args.scope == scope['name']:
            add_topic(relationships, scope, scopes, sheet, rc, inventory_filters, applications)
            break

    tree = ET.ElementTree(content)
    tree.write('content.xml')

    with zipfile.ZipFile(args.scope + '.xmind', 'w', zipfile.ZIP_DEFLATED) as file:
        file.write('content.xml')

    print('\ncreated ' + args.scope + '.xmind')


if __name__ == '__main__':
    main()
