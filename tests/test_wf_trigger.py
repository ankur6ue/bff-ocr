import pytest
import requests
import time
import uuid
import json

url = 'http://10.100.232.102:5001' # The root url of the flask app
url = 'http://127.0.0.1:5001'


def test_wf_trigger():
    r = requests.post(url + '/wf_trigger', {'image_list': 'trading-issue.jpg'})
    assert r.status_code == 200
    resp = json.loads(r.content)
    pod_name = resp['job_name']
    assert pod_name != ""



test_wf_trigger()
