"""
Schema definition
"""
from marshmallow import Schema, validate, fields, ValidationError
from ...utils.allowed_extensions import ALLOWED_EXTENSIONS


def image(image_str):
    """Return email_str if valid, raise an exception in other case."""
    extension = image_str.rsplit('.', 1)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError('{} is not a valid image extension'.format(image_str))
    return image_str


class BboxesSchema(Schema):
    file_name = fields.Str(validate=image, required=True)
