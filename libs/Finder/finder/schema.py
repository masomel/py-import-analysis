# -*- coding: utf-8 -*-

from datetime import datetime

from marshmallow import Schema, fields

from .__pkg__ import __version__


class DataSchema(Schema):
    """Schema for the data that is searched in the given file paths."""
    line_number = fields.String(default=None)
    line = fields.String(default=None)

    class Meta:
        fields = ('line_number', 'line')
        ordered = True


class ErrorSchema(Schema):
    """Schema for errors."""
    type = fields.String(default=None)
    message = fields.String(default=None)
    extra = fields.String(default=None)

    class Meta:
        fields = ('type', 'message', 'extra')
        ordered = True


class FinderSchema(Schema):
    """Finder API schema."""
    api_version = fields.String(default=__version__)
    requested_on = fields.DateTime(default=datetime.utcnow().isoformat())
    path = fields.String(default=None)
    total_items = fields.String(default=None)
    items = fields.Nested(DataSchema, many=True)
    error = fields.Nested(ErrorSchema, many=True)

    class Meta:
        fields = ('api_version',
                  'requested_on',
                  'path',
                  'total_items',
                  'items',
                  'error')
        ordered = True
