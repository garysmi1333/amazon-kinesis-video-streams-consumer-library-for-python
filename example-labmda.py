import json
import http.client

print('Loading function')

host = my_host_running_example.py

def lambda_handler(event, context):
    
    payload = json.dumps(event)
    
    headers = {"content-type":"application/json"}
    connection = http.client.HTTPSConnection(host,timeout=10)
    connection.request(method="POST",url="/stream",body=payload,headers=headers)
    response = connection.getresponse()
    
    if response.status == 204:
        return {'status': 'ok'}
    else:
        raise Exception('Something went wrong')