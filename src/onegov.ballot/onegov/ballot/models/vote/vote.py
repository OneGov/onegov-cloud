from collections import OrderedDict
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.vote.ballot import Ballot
from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class Vote(Base, ContentMixin, TimestampMixin,
           DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
           DerivedBallotsCountMixin):
    """ A vote describes the issue being voted on. For example,
    "Vote for Net Neutrality" or "Vote for Basic Income".

    """

    __tablename__ = 'votes'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'simple'
    }

    #: identifies the vote, may be used in the url, generated from the title
    id = Column(Text, primary_key=True)

    #: shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: all translations of the title
    title_translations = Column(HSTORE, nullable=False)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: identifies the date of the vote
    date = Column(Date, nullable=False)

    #: a vote contains n ballots
    ballots = relationship(
        'Ballot',
        cascade='all, delete-orphan',
        order_by='Ballot.type',
        backref=backref('vote'),
        lazy='dynamic'
    )

    def ballot(self, ballot_type, create=False):
        """ Returns the given ballot if it exists. Optionally creates the
        ballot.

        """

        result = [b for b in self.ballots if b.type == ballot_type]
        result = result[0] if result else None

        if not result and create:
            result = Ballot(type=ballot_type)
            self.ballots.append(result)

        return result

    @property
    def proposal(self):
        return self.ballot('proposal', create=True)

    @property
    def counted(self):
        """ Checks if there are results for all entitites. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

    @property
    def has_results(self):
        """ Returns True, if there are any results. """

        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            for result in ballot.results:
                if result.counted:
                    return True

        return False

    @property
    def answer(self):
        if not self.counted or not self.proposal:
            return None

        return 'accepted' if self.proposal.accepted else 'rejected'

    @property
    def yeas_percentage(self):
        """ The percentage of yeas (discounts empty/invalid ballots). """

        return self.yeas / ((self.yeas + self.nays) or 1) * 100

    @property
    def nays_percentage(self):
        """ The percentage of nays (discounts empty/invalid ballots). """

        return 100 - self.yeas_percentage

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        entities and the second value being the number of total entities.

        """

        ballot_ids = set(b.id for b in self.ballots)

        if not ballot_ids:
            return 0, 0

        query = object_session(self).query(BallotResult)
        query = query.with_entities(BallotResult.counted)
        query = query.filter(BallotResult.ballot_id.in_(ballot_ids))

        results = query.all()
        divider = len(ballot_ids) or 1

        return (
            int(sum(1 for r in results if r[0]) / divider),
            int(len(results) / divider)
        )

    #: the total yeas
    yeas = summarized_property('yeas')

    #: the total nays
    nays = summarized_property('nays')

    #: the total empty votes
    empty = summarized_property('empty')

    #: the total invalid votes
    invalid = summarized_property('invalid')

    #: the total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(ballot, attribute) for ballot in self.ballots)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(Ballot, attribute))])
        expr = expr.where(Ballot.vote_id == cls.id)
        expr = expr.label(attribute)

        return expr

    @property
    def last_modified(self):
        """ Returns last change of the vote, its ballots and any of its
        results.

        """
        ballots = object_session(self).query(Ballot.last_change)
        ballots = ballots.order_by(desc(Ballot.last_change))
        ballots = ballots.filter(Ballot.vote_id == self.id)
        ballots = ballots.first()[0] if ballots.first() else None

        changes = [ballots, self.last_change, self.last_result_change]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def last_result_change(self):
        """ Returns the last change of the results of the vote. """

        session = object_session(self)
        ballot_ids = session.query(Ballot.id)
        ballot_ids = ballot_ids.filter(Ballot.vote_id == self.id).all()
        if not ballot_ids:
            return None

        results = session.query(BallotResult.last_change)
        results = results.order_by(desc(BallotResult.last_change))
        results = results.filter(BallotResult.ballot_id.in_(ballot_ids))
        return results.first()[0] if results.first() else None

    #: may be used to store a link related to this vote
    related_link = meta_property('related_link')

    def clear_results(self):
        """ Clear all the results. """

        self.status = None

        for ballot in self.ballots:
            ballot.clear_results()

    def export(self):
        """ Returns all data connected to this vote as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        ballot result.

        """

        rows = []

        for ballot in self.ballots:
            for result in ballot.results:
                row = OrderedDict()

                titles = (
                    ballot.title_translations or self.title_translations or {}
                )
                for locale, title in titles.items():
                    row['title_{}'.format(locale)] = (title or '').strip()
                row['date'] = self.date.isoformat()
                row['shortcode'] = self.shortcode
                row['domain'] = self.domain
                row['status'] = self.status or 'unknown'
                row['type'] = ballot.type
                row['district'] = result.district or ''
                row['name'] = result.name
                row['entity_id'] = result.entity_id
                row['counted'] = result.counted
                row['yeas'] = result.yeas
                row['nays'] = result.nays
                row['invalid'] = result.invalid
                row['empty'] = result.empty
                row['eligible_voters'] = result.eligible_voters

                rows.append(row)

        return rows
