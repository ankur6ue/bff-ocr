"""
Implementation of Get bounding boxes. Given an image, returns the text bounding boxes
"""

import os.path
import subprocess
from flask.views import MethodView
from flask import request
from marshmallow import ValidationError
import json
from .errors import InternalServerError
from ..schemas.wf_trigger import WfTriggerSchema
import time
from ...utils.k8s import create_ocr_job

class WfTrigger(MethodView):
    """ Trigger an OCR workflow run
        ---
        post:
          url parameters:
            - Required:
                file_name: [string]
            - Optional:
                expiration: [int], default=1000
                content_size_min: [int] range=[min=1000, max=10000000], default=1000
                content_size_max: [int] range=[min=1000, max=10000000], default=10000000
          success response:
            200
              content: {'success': True, 'post_url': post_url, 'data': fields dictionary returned by
              generate_presigned_post from boto3 SDK}
           failure response:
            422: Bad client parameters
            404: Endpoint doesn't exist
    """
    def __init__(self, args):
        cfg = args.get("cfg")
        env_path = cfg.get("AWS_ENV_PATH")
        self.s3_bucket_name = cfg.get("S3_BUCKET_NAME")
        self.region_name = cfg.get("REGION_NAME")
        self.acl = cfg.get("ACL")
        # Whether we are working locally or dealing with AWS
        self.is_local = cfg.get("LOCAL")
        self.local_base_path = cfg.get("LOCAL_BASE_PATH")
        self.logger = args.get('logger')

    def post(self):
        """
            POST implementation
        """
        args = request.form

        try:
            vargs = WfTriggerSchema().load(args)
        # client validation error
        except ValidationError as err:
            self.logger.warn(err.messages)
            return err.messages, 422

        image_list = vargs['image_list']
        images = image_list.split(",")
        # coonvert list of images to space separated string
        images_str = " ".join(str(x) for x in images)

        try:
            # subprocess.Popen(["cd /home/ankur/dev/apps/ML/OCR/aster-ocr-workflow/", "build_and_run.sh", images_str])
            # job_name = "ocr_pod"
            job_name = create_ocr_job(images_str)
            return {'job_name': job_name, 'success': True}
        except ValueError as err: ## improve exception handling
            self.logger.warn(err)
            return {'job_name': "", 'success': False}
