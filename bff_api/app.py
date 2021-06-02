# -*- coding: utf-8 -*-
"""
An example flask application showing how to upload a file to S3
while creating a REST API using Flask-Restful.
Note: This method of uploading files is fine for smaller file sizes,
      but uploads should be queued using something like celery for
      larger ones.
"""
import redis
import os
from flask import Flask
from flask_cors import CORS
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from bff_api.api.resources.signed_url import UploadImage
from bff_api.api.resources.bboxes import Bboxes
from bff_api.api.resources.wf_status_update import WorkflowStatusUpdate
from bff_api.api.resources.wf_trigger import WfTrigger
from bff_api.api.resources.errors import register_error_handlers
from bff_api.utils.s3 import set_session_creds
from bff_api.utils.mysql import connect, create_database, create_table, delete_table
from healthcheck import HealthCheck


def init_sqldb(logger):
    mysql_host = 'localhost' if os.environ.get('MYSQL_HOST') is None else os.environ.get('MYSQL_HOST')
    config = {
        'user': 'root',
        'password': 'password',
        'host': mysql_host
    }
    try:
        cnx = connect(config, logger)
        cursor = cnx.cursor()
        delete_table(cursor, logger)
        create_table(cursor, logger)
    except: # catch any exception encountered with mysql, because that isn't fatal to our application
        logger.warn("error initializing mysql")
        return None
    else:
        if cnx:
            cnx.close()
        return config



# Renew session token every 10 min
def renew_aws_session_token(app):
    if os.path.exists('iamroles.txt'):
        with open('iamroles.txt', 'r') as f:
            iamrole = f.readline()
            set_session_creds(iamrole)
    elif os.environ.get('S3ACCESSIAMROLE') is not None:
        iamrole = os.environ.get('S3ACCESSIAMROLE')
        set_session_creds(app, iamrole)
    else:
        raise Exception('Error getting S3 access credentials, aborting')



# add your own check function to the healthcheck
def health_check():
    return True, "ok"


# Initialization
def create_app(config, testing=False):
    """Application factory, used to create application"""
    app = Flask("bff_api")
    CORS(app)
    app.config.from_object(config)
    # Connect with Redis and flush the database
    # use local host for redis if running from debugger, otherwise use REDIS_HOST passed as environment var
    redis_host = 'localhost' if os.environ.get('REDIS_HOST') is None else os.environ.get('REDIS_HOST')
    r = redis.Redis(host=redis_host, port=6379, db=0)
    r.flushdb()
    app.config["REDIS"] = r

    # Now deal with mysql db
    sql_cfg = init_sqldb(app.logger)
    app.config["MYSQL"] = sql_cfg

    health = HealthCheck()
    health.add_check(health_check)

    renew_aws_session_token(app)

    # Renew AWS session token every 10 min
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda:renew_aws_session_token(app), trigger="interval", seconds=10*60)
    scheduler.start()

    if testing is True:
        app.config["TESTING"] = True
    register_error_handlers(app)


    # register views
    upload_view = UploadImage.as_view('upload_image', {'cfg': app.config, 'logger': app.logger})
    app.add_url_rule('/upload_image', view_func=upload_view, methods=['POST'])

    bboxes_view = Bboxes.as_view('bboxes', {'cfg': app.config, 'logger': app.logger})
    app.add_url_rule('/bboxes', view_func=bboxes_view, methods=['GET'])

    wf_update_status_view = WorkflowStatusUpdate.as_view('wf_update_status', {'cfg': app.config, 'logger': app.logger})
    app.add_url_rule('/wf_update_status', view_func=wf_update_status_view, methods=['POST', 'GET'])

    wf_trigger_view = WfTrigger.as_view('wf_trigger', {'cfg': app.config, 'logger': app.logger})
    app.add_url_rule('/wf_trigger', view_func=wf_trigger_view, methods=['POST'])

    app.add_url_rule("/healthcheck", "healthcheck", view_func=lambda: health.run())

    ## base url
    @app.route('/')
    def base():
        return 'Hello, OCR-BFF!/n'

    atexit.register(lambda: scheduler.shutdown())
    return app

