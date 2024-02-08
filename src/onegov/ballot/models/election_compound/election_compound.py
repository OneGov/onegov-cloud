from onegov.ballot.models.election_compound.association import (
    ElectionCompoundAssociation)
from onegov.ballot.models.election_compound.mixins import (
    DerivedAttributesMixin)
from onegov.ballot.models.mixins import DomainOfInfluenceMixin
from onegov.ballot.models.mixins import ExplanationsPdfMixin
from onegov.ballot.models.mixins import LastModifiedMixin
from onegov.ballot.models.mixins import TitleTranslationsMixin
from onegov.ballot.models.party_result.mixins import (
    HistoricalPartyResultsMixin)
from onegov.ballot.models.party_result.mixins import PartyResultsCheckMixin
from onegov.ballot.models.party_result.mixins import PartyResultsOptionsMixin
from onegov.core.orm import Base, observes
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.core.utils import groupbylist
from onegov.file import NamedFile
from sqlalchemy import Column, Boolean
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy.orm import backref
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import datetime
    from collections.abc import Iterable
    from collections.abc import Mapping
    from onegov.ballot.types import DomainOfInfluence
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Session

    from .relationship import ElectionCompoundRelationship
    from ..election import Election
    from ..party_result.party_result import PartyResult
    from ..party_result.party_panachage_result import PartyPanachageResult

    rel = relationship


class ElectionCompound(
    Base, ContentMixin, LastModifiedMixin,
    DomainOfInfluenceMixin, TitleTranslationsMixin,
    PartyResultsOptionsMixin, PartyResultsCheckMixin,
    HistoricalPartyResultsMixin,
    ExplanationsPdfMixin, DerivedAttributesMixin
):

    __tablename__ = 'election_compounds'

    #: Identifies the election compound, may be used in the url
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

    #: The date of the elections
    date: 'Column[datetime.date]' = Column(Date, nullable=False)

    #: Doppelter Pukelsheim
    pukelsheim: 'Column[bool]' = Column(Boolean, nullable=False, default=False)

    #: Allow setting the status of the compound and its elections manually
    completes_manually: 'Column[bool]' = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: Status of the compound and its elections
    manually_completed: 'Column[bool]' = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: An election compound may contains n party results
    party_results: 'rel[AppenderQuery[PartyResult]]' = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        backref=backref('election_compound'),
        lazy='dynamic',
    )

    #: An election compound may contains n party panachage results
    party_panachage_results: 'rel[AppenderQuery[PartyPanachageResult]]'
    party_panachage_results = relationship(
        'PartyPanachageResult',
        cascade='all, delete-orphan',
        backref=backref('election_compound'),
        lazy='dynamic',
    )

    if TYPE_CHECKING:
        # backrefs
        associations: rel[AppenderQuery[ElectionCompoundAssociation]]
        related_compounds: rel[AppenderQuery[ElectionCompoundRelationship]]
        referencing_compounds: rel[AppenderQuery[ElectionCompoundRelationship]]

    #: Defines optional colors for parties
    colors: dict_property[dict[str, str]] = meta_property(
        'colors',
        default=dict
    )

    #: Defines the domain of the elections
    domain_elections: dict_property['DomainOfInfluence'] = meta_property(
        'domain_elections',
        default='district'
    )

    @property
    def elections(self) -> list['Election']:
        elections = (association.election for association in self.associations)
        return sorted(elections, key=lambda x: x.shortcode or '')

    # FIXME: Currently we leverage that this technically accepts a more general
    #        type than the getter (Iterable[Election]), however asymmetric
    #        properties are not supported in mypy, so we would need to define
    #        our own descriptor to actually make this work
    @elections.setter
    def elections(self, value: 'Iterable[Election]') -> None:
        self.associations = [  # type:ignore[assignment]
            ElectionCompoundAssociation(election_id=election.id)
            for election in value
        ]

        # update last result change (only newer)
        election_changes = [
            change
            for election in value
            if (change := election.last_result_change)
        ]
        if election_changes:
            new = max(election_changes)
            old = self.last_result_change
            if not old or (old and old < new):
                self.last_result_change = new

    @property
    def session(self) -> 'Session':
        return object_session(self)

    @property
    def progress(self) -> tuple[int, int]:
        """ Returns a tuple with the current progress.

        If the elections define a `domain_supersegment` (i.e. superregions),
        this is the number of fully counted supersegments vs. the total number
        of supersegments.

        If no `domain_supersegment` is defined, this is the number of counted
        elections vs. the total number of elections.

        """

        pairs = sorted(
            (e.domain_supersegment, e.completed)
            for e in self.elections
        )
        grouped = groupbylist(pairs, lambda x: x[0])

        if len(grouped) == 1 and grouped[0][0] == '':
            result = [completed for _, completed in grouped[0][1]]
        else:
            result = [all(c for _, c in segment) for _, segment in grouped]

        return sum(1 for r in result if r), len(result)

    @property
    def has_results(self) -> bool:
        """ Returns True, if the election compound has any results. """

        if self.has_party_results:
            return True
        if self.has_party_panachage_results:
            return True
        for election in self.elections:
            if election.has_results:
                return True

        return False

    @property
    def elected_candidates(self) -> list[tuple[str, str]]:
        """ Returns the first and last names of the elected candidates. """

        result = []
        for election in self.elections:
            result.extend(election.elected_candidates)

        return result

    #: may be used to store a link related to this election
    related_link: dict_property[str | None] = meta_property(
        'related_link'
    )
    related_link_label: dict_property[dict[str, str] | None] = meta_property(
        'related_link_label'
    )

    #: additional file in case of Doppelter Pukelsheim
    upper_apportionment_pdf = NamedFile()

    #: additional file in case of Doppelter Pukelsheim
    lower_apportionment_pdf = NamedFile()

    @property
    def relationships_for_historical_party_results(
        self
    ) -> 'AppenderQuery[ElectionCompoundRelationship]':
        return self.related_compounds

    def clear_results(self) -> None:
        """ Clears all related results. """

        self.last_result_change = None

        session = object_session(self)
        for result in self.party_results:
            session.delete(result)

        for panache_result in self.party_panachage_results:
            session.delete(panache_result)

        for election in self.elections:
            election.clear_results()
