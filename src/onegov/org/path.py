""" Contains the paths to the different models served by onegov.org. """
import sedate

from datetime import date

from onegov.api.models import ApiKey
from onegov.chat import MessageCollection
from onegov.chat import TextModule
from onegov.chat import TextModuleCollection
from onegov.core.converters import extended_date_converter
from onegov.core.converters import json_converter
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntry
from onegov.event import Event
from onegov.event import EventCollection
from onegov.event import Occurrence
from onegov.event import OccurrenceCollection
from onegov.file import File
from onegov.file.integration import get_file
from onegov.form import CompleteFormSubmission
from onegov.form import FormCollection
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.form import PendingFormSubmission
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.newsletter import Subscription
from onegov.org.app import OrgApp
from onegov.org.auth import MTANAuth
from onegov.org.converters import keywords_converter
from onegov.org.models import AtoZPages
from onegov.org.models import Clipboard
from onegov.org.models import Dashboard
from onegov.org.models import DirectorySubmissionAction
from onegov.org.models import Editor
from onegov.org.models import Export
from onegov.org.models import ExportCollection
from onegov.org.models import FormPersonMove
from onegov.org.models import GeneralFileCollection
from onegov.org.models import ImageFileCollection
from onegov.org.models import ImageSet
from onegov.org.models import ImageSetCollection
from onegov.org.models import LegacyFile
from onegov.org.models import LegacyFileCollection
from onegov.org.models import LegacyImage
from onegov.org.models import LegacyImageCollection
from onegov.org.models import News
from onegov.org.models import Organisation
from onegov.org.models import PageMove
from onegov.org.models import PagePersonMove
from onegov.org.models import PublicationCollection
from onegov.org.models import ResourcePersonMove
from onegov.org.models import ResourceRecipient
from onegov.org.models import ResourceRecipientCollection
from onegov.org.models import Search
from onegov.org.models import SiteCollection
from onegov.org.models import TicketNote
from onegov.org.models import Topic
from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.org.models.external_link import ExternalLinkCollection, \
    ExternalLink
from onegov.org.models.resource import FindYourSpotCollection
from onegov.page import PageCollection
from onegov.pay import PaymentProvider, Payment, PaymentCollection
from onegov.pay import PaymentProviderCollection
from onegov.people import Person, PersonCollection
from onegov.qrcode import QrCode
from onegov.reservation import Allocation
from onegov.reservation import Reservation
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket, TicketCollection
from onegov.ticket.collection import ArchivedTicketsCollection
from onegov.user import Auth, User, UserCollection
from onegov.user import UserGroup, UserGroupCollection
from uuid import UUID
from webob import exc


@OrgApp.path(model=Organisation, path='/')
def get_org(app):
    return app.org


@OrgApp.path(model=Auth, path='/auth', converters={'skip': bool})
def get_auth(app, to='/', skip=False, signup_token=None):
    return Auth(app, to=to, skip=skip, signup_token=signup_token)


@OrgApp.path(model=MTANAuth, path='/mtan')
def get_mtan_auth(app, to='/'):
    return MTANAuth(app, to=to)


@OrgApp.path(model=User, path='/benutzer/{id}', converters={'id': UUID})
def get_user(app, id):
    return UserCollection(app.session()).by_id(id)


@OrgApp.path(
    model=UserCollection,
    path='/usermanagement',
    converters={
        'active': [bool],
        'role': [str],
        'tag': [str],
        'provider': [str],
        'source': [str]
    }
)
def get_users(app, active=None, role=None, tag=None, provider=None,
              source=None):
    return UserCollection(
        app.session(),
        active=active, role=role, tag=tag, provider=provider, source=source
    )


@OrgApp.path(
    model=UserGroup,
    path='/user-groups/{id}',
    converters={'id': UUID}
)
def get_user_group(app, id):
    return UserGroupCollection(app.session()).by_id(id)


@OrgApp.path(
    model=UserGroupCollection,
    path='/usergroups',
)
def get_user_groups(app):
    return UserGroupCollection(app.session())


@OrgApp.path(model=Topic, path='/topics', absorb=True)
def get_topic(app, absorb):
    return PageCollection(app.session()).by_path(absorb, ensure_type='topic')


@OrgApp.path(
    model=News,
    path='/news',
    absorb=True,
    converters={
        'filter_years': [int],
        'filter_tags': [str]
    }
)
def get_news(app, absorb, filter_years, filter_tags):
    pages = PageCollection(app.session())

    old_path = '/{}/{}'.format('aktuelles', absorb)
    new_path = '/{}/{}'.format('news', absorb)

    news = (
        pages.by_path(new_path, ensure_type='news')
        or pages.by_path(old_path, ensure_type='news')
    )
    if news:
        news.filter_years = filter_years
        news.filter_tags = filter_tags

    return news


@OrgApp.path(model=GeneralFileCollection, path='/files')
def get_files(request, order_by='name'):
    return GeneralFileCollection(request.session, order_by=order_by)


@OrgApp.path(model=ImageFileCollection, path='/images')
def get_images(app):
    return ImageFileCollection(app.session())


@OrgApp.path(model=ExportCollection, path='/exports')
def get_exports(request, app):
    return ExportCollection(app)


@OrgApp.path(model=Export, path='/export/{id}')
def get_export(request, app, id):
    return ExportCollection(app).by_id(id)


@OrgApp.path(model=FormCollection, path='/forms')
def get_forms(app):
    return FormCollection(app.session())


@OrgApp.path(model=FormDefinition, path='/form/{name}')
def get_form(app, name):
    return FormCollection(app.session()).definitions.by_name(name)


@OrgApp.path(model=PendingFormSubmission, path='/form-preview/{id}',
             converters={'id': UUID})
def get_pending_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='pending', current_only=True)


@OrgApp.path(model=CompleteFormSubmission, path='/form-submission/{id}',
             converters={'id': UUID})
def get_complete_form_submission(app, id):
    return FormCollection(app.session()).submissions.by_id(
        id, state='complete', current_only=False)


@OrgApp.path(
    model=FormRegistrationWindow,
    path='/form-registration-window/{id}',
    converters={'id': UUID})
def get_form_registration_window(request, id):
    return FormCollection(request.session).registration_windows.by_id(id)


@OrgApp.path(model=File, path='/storage/{id}')
def get_file_for_org(request, app, id):
    """ Some files are kept private and out of any caches.

    This approach is not all that morepath-y, as we could override the views
    instead to change the required permissions, but this approach has the
    advantage that we don't need to overwrite multiple views and we do not
    have to care for additional views added in the future.

    """

    protected_filetypes = (
        'formfile',
        'messagefile',
    )

    obj = get_file(app, id)

    if not obj:
        return

    if obj.type in protected_filetypes:
        if not request.has_role('editor', 'admin'):
            obj = None
        else:
            @request.after
            def disable_cache(response):
                response.cache_control.no_cache = True
                response.cache_control.max_age = None
                response.cache_control.public = False
                response.cache_control.private = True

    return obj


@OrgApp.path(model=Editor, path='/editor/{action}/{trait}/{page_id}')
def get_editor(app, action, trait, page_id=0):
    if not Editor.is_supported_action(action):
        return None

    if page_id:
        page = PageCollection(app.session()).by_id(page_id)
    else:
        # adding root element with no parent (page=None)
        return Editor(action=action,
                      page=None,
                      trait=trait)

    if not page:
        return None

    if not page.is_supported_trait(trait):
        return None

    return Editor(action=action, page=page, trait=trait)


@OrgApp.path(model=PersonCollection, path='/people')
def get_people(app):
    return PersonCollection(app.session())


@OrgApp.path(model=Person, path='/person/{id}', converters={'id': UUID})
def get_person(app, id):
    return PersonCollection(app.session()).by_id(id)


@OrgApp.path(model=ChatCollection, path='/chats')
def get_chats(app, page=0, state='active'):
    return ChatCollection(
        app.session(),
        page=page,
        state=state,
    )


@OrgApp.path(model=Chat, path='/chat/{id}', converters={'id': UUID})
def get_chat(app, id):
    return ChatCollection(app.session()).by_id(id)


@OrgApp.path(model=Ticket, path='/ticket/{handler_code}/{id}',
             converters={'id': UUID})
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
        extra_parameters=extra_parameters,
    )


@OrgApp.path(
    model=ArchivedTicketsCollection, path='/tickets-archive/{handler}'
)
def get_archived_tickets(
        app, handler='ALL', page=0, group=None, owner=None,
        extra_parameters=None):
    return ArchivedTicketsCollection(
        app.session(),
        handler=handler,
        state='archived',
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


@OrgApp.path(model=ResourceCollection, path='/resources')
def get_resources(app):
    return app.libres_resources


@OrgApp.path(model=FindYourSpotCollection, path='/find-your-spot')
def get_find_my_spot(app, group=None):
    return FindYourSpotCollection(app.libres_context, group=group)


@OrgApp.path(
    model=Resource,
    path='/resource/{name}',
    converters={
        'date': date,
        'highlights_min': int,
        'highlights_max': int
    }
)
def get_resource(app, name, date=None, view=None,
                 highlights_min=None, highlights_max=None):

    resource = app.libres_resources.by_name(name)

    if resource:
        resource.date = date
        resource.highlights_min = highlights_min
        resource.highlights_max = highlights_max
        resource.view = view or resource.default_view or 'agendaWeek'

    return resource


@OrgApp.path(model=Allocation, path='/allocation/{resource}/{id}',
             converters={'resource': UUID})
def get_allocation(app, resource, id):
    resource = app.libres_resources.by_id(resource)

    if resource:
        allocation = resource.scheduler.allocations_by_ids((id, )).first()

        # always get the master, even if another id is requested
        return allocation and allocation.get_master()


@OrgApp.path(model=Reservation, path='/reservation/{resource}/{id}',
             converters={'resource': UUID})
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
             converters={'subject_id': int, 'target_id': int})
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


@OrgApp.path(
    model=OccurrenceCollection, path='/events',
    converters={
        'start': extended_date_converter,
        'end': extended_date_converter,
        'tags': [],
        'filter_keywords': keywords_converter,
        'locations': [],
        'search_query': json_converter,
    }
)
def get_occurrences(app, request, page=0, range=None, start=None, end=None,
                    tags=None, filter_keywords=None, locations=None,
                    search=None, search_query=None):

    if not search:
        search = app.settings.org.default_event_search_widget

    if search and search in app.config.event_search_widget_registry:
        cls = app.config.event_search_widget_registry[search]
        search_widget = cls(request, search_query)
    else:
        search_widget = None

    return OccurrenceCollection(
        app.session(),
        page=page,
        range=range,
        start=start,
        end=end,
        tags=tags,
        filter_keywords=filter_keywords,
        locations=locations,
        only_public=(not request.is_manager),
        search_widget=search_widget,
    )


@OrgApp.path(model=Occurrence, path='/event/{name}')
def get_occurrence(app, name):
    return OccurrenceCollection(app.session()).by_name(name)


@OrgApp.path(model=Event, path='/event-management/{name}')
def get_event(app, name):
    return EventCollection(app.session()).by_name(name)


@OrgApp.path(model=Search, path='/search')
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


@OrgApp.path(model=RecipientCollection, path='/subscribers')
def get_newsletter_recipients(app):
    return RecipientCollection(app.session())


@OrgApp.path(model=Subscription, path='/abonnement/{recipient_id}/{token}',
             converters={'recipient_id': UUID})
def get_subscription(app, recipient_id, token):
    recipient = RecipientCollection(app.session()).by_id(recipient_id)
    return recipient and Subscription(recipient, token)


@OrgApp.path(model=LegacyFile, path='/file/{filename}')
def get_legacy_file(app, filename):
    return LegacyFileCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=LegacyImage, path='/image/{filename}')
def get_image(app, filename):
    return LegacyImageCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=ImageSetCollection, path='/photoalbums')
def get_image_sets(app):
    return ImageSetCollection(app.session())


@OrgApp.path(model=ImageSet, path='/photoalbum/{id}')
def get_image_set(app, id):
    return ImageSetCollection(app.session()).by_id(id)


@OrgApp.path(
    model=ResourceRecipientCollection,
    path='/resource-recipients')
def get_resource_recipient_collection(app):
    return ResourceRecipientCollection(app.session())


@OrgApp.path(
    model=ResourceRecipient,
    path='/resource-recipient/{id}',
    converters={'id': UUID})
def get_resource_recipient(app, id):
    return ResourceRecipientCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentProviderCollection,
    path='/payment-provider')
def get_payment_provider_collection(app):
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session())


@OrgApp.path(
    model=PaymentProvider,
    path='/payment-provider-entry/{id}',
    converters={'id': UUID})
def get_payment_provider(app, id):
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session()).by_id(id)


@OrgApp.path(
    model=Payment,
    path='/payment/{id}',
    converters={'id': UUID})
def get_payment(app, id):
    return PaymentCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentCollection,
    path='/payments')
def get_payments(app, source='*', page=0):
    return PaymentCollection(app.session(), source, page)


@OrgApp.path(
    model=MessageCollection,
    path='/timeline')
def get_messages(app, channel_id='*', type='*',
                 newer_than=None, older_than=None, limit=25,
                 load='older-first'):
    return MessageCollection(
        session=app.session(),
        type=type,
        channel_id=channel_id,
        newer_than=newer_than,
        older_than=older_than,
        limit=min(25, limit),  # bind the limit to a max of 25
        load='newer-first' if load == 'newer-first' else 'older-first'
    )


@OrgApp.path(
    model=TextModuleCollection,
    path='/text-modules')
def get_text_modules(app):
    return TextModuleCollection(app.session())


@OrgApp.path(
    model=TextModule,
    path='/text-module/{id}',
    converters={'id': UUID}
)
def get_text_module(app, id):
    return TextModuleCollection(app.session()).by_id(id)


@OrgApp.path(
    model=DirectoryCollection,
    path='/directories')
def get_directories(app):
    return DirectoryCollection(app.session(), type='extended')


@OrgApp.path(
    model=Directory,
    path='/directory/{name}')
def get_directory(app, name):
    return DirectoryCollection(app.session(), type='extended').by_name(name)


@OrgApp.path(
    model=ExtendedDirectoryEntryCollection,
    path='/directories/{directory_name}',
    converters={
        'keywords': keywords_converter,
        'search_query': json_converter,
        'published_only': bool,
        'past_only': bool,
        'upcoming_only': bool
    })
def get_directory_entries(
        request, app, directory_name, keywords, page=0,
        search=None,
        search_query=None,
        published_only=None,
        past_only=None,
        upcoming_only=None
):
    directory = DirectoryCollection(app.session()).by_name(directory_name)

    if not search:
        search = app.settings.org.default_directory_search_widget

    if search and search in app.config.directory_search_widget_registry:
        cls = app.config.directory_search_widget_registry[search]
        search_widget = cls(request, directory, search_query)
    else:
        search_widget = None

    if not published_only and not request.is_manager:
        published_only = True

    if directory:
        collection = ExtendedDirectoryEntryCollection(
            directory=directory,
            type='extended',
            keywords=keywords,
            page=page,
            search_widget=search_widget,
            published_only=published_only,
            past_only=past_only,
            upcoming_only=upcoming_only
        )

        collection.access = directory.access

        return collection


@OrgApp.path(
    model=DirectoryEntry,
    path='/directories/{directory_name}/{name}')
def get_directory_entry(app, directory_name, name):
    directory = DirectoryCollection(app.session()).by_name(directory_name)

    if directory:
        return ExtendedDirectoryEntryCollection(
            directory=directory,
            type='extended'
        ).by_name(name)


@OrgApp.path(
    model=DirectorySubmissionAction,
    path='/directory-submission/{directory_id}/{submission_id}/{action}',
    converters={'directory_id': UUID, 'submission_id': UUID})
def get_directory_submission_action(app, directory_id, submission_id, action):
    action = DirectorySubmissionAction(
        session=app.session(),
        directory_id=directory_id,
        submission_id=submission_id,
        action=action)

    if action.valid:
        return action


@OrgApp.path(
    model=PublicationCollection,
    path='/publications',
    converters={'year': int})
def get_publication_collection(request, year=None):
    year = year or sedate.to_timezone(sedate.utcnow(), 'Europe/Zurich').year
    return PublicationCollection(request.session, year)


@OrgApp.path(
    model=Dashboard,
    path='/dashboard')
def get_dashboard(request):
    dashboard = Dashboard(request)

    if dashboard.is_available:
        return dashboard


@OrgApp.path(model=ExternalLinkCollection, path='/external-links')
def get_external_link_collection(request, type=None):
    return ExternalLinkCollection(request.session, type=type)


@OrgApp.path(model=ExternalLink, path='/external-link/{id}',
             converters={'id': UUID})
def get_external_link(request, id):
    return ExternalLinkCollection(request.session).by_id(id)


@OrgApp.path(model=QrCode, path='/qrcode',
             converters={'border': int, 'box_size': int})
def get_qr_code(app, payload, border=None, box_size=None, fill_color=None,
                back_color=None, img_format=None, encoding=None):
    return QrCode(
        payload,
        border=border,
        box_size=box_size,
        fill_color=fill_color,
        back_color=back_color,
        img_format=img_format,
        encoding=encoding
    )


@OrgApp.path(
    model=ApiKey, path='/api_keys/{key}/delete', converters={'key': UUID}
)
def get_api_key_for_delete(request, key):
    return request.session.query(ApiKey).filter_by(key=key).first()
