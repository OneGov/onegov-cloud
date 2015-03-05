from delorean import Delorean
from onegov.core.orm.types import UTCDateTime
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column


class TimestampMixin(object):
    """ Mixin providing created/modified timestamps for all records.

    The columns are deferred loaded as this is primarily for logging and future
    forensics.

    """

    @staticmethod
    def timestamp():
        return Delorean().datetime

    @declared_attr
    def created(cls):
        return deferred(Column(UTCDateTime, default=cls.timestamp))

    @declared_attr
    def modified(cls):
        return deferred(Column(UTCDateTime, onupdate=cls.timestamp))
