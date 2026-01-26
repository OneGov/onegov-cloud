from __future__ import annotations

from onegov.core.orm import Base, observes
from onegov.core.orm import translation_hybrid
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.types import HSTORE
from onegov.core.utils import groupbylist
from onegov.election_day.models.election_compound.mixins import (
    DerivedAttributesMixin)
from onegov.election_day.models.mixins import DomainOfInfluenceMixin
from onegov.election_day.models.mixins import ExplanationsPdfMixin
from onegov.election_day.models.mixins import IdFromTitlesMixin
from onegov.election_day.models.mixins import LastModifiedMixin
from onegov.election_day.models.mixins import TitleTranslationsMixin
from onegov.election_day.models.party_result.mixins import (
    HistoricalPartyResultsMixin)
from onegov.election_day.models.party_result.mixins import (
    PartyResultsCheckMixin)
from onegov.election_day.models.party_result.mixins import (
    PartyResultsOptionsMixin)
from onegov.file import NamedFile
from operator import itemgetter
from sqlalchemy import Column, Boolean
from sqlalchemy import Date
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from sqlalchemy.orm import relationship


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from collections.abc import Mapping
    from onegov.core.types import AppenderQuery
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompoundRelationship
    from onegov.election_day.models import Notification
    from onegov.election_day.models import PartyPanachageResult
    from onegov.election_day.models import PartyResult
    from onegov.election_day.models import Screen
    from onegov.election_day.types import DomainOfInfluence
    import datetime

    rel = relationship


class ElectionCompound(
    Base, ContentMixin, LastModifiedMixin,
    DomainOfInfluenceMixin, TitleTranslationsMixin, IdFromTitlesMixin,
    PartyResultsOptionsMixin, PartyResultsCheckMixin,
    HistoricalPartyResultsMixin,
    ExplanationsPdfMixin, DerivedAttributesMixin
):

    __tablename__ = 'election_compounds'

    @property
    def polymorphic_base(self) -> type[ElectionCompound]:
        return ElectionCompound

    #: Identifies the election compound, may be used in the url
    id: Column[str] = Column(Text, primary_key=True)

    #: external identifier
    external_id: Column[str | None] = Column(Text, nullable=True)

    #: all translations of the title
    title_translations: Column[Mapping[str, str]] = Column(
        HSTORE,
        nullable=False
    )

    #: the translated title (uses the locale of the request, falls back to the
    #: default locale of the app)
    title = translation_hybrid(title_translations)

    #: all translations of the short title
    short_title_translations: Column[Mapping[str, str] | None] = Column(
        HSTORE,
        nullable=True
    )

    #: the translated short title (uses the locale of the request, falls back
    #: to the default locale of the app)
    short_title = translation_hybrid(short_title_translations)

    @observes('title_translations', 'short_title_translations')
    def title_observer(
        self,
        title_translations: Mapping[str, str],
        short_title_translations: Mapping[str, str]
    ) -> None:
        if not self.id:
            self.id = self.id_from_title(object_session(self))

    #: Shortcode for cantons that use it
    shortcode: Column[str | None] = Column(Text, nullable=True)

    #: The date of the elections
    date: Column[datetime.date] = Column(Date, nullable=False)

    #: Doppelter Pukelsheim
    pukelsheim: Column[bool] = Column(Boolean, nullable=False, default=False)

    #: Allow setting the status of the compound and its elections manually
    completes_manually: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: Status of the compound and its elections
    manually_completed: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: An election compound may contains n party results
    party_results: relationship[list[PartyResult]] = relationship(
        'PartyResult',
        cascade='all, delete-orphan',
        back_populates='election_compound',
        overlaps='party_results'  # type: ignore[call-arg]
    )

    #: An election compound may contains n party panachage results
    party_panachage_results: rel[list[PartyPanachageResult]] = (
        relationship(
            'PartyPanachageResult',
            cascade='all, delete-orphan',
            back_populates='election_compound',
            overlaps='panachage_results'  # type: ignore[call-arg]
        )
    )

    #: An election compound may have related election compounds
    related_compounds: rel[AppenderQuery[ElectionCompoundRelationship]] = (
        relationship(
            'ElectionCompoundRelationship',
            foreign_keys='ElectionCompoundRelationship.source_id',
            cascade='all, delete-orphan',
            back_populates='source',
            lazy='dynamic'
        )
    )

    #: An election compound may be related by other election compounds
    referencing_compounds: rel[AppenderQuery[ElectionCompoundRelationship]] = (
        relationship(
            'ElectionCompoundRelationship',
            foreign_keys='ElectionCompoundRelationship.target_id',
            cascade='all, delete-orphan',
            back_populates='target',
            lazy='dynamic'
        )
    )

    #: Defines optional colors for parties
    colors: dict_property[dict[str, str]] = meta_property(
        'colors',
        default=dict
    )

    #: Defines the domain of the elections
    domain_elections: dict_property[DomainOfInfluence] = meta_property(
        'domain_elections',
        default='district'
    )

    #: An election compound may contain n elections
    elections: relationship[list[Election]] = relationship(
        'Election',
        cascade='all',
        back_populates='election_compound',
        order_by='Election.shortcode'
    )

    @observes('elections')
    def elections_observer(
        self,
        elections: Collection[Election]
    ) -> None:
        changes = {c for e in elections if (c := e.last_result_change)}
        if changes:
            new = max(changes)
            old = self.last_result_change
            if not old or (old and old < new):
                self.last_result_change = new

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
        grouped = groupbylist(pairs, itemgetter(0))

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

    #: notifcations linked to this election compound
    notifications: relationship[AppenderQuery[Notification]] = (
        relationship(  # type:ignore[misc]
            'onegov.election_day.models.notification.Notification',
            back_populates='election_compound',
            lazy='dynamic'
        )
    )

    #: screens linked to this election compound
    screens: relationship[AppenderQuery[Screen]] = relationship(
        'Screen',
        back_populates='election_compound',
    )

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
    ) -> AppenderQuery[ElectionCompoundRelationship]:
        return self.related_compounds

    def clear_results(self, clear_all: bool = False) -> None:
        """ Clears all related results. """

        self.last_result_change = None

        self.party_results = []
        self.party_panachage_results = []

        for election in self.elections:
            election.clear_results(clear_all)
