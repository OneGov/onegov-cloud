from onegov.core.converters import extended_date_converter
from onegov.landsgemeinde.app import LandsgemeindeApp
from onegov.landsgemeinde.collections import AgendaItemCollection
from onegov.landsgemeinde.collections import AssemblyCollection
from onegov.landsgemeinde.models import AgendaItem
from onegov.landsgemeinde.models import Assembly
from uuid import UUID


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
    converters=dict(id=UUID)
)
def get_agenda_item(app, date, number):
    return AgendaItemCollection(app.session(), date).by_number(number)
