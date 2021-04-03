"""
Implementation of Upload view. This view takes an input image name and returns a signed URL that can be used to
upload the image to S3
"""

from flask.views import MethodView
from flask import request
from marshmallow import ValidationError
from .errors import InternalServerError
from ...utils.aws_auth import AWSAuth
from ...utils.allowed_extensions import FILE_CONTENT_TYPES
from ..schemas.upload import UploadSchema


class UploadImage(MethodView):
    """ Generates a pre-signed URL that can be used to post an image to AWS S3
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
        if env_path and self.s3_bucket_name and self.region_name:
            self.aws_auth = AWSAuth(env_path)
            self.logger = args.get('logger')

    def post(self):
        """
            Post implementation
        """
        if self.aws_auth is None or self.s3_bucket_name is None:
            raise InternalServerError

        args = request.form

        try:
            vargs = UploadSchema().load(args)
        # client validation error
        except ValidationError as err:
            self.logger.info(err.messages)
            return err.messages, 422

        image_name = vargs['file_name']
        content_size_min = vargs['content_size_min']
        content_size_max = vargs['content_size_max']
        expiration = vargs['expiration']
        extension = image_name.rsplit('.', 1)[1].lower()
        object_name = 'images/' + image_name
        # Note if your bucket is not publicly accessible (to be accessed by assuming an IAM role),
        # you must set the acl to private, otherwise you'll get an access denied error
        fields = {"acl": self.acl, "Content-Type": FILE_CONTENT_TYPES[extension]}
        conditions = [
            {"acl": "private"},
            {"Content-Type": FILE_CONTENT_TYPES[extension]},
            ["content-length-range", content_size_min, content_size_max]
        ]
        try:
            resp = self.aws_auth.create_presigned_post(self.region_name, self.s3_bucket_name,
                                                       object_name, fields=fields,
                                                       conditions=conditions, expiration=expiration)
            post_url = resp['url']
            data = resp['fields']
            return {'success': True, 'post_url': post_url, 'data': data}
        except ValueError as err:
            self.logger.info(err)
            raise InternalServerError("Internal Server Error")
