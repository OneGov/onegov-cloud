from __future__ import annotations

from onegov.core.security import Private
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.landsgemeinde.request import LandsgemeindeRequest


@LandsgemeindeApp.json(
    model=PersonFunctionSuggestion,
    permission=Private
)
def suggest_person_function(
    self: PersonFunctionSuggestion,
    request: LandsgemeindeRequest
) -> JSON_ro:
    return self.query()


@LandsgemeindeApp.json(
    model=PersonNameSuggestion,
    permission=Private
)
def suggest_person_name(
    self: PersonNameSuggestion,
    request: LandsgemeindeRequest
) -> JSON_ro:
    return self.query()


@LandsgemeindeApp.json(
    model=PersonPlaceSuggestion,
    permission=Private
)
def suggest_person_place(
    self: PersonPlaceSuggestion,
    request: LandsgemeindeRequest
) -> JSON_ro:
    return self.query()


@LandsgemeindeApp.json(
    model=PersonPoliticalAffiliationSuggestion,
    permission=Private
)
def suggest_person_political_affiliation(
    self: PersonPoliticalAffiliationSuggestion,
    request: LandsgemeindeRequest
) -> JSON_ro:
    return self.query()
