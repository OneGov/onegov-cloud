from onegov.core.orm.types import UTCDateTime
from sedate import utcnow
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy import func
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column
from sqlalchemy.ext.hybrid import hybrid_property


class TimestampMixin(object):
    """ Mixin providing created/modified timestamps for all records.

    The columns are deferred loaded as this is primarily for logging and future
    forensics.

    """

    @staticmethod
    def timestamp():
        return utcnow()

    @declared_attr
    def created(cls):
        return deferred(Column(UTCDateTime, default=cls.timestamp))

    @declared_attr
    def modified(cls):
        return deferred(Column(UTCDateTime, onupdate=cls.timestamp))

    @hybrid_property
    def last_change(self):
        """ Returns the self.modified if not NULL, else self.created. """
        return self.modified or self.created

    @last_change.expression
    def last_change(cls):
        return func.coalesce(cls.modified, cls.created)
