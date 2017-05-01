from onegov.core.orm.types import JSON
from sqlalchemy import Column, Enum
from sqlalchemy.ext.declarative import declared_attr


class DomainOfInfluenceMixin(object):
    """ Defines the defines the scope of the election or vote - eCH-0155 calls
    this the domain of influence. Unlike eCH-0155 we refrain from putting this
    in a separate model. We also only include domains we currently support.

    """

    #: scope of the election or vote
    @declared_attr
    def domain(cls):
        return Column(
            Enum(
                'federation',
                'canton',
                'municipality',
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


class StatusMixin(object):
    """ Mixin providing status indication for votes and elections."""

    #: Status of the election or vote
    @declared_attr
    def status(cls):
        return Column(
            Enum(
                'unknown',
                'interim',
                'final',
                name='election_or_vote_status'
            ),
            nullable=True
        )

    @property
    def completed(self):
        """ Returns True, if the election or vote is completed.

        The status is evaluated in the first place. If the status is not known,
        it is guessed from the progress / counted fields.

        """

        if self.status == 'final':
            return True
        if self.status == 'interim':
            return False

        if self.progress[1] == 0:
            return False

        return self.counted
