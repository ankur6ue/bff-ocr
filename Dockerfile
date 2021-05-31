# FROM prefecthq/prefect:0.14.5-python3.7 as base_image
FROM python:3.8

# Install pip
RUN python -m pip install --upgrade pip

ENV PREFECT__USER_CONFIG_PATH='/opt/prefect/config.toml'
ENV BASE_INSTALL_DIR='/opt/bff-ocr'
# needed to get rid of ImportError: libGL.so.1:
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
# needed to get rid of ImportError: libtk8.6.so
RUN apt-get install tk -y
RUN apt-get install nano
COPY requirements.txt /tmp/requirements.txt
WORKDIR /tmp
RUN pip install -r requirements.txt

RUN mkdir -p $BASE_INSTALL_DIR
RUN mkdir -p $BASE_INSTALL_DIR/tests
RUN mkdir -p /root/.kube

WORKDIR $BASE_INSTALL_DIR
COPY /bff_api $BASE_INSTALL_DIR/bff_api
COPY /tests $BASE_INSTALL_DIR/tests
COPY test_app_conda_env.py $BASE_INSTALL_DIR/
COPY ocr-job.yaml $BASE_INSTALL_DIR/ocr-job.yaml
