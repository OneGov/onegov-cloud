from onegov.ballot.models.vote.ballot_result import BallotResult
from onegov.ballot.models.vote.ballot import Ballot
from onegov.ballot.models.vote.mixins import DerivedBallotsCountMixin
from collections import OrderedDict
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import HSTORE
from onegov.core.utils import increment_name
from onegov.core.utils import normalize_for_url
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


class Vote(Base, TimestampMixin, DerivedBallotsCountMixin,
           DomainOfInfluenceMixin, ContentMixin, StatusMixin):
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

    #: title of the vote
    title_translations = Column(HSTORE, nullable=False)
    title = translation_hybrid(title_translations)

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

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            id = normalize_for_url(self.title) or 'vote'
            session = object_session(self)
            while session.query(Vote.id).filter(Vote.id == id).first():
                id = increment_name(id)
            self.id = id

    @property
    def counted(self):
        if not self.ballots.first():
            return False

        for ballot in self.ballots:
            if not ballot.counted:
                return False

        return True

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

    #: the total elegible voters
    elegible_voters = summarized_property('elegible_voters')

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
    def last_result_change(self):
        """ Gets the latest created/modified date of the vote or amongst the
        results of this vote.

        """

        last_changes = []
        if self.last_change:
            last_changes.append(self.last_change)

        session = object_session(self)

        ballots = session.query(Ballot)
        ballots = ballots.filter(Ballot.vote_id == self.id)
        ballots = ballots.all()
        for ballot in ballots:
            last_changes.append(ballot.last_change)

        ballot_ids = [ballot.id for ballot in ballots]
        if ballot_ids:
            results = session.query(BallotResult)
            results = results.with_entities(BallotResult.last_change)
            results = results.order_by(desc(BallotResult.last_change))
            results = results.filter(BallotResult.ballot_id.in_(ballot_ids))

            last_change = results.first()
            if last_change:
                last_changes.append(last_change[0])

        if not len(last_changes):
            return None

        return max(last_changes)

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
                row['group'] = result.group
                row['entity_id'] = result.entity_id
                row['counted'] = result.counted
                row['yeas'] = result.yeas
                row['nays'] = result.nays
                row['invalid'] = result.invalid
                row['empty'] = result.empty
                row['elegible_voters'] = result.elegible_voters

                rows.append(row)

        return rows
