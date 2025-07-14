import json
import argparse
from tetpyclient import RestClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_args():
	parser = argparse.ArgumentParser(description='Copy scopes from json file to specified root scope')
	parser.add_argument('-f', dest='file',  help='json file to copy from',required=True)
	parser.add_argument('-r', dest='root',  help='root scope to copy under (add in UI first)',required=True)	
	args = parser.parse_args()
	return args

def get_parent_name(s):
    x = s.split(':')
    x.pop()
    return ':'.join(x)

def main():
	args = get_args()
	root = args.root	
	scopes = json.loads(open(args.file,'r').read())
	scopes = sorted(scopes, key=lambda x: x['created_at'])

	rc = RestClient(json.loads(open('endpoint.json', 'r').read())['api_endpoint'], credentials_file='./credentials.json',verify=False)

	scope_ids = []
	resp = rc.get('/app_scopes/',timeout=30.0)
	app_scopes = json.loads(resp.content)	

	for app_scope in app_scopes:
		if app_scope['name'].split(':')[0]==args.root:
			scope_ids.append([app_scope['id'],app_scope['name']])

	for scope in scopes:
		if root + ':' in scope['name']:

			parent_id=''
			parent_name=get_parent_name(scope['name'])

			for scope_id in scope_ids:
				if scope_id[1]==parent_name:
					parent_id=scope_id[0]
					break
			req_payload = {
				'short_name': scope['short_name'],
				'short_query': scope['short_query'],
				'parent_app_scope_id': parent_id,
			}
			
			print('copy '+scope['name'])			
			resp = rc.post('/app_scopes', json_body=json.dumps(req_payload))
			print('    ' + str(resp.status_code)+' '+resp.reason)
			if resp.status_code == 200:
				scope_ids.append([json.loads(resp.content)['id'],json.loads(resp.content)['name']])
				scope_ids.sort(reverse=True)
			else:
				print('    ' + str(resp.status_code) + ' ' + resp.text)


if __name__ == '__main__':
	main()