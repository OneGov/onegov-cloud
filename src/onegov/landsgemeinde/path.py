from __future__ import annotations

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
from onegov.org.models import Search


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.landsgemeinde.request import LandsgemeindeRequest


@LandsgemeindeApp.path(
    model=AssemblyCollection,
    path='/assemblies'
)
def get_assemblies(app: LandsgemeindeApp) -> AssemblyCollection:
    return AssemblyCollection(app.session())


@LandsgemeindeApp.path(
    model=Assembly,
    path='/assembly/{date}',
    converters={'date': extended_date_converter}
)
def get_assembly(app: LandsgemeindeApp, date: date) -> Assembly | None:
    return AssemblyCollection(app.session()).by_date(date)


@LandsgemeindeApp.path(
    model=AgendaItemCollection,
    path='/traktanden/{date}',
    converters={'date': extended_date_converter}
)
def get_agenda_items(
    app: LandsgemeindeApp,
    date: date
) -> AgendaItemCollection:
    return AgendaItemCollection(app.session(), date)


@LandsgemeindeApp.path(
    model=AgendaItem,
    path='/traktandum/{date}/{number}',
    converters={'date': extended_date_converter, 'number': int}
)
def get_agenda_item(
    app: LandsgemeindeApp,
    date: date,
    number: int
) -> AgendaItem | None:
    return AgendaItemCollection(app.session(), date).by_number(number)


@LandsgemeindeApp.path(
    model=VotumCollection,
    path='/vota/{date}/{agenda_item_number}',
    converters={
        'date': extended_date_converter,
        'agenda_item_number': int
    }
)
def get_vota(
    app: LandsgemeindeApp,
    date: date,
    agenda_item_number: int
) -> VotumCollection:
    return VotumCollection(app.session(), date, agenda_item_number)


@LandsgemeindeApp.path(
    model=Votum,
    path='/votum/{date}/{agenda_item_number}/{number}',
    converters={
        'date': extended_date_converter,
        'agenda_item_number': int,
        'number': int
    }
)
def get_votum(
    app: LandsgemeindeApp,
    date: date,
    agenda_item_number: int,
    number: int
) -> Votum | None:
    return VotumCollection(
        app.session(), date, agenda_item_number
    ).by_number(number)


@LandsgemeindeApp.path(
    model=PersonFunctionSuggestion,
    path='/suggestion/person/function'
)
def get_person_function_suggestion(
    app: LandsgemeindeApp,
    term: str | None = None
) -> PersonFunctionSuggestion:
    return PersonFunctionSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonNameSuggestion,
    path='/suggestion/person/name'
)
def get_person_name_suggestion(
    app: LandsgemeindeApp,
    term: str | None = None
) -> PersonNameSuggestion:
    return PersonNameSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonPlaceSuggestion,
    path='/suggestion/person/place'
)
def get_person_place_suggestion(
    app: LandsgemeindeApp,
    term: str | None = None
) -> PersonPlaceSuggestion:
    return PersonPlaceSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=PersonPoliticalAffiliationSuggestion,
    path='/suggestion/person/political-affiliation'
)
def get_person_political_affiliation_suggestion(
    app: LandsgemeindeApp,
    term: str | None = None
) -> PersonPoliticalAffiliationSuggestion:
    return PersonPoliticalAffiliationSuggestion(app.session(), term)


@LandsgemeindeApp.path(
    model=Search,
    path='/search',
    converters={
        'type': [str],
        'start': extended_date_converter,
        'end': extended_date_converter,
        'page': int
    }
)
def get_search(
    request: LandsgemeindeRequest,
    q: str = '',
    type: list[str] | None = None,
    start: date | None = None,
    end: date | None = None,
    page: int = 0
) -> Search:
    return Search(request, q, start=start, end=end, types=type, page=page)
