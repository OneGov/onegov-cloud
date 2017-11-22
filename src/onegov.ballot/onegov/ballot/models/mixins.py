from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property


class DomainOfInfluenceMixin(object):
    """ Defines the scope of the election or vote - eCH-0155 calls this the
    domain of influence. Unlike eCH-0155 we refrain from putting this in a
    separate model. We also only include domains we currently support.

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


def summarized_property(name):
    """ Adds an attribute as hybrid_property which returns the sum of the
    underlying results if called.

    Requires the class to define two aggregation functions.

    Usage::

        class Model():
            votes = summarized_property('votes')

            results = relationship('Result', ...)

            def aggregate_results(self, attribute):
                return sum(getattr(res, attribute) for res in self.results)

            @staticmethod
            def aggregate_results_expression(cls, attribute):
                expr = select([func.sum(getattr(Result, attribute))])
                expr = expr.where(Result.xxx_id == cls.id)
                expr = expr.label(attribute)
                return expr

    """

    def getter(self):
        return self.aggregate_results(name)

    def expression(cls):
        return cls.aggregate_results_expression(cls, name)

    return hybrid_property(getter, expr=expression)
