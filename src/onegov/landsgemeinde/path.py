from onegov.core.converters import extended_date_converter
from onegov.landsgemeinde.app import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.collections import VotumCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models import PersonFunctionSuggestion
from onegov.landsgemeinde.models import PersonNameSuggestion
from onegov.landsgemeinde.models import PersonPlaceSuggestion
from onegov.landsgemeinde.models import PersonPoliticalAffiliationSuggestion
from onegov.landsgemeinde.models import Votum


@LandsgemeindeApp.path(
    model=AssemblyCollection,
    path='/landsgemeinden'
)
def get_assemblies(app):
    return AssemblyCollection(app.session())


@LandsgemeindeApp.path(
    model=Assembly,
    path='/landsgemeinde/{date}',
    converters=dict(date=extended_date_converter)
)
def get_assembly(app, date):
    return AssemblyCollection(app.session()).by_date(date)


@LandsgemeindeApp.path(
    model=AgendaItemCollection,
    path='/traktanden/{date}',
    converters=dict(date=extended_date_converter)
)
def get_agenda_items(app, date):
    return AgendaItemCollection(app.session(), date)


@LandsgemeindeApp.path(
    model=AgendaItem,
    path='/traktandum/{date}/{number}',
    converters=dict(date=extended_date_converter, number=int)
)
def get_agenda_item(app, date, number):
    return AgendaItemCollection(app.session(), date).by_number(number)


@LandsgemeindeApp.path(
    model=VotumCollection,
    path='/vota/{date}/{agenda_item_number}',
    converters=dict(
        date=extended_date_converter,
        agenda_item_number=int
    )
)
def get_vota(app, date, agenda_item_number):
    return VotumCollection(app.session(), date, agenda_item_number)


@LandsgemeindeApp.path(
    model=Votum,
    path='/votum/{date}/{agenda_item_number}/{number}',
    converters=dict(
        date=extended_date_converter,
        agenda_item_number=int,
        number=int
    )
)
def get_votum(app, date, agenda_item_number, number):
    return VotumCollection(
        app.session(), date, agenda_item_number
    ).by_number(number)


@LandsgemeindeApp.path(
    model=PersonFunctionSuggestion,
    path='/suggestion/person/function'
)
def get_person_function_suggestion(app, term=None):
    return PersonFunctionSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonNameSuggestion,
    path='/suggestion/person/name'
)
def get_person_name_suggestion(app, term=None):
    return PersonNameSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonPlaceSuggestion,
    path='/suggestion/person/place'
)
def get_person_place_suggestion(app, term=None):
    return PersonPlaceSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonPoliticalAffiliationSuggestion,
    path='/suggestion/person/political-affiliation'
)
def get_person_political_affiliation_suggestion(app, term=None):
    return PersonPoliticalAffiliationSuggestion(app.session(), term)
