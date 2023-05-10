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
    path='/agenda-items/{assembly_id}',
    converters=dict(assembly_id=UUID)
)
def get_agenda_items(app, assembly_id):
    return AgendaItemCollection(app.session(), assembly_id)


@LandsgemeindeApp.path(
    model=AgendaItem,
    path='/agenda-item/{id}',
    converters=dict(id=UUID)
)
def get_agenda_item(app, id):
    return AgendaItemCollection(app.session()).by_id(id)
