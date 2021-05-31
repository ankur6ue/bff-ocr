import pytest
import os
import sys
import time
from prettytable import PrettyTable
# add path to bff_api. Need this because the below doesn't work
# from ..bff_api.utils.k8s import create_job
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from bff_api.utils.k8s import create_job, get_job_status, delete_job


def test_status_of_nonexistent_job():
    job_name = "dontexist"
    status = get_job_status(job_name)
    assert status == None


def test_run_jobs_and_get_status():
    job_yaml_path = os.path.join(os.path.dirname(__file__), "yaml/test-job1.yaml")

    num_jobs = 4
    jobs = []
    for job_idx in range(0, num_jobs):
        job_name = create_job(job_yaml_path)
        time.sleep(0.5)
        jobs.append(job_name)

    all_succeeded = False
    start = time.time()

    while not all_succeeded:
        pt = PrettyTable()
        pt.field_names = ["job_name", "start_time", "completion_time", "execution_time", "success"]
        all_succeeded = True
        # check status every second
        time.sleep(1)
        finished_jobs = []

        for job in jobs:
            status = get_job_status(job)
            # if job succeeded, delete it. If jobs are not deleted after completion, it can take longer to start
            # following jobs
            if status['succeeded']:
                finished_jobs.append(job)
            all_succeeded = all_succeeded & False if status['succeeded'] == None else status['succeeded']
            pt.add_row([job, status['start_time'], status['completion_time'], status['execution_time'], status['succeeded']])
        print(pt)

        if len(finished_jobs) > 0:
            for job in finished_jobs:
                delete_job(job)
                jobs.remove(job)
    print("total execution time: {0}".format(time.time() - start))

test_status_of_nonexistent_job()