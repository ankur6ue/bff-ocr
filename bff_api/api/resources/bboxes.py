"""
Implementation of Get bounding boxes. Given an image, returns the text bounding boxes
"""

import os.path
from flask.views import MethodView
from flask import request
from marshmallow import ValidationError
import json
from .errors import InternalServerError
from ...utils.aws_auth import AWSAuth
from ...utils.s3 import s3_to_local
from ...utils.allowed_extensions import FILE_CONTENT_TYPES
from ..schemas.bboxes import BboxesSchema


class Bboxes(MethodView):
    """ Returns a list of bounding boxes
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
        self.s3_bucket_name = cfg.get("S3_BUCKET_NAME")
        self.region_name = cfg.get("REGION_NAME")
        self.acl = cfg.get("ACL")
        # Whether we are working locally or dealing with AWS
        self.is_local = cfg.get("LOCAL")
        self.local_base_path = os.environ.get("HOME") + cfg.get("LOCAL_BASE_PATH")
        self.logger = args.get('logger')

    def get(self):
        """
            GET implementation
        """
        if self.s3_bucket_name is None:
            raise InternalServerError

        args = request.args

        try:
            vargs = BboxesSchema().load(args)
        # client validation error
        except ValidationError as err:
            self.logger.warn(err.messages)
            return err.messages, 422

        image_name = vargs['file_name']
        # if image_name is receipt.jpg, this will be receipt
        base_image_name = image_name.rsplit('.', 1)[0]

        # The goal of the code below is the read the bbox.txt and results.json file located on S3 in a folder
        # named after the input image. The bbox.txt file contains the bounding box coordinates for each word
        # detected on the input image by the OCR system and the results.json file contains the corresponding
        # text recognition results. The recognition result strings are appended to the bounding box coordinates
        # and returned to the client, where they can drawn on the input image to present the OCR word detection +
        # recognition results.

        # first copy OCR results from s3 to local
        dest_path = os.path.join(self.local_base_path, 'results', base_image_name)
        file_paths = s3_to_local(self.s3_bucket_name, 'results/' + base_image_name, ['.json'],
                                 dest_path, self.logger)
        # index of bboxes.json in the file_paths list
        bbox_index = [idx for idx, s in enumerate(file_paths) if 'bboxes.json' in s][0]
        results_json_index = [idx for idx, s in enumerate(file_paths) if 'results.json' in s][0]
        bbox_file_path = file_paths[bbox_index]
        rec_results_file_path = file_paths[results_json_index]
        with open(rec_results_file_path) as f:
            rec_results = json.load(f)

        with open(bbox_file_path) as f:
            boxes = json.load(f)

        return {'success': True, 'boxes': boxes, 'rec_results': rec_results}
