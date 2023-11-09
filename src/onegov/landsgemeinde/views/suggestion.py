from onegov.core.security import Private
from onegov.landsgemeinde import LandsgemeindeApp
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion


@LandsgemeindeApp.json(
    model=PersonFunctionSuggestion,
    permission=Private
)
def suggest_person_function(self, request):
    return self.query()


@LandsgemeindeApp.json(
    model=PersonNameSuggestion,
    permission=Private
)
def suggest_person_name(self, request):
    return self.query()


@LandsgemeindeApp.json(
    model=PersonPlaceSuggestion,
    permission=Private
)
def suggest_person_place(self, request):
    return self.query()


@LandsgemeindeApp.json(
    model=PersonPoliticalAffiliationSuggestion,
    permission=Private
)
def suggest_person_political_affiliation(self, request):
    return self.query()
