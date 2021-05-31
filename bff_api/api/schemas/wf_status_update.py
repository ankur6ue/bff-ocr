"""
Schema definition
"""
from marshmallow import Schema, validate, fields, ValidationError


class WfPostStatusUpdateSchema(Schema):
    job_name = fields.Str(required=True)
    timestamp = fields.DateTime(required=True)
    status_msg = fields.Str(required=True)
    is_completed = fields.Boolean(required=True)
    success = fields.Boolean(required=True)

class WfGetStatusUpdateSchema(Schema):
    job_name = fields.Str(required=True)