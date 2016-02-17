from sqlalchemy import Column, Enum


class DomainOfInfluenceMixin(object):
    """ tbd
    """

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
