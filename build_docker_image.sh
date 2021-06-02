#!/bin/bash
# Note: /bin/sh doesn't support arrays!

# Input param specifies whether to run a docker container or a kubernetes pod
if [ -z "$1" ]
  then
    echo "Must provide application run mode - docker container (docker) or kubernetes service (k8s)"
    exit
fi

run_modes=(k8s docker)
# ${run_modes[*]} or ${run_modes[@]} references all elements of the array
if [[ ! " ${run_modes[@]} " =~ " $1 " ]] ;then
    echo "$1: not recognized. Valid names are:"
    echo "${run_modes[@]}"
    exit 1
fi

# build docker image
IMAGE_NAME=bff_api
CONTAINER_NAME=bff_api
# copy ocr-job.yaml from k8s to this directory
cp ../k8s/ocr-job.yaml ./
# build the bff_api docker image. This is the main server for the OCR system. It runs endpoints for triggering
# workflows, getting/posting workflow status updates etc.
docker build -t "$IMAGE_NAME" .

# deploy to any worker nodes on our kubernetes cluster
REPONAME=bff-ocr
. ../deploy/deploy_workers.sh
deploy_workers ${IMAGE_NAME} ${REPONAME}

# Must make sure redis is running before we can run the bff-api server
if [[ "$1" == "docker" ]]; then

  # we read aws creds from .aws directory
  # the IAM role we need to assume
  # IP address of docker host gateway so we can talk to redis running on host computer
  docker ps --filter "name=$CONTAINER_NAME" -aq | xargs docker stop | xargs docker rm
  docker run  --name=$CONTAINER_NAME -v $HOME/.aws/:/root/.aws \
  --env-file ../credentials/iamroles.txt \
  -e REDIS_HOST=172.17.0.1 \
  -p 5001:5001 \
  -it $IMAGE_NAME python3 test_app_conda_env.py
fi

if [[ "$1" == "k8s" ]]; then
  echo "creating bff-ocr pod, service and ingress on port 5001"
  # Delete any existing ocr-bff pod/svc and recreate
  kubectl delete pod ocr-bff-pod -n dev --force
  kubectl delete svc ocr-bff-svc -n dev --force
  kubectl create -f ../k8s/ocr-bff-pod.yaml -n dev
  kubectl expose pod ocr-bff-pod --port 5001 --name ocr-bff-svc -n dev

  # expose as svc

fi
