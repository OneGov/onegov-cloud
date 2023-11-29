from onegov.ballot.models.election.candidate import Candidate
from onegov.ballot.models.election.election_result import ElectionResult
from onegov.ballot.models.election.mixins import DerivedAttributesMixin
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import StatusMixin
from onegov.ballot.models.mixins import summarized_property
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.party_result.mixins import PartyResultsOptionsMixin
from onegov.core.orm import Base
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from collections.abc import Mapping
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Query
    from sqlalchemy.sql import ColumnElement
    from typing import NamedTuple

    from .relationship import ElectionRelationship
    from ..election_compound import ElectionCompoundAssociation

    class VotesByDistrictRow(NamedTuple):
        election_id: str
        district: str
        entities: list[int]
        counted: bool
        votes: int


class Election(Base, ContentMixin, LastModifiedMixin,
               DomainOfInfluenceMixin, StatusMixin, TitleTranslationsMixin,
               DerivedAttributesMixin, ExplanationsPdfMixin,
               PartyResultsOptionsMixin):

    __tablename__ = 'elections'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    # FIXME: is this actually nullable? The polymorphic identity seems
    #        to suggest otherwise...
    type: 'Column[str | None]' = Column(Text, nullable=True)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'majorz'
    }

    #: Identifies the election, may be used in the url
    id: 'Column[str]' = Column(Text, primary_key=True)

    #: external identifier
    external_id: 'Column[str | None]' = Column(Text, nullable=True)

    #: all translations of the title
    title_translations: 'Column[Mapping[str, str]]' = Column(
        HSTORE,
        nullable=False
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    @observes('title_translations')
    def title_observer(self, translations: 'Mapping[str, str]') -> None:
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode: 'Column[str | None]' = Column(Text, nullable=True)

    #: The date of the election
    date: 'Column[datetime.date]' = Column(Date, nullable=False)

    #: Number of mandates
    number_of_mandates: 'Column[int]' = Column(
        Integer,
        nullable=False,
        default=lambda: 0
    )

    @property
    def allocated_mandates(self) -> int:
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
    majority_type: dict_property[str | None] = meta_property('majority_type')

    #: Absolute majority
    absolute_majority: 'Column[int | None]' = Column(Integer, nullable=True)

    if TYPE_CHECKING:
        counted: Column[bool]

    @hybrid_property  # type:ignore[no-redef]
    def counted(self) -> bool:
        """ True if all results have been counted. """

        count = self.results.count()
        if not count:
            return False

        return (sum(1 for r in self.results if r.counted) == count)

    @counted.expression  # type:ignore[no-redef]
    def counted(cls) -> 'ColumnElement[bool]':
        expr = select([
            func.coalesce(func.bool_and(ElectionResult.counted), False)
        ])
        expr = expr.where(ElectionResult.election_id == cls.id)
        expr = expr.label('counted')

        return expr

    @property
    def progress(self) -> tuple[int, int]:
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
    def counted_entities(self) -> list[str]:
        """ Returns the names of the already counted entities.

        Might contain an empty string in case of expats.

        """

        query = object_session(self).query(ElectionResult.name)
        query = query.filter(ElectionResult.counted.is_(True))
        query = query.filter(ElectionResult.election_id == self.id)
        query = query.order_by(ElectionResult.name)
        return [result.name for result in query.all()]

    @property
    def has_results(self) -> bool:
        """ Returns True, if the election has any results. """

        for result in self.results:
            if result.counted:
                return True
        return False

    #: An election contains n candidates
    candidates: 'relationship[AppenderQuery[Candidate]]' = relationship(
        'Candidate',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='Candidate.candidate_id',
    )

    #: An election contains n results, one for each political entity
    results: 'relationship[AppenderQuery[ElectionResult]]' = relationship(
        'ElectionResult',
        cascade='all, delete-orphan',
        backref=backref('election'),
        lazy='dynamic',
        order_by='ElectionResult.district, ElectionResult.name',
    )

    if TYPE_CHECKING:
        # backrefs
        associations: relationship[AppenderQuery[ElectionCompoundAssociation]]
        related_elections: relationship[AppenderQuery[ElectionRelationship]]
        referencing_elections: relationship[
            AppenderQuery[ElectionRelationship]]

    #: The total eligible voters
    eligible_voters = summarized_property('eligible_voters')

    #: The expats
    expats = summarized_property('expats')

    #: The total received ballots
    received_ballots = summarized_property('received_ballots')

    #: The total accounted ballots
    accounted_ballots = summarized_property('accounted_ballots')

    #: The total blank ballots
    blank_ballots = summarized_property('blank_ballots')

    #: The total invalid ballots
    invalid_ballots = summarized_property('invalid_ballots')

    #: The total accounted votes
    accounted_votes = summarized_property('accounted_votes')

    def aggregate_results(self, attribute: str) -> int:
        """ Gets the sum of the given attribute from the results. """

        return sum(getattr(result, attribute) or 0 for result in self.results)

    @staticmethod
    def aggregate_results_expression(
        cls: 'Election',
        attribute: str
    ) -> 'ColumnElement[int]':
        """ Gets the sum of the given attribute from the results,
        as SQL expression.

        """

        expr = select([
            func.coalesce(
                func.sum(getattr(ElectionResult, attribute)),
                0
            )
        ])
        expr = expr.where(ElectionResult.election_id == cls.id)
        return expr.label(attribute)

    @property
    def elected_candidates(self) -> list[tuple[str, str]]:
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
    related_link: dict_property[str | None] = meta_property('related_link')
    related_link_label: dict_property[dict[str, str] | None] = meta_property(
        'related_link_label'
    )

    #: may be used to mark an election as a tacit election
    tacit: dict_property[bool] = meta_property('tacit', default=False)

    #: may be used to indicate that the vote contains expats as seperate
    #: results (typically with entity_id = 0)
    has_expats: dict_property[bool] = meta_property('expats', default=False)

    #: The segment of the domain. This might be the district, if this is a
    #: regional (district) election; the region, if it's a regional (region)
    #: election or the municipality, if this is a communal election.
    domain_segment: dict_property[str] = meta_property(
        'domain_segment',
        default=''
    )

    #: The supersegment of the domain. This might be superregion, if it's a
    #: regional (region) election.
    domain_supersegment: dict_property[str] = meta_property(
        'domain_supersegment',
        default=''
    )

    @property
    def votes_by_district(self) -> 'Query[VotesByDistrictRow]':
        query = self.results.order_by(None)
        results = query.with_entities(
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
    colors: dict_property[dict[str, str]] = meta_property(
        'colors',
        default=dict
    )

    def clear_results(self) -> None:
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
