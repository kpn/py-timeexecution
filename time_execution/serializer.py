"""
Module copied from elasticsearch package to serialize data in same way as elasticsearch does.
Link: https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/serializer.py#L24
"""
import json
import uuid
from datetime import date, datetime
from decimal import Decimal

from six import string_types


class SerializationError(Exception):
    pass


class JSONSerializer(object):
    def default(self, data):
        if isinstance(data, (date, datetime)):
            return data.isoformat()
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, uuid.UUID):
            return str(data)
        raise TypeError("Unable to serialize %r (type: %s)" % (data, type(data)))

    def loads(self, s):
        try:
            return json.loads(s)
        except (ValueError, TypeError) as e:
            raise SerializationError(s, e)

    def dumps(self, data):
        # don't serialize strings
        if isinstance(data, string_types):
            return data

        try:
            return json.dumps(data, default=self.default, ensure_ascii=False, separators=(',', ':'))
        except (ValueError, TypeError) as e:
            raise SerializationError(data, e)
