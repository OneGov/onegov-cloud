from onegov.core.orm.types import JSON
from sqlalchemy import Column, Enum
from sqlalchemy.ext.declarative import declared_attr


class DomainOfInfluenceMixin(object):
    #: defines the scope of the vote - eCH-0155 calls this the domain of
    #: influence. Unlike eCH-0155 we refrain from putting this in a separate
    #: model. We also only include domains we currently support.
    domain = Column(
        Enum(
            'federation',
            'canton',
            name='domain_of_influence'
        ),
        nullable=False
    )


class MetaMixin(object):
    """ Mixin providing a meta/content JSON pair. Meta is a JSON column loaded
    with each request, content is a JSON column loaded deferred (to be shown
    only in the detail view).

    """

    #: metadata associated with the form, for storing small amounts of data
    @declared_attr
    def meta(cls):
        return Column(JSON, nullable=False, default=dict)
