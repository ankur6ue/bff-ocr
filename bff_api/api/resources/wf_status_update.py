"""
Implementation of Get bounding boxes. Given an image, returns the text bounding boxes
"""

import os.path
import sys
from flask.views import MethodView
from flask import request
from marshmallow import ValidationError
import pickle
import mysql.connector
from mysql.connector import errorcode
import datetime
from ...utils.allowed_extensions import FILE_CONTENT_TYPES
from ..schemas.wf_status_update import WfGetStatusUpdateSchema, WfPostStatusUpdateSchema
from ...utils.k8s import get_job_status
from ...utils.mysql import add_row, update_row, get_row
class WorkflowStatusUpdate(MethodView):
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
        env_path = cfg.get("AWS_ENV_PATH")
        self.s3_bucket_name = cfg.get("S3_BUCKET_NAME")
        self.region_name = cfg.get("REGION_NAME")
        self.acl = cfg.get("ACL")
        # Whether we are working locally or dealing with AWS
        self.is_local = cfg.get("LOCAL")
        self.local_base_path = cfg.get("LOCAL_BASE_PATH")
        self.logger = args.get('logger')
        self.status = {}
        self.redis = cfg.get("REDIS")
        self.mysql_cfg = cfg.get("MYSQL")

    def post(self):
        """
            POST implementation
        """
        args = request.form

        try:
            vargs = WfPostStatusUpdateSchema().load(args)
        # client validation error
        except ValidationError as err:
            self.logger.info(err.messages)
            return err.messages, 422

        status = {}
        job_name = vargs['job_name']
        status["status_msg"] = vargs['status_msg']
        status["is_completed"] = vargs['is_completed']
        status["success"] = vargs['success']
        status["timestamp"] = vargs['timestamp']
        key = str(job_name)
        # Send to redis
        self.redis.rpush(key, pickle.dumps(status))

        # if status message is "start", also log in mysql database
        if status["status_msg"] == "Flow started" and self.mysql_cfg:
            add_row(self.mysql_cfg, job_name, status, self.logger)

        if status["is_completed"] == True and self.mysql_cfg:
            update_row(self.mysql_cfg, job_name, status, self.logger)


        self.logger.info("key={0}".format(key))
        self.logger.info(status["status_msg"])
        self.logger.info(status["is_completed"])

        return {'success': True}

    def get(self):
        """
            POST implementation
        """
        args = request.args

        try:
            vargs = WfGetStatusUpdateSchema().load(args)
        # client validation error
        except ValidationError as err:
            self.logger.info(err.messages)
            return err.messages, 422
        job_name = vargs['job_name']

        # if job_status is not None, then this job has started running and may have sent some status updates
        # already..

        # get accumulated status updates for this job_name
        # This is because the job_name is the job-name (eg., ocr-job-ee6e24), while the status notifications
        # stored in redis are keyed by the pod-name, which has an extra 6 character uuid appended to it
        # (eg., ocr-job-ee6e24-gh5643)
        # Find all keys that have job_name as the prefix.
        keys = self.redis.keys(job_name + '*')
        l = []
        if len(keys) > 0:
            key = keys[0]
            while self.redis.llen(key) != 0:
                l.append(pickle.loads(self.redis.lpop(key)))

            update = WfPostStatusUpdateSchema()
            return {'success': True, "status": update.dump(l, many=True)}

        # if no job updates in redis, job must be either:
        # non-existent: bad job name
        # pending: not scheduled for execution yet
        # started execution: no status update needs to be sent in this case, because the client can just wait
        # for log messages to arrive
        # completed execution: the job status could be success or failure (some tasks failed). There could also
        # be a case where the python code crashed, in which case, the job completed status update would have not
        # been sent.
        # job_status = get_row(self.mysql_cfg, job_name, self.logger)
        job_k8s_status = get_job_status(job_name)
        update = WfPostStatusUpdateSchema()
        # case 1: job doesn't exist
        if job_k8s_status is None:
            return {'success': False, "status": update.dump([{"status_msg": "bad job name",
                                                             "is_completed": False,
                                                             "success": False,
                                                             "job_name": job_name}], many=True)}
        else:
            # case 2: job is pending
            k8s_start_time = job_k8s_status['start_time']
            k8s_completion_time = job_k8s_status['completion_time']
            if k8s_start_time is None:
                return {'success': False, "status": update.dump([{"status_msg": "pending",
                                                                  "is_completed": False,
                                                                  "success": False,
                                                                  "job_name": job_name}], many=True)}
            # case 3: job finished, figure out if it successfully finished execution, was unsuccessful (eg., some
            # task failed), or crashed. If it crashed, completion_time would not have been recorded
            if k8s_start_time and k8s_completion_time:
                # print("printing job status" + job_status, file=sys.stderr)
                # get job status in the datatabse
                if self.mysql_cfg:
                    job_status = get_row(self.mysql_cfg, job_name, self.logger)
                    if job_status:
                        start_time = job_status[1]
                        completion_time = job_status[2]
                        success = job_status[3]
                        print("success: {0}".format(success), file=sys.stderr)
                        is_complete = True if completion_time is not None else False
                        status_msg = "finished" if is_complete else "crashed"
                        return {'success': True, "status": update.dump([{"status_msg": status_msg,
                                                                         "is_completed": is_complete,
                                                                         "success": success,
                                                                         "job_name": job_name}], many=True)}
                    else: # no job_status found, assume job successfully finished
                        status_msg = "finished"
                        is_complete = True
                        success = True
                        # no jobs database, assume job successfully finished execution
                        return {'success': True, "status": update.dump([{"status_msg": status_msg,
                                                                         "is_completed": is_complete,
                                                                         "success": success,
                                                                         "job_name": job_name}], many=True)}

                else: # no jobs database
                    status_msg = "finished"
                    is_complete = True
                    success = True
                    # no jobs database, assume job successfully finished execution
                    return {'success': True, "status": update.dump([{"status_msg": status_msg,
                                                                     "is_completed": is_complete,
                                                                     "success": success,
                                                                     "job_name": job_name}], many=True)}
            # job started running, but hasn't finished
            if k8s_start_time and k8s_completion_time is None:
                update = WfPostStatusUpdateSchema()
                return {'success': True, "status": update.dump([{"status_msg": "running",
                                                                  "is_completed": False,
                                                                  "success": False,
                                                                  "job_name": job_name}], many=True)}




