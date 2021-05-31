"""
Schema definition
"""
from marshmallow import Schema, validate, fields, ValidationError


class WfTriggerSchema(Schema):
    image_list = fields.String(required=True)

