""" Contains the paths to the different models served by onegov.org. """

from datetime import date
from onegov.chat import MessageCollection
from onegov.core.converters import extended_date_converter
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
from onegov.newsletter import (
    Newsletter,
    NewsletterCollection,
    Subscription,
    RecipientCollection,
)
from onegov.org.app import OrgApp
from onegov.org.models import (
    AtoZPages,
    Clipboard,
    Editor,
    Export,
    ExportCollection,
    FormPersonMove,
    GeneralFileCollection,
    ImageFileCollection,
    ImageSet,
    ImageSetCollection,
    LegacyFile,
    LegacyFileCollection,
    LegacyImage,
    LegacyImageCollection,
    News,
    Organisation,
    PageMove,
    PagePersonMove,
    ResourcePersonMove,
    ResourceRecipient,
    ResourceRecipientCollection,
    Search,
    SiteCollection,
    TicketNote,
    Topic,
)
from onegov.page import PageCollection
from onegov.pay import PaymentProvider, Payment, PaymentCollection
from onegov.pay import PaymentProviderCollection
from onegov.people import Person, PersonCollection
from onegov.reservation import Allocation
from onegov.reservation import Reservation
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.user import Auth, User, UserCollection
from webob import exc
from uuid import UUID


@OrgApp.path(model=Organisation, path='/')
def get_org(app):
    return app.org


@OrgApp.path(model=Auth, path='/auth', converters=dict(skip=bool))
def get_auth(app, to='/', skip=False, signup_token=None):
    return Auth.from_app(app, to, skip, signup_token)


@OrgApp.path(model=User, path='/benutzer/{id}', converters=dict(id=UUID))
def get_user(app, id):
    return UserCollection(app.session()).by_id(id)


@OrgApp.path(
    model=UserCollection,
    path='/benutzerverwaltung',
    converters=dict(active=[bool], role=[str])
)
def get_users(app, active=None, role=None):
    return UserCollection(app.session(), active=active, role=role)


@OrgApp.path(model=Topic, path='/themen', absorb=True)
def get_topic(app, absorb):
    return PageCollection(app.session()).by_path(absorb, ensure_type='topic')


@OrgApp.path(model=News, path='/aktuelles', absorb=True)
def get_news(app, absorb):
    absorb = '/{}/{}'.format('aktuelles', absorb)
    return PageCollection(app.session()).by_path(absorb, ensure_type='news')


@OrgApp.path(model=GeneralFileCollection, path='/dateien')
def get_files(app):
    return GeneralFileCollection(app.session())


@OrgApp.path(model=ImageFileCollection, path='/bilder')
def get_images(app):
    return ImageFileCollection(app.session())


@OrgApp.path(model=ExportCollection, path='/exporte')
def get_exports(request, app):
    return ExportCollection(app)


@OrgApp.path(model=Export, path='/export/{id}')
def get_export(request, app, id):
    return ExportCollection(app).by_id(id)


@OrgApp.path(model=FormCollection, path='/formulare')
def get_forms(app):
    return FormCollection(app.session())


@OrgApp.path(model=FormDefinition, path='/formular/{name}')
def get_form(app, name):
    return FormCollection(app.session()).definitions.by_name(name)


@OrgApp.path(model=PendingFormSubmission, path='/formular-eingabe/{id}',
             converters=dict(id=UUID))
def get_pending_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='pending', current_only=True)


@OrgApp.path(model=CompleteFormSubmission, path='/formular-eingang/{id}',
             converters=dict(id=UUID))
def get_complete_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='complete', current_only=False)


@OrgApp.path(model=FormSubmissionFile, path='/formular-datei/{id}',
             converters=dict(id=UUID))
def get_form_submission_file(app, id):
    return FormCollection(app.session()).submissions.file_by_id(id)


@OrgApp.path(model=Editor, path='/editor/{action}/{trait}/{page_id}')
def get_editor(app, action, trait, page_id):
    if not Editor.is_supported_action(action):
        return None

    page = PageCollection(app.session()).by_id(page_id)

    if not page.is_supported_trait(trait):
        return None

    if page is not None:
        return Editor(action=action, page=page, trait=trait)


@OrgApp.path(model=PersonCollection, path='/personen')
def get_people(app):
    return PersonCollection(app.session())


@OrgApp.path(model=Person, path='/person/{id}', converters=dict(id=UUID))
def get_person(app, id):
    return PersonCollection(app.session()).by_id(id)


@OrgApp.path(model=Ticket, path='/ticket/{handler_code}/{id}',
             converters=dict(id=UUID))
def get_ticket(app, handler_code, id):
    return TicketCollection(app.session()).by_id(
        id, ensure_handler_code=handler_code)


@OrgApp.path(model=TicketCollection, path='/tickets/{handler}/{state}')
def get_tickets(app, handler='ALL', state='open', page=0, group=None,
                owner=None, extra_parameters=None):
    return TicketCollection(
        app.session(),
        handler=handler,
        state=state,
        page=page,
        group=group,
        owner=owner or '*',
        extra_parameters=extra_parameters
    )


@OrgApp.path(
    model=TicketNote,
    path='/ticket-notes/{id}')
def get_ticket_note(app, id):
    return MessageCollection(app.session(), type='ticket_note').by_id(id)


@OrgApp.path(model=ResourceCollection, path='/ressourcen')
def get_resources(app):
    return app.libres_resources


@OrgApp.path(model=Resource, path='/ressource/{name}', converters=dict(
             date=date, highlights_min=int, highlights_max=int))
def get_resource(app, name, date=None, view='agendaWeek',
                 highlights_min=None, highlights_max=None):

    resource = app.libres_resources.by_name(name)

    if resource:
        resource.date = date
        resource.highlights_min = highlights_min
        resource.highlights_max = highlights_max
        resource.view = view

    return resource


@OrgApp.path(model=Allocation, path='/einteilung/{resource}/{id}',
             converters=dict(resource=UUID))
def get_allocation(app, resource, id):
    resource = app.libres_resources.by_id(resource)

    if resource:
        allocation = resource.scheduler.allocations_by_ids((id, )).first()

        # always get the master, even if another id is requested
        return allocation and allocation.get_master()


@OrgApp.path(model=Reservation, path='/reservation/{resource}/{id}',
             converters=dict(resource=UUID))
def get_reservation(app, resource, id):
    resource = app.libres_resources.by_id(resource)

    if resource:
        query = resource.scheduler.managed_reservations()
        query = query.filter(Reservation.id == id)

        return query.first()


@OrgApp.path(model=Clipboard, path='/clipboard/copy/{token}')
def get_clipboard(request, token):
    clipboard = Clipboard(request, token)

    # the url is None if the token is invalid
    if clipboard.url:
        return clipboard


@OrgApp.path(model=SiteCollection, path='/sitecollection')
def get_sitecollection(app):
    return SiteCollection(app.session())


@OrgApp.path(model=PageMove,
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


@OrgApp.path(model=PagePersonMove,
             path='/move/page-person/{key}/{subject}/{direction}/{target}')
def get_person_move(app, key, subject, direction, target):
    if subject == target:
        raise exc.HTTPBadRequest()

    session = app.session()
    page = PageCollection(session).by_id(key)

    if page:
        return PagePersonMove(session, page, subject, target, direction)


@OrgApp.path(model=FormPersonMove,
             path='/move/form-person/{key}/{subject}/{direction}/{target}')
def get_form_move(app, key, subject, direction, target):
    session = app.session()
    form = FormCollection(session).definitions.by_name(key)

    if form:
        return FormPersonMove(session, form, subject, target, direction)


@OrgApp.path(
    model=ResourcePersonMove,
    path='/move/resource-person/{key}/{subject}/{direction}/{target}')
def get_resource_move(app, key, subject, direction, target):
    session = app.session()
    resource = ResourceCollection(app.libres_context).by_id(key)

    if resource:
        return ResourcePersonMove(
            session, resource, subject, target, direction)


@OrgApp.path(model=OccurrenceCollection, path='/veranstaltungen',
             converters=dict(start=extended_date_converter,
                             end=extended_date_converter, tags=[]))
def get_occurrences(app, page=0, start=None, end=None, tags=None):
    return OccurrenceCollection(app.session(), page, start, end, tags)


@OrgApp.path(model=Occurrence, path='/veranstaltung/{name}')
def get_occurrence(app, name):
    return OccurrenceCollection(app.session()).by_name(name)


@OrgApp.path(model=EventCollection, path='/events')
def get_events(app, page=0, state='published'):
    return EventCollection(app.session(), page, state)


@OrgApp.path(model=Event, path='/event/{name}')
def get_event(app, name):
    return EventCollection(app.session()).by_name(name)


@OrgApp.path(model=Search, path='/suche')
def get_search(request, q='', page=0):
    return Search(request, q, page)


@OrgApp.path(model=AtoZPages, path='/a-z')
def get_a_to_z(request):
    return AtoZPages(request)


@OrgApp.path(model=NewsletterCollection, path='/newsletters')
def get_newsletters(app):
    return NewsletterCollection(app.session())


@OrgApp.path(model=Newsletter, path='/newsletter/{name}')
def get_newsletter(app, name):
    return get_newsletters(app).by_name(name)


@OrgApp.path(model=RecipientCollection, path='/abonnenten')
def get_newsletter_recipients(app):
    return RecipientCollection(app.session())


@OrgApp.path(model=Subscription, path='/abonnement/{recipient_id}/{token}',
             converters=dict(recipient_id=UUID))
def get_subscription(app, recipient_id, token):
    recipient = RecipientCollection(app.session()).by_id(recipient_id)
    return recipient and Subscription(recipient, token)


@OrgApp.path(model=LegacyFile, path='/datei/{filename}')
def get_file(app, filename):
    return LegacyFileCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=LegacyImage, path='/bild/{filename}')
def get_image(app, filename):
    return LegacyImageCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=ImageSetCollection, path='/fotoalben')
def get_image_sets(app):
    return ImageSetCollection(app.session())


@OrgApp.path(model=ImageSet, path='/fotoalbum/{id}')
def get_image_set(app, id):
    return ImageSetCollection(app.session()).by_id(id)


@OrgApp.path(
    model=ResourceRecipientCollection,
    path='/ressourcen-empfang')
def get_resource_recipient_collection(app):
    return ResourceRecipientCollection(app.session())


@OrgApp.path(
    model=ResourceRecipient,
    path='/ressourcen-empfaenger/{id}',
    converters=dict(id=UUID))
def get_resource_recipient(app, id):
    return ResourceRecipientCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentProviderCollection,
    path='/zahlungsanbieter')
def get_payment_provider_collection(app):
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session())


@OrgApp.path(
    model=PaymentProvider,
    path='/zahlungsanbieter-eintrag/{id}',
    converters=dict(id=UUID))
def get_payment_provider(app, id):
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session()).by_id(id)


@OrgApp.path(
    model=Payment,
    path='/zahlung/{id}',
    converters=dict(id=UUID))
def get_payment(app, id):
    return PaymentCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentCollection,
    path='/zahlungen')
def get_payments(app, source='*', page=0):
    return PaymentCollection(app.session(), source, page)


@OrgApp.path(
    model=MessageCollection,
    path='/timeline')
def get_messages(app, channel_id='*', type='*',
                 newer_than=None, older_than=None, limit=25):
    return MessageCollection(
        session=app.session(),
        type=type,
        channel_id=channel_id,
        newer_than=newer_than,
        older_than=older_than,
        limit=min(25, limit)  # bind the limit to a max of 25
    )
