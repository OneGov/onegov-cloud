""" Contains the paths to the different models served by onegov.org. """
from __future__ import annotations

import sedate
from datetime import date, datetime
from onegov.api.models import ApiKey
from onegov.chat import MessageCollection
from onegov.chat import TextModule
from onegov.chat import TextModuleCollection
from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.core.converters import extended_date_converter
from onegov.core.converters import datetime_year_converter
from onegov.core.converters import json_converter
from onegov.core.converters import LiteralConverter
from onegov.core.orm.abstract import MoveDirection
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntry
from onegov.directory.collections.directory import EntryRecipientCollection
from onegov.directory.models.directory import EntrySubscription
from onegov.event import Event
from onegov.event import EventCollection
from onegov.event import Occurrence
from onegov.event import OccurrenceCollection
from onegov.event.collections.occurrences import DateRange
from onegov.file import File
from onegov.file.integration import get_file
from onegov.form import CompleteFormSubmission
from onegov.form import FormCollection
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.form import PendingFormSubmission
from onegov.form.collection import SurveyCollection
from onegov.org.models.document_form import (
    FormDocumentCollection, FormDocument)
from onegov.form.models.submission import SurveySubmission
from onegov.form.models.definition import SurveyDefinition
from onegov.form.models.survey_window import SurveySubmissionWindow
from onegov.newsletter import Newsletter
from onegov.newsletter import NewsletterCollection
from onegov.newsletter import RecipientCollection
from onegov.newsletter import Subscription
from onegov.org.app import OrgApp
from onegov.org.auth import MTANAuth
from onegov.org.converters import keywords_converter
from onegov.org.models import AtoZPages, PushNotificationCollection
from onegov.org.models import RISCommissionMembershipCollection
from onegov.org.models import RISCommissionMembership
from onegov.org.models import CitizenDashboard, Dashboard
from onegov.org.models import Clipboard
from onegov.org.models import DirectorySubmissionAction
from onegov.org.models import Editor
from onegov.org.models import Export
from onegov.org.models import ExportCollection
from onegov.org.models import ExtendedDirectory
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
from onegov.org.models import NewsCollection
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
from onegov.org.models import TraitInfo
from onegov.org.models import (
    Meeting,
    MeetingItem,
    MeetingCollection,
    RISCommission,
    RISCommissionCollection,
    RISParliamentarian,
    RISParliamentarianCollection,
    RISParliamentarianRole,
    RISParliamentarianRoleCollection,
    RISParliamentaryGroup,
    RISParliamentaryGroupCollection,
    PoliticalBusiness,
    PoliticalBusinessCollection,
)
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink)
from onegov.org.models.political_business import PoliticalBusinessStatus
from onegov.org.models.political_business import PoliticalBusinessType
from onegov.org.models.resource import FindYourSpotCollection
from onegov.org.models.ticket import FilteredArchivedTicketCollection
from onegov.org.models.ticket import FilteredTicketCollection
from onegov.page import PageCollection
from onegov.pay import Payment, PaymentCollection
from onegov.pay import PaymentProvider, PaymentProviderCollection
from onegov.people import Person, PersonCollection
from onegov.qrcode import QrCode
from onegov.reservation import Allocation
from onegov.reservation import Reservation
from onegov.reservation import Resource
from onegov.reservation import ResourceCollection
from onegov.ticket import Ticket, TicketCollection, TicketInvoiceCollection
from onegov.ticket.collection import ArchivedTicketCollection
from onegov.user import Auth, User, UserCollection
from onegov.user import UserGroup, UserGroupCollection
from onegov.core.converters import datetime_converter
from uuid import UUID
from webob import exc, Response


from typing import Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from onegov.ticket.collection import ExtendedTicketState


@OrgApp.path(model=Organisation, path='/')
def get_org(app: OrgApp) -> Organisation:
    return app.org


@OrgApp.path(model=Auth, path='/auth', converters={'skip': bool})
def get_auth(
    app: OrgApp,
    to: str = '/',
    skip: bool = False,
    signup_token: str | None = None
) -> Auth:
    return Auth(app, to=to, skip=skip, signup_token=signup_token)


@OrgApp.path(model=MTANAuth, path='/mtan')
def get_mtan_auth(app: OrgApp, to: str = '/') -> MTANAuth:
    return MTANAuth(app, to=to)


@OrgApp.path(model=User, path='/benutzer/{id}', converters={'id': UUID})
def get_user(app: OrgApp, id: UUID) -> User | None:
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
def get_users(
    app: OrgApp,
    active: list[bool] | None = None,
    role: list[str] | None = None,
    tag: list[str] | None = None,
    provider: list[str] | None = None,
    source: list[str] | None = None
) -> UserCollection:
    return UserCollection(
        app.session(),
        active=active, role=role, tag=tag, provider=provider, source=source
    )


@OrgApp.path(
    model=UserGroup,
    path='/user-groups/{id}',
    converters={'id': UUID}
)
def get_user_group(app: OrgApp, id: UUID) -> UserGroup | None:
    return UserGroupCollection(app.session()).by_id(id)


@OrgApp.path(
    model=UserGroupCollection,
    path='/usergroups',
)
def get_user_groups(app: OrgApp) -> UserGroupCollection[UserGroup]:
    return UserGroupCollection(app.session())


@OrgApp.path(model=Topic, path='/topics', absorb=True)
def get_topic(app: OrgApp, absorb: str) -> Topic | None:
    return PageCollection(  # type:ignore[return-value]
        app.session()).by_path(absorb, ensure_type='topic')


@OrgApp.path(
    model=News,
    path='/news',
    absorb=True,
    converters={
        'filter_years': [datetime_year_converter],
        'filter_tags': [str],
        'page': int
    }
)
def get_news(
    request: OrgRequest,
    absorb: str,
    filter_years: list[int],
    filter_tags: list[str],
    page: int = 0,
) -> News | NewsCollection | None:

    pages = PageCollection(request.session)

    old_path = '/aktuelles/' + absorb
    new_path = '/news/' + absorb

    news: News | None = (
        pages.by_path(new_path, ensure_type='news')  # type:ignore[assignment]
        or pages.by_path(old_path, ensure_type='news')
    )
    if news is not None and news.parent_id is None and request.method == 'GET':
        return NewsCollection(
            request,
            page=page,
            filter_years=filter_years,
            filter_tags=filter_tags,
            root=news,
        )
    return news


@OrgApp.path(model=GeneralFileCollection, path='/files')
def get_files(
    request: OrgRequest,
    order_by: str = 'name'
) -> GeneralFileCollection:
    return GeneralFileCollection(request.session, order_by=order_by)


@OrgApp.path(model=ImageFileCollection, path='/images')
def get_images(app: OrgApp) -> ImageFileCollection:
    return ImageFileCollection(app.session())


@OrgApp.path(model=ExportCollection, path='/exports')
def get_exports(request: OrgRequest, app: OrgApp) -> ExportCollection:
    return ExportCollection(app)


@OrgApp.path(model=Export, path='/export/{id}')
def get_export(request: OrgRequest, app: OrgApp, id: str) -> Export | None:
    return ExportCollection(app).by_id(id)


@OrgApp.path(model=FormCollection, path='/forms')
def get_forms(app: OrgApp) -> FormCollection:
    return FormCollection(app.session())


@OrgApp.path(model=FormDefinition, path='/form/{name}')
def get_form(app: OrgApp, name: str) -> FormDefinition | None:
    return FormCollection(app.session()).definitions.by_name(name)


@OrgApp.path(model=SurveyCollection, path='/surveys')
def get_surveys(app: OrgApp) -> SurveyCollection | None:
    return SurveyCollection(app.session())


@OrgApp.path(model=SurveyDefinition, path='/survey/{name}')
def get_survey(app: OrgApp, name: str) -> SurveyDefinition | None:
    return SurveyCollection(app.session()).definitions.by_name(name)


@OrgApp.path(model=SurveySubmission, path='/survey-submission/{id}',
             converters={'id': UUID})
def get_pending_survey_submission(
    app: OrgApp,
    id: UUID
) -> SurveySubmission | None:
    return SurveyCollection(app.session()).submissions.by_id(
        id, current_only=True)


@OrgApp.path(model=PendingFormSubmission, path='/form-preview/{id}',
             converters={'id': UUID})
def get_pending_form_submission(
    app: OrgApp,
    id: UUID
) -> PendingFormSubmission | None:
    return FormCollection(app.session()).submissions.by_id(  # type:ignore
        id, state='pending', current_only=True)


@OrgApp.path(model=CompleteFormSubmission, path='/form-submission/{id}',
             converters={'id': UUID})
def get_complete_form_submission(
    app: OrgApp,
    id: UUID
) -> CompleteFormSubmission | None:
    return FormCollection(app.session()).submissions.by_id(  # type:ignore
        id, state='complete', current_only=False)


@OrgApp.path(
    model=FormRegistrationWindow,
    path='/form-registration-window/{id}',
    converters={'id': UUID})
def get_form_registration_window(
    request: OrgRequest,
    id: UUID
) -> FormRegistrationWindow | None:
    return FormCollection(request.session).registration_windows.by_id(id)


@OrgApp.path(
    model=SurveySubmissionWindow,
    path='/survey-submission-window/{id}',
    converters={'id': UUID})
def get_survey_submission_window(
    request: OrgRequest,
    id: UUID
) -> SurveySubmissionWindow | None:
    return SurveyCollection(request.session).submission_windows.by_id(id)


@OrgApp.path(model=File, path='/storage/{id}')
def get_file_for_org(
    request: OrgRequest,
    app: OrgApp,
    id: str
) -> File | None:
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
        return None

    if obj.type in protected_filetypes:
        if not request.has_role('editor', 'admin'):
            obj = None
        else:
            @request.after
            def disable_cache(response: Response) -> None:
                response.cache_control.no_cache = True
                response.cache_control.max_age = -1
                response.cache_control.public = False
                response.cache_control.private = True

    return obj


@OrgApp.path(
    model=Editor,
    path='/editor/{action}/{trait}/{page_id}',
    converters={'page_id': int}
)
def get_editor(
    app: OrgApp,
    action: str,
    trait: str,
    page_id: int = 0
) -> Editor | None:

    if not Editor.is_supported_action(action):
        return None

    if page_id:
        page = PageCollection(app.session()).by_id(page_id)
    else:
        if action != 'new' and action != 'new-root':
            return None

        # adding root element with no parent (page=None)
        return Editor(action=action,
                      page=None,
                      trait=trait)

    if not isinstance(page, TraitInfo):
        return None

    if not page.is_supported_trait(trait):  # type:ignore[unreachable]
        return None

    return Editor(action=action, page=page, trait=trait)


@OrgApp.path(model=PersonCollection, path='/people')
def get_people(app: OrgApp) -> PersonCollection:
    return PersonCollection(app.session())


@OrgApp.path(model=Person, path='/person/{id}', converters={'id': UUID})
def get_person(app: OrgApp, id: UUID) -> Person | None:
    return PersonCollection(app.session()).by_id(id)


@OrgApp.path(model=ChatCollection, path='/chats')
def get_chats(
    app: OrgApp,
    page: int = 0,
    state: str = 'active'
) -> ChatCollection:
    return ChatCollection(
        app.session(),
        page=page,
        state=state,
    )


@OrgApp.path(model=Chat, path='/chat/{id}', converters={'id': UUID})
def get_chat(app: OrgApp, id: UUID) -> Chat | None:
    return ChatCollection(app.session()).by_id(id)


@OrgApp.path(model=Ticket, path='/ticket/{handler_code}/{id}',
             converters={'id': UUID})
def get_ticket(app: OrgApp, handler_code: str, id: UUID) -> Ticket | None:
    return TicketCollection(app.session()).by_id(
        id, ensure_handler_code=handler_code)


@OrgApp.path(
    model=TicketCollection,
    path='/tickets/{handler}/{state}',
    converters={'page': int, 'state': LiteralConverter(
        'open',
        'pending',
        'closed',
        'archived',
        'all',
        'unfinished'
    )}
)
def get_tickets(
    request: OrgRequest,
    handler: str = 'ALL',
    state: ExtendedTicketState | None = 'open',
    page: int = 0,
    group: str | None = None,
    owner: str | None = None,
    submitter: str | None = None,
    q: str | None = None,
    extra_parameters: dict[str, str] | None = None
) -> TicketCollection | None:

    if state is None:
        return None

    return FilteredTicketCollection(
        request.session,
        handler=handler,
        state=state,
        page=page,
        group=group,
        owner=owner or '*',
        submitter=submitter or '*',
        term=q,
        extra_parameters=extra_parameters,
        request=request,
    )


@OrgApp.path(
    model=ArchivedTicketCollection,
    path='/tickets-archive/{handler}',
    converters={'page': int}
)
def get_archived_tickets(
    request: OrgRequest,
    handler: str = 'ALL',
    page: int = 0,
    group: str | None = None,
    owner: str | None = None,
    submitter: str | None = None,
    q: str | None = None,
    extra_parameters: dict[str, str] | None = None
) -> ArchivedTicketCollection:
    return FilteredArchivedTicketCollection(
        request.session,
        handler=handler,
        state='archived',
        page=page,
        group=group,
        owner=owner or '*',
        submitter=submitter or '*',
        term=q,
        extra_parameters=extra_parameters,
        request=request,
    )


@OrgApp.path(
    model=TicketNote,
    path='/ticket-notes/{id}')
def get_ticket_note(app: OrgApp, id: str) -> TicketNote | None:
    return MessageCollection(app.session(), type='ticket_note').by_id(id)


@OrgApp.path(model=ResourceCollection, path='/resources')
def get_resources(app: OrgApp) -> ResourceCollection:
    return app.libres_resources


@OrgApp.path(model=FindYourSpotCollection, path='/find-your-spot')
def get_find_my_spot(
    app: OrgApp,
    group: str | None = None,
    subgroup: str | None = None,
) -> FindYourSpotCollection:
    return FindYourSpotCollection(
        app.libres_context,
        group=group,
        subgroup=subgroup
    )


@OrgApp.path(
    model=Resource,
    path='/resource/{name}',
    converters={
        'date': date,
        'highlights_min': int,
        'highlights_max': int
    }
)
def get_resource(
    app: OrgApp,
    name: str,
    date: date | None = None,
    view: str | None = None,
    highlights_min: int | None = None,
    highlights_max: int | None = None
) -> Resource | None:

    resource = app.libres_resources.by_name(name)

    if resource:
        resource.date = date
        resource.highlights_min = highlights_min
        resource.highlights_max = highlights_max
        resource.view = view or resource.default_view or 'timeGridWeek'

    return resource


@OrgApp.path(model=Allocation, path='/allocation/{resource}/{id}',
             converters={'resource': UUID, 'id': int})
def get_allocation(app: OrgApp, resource: UUID, id: int) -> Allocation | None:
    res = app.libres_resources.by_id(resource)

    if res is not None:
        allocation = res.scheduler.allocations_by_ids((id, )).first()

        # always get the master, even if another id is requested
        return allocation and allocation.get_master()  # type:ignore
    return None


@OrgApp.path(model=Reservation, path='/reservation/{resource}/{id}',
             converters={'resource': UUID, 'id': int})
def get_reservation(
    app: OrgApp,
    resource: UUID,
    id: int
) -> Reservation | None:

    res = app.libres_resources.by_id(resource)

    if res is not None:
        query = res.scheduler.managed_reservations()
        query = query.filter(Reservation.id == id)

        return query.first()  # type:ignore[return-value]
    return None


@OrgApp.path(model=Clipboard, path='/clipboard/copy/{token}')
def get_clipboard(request: OrgRequest, token: str) -> Clipboard | None:
    clipboard = Clipboard(request, token)

    # the url is None if the token is invalid
    if clipboard.url:
        return clipboard
    return None


@OrgApp.path(model=SiteCollection, path='/sitecollection')
def get_sitecollection(app: OrgApp) -> SiteCollection:
    return SiteCollection(app.session())


@OrgApp.path(
    model=PageMove,
    path='/move/page/{subject_id}/{direction}/{target_id}',
    converters={
        'subject_id': int,
        'target_id': int,
        'direction': MoveDirection,
    }
)
def get_page_move(
    app: OrgApp,
    subject_id: int,
    direction: MoveDirection,
    target_id: int
) -> PageMove | None:

    if subject_id == target_id:
        raise exc.HTTPBadRequest()

    session = app.session()
    pages = PageCollection(session)

    subject = pages.by_id(subject_id)
    target = pages.by_id(target_id)

    if subject and target:
        return PageMove(session, subject, target, direction)
    return None


@OrgApp.path(
    model=PagePersonMove,
    path='/move/page-person/{key}/{subject}/{direction}/{target}',
    converters={'key': int, 'direction': MoveDirection}
)
def get_person_move(
    app: OrgApp,
    key: int,
    subject: str,
    direction: MoveDirection,
    target: str
) -> PagePersonMove | None:

    if subject == target:
        raise exc.HTTPBadRequest()

    session = app.session()
    page = PageCollection(session).by_id(key)

    if isinstance(page, PersonLinkExtension):
        return PagePersonMove(  # type:ignore[unreachable]
            session,
            page,
            subject,
            target,
            direction
        )
    return None


@OrgApp.path(
    model=FormPersonMove,
    path='/move/form-person/{key}/{subject}/{direction}/{target}',
    converters={'direction': MoveDirection}
)
def get_form_move(
    app: OrgApp,
    key: str,
    subject: str,
    direction: MoveDirection,
    target: str
) -> FormPersonMove | None:

    session = app.session()
    form = FormCollection(session).definitions.by_name(key)

    if isinstance(form, PersonLinkExtension):
        return FormPersonMove(  # type:ignore[unreachable]
            session,
            form,
            subject,
            target,
            direction
        )
    return None


@OrgApp.path(
    model=ResourcePersonMove,
    path='/move/resource-person/{key}/{subject}/{direction}/{target}',
    converters={'key': UUID, 'direction': MoveDirection}
)
def get_resource_move(
    app: OrgApp,
    key: UUID,
    subject: str,
    direction: MoveDirection,
    target: str
) -> ResourcePersonMove | None:

    session = app.session()
    resource = ResourceCollection(app.libres_context).by_id(key)

    if isinstance(resource, PersonLinkExtension):
        return ResourcePersonMove(  # type:ignore[unreachable]
            session,
            resource,
            subject,
            target,
            direction
        )
    return None


@OrgApp.path(
    model=OccurrenceCollection, path='/events',
    converters={
        'page': int,
        'range': LiteralConverter(DateRange),
        'start': extended_date_converter,
        'end': extended_date_converter,
        'tags': [],
        'filter_keywords': keywords_converter,
        'locations': [],
        'search_query': json_converter,
    }
)
def get_occurrences(
    app: OrgApp,
    request: OrgRequest,
    page: int = 0,
    range: DateRange | None = None,
    start: date | None = None,
    end: date | None = None,
    tags: list[str] | None = None,
    filter_keywords: dict[str, list[str]] | None = None,
    locations: list[str] | None = None,
    search: str | None = None,
    search_query: dict[str, Any] | None = None
) -> OccurrenceCollection:

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
def get_occurrence(app: OrgApp, name: str) -> Occurrence | None:
    return OccurrenceCollection(app.session()).by_name(name)


@OrgApp.path(model=Event, path='/event-management/{name}')
def get_event(app: OrgApp, name: str) -> Event | None:
    return EventCollection(app.session()).by_name(name)


@OrgApp.path(
    model=Search,
    path='/search',
    converters={
        'type': [str],
        'page': int
    }
)
def get_search(
    request: OrgRequest,
    q: str = '',
    type: list[str] | None = None,
    page: int = 0
) -> Search:
    return Search(request, q, types=type, page=page)


@OrgApp.path(model=AtoZPages, path='/a-z')
def get_a_to_z(request: OrgRequest) -> AtoZPages:
    return AtoZPages(request)


@OrgApp.path(model=NewsletterCollection, path='/newsletters')
def get_newsletters(app: OrgApp) -> NewsletterCollection:
    return NewsletterCollection(app.session())


@OrgApp.path(model=Newsletter, path='/newsletter/{name}')
def get_newsletter(app: OrgApp, name: str) -> Newsletter | None:
    return get_newsletters(app).by_name(name)


@OrgApp.path(model=RecipientCollection, path='/subscribers')
def get_newsletter_recipients(app: OrgApp) -> RecipientCollection:
    return RecipientCollection(app.session())


@OrgApp.path(model=Subscription, path='/abonnement/{recipient_id}/{token}',
             converters={'recipient_id': UUID})
def get_subscription(
    app: OrgApp,
    recipient_id: UUID,
    token: str
) -> Subscription | None:
    recipient = RecipientCollection(app.session()).by_id(recipient_id)
    return Subscription(recipient, token) if recipient else None


@OrgApp.path(model=EntrySubscription,
             path='/entry_subscription/{recipient_id}/{token}',
             converters={'recipient_id': UUID})
def get_entry_subscription(
    app: OrgApp,
    recipient_id: UUID,
    token: str
) -> EntrySubscription | None:
    recipient = EntryRecipientCollection(app.session()).by_id(recipient_id)
    return EntrySubscription(recipient, token) if recipient else None


@OrgApp.path(model=LegacyFile, path='/file/{filename}')
def get_legacy_file(app: OrgApp, filename: str) -> LegacyFile | None:
    return LegacyFileCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=LegacyImage, path='/image/{filename}')
def get_image(app: OrgApp, filename: str) -> LegacyImage | None:
    return LegacyImageCollection(app).get_file_by_filename(filename)


@OrgApp.path(model=ImageSetCollection, path='/photoalbums')
def get_image_sets(app: OrgApp) -> ImageSetCollection:
    return ImageSetCollection(app.session())


@OrgApp.path(model=ImageSet, path='/photoalbum/{id}')
def get_image_set(app: OrgApp, id: str) -> ImageSet | None:
    return ImageSetCollection(app.session()).by_id(id)


@OrgApp.path(
    model=ResourceRecipientCollection,
    path='/resource-recipients')
def get_resource_recipient_collection(
    app: OrgApp
) -> ResourceRecipientCollection:
    return ResourceRecipientCollection(app.session())


@OrgApp.path(
    model=ResourceRecipient,
    path='/resource-recipient/{id}',
    converters={'id': UUID})
def get_resource_recipient(app: OrgApp, id: UUID) -> ResourceRecipient | None:
    return ResourceRecipientCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentProviderCollection,
    path='/payment-provider')
def get_payment_provider_collection(
    app: OrgApp
) -> PaymentProviderCollection | None:
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session())
    return None


@OrgApp.path(
    model=PaymentProvider,
    path='/payment-provider-entry/{id}',
    converters={'id': UUID})
def get_payment_provider(
    app: OrgApp,
    id: UUID
) -> PaymentProvider[Payment] | None:
    if app.payment_providers_enabled:
        return PaymentProviderCollection(app.session()).by_id(id)
    return None


@OrgApp.path(
    model=Payment,
    path='/payment/{id}',
    converters={'id': UUID})
def get_payment(app: OrgApp, id: UUID) -> Payment | None:
    return PaymentCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PaymentCollection,
    path='/payments',
    converters={
        'page': int,
        'start': datetime_converter,
        'end': datetime_converter,
        'status': str,
        'payment_type': str,
        'ticket_group': [str],
        'ticket_start': extended_date_converter,
        'ticket_end': extended_date_converter,
        'reservation_start': extended_date_converter,
        'reservation_end': extended_date_converter
    }
)
def get_payments(
    app: OrgApp,
    source: str = '*',
    page: int = 0,
    start: datetime | None = None,
    end: datetime | None = None,
    status: str | None = None,
    payment_type: str | None = None,
    ticket_group: list[str] | None = None,
    ticket_start: date | None = None,
    ticket_end: date | None = None,
    reservation_start: date | None = None,
    reservation_end: date | None = None
) -> PaymentCollection:
    return PaymentCollection(
        session=app.session(),
        source=source,
        page=page,
        start=start,
        end=end,
        status=status,
        payment_type=payment_type,
        ticket_group=ticket_group,
        ticket_start=ticket_start,
        ticket_end=ticket_end,
        reservation_start=reservation_start,
        reservation_end=reservation_end
    )


@OrgApp.path(
    model=TicketInvoiceCollection,
    path='/invoices',
    converters={
        'page': int,
        'ticket_group': [str],
        'ticket_start': extended_date_converter,
        'ticket_end': extended_date_converter,
        'reservation_start': extended_date_converter,
        'reservation_end': extended_date_converter,
        'has_payment': bool,
        'invoiced': bool,
    }
)
def get_invoices(
    app: OrgApp,
    page: int = 0,
    ticket_group: list[str] | None = None,
    ticket_start: date | None = None,
    ticket_end: date | None = None,
    reservation_start: date | None = None,
    reservation_end: date | None = None,
    has_payment: bool | None = None,
    invoiced: bool | None = None,
) -> TicketInvoiceCollection:
    return TicketInvoiceCollection(
        session=app.session(),
        page=page,
        ticket_group=ticket_group,
        ticket_start=ticket_start,
        ticket_end=ticket_end,
        reservation_start=reservation_start,
        reservation_end=reservation_end,
        has_payment=has_payment,
        invoiced=invoiced,
    )


@OrgApp.path(
    model=MessageCollection,
    path='/timeline',
    converters={'limit': int}
)
def get_messages(
    app: OrgApp,
    channel_id: str = '*',
    type: str = '*',
    newer_than: str | None = None,
    older_than: str | None = None,
    limit: int = 25,
    load: str = 'older-first'
) -> MessageCollection[Any]:
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
def get_text_modules(app: OrgApp) -> TextModuleCollection:
    return TextModuleCollection(app.session())


@OrgApp.path(
    model=TextModule,
    path='/text-module/{id}',
    converters={'id': UUID}
)
def get_text_module(app: OrgApp, id: UUID) -> TextModule | None:
    return TextModuleCollection(app.session()).by_id(id)


@OrgApp.path(
    model=DirectoryCollection,
    path='/directories')
def get_directories(app: OrgApp) -> DirectoryCollection[ExtendedDirectory]:
    return DirectoryCollection(app.session(), type='extended')


@OrgApp.path(
    model=Directory,
    path='/directory/{name}')
def get_directory(app: OrgApp, name: str) -> Directory | None:
    return DirectoryCollection(app.session(), type='extended').by_name(name)


@OrgApp.path(
    model=ExtendedDirectoryEntryCollection,
    path='/directories/{directory_name}',
    converters={
        'page': int,
        'keywords': keywords_converter,
        'search_query': json_converter,
        'published_only': bool,
        'past_only': bool,
        'upcoming_only': bool
    })
def get_directory_entries(
    request: OrgRequest,
    app: OrgApp,
    directory_name: str,
    keywords: dict[str, list[str]],
    page: int = 0,
    search: str | None = None,
    search_query: dict[str, Any] | None = None,
    published_only: bool = False,
    past_only: bool = False,
    upcoming_only: bool = False
) -> ExtendedDirectoryEntryCollection | None:

    directory = DirectoryCollection(app.session()).by_name(directory_name)
    if not isinstance(directory, ExtendedDirectory):
        return None

    if not search:
        search = app.settings.org.default_directory_search_widget

    if search and search in app.config.directory_search_widget_registry:
        cls = app.config.directory_search_widget_registry[search]
        search_widget = cls(request, directory, search_query)
    else:
        search_widget = None

    if not published_only and not request.is_manager:
        published_only = True

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

    collection.access = directory.access  # type:ignore[attr-defined]
    return collection


@OrgApp.path(
    model=DirectoryEntry,
    path='/directories/{directory_name}/{name}')
def get_directory_entry(
    app: OrgApp,
    directory_name: str,
    name: str
) -> DirectoryEntry | None:

    directory = DirectoryCollection(app.session()).by_name(directory_name)

    if isinstance(directory, ExtendedDirectory):
        return ExtendedDirectoryEntryCollection(
            directory=directory,
            type='extended'
        ).by_name(name)
    return None


@OrgApp.path(
    model=DirectorySubmissionAction,
    path='/directory-submission/{directory_id}/{submission_id}/{action}',
    converters={'directory_id': UUID, 'submission_id': UUID})
def get_directory_submission_action(
    app: OrgApp,
    directory_id: UUID,
    submission_id: UUID,
    action: str
) -> DirectorySubmissionAction | None:

    submission_action = DirectorySubmissionAction(
        session=app.session(),
        directory_id=directory_id,
        submission_id=submission_id,
        action=action
    )

    if submission_action.valid:
        return submission_action
    return None


@OrgApp.path(
    model=PublicationCollection,
    path='/publications',
    converters={'year': datetime_year_converter})
def get_publication_collection(
    request: OrgRequest,
    year: int | None = None
) -> PublicationCollection:
    year = year or sedate.to_timezone(sedate.utcnow(), 'Europe/Zurich').year
    return PublicationCollection(request.session, year)


@OrgApp.path(
    model=Dashboard,
    path='/dashboard')
def get_dashboard(request: OrgRequest) -> Dashboard | None:
    dashboard = Dashboard(request)

    if dashboard.is_available:
        return dashboard
    return None


@OrgApp.path(
    model=CitizenDashboard,
    path='/citizen-dashboard')
def get_citizen_dashboard(request: OrgRequest) -> CitizenDashboard | None:
    dashboard = CitizenDashboard(request)

    if dashboard.is_available:
        return dashboard
    return None


@OrgApp.path(model=ExternalLinkCollection, path='/external-links')
def get_external_link_collection(
    request: OrgRequest,
    type: str | None = None
) -> ExternalLinkCollection:
    return ExternalLinkCollection(request.session, type=type)


@OrgApp.path(model=ExternalLink, path='/external-link/{id}',
             converters={'id': UUID})
def get_external_link(request: OrgRequest, id: UUID) -> ExternalLink | None:
    return ExternalLinkCollection(request.session).by_id(id)


@OrgApp.path(model=FormDocumentCollection, path='/document-forms')
def get_document_form_collection(
    request: OrgRequest,
    type: str | None = None
) -> FormDocumentCollection:
    return FormDocumentCollection(request.session, type=type)


@OrgApp.path(model=FormDocument, path='/document-form/{name}')
def get_document_form_page(app: OrgApp, name: str) -> FormDocument | None:
    return FormDocumentCollection(app.session()).by_name(name)


@OrgApp.path(
    model=QrCode, path='/qrcode',
    converters={
        'border': int,
        'box_size': int,
        'encoding': LiteralConverter('base64')
    })
def get_qr_code(
    app: OrgApp,
    payload: str,
    border: int | None = None,
    box_size: int | None = None,
    fill_color: str | None = None,
    back_color: str | None = None,
    img_format: str | None = None,
    encoding: Literal['base64'] | None = None
) -> QrCode:
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
def get_api_key_for_delete(request: OrgRequest, key: UUID) -> ApiKey | None:
    return request.session.query(ApiKey).filter_by(key=key).first()


@OrgApp.path(model=PushNotificationCollection, path='/push-notifications')
def get_sent_notification_collection(
    request: OrgRequest,
) -> PushNotificationCollection:
    return PushNotificationCollection(request.session)


# RIS paths
@OrgApp.path(
    model=RISParliamentarianCollection,
    path='/parliamentarians',
    converters={
        'active': [bool],
        'party': [str]
    }
)
def get_parliamentarians(
    app: OrgApp,
    active: list[bool] | None = None,
    party: list[str] | None = None
) -> RISParliamentarianCollection:
    return RISParliamentarianCollection(
        app.session(),
        active=active or [True],
        party=party
    )


@OrgApp.path(
    model=RISParliamentarian,
    path='/parliamentarian/{id}',
    converters={'id': UUID}
)
def get_parliamentarian(
    app: OrgApp,
    id: UUID
) -> RISParliamentarian | None:
    return RISParliamentarianCollection(app.session()).by_id(id)


@OrgApp.path(
    model=RISParliamentarianRoleCollection,
    path='/parliamentarian-roles',
)
def get_parliamentarian_roles(
    app: OrgApp,
) -> RISParliamentarianRoleCollection:
    return RISParliamentarianRoleCollection(app.session())


@OrgApp.path(
    model=RISParliamentarianRole,
    path='/parliamentarian-role/{id}',
    converters={'id': UUID}
)
def get_parliamentarian_role(
    app: OrgApp,
    id: UUID
) -> RISParliamentarianRole | None:
    return RISParliamentarianRoleCollection(app.session()).by_id(id)


@OrgApp.path(
    model=RISParliamentaryGroupCollection,
    path='/parliamentary-groups',
    converters={'active': bool}
)
def get_parliamentary_groups(
    app: OrgApp,
    active: bool = True
) -> RISParliamentaryGroupCollection:
    return RISParliamentaryGroupCollection(app.session(), active)


@OrgApp.path(
    model=RISParliamentaryGroup,
    path='/parliamentary-group/{id}',
    converters={'id': UUID}
)
def get_parliamentary_group(
    app: OrgApp,
    id: UUID
) -> RISParliamentaryGroup | None:
    return RISParliamentaryGroupCollection(app.session()).by_id(id)


@OrgApp.path(
    model=RISCommissionCollection,
    path='/commissions',
    converters={'active': bool}
)
def get_commissions(
    app: OrgApp,
    active: bool = True
) -> RISCommissionCollection:
    return RISCommissionCollection(app.session(), active)


@OrgApp.path(
    model=RISCommission,
    path='/commission/{id}',
    converters={'id': UUID}
)
def get_commission(
    app: OrgApp,
    id: UUID
) -> RISCommission | None:
    return RISCommissionCollection(app.session()).by_id(id)


@OrgApp.path(
    model=MeetingCollection,
    path='/meetings',
    converters={'past': bool}
)
def get_meetings(
    app: OrgApp,
    past: bool = True  # show past meetings by default
) -> MeetingCollection:
    return MeetingCollection(app.session(), past)


@OrgApp.path(
    model=Meeting,
    path='/meeting/{id}',
    converters={'id': UUID}
)
def get_meeting(
    app: OrgApp,
    id: UUID
) -> Meeting | None:
    return MeetingCollection(app.session()).by_id(id)


@OrgApp.path(
    model=PoliticalBusinessCollection,
    path='/political-businesses',
    converters={
        'page': int,
        'status': [LiteralConverter(PoliticalBusinessStatus)],
        'types': [LiteralConverter(PoliticalBusinessType)],
        'years': [int],
    }
)
def get_political_businesses(
    app: OrgApp,
    page: int = 0,
    status: list[PoliticalBusinessStatus] | None = None,
    types: list[PoliticalBusinessType] | None = None,
    years: list[int] | None = None,
) -> PoliticalBusinessCollection:
    return PoliticalBusinessCollection(
        app.session(),
        page=page,
        status=status,
        types=types,
        years=years,
    )


@OrgApp.path(
    model=PoliticalBusiness,
    path='/political-business/{id}',
    converters={'id': UUID}
)
def get_political_business(
    app: OrgApp,
    id: UUID
) -> PoliticalBusiness | None:
    return PoliticalBusinessCollection(app.session()).by_id(id)


@OrgApp.path(
    model=MeetingItem,
    path='/meeting-item/{id}',
    converters={'id': UUID}
)
def get_meeting_item(
    app: OrgApp,
    id: UUID
) -> MeetingItem | None:
    session = app.session()
    res = session.query(MeetingItem).filter(MeetingItem.id == id).first()
    return res


@OrgApp.path(
    model=RISCommissionMembership,
    path='/commission-membership/{id}',
    converters={'id': UUID}
)
def get_commission_membership(
    app: OrgApp,
    id: UUID
) -> RISCommissionMembership | None:
    return RISCommissionMembershipCollection(app.session()).by_id(id)
