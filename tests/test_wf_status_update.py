import pytest
import requests
import time
import uuid
import time
import json
import redis
import threading
import datetime as dt
from prettytable import PrettyTable
# This is the URL for the kubernetes ingress + prefix path for the ocr-bff service
url = 'http://127.0.0.1:30553/ocr-bff'
# url = 'http://127.0.0.1:5001'
redis_url = '10.100.184.216'

def test_wf_status_update():
    wf_id = uuid.uuid1()
    r = requests.post(url + '/wf_update_status', {'uuid': wf_id.urn, 'status_msg': 'hello', 'is_completed': True})
    assert r.status_code == 200


def test_wf_status_update_missing_field():
    wf_id = uuid.uuid1()
    r = requests.post(url + '/wf_update_status', {'is_completed': True})
    assert r.status_code == 200


# Trigger a job and check the status updates in redis directly
def test_get_wf_status_update1():
    r = requests.post(url + '/wf_trigger', {'image_list': 'trading-issue.jpg'})
    assert r.status_code == 200

    r = redis.Redis(host=redis_url, port=6379, db=0)
    keys = r.keys('*')
    for key in keys:
        type = r.type(key)
        vals = r.lrange(key, 0, -1)
        print(vals)


# Send a start_workflow status update message
def test_get_wf_status_update2():
    msg = "Flow started"
    uuid6 = str(uuid.uuid4())[:6]
    job_name = "ocr-job-{0}".format(uuid6)
    # add another 6 characters for the pod_name. Remember, status updates are sent by a pod
    uuid6 = str(uuid.uuid4())[:6]
    pod_name = "{0}-{1}".format(job_name, uuid6)
    r = requests.post(url + '/wf_update_status', {'job_name': pod_name,
                                                       'timestamp': dt.datetime.now(),
                                                       'status_msg': msg,
                                                       'is_completed': False,
                                                       'success': False},
                      timeout=0.1)

    assert r.status_code == 200
    # get status of non-existent job and verify it returns bad job
    # remmber, status get requests use the job_name, not pod_name
    r = requests.get(url + '/wf_update_status', {'job_name': job_name})

    # get status and verify it returns pending
    r = requests.get(url + '/wf_update_status', {'job_name': job_name})
    r = requests.get(url + '/wf_update_status', {'job_name': "job1"})

    msg = "workflow_complete"
    r = requests.post(url + '/wf_update_status', {'job_name': "job1",
                                                  'timestamp': dt.datetime.now(),
                                                  'status_msg': msg,
                                                  'is_completed': True,
                                                  'success': True},
                      timeout=0.1)
    assert r.status_code == 200



# Trigger a job and call the update_status endpoint. If the status of the job is completed, read the bounding boxes
def test_get_wf_status_update3():
    jobs = []
    imgs = ['trading-issue.jpg', 'IMG-9134.jpg']
    # imgs = ['doesntexist.jpg']
    num_jobs = len(imgs)
    for job_idx in range(0, num_jobs):
        # trading_issue.jpg is already stored in S3
        r = requests.post(url + '/wf_trigger', {'image_list': imgs[job_idx]})
        assert r.status_code == 200.
        resp = json.loads(r.content)
        assert resp['success'] is True
        job_name = resp['job_name']
        jobs.append(job_name)
    print_job_status(jobs)


def print_job_status(jobs):
    all_completed = True
    pt = PrettyTable()
    pt.field_names = ["job_name", "status_msg", "success"]
    for job in jobs:
        r = requests.get(url + '/wf_update_status', {'job_name': job})
        content_json = json.loads(r.content)
        is_completed = False
        content_list = content_json['status']
        for l in content_list:
            pt.add_row([job, l['status_msg'], l["success"]])
            is_completed = l['is_completed']
            all_completed = all_completed & is_completed
    print(pt)
    if not all_completed:
        threading.Timer(2.0, lambda: print_job_status(jobs)).start()
    else:
        print("all jobs finished")


test_get_wf_status_update3()
