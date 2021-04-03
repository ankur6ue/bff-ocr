# -*- coding: utf-8 -*-
"""
An example flask application showing how to upload a file to S3
while creating a REST API using Flask-Restful.
Note: This method of uploading files is fine for smaller file sizes,
      but uploads should be queued using something like celery for
      larger ones.
"""
from flask import Flask
from flask_cors import CORS
from bff_api.api.resources.signed_url import UploadImage
from bff_api.api.resources.errors import register_error_handlers


# Initialization
def create_app(config, testing=False):
    """Application factory, used to create application"""
    app = Flask("bff_api")
    CORS(app)
    app.config.from_object(config)

    if testing is True:
        app.config["TESTING"] = True
    register_error_handlers(app)
    # register views
    upload_view = UploadImage.as_view('upload_image', {'cfg': app.config, 'logger': app.logger})
    app.add_url_rule('/upload_image', view_func=upload_view, methods=['POST'])
    return app


if __name__ == '__main__':
    app_ = create_app('config')
    app_.run(debug=True, port=5001)
