from onegov.core.orm.types import JSON
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import deferred
from sqlalchemy.schema import Column


class ContentMixin(object):
    """ Mixin providing a meta/content JSON pair. Meta is a JSON column loaded
    with each request, content is a JSON column loaded deferred (to be shown
    only in the detail view).

    """

    #: metadata associated with the form, for storing small amounts of data
    @declared_attr
    def meta(cls):
        return Column(JSON, nullable=False, default=dict)

    #: content associated with the form, for storing things like long texts
    @declared_attr
    def content(cls):
        return deferred(Column(JSON, nullable=False, default=dict))
