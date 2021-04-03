"""
Helper functions
"""
from flask import jsonify


def register_error_handlers(app):
    """
    Regisers error handlers
    """
    app.register_error_handler(InternalServerError, handle_invalid_usage)


def handle_invalid_usage(error):
    """
    Invalid usage handler
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


class InternalServerError(Exception):
    """
    Custom Exception Definition
    """
    status_code = 500

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv
