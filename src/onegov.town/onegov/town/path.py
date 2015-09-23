""" Contains the paths to the different models served by onegov.town. """

from datetime import date
from libres.db.models import Allocation, Reservation
from onegov.event import (
    Event,
    EventCollection,
    Occurrence,
    OccurrenceCollection
)
from onegov.form import (
    FormDefinition,
    FormCollection,
    FormSubmissionFile,
    CompleteFormSubmission,
    PendingFormSubmission
)
from onegov.libres import ResourceCollection
from onegov.libres.models import Resource
from onegov.town.app import TownApp
from onegov.town.converters import extended_date_converter
from onegov.town.models import (
    Clipboard,
    Editor,
    File,
    FileCollection,
    Image,
    ImageCollection,
    News,
    Search,
    SiteCollection,
    Thumbnail,
    Topic,
    Town
)
from onegov.page import PageCollection
from onegov.people import Person, PersonCollection
from onegov.ticket import Ticket, TicketCollection


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Topic, path='/themen', absorb=True)
def get_topic(app, absorb):
    return PageCollection(app.session()).by_path(absorb, ensure_type='topic')


@TownApp.path(model=News, path='/aktuelles', absorb=True)
def get_news(app, absorb):
    absorb = '/{}/{}'.format('aktuelles', absorb)
    return PageCollection(app.session()).by_path(absorb, ensure_type='news')


@TownApp.path(model=FileCollection, path='/dateien')
def get_files(app):
    return FileCollection(app)


@TownApp.path(model=File, path='/datei/{filename}')
def get_file(app, filename):
    return FileCollection(app).get_file_by_filename(filename)


@TownApp.path(model=ImageCollection, path='/bilder')
def get_images(app):
    return ImageCollection(app)


@TownApp.path(model=Image, path='/bild/{filename}')
def get_image(app, filename):
    return ImageCollection(app).get_file_by_filename(filename)


@TownApp.path(model=Thumbnail, path='/thumbnails/{filename}')
def get_thumbnail(app, filename):
    return ImageCollection(app).get_thumbnail_by_filename(filename)


@TownApp.path(model=FormCollection, path='/formulare')
def get_forms(app):
    return FormCollection(app.session())


@TownApp.path(model=FormDefinition, path='/formular/{name}')
def get_form(app, name):
    return FormCollection(app.session()).definitions.by_name(name)


@TownApp.path(model=PendingFormSubmission, path='/formular-eingabe/{id}')
def get_pending_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='pending', current_only=True)


@TownApp.path(model=CompleteFormSubmission, path='/formular-eingang/{id}')
def get_complete_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='complete', current_only=False)


@TownApp.path(model=FormSubmissionFile, path='/formular-datei/{id}')
def get_form_submission_file(app, id):
    return FormCollection(app.session()).submissions.file_by_id(id)


@TownApp.path(model=Editor, path='/editor/{action}/{trait}/{page_id}')
def get_editor(app, action, trait, page_id):
    if not Editor.is_supported_action(action):
        return None

    page = PageCollection(app.session()).by_id(page_id)

    if not page.is_supported_trait(trait):
        return None

    if page is not None:
        return Editor(action=action, page=page, trait=trait)


@TownApp.path(model=PersonCollection, path='/personen')
def get_people(app):
    return PersonCollection(app.session())


@TownApp.path(model=Person, path='/person/{id}')
def get_person(app, id):
    return PersonCollection(app.session()).by_id(id)


@TownApp.path(model=Ticket, path='/ticket/{handler_code}/{id}')
def get_ticket(app, handler_code, id):
    return TicketCollection(app.session()).by_id(
        id, ensure_handler_code=handler_code)


@TownApp.path(model=TicketCollection, path='/tickets/{handler}/{state}')
def get_tickets(app, handler='ALL', state='open', page=0,
                extra_parameters=None):
    return TicketCollection(
        app.session(),
        handler=handler,
        state=state,
        page=page,
        extra_parameters=extra_parameters
    )


@TownApp.path(model=ResourceCollection, path='/ressourcen')
def get_resources(app):
    return ResourceCollection(app.libres_context)


@TownApp.path(model=Resource, path='/ressource/{name}',
              converters=dict(date=date, highlights=[int]))
def get_resource(app, name, date=None, highlights=tuple()):

    resource = ResourceCollection(app.libres_context).by_name(name)
    resource.date = date
    resource.highlights = highlights

    return resource


@TownApp.path(model=Allocation, path='/einteilung/{resource}/{id}')
def get_allocation(app, resource, id):
    scheduler = ResourceCollection(
        app.libres_context).scheduler_by_id(resource)

    if scheduler:
        allocation = scheduler.allocations_by_ids((id, )).first()

        # always get the master, even if another id is requested
        return allocation and allocation.get_master()


@TownApp.path(model=Reservation, path='/reservation/{resource}/{id}')
def get_reservation(app, resource, id):
    scheduler = ResourceCollection(
        app.libres_context).scheduler_by_id(resource)

    if scheduler:
        query = scheduler.managed_reservations()
        query = query.filter(Reservation.id == id)

        return query.first()


@TownApp.path(model=Clipboard, path='/clipboard/copy/{token}')
def get_clipboard(request, token):
    clipboard = Clipboard(request, token)

    # the url is None if the token is invalid
    if clipboard.url:
        return clipboard


@TownApp.path(model=SiteCollection, path='/sitecollection')
def get_sitecollection(app):
    return SiteCollection(app.session())


@TownApp.path(model=OccurrenceCollection, path='/veranstaltungen',
              converters=dict(start=extended_date_converter,
                              end=extended_date_converter, tags=[]))
def get_occurrences(app, page=0, start=None, end=None, tags=None):
    return OccurrenceCollection(app.session(), page, start, end, tags)


@TownApp.path(model=Occurrence, path='/veranstaltung/{name}')
def get_occurrence(app, name):
    return OccurrenceCollection(app.session()).by_name(name)


@TownApp.path(model=EventCollection, path='/events')
def get_events(app, page=0, state='published'):
    return EventCollection(app.session(), page, state)


@TownApp.path(model=Event, path='/event/{name}')
def get_event(app, name):
    return EventCollection(app.session()).by_name(name)


@TownApp.path(model=Search, path='/suche')
def get_search(request, q='', page=0):
    return Search(request, q, page)
