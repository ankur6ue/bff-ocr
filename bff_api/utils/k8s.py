import kubernetes
from kubernetes.client.rest import ApiException
from kubernetes import client, config
import time
import os
import uuid
import yaml

JOB_NAME = "ocr-job"
NAMESPACE = "dev"
IMAGE_NAME = "ocr_prefect"


def create_ocr_job(img_str, resources=None):
    config.load_kube_config()
    api_instance = client.BatchV1Api()
    print(os.path.join(os.path.dirname(__file__), "../../ocr-job.yaml"))
    with open(os.path.join(os.path.dirname(__file__), "../../ocr-job.yaml")) as f:
        dep = yaml.safe_load(f)
        uuid6 = str(uuid.uuid4())[:6]
        dep['metadata']['name'] = "ocr-job-{0}".format(uuid6)
        dep['spec']['template']['spec']['containers'][0]['command'][2] = "python run_flow.py -i {0}".format(img_str)
        if resources is not None: # if the user specified custom CPU/Memory requests/limits, use those
            dep['spec']['template']['spec']['containers'][0]['resources']['requests']['memory'] = resources['requests']['memory']
            dep['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = resources['limits']['memory']
            dep['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'] = resources['requests']['cpu']
            dep['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = resources['limits']['cpu']
        try:
            api_response = api_instance.create_namespaced_job(
                body=dep,
                namespace=NAMESPACE)
            print("Job created. status='%s'" % str(api_response.status))
            return api_response.metadata.name
        except ApiException as e:
            raise ValueError("Error creating job, reason: {0}".format(e.reason))


def get_job_status(job):
    config.load_kube_config()
    api_instance = client.BatchV1Api()
    try:
        api_response = api_instance.read_namespaced_job(job, NAMESPACE)
        if api_response:
            st = api_response.status.start_time
            ct = api_response.status.completion_time
            # if either completion time or start time is None, et (execution time) is None.
            et = None if not ct or not st else ct - st
            s = api_response.status.succeeded
            return {'start_time': st, 'completion_time': ct, 'execution_time': et, 'succeeded': s}
        else:
            return None
    except ApiException as e:
        # job not found, ok to return None, don't reraise
        return None
        # raise ValueError("Error creating job, reason: {0}".format(e.reason))



def create_job(ocr_yaml_path, resources=None):
    config.load_kube_config()
    api_instance = client.BatchV1Api()
    print(ocr_yaml_path)
    with open(ocr_yaml_path) as f:
        dep = yaml.safe_load(f)
        uuid6 = str(uuid.uuid4())[:6]
        dep['metadata']['name'] = "job-{0}".format(uuid6)
        if resources is not None: # if the user specified custom CPU/Memory requests/limits, use those
            dep['spec']['template']['spec']['containers'][0]['resources']['requests']['memory'] = resources['requests']['memory']
            dep['spec']['template']['spec']['containers'][0]['resources']['limits']['memory'] = resources['limits']['memory']
            dep['spec']['template']['spec']['containers'][0]['resources']['requests']['cpu'] = resources['requests']['cpu']
            dep['spec']['template']['spec']['containers'][0]['resources']['limits']['cpu'] = resources['limits']['cpu']
        try:
            api_response = api_instance.create_namespaced_job(
                body=dep,
                namespace=NAMESPACE)
            print("Job created. status='%s'" % str(api_response.status))
            return api_response.metadata.name
        except ApiException as e:
            raise ValueError("Error creating job, reason: {0}".format(e.reason))

def update_job(api_instance, job):
    # Update container image
    job.spec.template.spec.containers[0].image = "perl"
    api_response = api_instance.patch_namespaced_job(
        name=JOB_NAME,
        namespace="default",
        body=job)
    print("Job updated. status='%s'" % str(api_response.status))


def delete_job(job):
    config.load_kube_config()
    api_instance = client.BatchV1Api()
    try:
        api_response = api_instance.delete_namespaced_job(
            name=job,
            namespace=NAMESPACE,
            body=client.V1DeleteOptions(
                propagation_policy='Foreground',
                grace_period_seconds=0))
        print("Job deleted. status='%s'" % str(api_response.status))
    except kubernetes.client.exceptions.ApiException as e:
        print('error deleting job, reason: {0}'.format(e.reason))


def create_k8s_job(img_str):
    # Configs can be set in Configuration class directly or using helper
    # utility. If no argument provided, the config will be loaded from
    # default location.
    config.load_kube_config(os.path.join(os.environ["HOME"], '.kube/config'))
    batch_v1 = client.BatchV1Api()
    # Create a job object with client-python API. The job we
    # created is same as the `pi-job.yaml` in the /examples folder.
    # delete_job(batch_v1)
    # time.sleep(1)
    return create_ocr_job(batch_v1, img_str)