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
from onegov.newsletter import (
    Newsletter,
    NewsletterCollection,
    Subscription,
    RecipientCollection,
)
from onegov.town.app import TownApp
from onegov.town.converters import extended_date_converter
from onegov.town.models import (
    AtoZPages,
    Clipboard,
    Editor,
    File,
    FileCollection,
    FormPersonMove,
    Image,
    ImageCollection,
    News,
    PageMove,
    PagePersonMove,
    ResourcePersonMove,
    Search,
    SiteCollection,
    Thumbnail,
    Topic,
    Town,
)
from onegov.page import PageCollection
from onegov.people import Person, PersonCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.user import Auth
from webob import exc


@TownApp.path(model=Town, path='/')
def get_town(app):
    return app.town


@TownApp.path(model=Auth, path='/auth')
def get_auth(app, to='/'):
    return Auth.from_app(app, to)


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
def get_tickets(app, handler='ALL', state='open', page=0, group=None,
                extra_parameters=None):
    return TicketCollection(
        app.session(),
        handler=handler,
        state=state,
        page=page,
        group=group,
        extra_parameters=extra_parameters
    )


@TownApp.path(model=ResourceCollection, path='/ressourcen')
def get_resources(app):
    return app.libres_resources


@TownApp.path(model=Resource, path='/ressource/{name}',
              converters=dict(date=date, highlights=[int]))
def get_resource(app, name, date=None, highlights=tuple(), view='agendaWeek'):

    resource = app.libres_resources.by_name(name)

    if resource:
        resource.date = date
        resource.highlights = highlights
        resource.view = view

    return resource


@TownApp.path(model=Allocation, path='/einteilung/{resource}/{id}')
def get_allocation(app, resource, id):
    resource = app.libres_resources.by_id(resource)

    if resource:
        allocation = resource.scheduler.allocations_by_ids((id, )).first()

        # always get the master, even if another id is requested
        return allocation and allocation.get_master()


@TownApp.path(model=Reservation, path='/reservation/{resource}/{id}')
def get_reservation(app, resource, id):
    resource = app.libres_resources.by_id(resource)

    if resource:
        query = resource.scheduler.managed_reservations()
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


@TownApp.path(model=PageMove,
              path='/move/page/{subject_id}/{direction}/{target_id}',
              converters=dict(subject_id=int, target_id=int))
def get_page_move(app, subject_id, direction, target_id):
    if subject_id == target_id:
        raise exc.HTTPBadRequest()

    session = app.session()
    pages = PageCollection(session)

    subject = pages.by_id(subject_id)
    target = pages.by_id(target_id)

    if subject and target:
        return PageMove(session, subject, target, direction)


@TownApp.path(model=PagePersonMove,
              path='/move/page-person/{key}/{subject}/{direction}/{target}')
def get_person_move(app, key, subject, direction, target):
    if subject == target:
        raise exc.HTTPBadRequest()

    session = app.session()
    page = PageCollection(session).by_id(key)

    if page:
        return PagePersonMove(session, page, subject, target, direction)


@TownApp.path(model=FormPersonMove,
              path='/move/form-person/{key}/{subject}/{direction}/{target}')
def get_form_move(app, key, subject, direction, target):
    session = app.session()
    form = FormCollection(session).definitions.by_name(key)

    if form:
        return FormPersonMove(session, form, subject, target, direction)


@TownApp.path(
    model=ResourcePersonMove,
    path='/move/resource-person/{key}/{subject}/{direction}/{target}')
def get_resource_move(app, key, subject, direction, target):
    session = app.session()
    resource = ResourceCollection(app.libres_context).by_id(key)

    if resource:
        return ResourcePersonMove(
            session, resource, subject, target, direction)


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


@TownApp.path(model=AtoZPages, path='/a-z')
def get_a_to_z(request):
    return AtoZPages(request)


@TownApp.path(model=NewsletterCollection, path='/newsletters')
def get_newsletters(app):
    return NewsletterCollection(app.session())


@TownApp.path(model=Newsletter, path='/newsletter/{name}')
def get_newsletter(app, name):
    return get_newsletters(app).by_name(name)


@TownApp.path(model=RecipientCollection, path='/abonnenten')
def get_newsletter_recipients(app):
    return RecipientCollection(app.session())


@TownApp.path(model=Subscription, path='/abonnement/{recipient_id}/{token}')
def get_subscription(app, recipient_id, token):
    recipient = RecipientCollection(app.session()).by_id(recipient_id)
    return recipient and Subscription(recipient, token)
