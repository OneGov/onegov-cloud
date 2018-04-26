from collections import OrderedDict
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.mixins import DerivedAttributesMixin
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
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
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class Election(Base, ContentMixin, TimestampMixin,
               DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
               DerivedAttributesMixin):

    __tablename__ = 'elections'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<http://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'majorz'
    }

    #: Identifies the election, may be used in the url
    id = Column(Text, primary_key=True)

    #: all translations of the title
    title_translations = Column(HSTORE, nullable=False)

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations):
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode = Column(Text, nullable=True)

    #: The date of the election
    date = Column(Date, nullable=False)

    #: Number of mandates
    number_of_mandates = Column(Integer, nullable=False, default=lambda: 0)

    @property
    def allocated_mandates(self):
        """ Number of already allocated mandates/elected candidates. """

        results = object_session(self).query(
            func.count(
                func.nullif(Candidate.elected, False)
            )
        )
        results = results.filter(Candidate.election_id == self.id)

        mandates = results.first()
        return mandates and mandates[0] or 0

    #: Absolute majority
    absolute_majority = Column(Integer, nullable=True, default=lambda: 0)

    @hybrid_property
    def counted(self):
        """ True if all results have been counted. """

        count = self.results.count()
        if not count:
            return False

        return (sum(1 for r in self.results if r.counted) == count)

    @counted.expression
    def counted(cls):
        expr = select([
            func.coalesce(func.bool_and(ElectionResult.counted), False)
        ])
        expr = expr.where(ElectionResult.election_id == cls.id)
        expr = expr.label('counted')

        return expr

    @property
    def progress(self):
        """ Returns a tuple with the first value being the number of counted
        election results and the second value being the number of total
        results.

        """

        query = object_session(self).query(ElectionResult)
        query = query.with_entities(ElectionResult.counted)
        query = query.filter(ElectionResult.election_id == self.id)

        results = query.all()

        return sum(1 for r in results if r[0]), len(results)

    @property
    def has_results(self):
        """ Returns True, if the election has any results. """

        for result in self.results:
            if result.counted:
                return True

        return False

    #: An election contains n candidates
    candidates = relationship(
        'Candidate',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='Candidate.candidate_id',
    )

    #: An election contains n results, one for each political entity
    results = relationship(
        'ElectionResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='ElectionResult.district, ElectionResult.name',
    )

    #: The total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    #: The total recceived ballots
    received_ballots = summarized_property('received_ballots')

    #: The total accounted ballots
    accounted_ballots = summarized_property('accounted_ballots')

    #: The total blank ballots
    blank_ballots = summarized_property('blank_ballots')

    #: The total invalid ballots
    invalid_ballots = summarized_property('invalid_ballots')

    #: The total accounted votes
    accounted_votes = summarized_property('accounted_votes')

    def aggregate_results(self, attribute):
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(result, attribute) for result in self.results)

    @staticmethod
    def aggregate_results_expression(cls, attribute):
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([func.sum(getattr(ElectionResult, attribute))])
        expr = expr.where(ElectionResult.election_id == cls.id)
        expr = expr.label(attribute)
        return expr

    @property
    def last_modified(self):
        """ Returns last change of the election, its candidates and any of its
        results.

        """
        candidates = object_session(self).query(Candidate.last_change)
        candidates = candidates.order_by(desc(Candidate.last_change))
        candidates = candidates.filter(Candidate.election_id == self.id)
        candidates = candidates.first()[0] if candidates.first() else None

        changes = [candidates, self.last_change, self.last_result_change]
        changes = [change for change in changes if change]
        return max(changes) if changes else None

    @property
    def last_result_change(self):
        """ Returns the last change of the results of the election and the
        candidates.

        """

        session = object_session(self)

        results = session.query(ElectionResult.last_change)
        results = results.order_by(desc(ElectionResult.last_change))
        results = results.filter(ElectionResult.election_id == self.id)
        results = results.first()[0] if results.first() else None

        ids = session.query(Candidate.id)
        ids = ids.filter(Candidate.election_id == self.id).all()
        if not ids:
            return results

        candidates = session.query(CandidateResult.last_change)
        candidates = candidates.order_by(desc(CandidateResult.last_change))
        candidates = candidates.filter(CandidateResult.candidate_id.in_(ids))
        candidates = candidates.first()[0] if candidates.first() else None

        changes = [change for change in (results, candidates) if change]
        return max(changes) if changes else None

    @property
    def elected_candidates(self):
        """ Returns the first and last names of the elected candidates. """

        results = object_session(self).query(
            Candidate.first_name,
            Candidate.family_name
        )
        results = results.filter(
            Candidate.election_id == self.id,
            Candidate.elected.is_(True)
        )
        results = results.order_by(
            Candidate.family_name,
            Candidate.first_name
        )

        return [(r.first_name, r.family_name) for r in results]

    #: may be used to store a link related to this election
    related_link = meta_property('related_link')

    #: may be used to mark an election as a tacit election
    tacit = meta_property('tacit', default=False)

    #: may be used to mark an election as distinct, e.g. a regional election
    #: containing only the municipalities of one district of a canton.
    distinct = meta_property('distinct', default=True)

    def clear_results(self):
        """ Clears all the results. """

        self.absolute_majority = None
        self.status = None

        session = object_session(self)
        for candidate in self.candidates:
            session.delete(candidate)
        for result in self.results:
            session.delete(result)

    def export(self):
        """ Returns all data connected to this election as list with dicts.

        This is meant as a base for json/csv/excel exports. The result is
        therefore a flat list of dictionaries with repeating values to avoid
        the nesting of values. Each record in the resulting list is a single
        candidate result for each political entity. Party results are not
        included in the export (since they are not really connected with the
        lists).

        """

        session = object_session(self)

        ids = session.query(ElectionResult.id)
        ids = ids.filter(ElectionResult.election_id == self.id)

        results = session.query(
            CandidateResult.votes,
            Election.title_translations,
            Election.date,
            Election.domain,
            Election.type,
            Election.number_of_mandates,
            Election.absolute_majority,
            Election.status,
            ElectionResult.district,
            ElectionResult.name,
            ElectionResult.entity_id,
            ElectionResult.counted,
            ElectionResult.eligible_voters,
            ElectionResult.received_ballots,
            ElectionResult.blank_ballots,
            ElectionResult.invalid_ballots,
            ElectionResult.unaccounted_ballots,
            ElectionResult.accounted_ballots,
            ElectionResult.blank_votes,
            ElectionResult.invalid_votes,
            ElectionResult.accounted_votes,
            Candidate.family_name,
            Candidate.first_name,
            Candidate.candidate_id,
            Candidate.elected,
            Candidate.party,
        )
        results = results.outerjoin(CandidateResult.candidate)
        results = results.outerjoin(CandidateResult.election_result)
        results = results.outerjoin(Candidate.election)
        results = results.filter(CandidateResult.election_result_id.in_(ids))
        results = results.order_by(
            ElectionResult.district,
            ElectionResult.name,
            Candidate.family_name,
            Candidate.first_name
        )

        rows = []
        for result in results:
            row = OrderedDict()
            for locale, title in (result[1] or {}).items():
                row['election_title_{}'.format(locale)] = (title or '').strip()
            row['election_date'] = result[2].isoformat()
            row['election_domain'] = result[3]
            row['election_type'] = result[4]
            row['election_mandates'] = result[5]
            row['election_absolute_majority'] = result[6]
            row['election_status'] = result[7] or 'unknown'

            row['entity_district'] = result[8] or ''
            row['entity_name'] = result[9]
            row['entity_id'] = result[10]
            row['entity_counted'] = result[11]
            row['entity_eligible_voters'] = result[12]
            row['entity_received_ballots'] = result[13]
            row['entity_blank_ballots'] = result[14]
            row['entity_invalid_ballots'] = result[15]
            row['entity_unaccounted_ballots'] = result[16]
            row['entity_accounted_ballots'] = result[17]
            row['entity_blank_votes'] = result[18]
            row['entity_invalid_votes'] = result[19]
            row['entity_accounted_votes'] = result[20]

            row['candidate_family_name'] = result[21]
            row['candidate_first_name'] = result[22]
            row['candidate_id'] = result[23]
            row['candidate_elected'] = result[24]
            row['candidate_party'] = result[25]
            row['candidate_votes'] = result[0]

            rows.append(row)

        return rows
