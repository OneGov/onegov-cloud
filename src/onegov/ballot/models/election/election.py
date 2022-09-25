from collections import OrderedDict
from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.candidate_result import CandidateResult
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.mixins import DerivedAttributesMixin
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import select
from sqlalchemy import Text
from sqlalchemy_utils import observes
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


class Election(Base, ContentMixin, LastModifiedMixin,
               DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
               DerivedAttributesMixin, ExplanationsPdfMixin):

    __tablename__ = 'elections'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
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

        # Unless an election is finished, allocated mandates are 0
        if not self.completed:
            return 0

        results = object_session(self).query(
            func.count(
                func.nullif(Candidate.elected, False)
            )
        )
        results = results.filter(Candidate.election_id == self.id)

        mandates = results.first()
        return mandates and mandates[0] or 0

    #: Defines the type of majority (e.g. 'absolute', 'relative')
    majority_type = meta_property('majority_type')

    #: Absolute majority
    absolute_majority = Column(Integer, nullable=True)

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
    def counted_entities(self):
        """ Returns the names of the already counted entities. """

        query = object_session(self).query(ElectionResult.name)
        query = query.filter(ElectionResult.counted.is_(True))
        query = query.filter(ElectionResult.election_id == self.id)
        query = query.order_by(ElectionResult.name)
        return [result.name for result in query.all() if result.name]

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

    # sum of eligible voters of only if ElectionResult.counted is true
    counted_eligible_voters = summarized_property('counted_eligible_voters')

    #: The expats
    expats = summarized_property('expats')

    #: The total received ballots
    received_ballots = summarized_property('received_ballots')

    #: The total of all counted balled where ElectionResult.counted is true
    counted_received_ballots = summarized_property('counted_received_ballots')

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

        return sum(getattr(result, attribute) or 0 for result in self.results)

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
    related_link_label = meta_property('related_link_label')

    #: may be used to mark an election as a tacit election
    tacit = meta_property('tacit', default=False)

    #: may be used to indicate that the vote contains expats as seperate
    #: results (typically with entity_id = 0)
    has_expats = meta_property('expats', default=False)

    #: The segment of the domain. This might be the district, if this is a
    #: regional (district) election; the region, if it's a regional (region)
    #: election or the municipality, if this is a communal election.
    domain_segment = meta_property('domain_segment', default='')

    #: The supersegment of the domain. This might be superregion, if it's a
    #: regional (region) election.
    domain_supersegment = meta_property('domain_supersegment', default='')

    @property
    def votes_by_district(self):
        results = self.results.order_by(None)
        results = results.with_entities(
            self.__class__.id.label('election_id'),
            ElectionResult.district,
            func.array_agg(
                ElectionResult.entity_id.distinct()).label('entities'),
            func.coalesce(
                func.bool_and(ElectionResult.counted), False
            ).label('counted'),
            func.coalesce(
                func.sum(ElectionResult.accounted_ballots), 0).label('votes')
        )
        results = results.group_by(
            ElectionResult.district,
            self.__class__.id.label('election_id')
        )
        return results

    #: Defines optional colors for lists and parties
    colors = meta_property('colors', default=dict)

    def clear_results(self):
        """ Clears all the results. """

        self.absolute_majority = None
        self.status = None
        self.last_result_change = None

        session = object_session(self)
        session.query(Candidate).filter(
            Candidate.election_id == self.id
        ).delete()
        session.query(ElectionResult).filter(
            ElectionResult.election_id == self.id
        ).delete()

    def export(self, locales):
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
            ElectionResult.superregion,
            ElectionResult.district,
            ElectionResult.name,
            ElectionResult.entity_id,
            ElectionResult.counted,
            ElectionResult.eligible_voters,
            ElectionResult.expats,
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
            Candidate.gender,
            Candidate.year_of_birth,
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
            translations = result.title_translations or {}
            for locale in locales:
                title = translations.get(locale, '') or ''
                row[f'election_title_{locale}'] = title.strip()
            row['election_date'] = result.date.isoformat()
            row['election_domain'] = result.domain
            row['election_type'] = result.type
            row['election_mandates'] = result.number_of_mandates
            row['election_absolute_majority'] = result.absolute_majority
            row['election_status'] = result.status or 'unknown'
            row['entity_superregion'] = result.superregion or ''
            row['entity_district'] = result.district or ''
            row['entity_name'] = result.name
            row['entity_id'] = result.entity_id
            row['entity_counted'] = result.counted
            row['entity_eligible_voters'] = result.eligible_voters
            row['entity_expats'] = result.expats
            row['entity_received_ballots'] = result.received_ballots
            row['entity_blank_ballots'] = result.blank_ballots
            row['entity_invalid_ballots'] = result.invalid_ballots
            row['entity_unaccounted_ballots'] = result.unaccounted_ballots
            row['entity_accounted_ballots'] = result.accounted_ballots
            row['entity_blank_votes'] = result.blank_votes
            row['entity_invalid_votes'] = result.invalid_votes
            row['entity_accounted_votes'] = result.accounted_votes
            row['candidate_family_name'] = result.family_name
            row['candidate_first_name'] = result.first_name
            row['candidate_id'] = result.candidate_id
            row['candidate_elected'] = result.elected
            row['candidate_party'] = result.party
            row['candidate_gender'] = result.gender or ''
            row['candidate_year_of_birth'] = result.year_of_birth or ''
            row['candidate_votes'] = result.votes
            rows.append(row)

        return rows
