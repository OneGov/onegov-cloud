from __future__ import annotations

import secrets
from functools import cached_property

from onegov.core.elements import Confirm, Intercooler, Link, LinkGroup
from onegov.core.static import StaticFile
from onegov.core.utils import append_query_param, to_html_ul
from onegov.chat.collections import ChatCollection
from onegov.chat.models import Chat
from onegov.directory import DirectoryCollection, DirectoryEntry, Directory
from onegov.event import Event
from onegov.event import OccurrenceCollection, Occurrence
from onegov.org.elements import QrCodeLink, IFrameLink
from onegov.org.layout import (
    Layout as OrgLayout,
    DefaultLayout as OrgDefaultLayout,
    DefaultMailLayout as OrgDefaultMailLayout,
    AdjacencyListLayout as OrgAdjacencyListLayout,
    AllocationEditFormLayout as OrgAllocationEditFormLayout,
    AllocationRulesLayout as OrgAllocationRulesLayout,
    ArchivedTicketsLayout as OrgArchivedTicketsLayout,
    DashboardLayout as OrgDashboardLayout,
    DirectoryCollectionLayout as OrgDirectoryCollectionLayout,
    DirectoryLayout as OrgDirectoryLayout,
    DirectoryEntryCollectionLayout as OrgDirectoryEntryCollectionLayout,
    DirectoryEntryLayout as OrgDirectoryEntryLayout,
    EditorLayout as OrgEditorLayout,
    EventLayout as OrgEventLayout,
    ExportCollectionLayout as OrgExportCollectionLayout,
    ExternalLinkLayout as OrgExternalLinkLayout,
    FindYourSpotLayout as OrgFindYourSpotLayout,
    FormCollectionLayout as OrgFormCollectionLayout,
    FormDefinitionLayout as OrgFormDefinitionLayout,
    SurveyCollectionLayout as OrgSurveyCollectionLayout,
    FormEditorLayout as OrgFormEditorLayout,
    FormSubmissionLayout as OrgFormSubmissionLayout,
    SurveySubmissionLayout as OrgSurveySubmissionLayout,
    SurveySubmissionWindowLayout as OrgSurveySubmissionWindowLayout,
    FormDocumentLayout as OrgFormDocumentLayout,
    HomepageLayout as OrgHomepageLayout,
    ImageSetCollectionLayout as OrgImageSetCollectionLayout,
    ImageSetLayout as OrgImageSetLayout,
    MessageCollectionLayout as OrgMessageCollectionLayout,
    NewsLayout as OrgNewsLayout,
    NewsletterLayout as OrgNewsletterLayout,
    PageLayout as OrgTopicLayout,
    PaymentCollectionLayout as OrgPaymentCollectionLayout,
    PaymentProviderLayout as OrgPaymentProviderLayout,
    PersonCollectionLayout as OrgPersonCollectionLayout,
    PersonLayout as OrgPersonLayout,
    PublicationLayout as OrgPublicationLayout,
    OccurrenceLayout as OrgOccurrenceLayout,
    OccurrencesLayout as OrgOccurrencesLayout,
    RecipientLayout as OrgRecipientLayout,
    ReservationLayout as OrgReservationLayout,
    ResourceLayout as OrgResourceLayout,
    ResourcesLayout as OrgResourcesLayout,
    ResourceRecipientsLayout as OrgResourceRecipientsLayout,
    ResourceRecipientsFormLayout as OrgResourceRecipientsFormLayout,
    SettingsLayout as OrgSettingsLayout,
    TextModuleLayout as OrgTextModuleLayout,
    TextModulesLayout as OrgTextModulesLayout,
    TicketChatMessageLayout as OrgTicketChatMessageLayout,
    TicketInvoiceLayout as OrgTicketInvoiceLayout,
    TicketInvoiceCollectionLayout as OrgTicketInvoiceCollectionLayout,
    TicketLayout as OrgTicketLayout,
    TicketNoteLayout as OrgTicketNoteLayout,
    TicketsLayout as OrgTicketsLayout,
    UserLayout as OrgUserLayout,
    UserGroupLayout as OrgUserGroupLayout,
    UserGroupCollectionLayout as OrgUserGroupCollectionLayout,
    UserManagementLayout as OrgUserManagementLayout)
from onegov.form import FormDefinition
from onegov.org.models import GeneralFile
from onegov.org.models import ImageSet
from onegov.org.models import Meeting
from onegov.org.models import MeetingCollection
from onegov.org.models import MeetingItem
from onegov.org.models import News
from onegov.org.models import PageMove
from onegov.org.models import PoliticalBusiness
from onegov.org.models import PoliticalBusinessCollection
from onegov.org.models import RISCommission
from onegov.org.models import RISCommissionCollection
from onegov.org.models import RISParliamentarian
from onegov.org.models import RISParliamentarianCollection
from onegov.org.models import RISParliamentaryGroup
from onegov.org.models import RISParliamentaryGroupCollection
from onegov.org.models import Topic
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.page import PageCollection
from onegov.people import Person
from onegov.reservation import Resource
from onegov.stepsequence import step_sequences
from onegov.stepsequence.extension import StepsLayoutExtension
from onegov.ticket import Ticket
from onegov.user import User
from onegov.town6 import _
from onegov.town6.theme import user_options
from onegov.town6.request import TownRequest
from onegov.town6 import TownApp


from typing import Any, NamedTuple, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from onegov.form import FormSubmission
    from onegov.form.models.definition import SurveyDefinition
    from onegov.form.models.submission import SurveySubmission
    from onegov.org.models import ExtendedDirectoryEntry
    from onegov.org.request import PageMeta
    from onegov.page import Page
    from typing import TypeAlias

    NavigationEntry: TypeAlias = tuple[
        PageMeta,
        Link,
        tuple['NavigationEntry', ...]
    ]

T = TypeVar('T')


class PartnerCard(NamedTuple):
    url: str | None
    image_url: str | None
    lead: str | None


class Layout(OrgLayout):

    app: TownApp
    request: TownRequest

    def __init__(self, model: Any, request: TownRequest,
                 edit_mode: bool = False) -> None:
        super().__init__(model, request)
        self.request.include('foundation6')
        self.edit_mode = edit_mode

    @property
    def primary_color(self) -> str:
        return (self.org.theme_options or {}).get(
            'primary-color-ui', user_options['primary-color-ui'])

    @cached_property
    def font_awesome_path(self) -> str:
        return self.request.link(StaticFile(
            'font-awesome5/css/all.min.css',
            version=self.app.version
        ))

    @cached_property
    def sentry_init_path(self) -> str:
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    @cached_property
    def drilldown_back(self) -> str:
        back = self.request.translate(_('back'))
        return (
            '<li class="js-drilldown-back">'
            f'<a tabindex="0">{back}</a></li>'
        )

    @property
    def on_homepage(self) -> bool:
        return self.request.url == self.homepage_url

    @property
    def partners(self) -> list[PartnerCard]:
        partner_attrs = [key for key in dir(self.org) if 'partner' in key]
        partner_count = int(len(partner_attrs) / 3)

        return [
            PartnerCard(
                url=url,
                image_url=image_url,
                lead=lead,
            )
            for ix in range(1, partner_count + 1)
            if any((
                (url := getattr(self.org, f'partner_{ix}_url')),
                (image_url := getattr(self.org, f'partner_{ix}_img')),
                (lead := getattr(self.org, f'partner_{ix}_name')),
            ))
        ]

    @property
    def show_partners(self) -> bool:
        if self.on_homepage:
            if '<partner' in (self.org.homepage_structure or ''):
                # The widget is rendered
                return False
        if self.org.always_show_partners and not self.request.is_admin:
            return True
        return False

    @cached_property
    def search_keybindings_help(self) -> str:
        return self.request.translate(
            _('Press ${shortcut} to open Search',
              mapping={'shortcut': 'Ctrl+Shift+F / Ctrl+Shift+S'})
        )

    @cached_property
    def page_collection(self) -> PageCollection:
        return PageCollection(self.request.session)

    def page_by_path(self, path: str) -> Page | None:
        return self.page_collection.by_path(path)


class DefaultLayout(OrgDefaultLayout, Layout):

    if TYPE_CHECKING:
        app: TownApp
        request: TownRequest

        def __init__(self, model: Any, request: TownRequest) -> None: ...

    @cached_property
    def top_navigation(self) -> tuple[NavigationEntry, ...]:  # type:ignore

        def yield_children(page: PageMeta) -> NavigationEntry:
            if page.type != 'news':
                children = tuple(
                    yield_children(p)
                    for p in page.children
                )
            else:
                children = ()
            return (
                page,
                Link(page.title, page.link(self.request)),
                children
            )

        return tuple(yield_children(page) for page in self.root_pages)

    @cached_property
    def sortable_url_template(self) -> str:
        return self.csrf_protected_url(
            self.request.class_link(
                PageMove,
                {
                    'subject_id': '{subject_id}',
                    'target_id': '{target_id}',
                    'direction': '{direction}'
                }
            )
        )

    @cached_property
    def ris_overview_url(self) -> str:
        if self.request.is_logged_in:
            return self.request.link(self.request.app.org, 'ris-settings')

        if self.request.app.org.ris_main_url:
            return self.request.link(
                self.request.app.org, self.request.app.org.ris_main_url
            )

        # fallback to the homepage
        return self.request.link(self.request.app.org, '')


class DefaultMailLayout(OrgDefaultMailLayout, Layout):
    """ A special layout for creating HTML E-Mails. """
    app: TownApp
    request: TownRequest


class AdjacencyListLayout(OrgAdjacencyListLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class SettingsLayout(OrgSettingsLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=Topic, request=TownRequest)
class PageLayout(OrgTopicLayout, AdjacencyListLayout):

    app: TownApp
    request: TownRequest

    @cached_property
    def contact_html(self) -> str:
        return self.model.contact_html or to_html_ul(
            self.org.contact
        )


@TownApp.layout(model=News, request=TownRequest)
class NewsLayout(OrgNewsLayout, AdjacencyListLayout):

    app: TownApp
    request: TownRequest

    @cached_property
    def contact_html(self) -> str:
        return self.model.contact_html or to_html_ul(
            self.org.contact, convert_dashes=False
        )


class EditorLayout(OrgEditorLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class FormEditorLayout(OrgFormEditorLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@step_sequences.registered_step(
    1, _('Form'), cls_after='FormSubmissionLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='FormSubmissionLayout',
    cls_after='TicketChatMessageLayout'
)
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='DirectoryEntryCollectionLayout',
    cls_after='TicketChatMessageLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='EventLayout',
    cls_after='TicketChatMessageLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='DirectoryEntryLayout',
    cls_after='TicketChatMessageLayout'
)
class FormSubmissionLayout(
    StepsLayoutExtension,
    OrgFormSubmissionLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest
    model: FormSubmission | FormDefinition

    if TYPE_CHECKING:
        def __init__(
            self,
            model: FormSubmission | FormDefinition,
            request: TownRequest,
            title: str | None = None,
            *,
            hide_steps: bool = False
        ) -> None: ...

    @property
    def step_position(self) -> int | None:
        if self.request.view_name == 'send-message':
            return None
        if self.model.__class__.__name__ == 'CustomFormDefinition':
            return 1
        return 2


class SurveySubmissionLayout(
    StepsLayoutExtension,
    OrgSurveySubmissionLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest
    model: SurveySubmission | SurveyDefinition

    if TYPE_CHECKING:
        def __init__(
            self,
            model: SurveySubmission | SurveyDefinition,
            request: TownRequest,
            title: str | None = None,
            *,
            hide_steps: bool = False
        ) -> None: ...

    @property
    def step_position(self) -> int | None:
        if self.request.view_name == 'send-message':
            return None
        if self.model.__class__.__name__ == 'SurveyDefinition':
            return 1
        return 2


class FormDocumentLayout(OrgFormDocumentLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class FormCollectionLayout(OrgFormCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=FormDefinition, request=TownRequest)
class FormDefinitionLayout(OrgFormDefinitionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class SurveySubmissionWindowLayout(OrgSurveySubmissionWindowLayout,
                                   DefaultLayout):

    app: TownApp
    request: TownRequest


class SurveyCollectionLayout(OrgSurveyCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class PersonCollectionLayout(OrgPersonCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=Person, request=TownRequest)
class PersonLayout(OrgPersonLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class TicketsLayout(OrgTicketsLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ArchivedTicketsLayout(OrgArchivedTicketsLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=Ticket, request=TownRequest)
class TicketLayout(OrgTicketLayout, DefaultLayout):

    app: TownApp
    request: TownRequest

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        links = super().editbar_links
        if links is not None and self.request.is_manager:
            if self.request.app.org.gever_endpoint:
                links.append(
                    Link(
                        text=_('Upload to Gever'),
                        url=self.request.link(self.model, 'send-to-gever'),
                        attrs={'class': 'upload'},
                        traits=(
                            Confirm(
                                _('Do you really want to upload this ticket?'),
                                _('This will upload this ticket to the '
                                  'Gever instance, if configured.'),
                                _('Upload Ticket'),
                                _('Cancel')
                            )
                        )
                    )
                )
        return links


class TicketNoteLayout(OrgTicketNoteLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class TicketInvoiceLayout(OrgTicketInvoiceLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='FormSubmissionLayout')
@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='EventLayout')
@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='ReservationLayout')
class TicketChatMessageLayout(
    StepsLayoutExtension,
    OrgTicketChatMessageLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest
    if TYPE_CHECKING:
        def __init__(
            self,
            model: Ticket,
            request: TownRequest,
            internal: bool = False,
            *,
            hide_steps: bool = False,
        ) -> None: ...

    @property
    def step_position(self) -> int:
        return 3


class TextModulesLayout(OrgTextModulesLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class TextModuleLayout(OrgTextModuleLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ResourcesLayout(OrgResourcesLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class FindYourSpotLayout(OrgFindYourSpotLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ResourceRecipientsLayout(OrgResourceRecipientsLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ResourceRecipientsFormLayout(
    OrgResourceRecipientsFormLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=Resource, request=TownRequest)
class ResourceLayout(OrgResourceLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@step_sequences.registered_step(
    1, _('Form'), cls_after='ReservationLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='ReservationLayout', cls_after='TicketChatMessageLayout')
class ReservationLayout(
    StepsLayoutExtension,
    OrgReservationLayout,
    ResourceLayout
):

    app: TownApp
    request: TownRequest
    editbar_links = None

    if TYPE_CHECKING:
        def __init__(
            self,
            model: Resource,
            request: TownRequest,
            *,
            hide_steps: bool = False,
        ) -> None: ...

    @property
    def step_position(self) -> int | None:
        """ Note the last step is the ticket status page with step 3. """
        view_name = self.request.view_name
        if view_name == 'form':
            return 1
        if view_name == 'confirmation':
            return 2
        return None


class AllocationRulesLayout(OrgAllocationRulesLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class AllocationEditFormLayout(OrgAllocationEditFormLayout, DefaultLayout):
    """ Same as the resource layout, but with different editbar links, because
    there's not really an allocation view, but there are allocation forms.

    """
    app: TownApp
    request: TownRequest


class OccurrencesLayout(OrgOccurrencesLayout, DefaultLayout):

    app: TownApp
    request: TownRequest

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links = super().editbar_links
        if self.request.is_manager:
            links.append(
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Event'),
                            url=self.request.link(self.model, 'enter-event'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                )
            )
        return links


@TownApp.layout(model=Occurrence, request=TownRequest)
class OccurrenceLayout(OrgOccurrenceLayout, DefaultLayout):

    app: TownApp
    request: TownRequest

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        links = super().editbar_links or []
        if self.request.is_manager:
            copy_url = self.request.link(
                OccurrenceCollection(self.request.session), 'enter-event')
            copy_url = append_query_param(copy_url,
                                          'event_id', self.model.event.id.hex)

            links.append(
                Link(
                    text=_('Copy'),
                    url=copy_url,
                    attrs={'class': 'copy-link'}
                )
            )
        return links


@step_sequences.registered_step(1, _('Form'), cls_after='FormSubmissionLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='EventLayout',
    cls_after='TicketChatMessageLayout'
)
@TownApp.layout(model=Event, request=TownRequest)
class EventLayout(StepsLayoutExtension, OrgEventLayout, DefaultLayout):

    app: TownApp
    request: TownRequest
    model: Event

    if TYPE_CHECKING:
        def __init__(
            self,
            model: Event,
            request: TownRequest,
            *,
            hide_steps: bool = False
        ) -> None: ...

    @property
    def step_position(self) -> int:
        if self.request.view_name == 'new':
            return 1
        return 2


class NewsletterLayout(OrgNewsletterLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class RecipientLayout(OrgRecipientLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ImageSetCollectionLayout(OrgImageSetCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=ImageSet, request=TownRequest)
class ImageSetLayout(OrgImageSetLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class UserManagementLayout(OrgUserManagementLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=User, request=TownRequest)
class UserLayout(OrgUserLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class UserGroupCollectionLayout(OrgUserGroupCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class UserGroupLayout(OrgUserGroupLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ExportCollectionLayout(OrgExportCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class PaymentProviderLayout(OrgPaymentProviderLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class PaymentCollectionLayout(OrgPaymentCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class TicketInvoiceCollectionLayout(
    OrgTicketInvoiceCollectionLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest


class MessageCollectionLayout(OrgMessageCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class DirectoryCollectionLayout(OrgDirectoryCollectionLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=Directory, request=TownRequest)
class DirectoryLayout(OrgDirectoryLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@step_sequences.registered_step(
    1, _('Form'), cls_after='FormSubmissionLayout'
)
class DirectoryEntryCollectionLayout(
    StepsLayoutExtension,
    OrgDirectoryEntryCollectionLayout,
    DefaultLayout
):

    if TYPE_CHECKING:
        app: TownApp
        request: TownRequest

        def __init__(
            self,
            model: ExtendedDirectoryEntryCollection,
            request: TownRequest,
            *,
            hide_steps: bool = False,
        ) -> None: ...

    @property
    def step_position(self) -> int:
        return 1

    # FIXME: Is there a reason we don't add the export link in Town6?
    #        If not then just delete this method and use the one from Org
    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:

        export_link = Link(
            text=_('Export'),
            url=self.request.link(self.model, name='+export'),
            attrs={'class': 'export-link'}
        )

        def links() -> Iterator[Link | LinkGroup]:
            qr_link = None
            if self.request.is_admin:
                yield Link(
                    text=_('Configure'),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                )

            if self.request.is_manager:
                yield export_link

                yield Link(
                    text=_('Import'),
                    url=self.request.class_link(
                        ExtendedDirectoryEntryCollection, {
                            'directory_name': self.model.directory_name
                        }, name='+import'
                    ),
                    attrs={'class': 'import-link'}
                )

                qr_link = QrCodeLink(
                    text=_('QR'),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                )

            if self.request.is_admin:
                yield Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete "${title}"?',
                                mapping={
                                    'title': self.model.directory.title
                                }
                            ),
                            _('All entries will be deleted as well!'),
                            _('Delete directory'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                DirectoryCollection
                            )
                        )
                    )
                )
                yield Link(
                    text=self.request.translate(_('Change URL')),
                    url=self.request.link(
                        self.model.directory,
                        'change-url'),
                    attrs={'class': 'internal-url'},
                )

            if self.request.is_manager:
                yield LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Entry'),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-directory-entry'}
                        )
                    ]
                )

            if qr_link:
                yield qr_link
            if self.request.is_manager:
                yield IFrameLink(
                    text=_('iFrame'),
                    url=self.request.link(self.model),
                    attrs={'class': 'new-iframe'}
                )

        return list(links())


@step_sequences.registered_step(1, _('Form'), cls_after='FormSubmissionLayout')
@TownApp.layout(model=DirectoryEntry, request=TownRequest)
class DirectoryEntryLayout(
    StepsLayoutExtension,
    OrgDirectoryEntryLayout,
    DefaultLayout
):

    app: TownApp
    request: TownRequest

    if TYPE_CHECKING:
        def __init__(
            self,
            model: ExtendedDirectoryEntry,
            request: TownRequest,
            *,
            hide_steps: bool = False
        ) -> None: ...

    @property
    def step_position(self) -> int:
        return 1


class PublicationLayout(OrgPublicationLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class DashboardLayout(OrgDashboardLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


@TownApp.layout(model=GeneralFile, request=TownRequest)
class GeneralFileCollectionLayout(DefaultLayout):

    def __init__(self, model: Any, request: TownRequest) -> None:
        """
        The order of assets differ from org where common.js must come first
        including jquery. Here, the foundation6 assets contain jquery and must
        come first.
        """
        super().__init__(model, request)
        request.include('upload')
        request.include('prompt')

    @cached_property
    def breadcrumbs(self) -> Sequence[Link]:
        name = self.model.name[:40]
        if len(name) == 40:
            name = name[:37] + '...'

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Files'), self.files_url),
            Link(name, self.files_url_with_anchor(self.model)),
        ]


class ImageFileCollectionLayout(DefaultLayout):

    def __init__(self, model: Any, request: TownRequest) -> None:
        super().__init__(model, request)
        request.include('upload')
        request.include('editalttext')


class ExternalLinkLayout(OrgExternalLinkLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class HomepageLayout(OrgHomepageLayout, DefaultLayout):

    app: TownApp
    request: TownRequest


class ChatLayout(DefaultLayout):

    def __init__(self, model: Any, request: TownRequest) -> None:
        super().__init__(model, request)

        token = self.make_websocket_token()

        # Make token available to JavaScript when creating the WebSocket
        # connection.
        self.custom_body_attributes['data-websocket-token'] = token

        # Store the WebSocket token in the session check when the connection is
        # initiated.
        request.browser_session['websocket_token'] = token

    def make_websocket_token(self) -> str:
        """
        A user (authenticated or anonymous) attempts to create a chat
        connection. For the connection to succeed, they must present a one-time
        token to the WebSocket server.

        TODO: Add lifespan to the token?
        """
        return secrets.token_hex(16)


class StaffChatLayout(ChatLayout):

    def __init__(self, model: Any, request: TownRequest) -> None:
        super().__init__(model, request)
        self.request.include('websockets')
        self.request.include('staff-chat')

        self.custom_body_attributes['data-websocket-endpoint'] = (
            self.app.websockets_client_url(request))

        self.custom_body_attributes['data-websocket-schema'] = (
            self.app.schema)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Chats'), self.request.link(
                self.request.app.org, name='chats'
            ))
        ]


class ClientChatLayout(ChatLayout):

    def __init__(self, model: Any, request: TownRequest) -> None:
        super().__init__(model, request)
        self.request.include('websockets')
        self.request.include('client-chat')

        self.custom_body_attributes['data-websocket-endpoint'] = (
            self.app.websockets_client_url(request))
        self.custom_body_attributes['data-websocket-schema'] = (
            self.app.schema)


class ChatInitiationFormLayout(DefaultLayout):
    pass


class ArchivedChatsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        bc = [
            Link(_('Homepage'), self.homepage_url),
            Link(
                _('Chat Archive'),
                self.request.class_link(
                    ChatCollection, {
                        'state': 'archived',
                    },
                    name='archive'
                ),
                attrs={
                    'class': ('chats'),
                }
            )
        ]

        if isinstance(self.model, Chat):
            bc.append(
                Link(self.model.customer_name, self.request.link(
                    self.model, 'staff-view'
                ))
            )

        return bc


class MeetingCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Meetings')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model)),
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Meeting'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-meeting'},
                        ),
                    ],
                ),
            ]
        return None


@TownApp.layout(model=Meeting, request=TownRequest)
class MeetingLayout(DefaultLayout):

    @cached_property
    def collection(self) -> MeetingCollection:
        return MeetingCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.title

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        title = (
            self.title + ' - ' +
            self.format_date(self.model.start_datetime, 'date')
            if self.model.start_datetime
            else self.title
        )

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(_('Meetings'), self.request.class_link(MeetingCollection)),
            Link(title, self.request.link(self.model)),
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'},
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(self.request.link(self.model)),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this meeting?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete meeting'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.collection
                            )
                        )
                    )
                ),
                Link(
                    text=_('Export'),
                    url=self.request.link(self.model, name='+export'),
                    attrs={'class': 'export-link'}
                )
            ]
        return None


@TownApp.layout(model=MeetingItem, request=TownRequest)
class MeetingItemLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        title = (
            self.model.meeting.title + ' - ' +
            self.format_date(self.model.meeting.start_datetime, 'date')
            if self.model.meeting.start_datetime
            else self.model.meeting.title
        )

        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(
                _('Meetings'),
                self.request.class_link(MeetingCollection)
            ),
            Link(
                title,
                self.request.link(self.model, fragment=self.model.title))
        ]


class RISParliamentarianCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Parliamentarians')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Parliamentarian'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-parliamentarian'},
                        ),
                    ],
                ),
            ]
        return None


@TownApp.layout(model=RISParliamentarian, request=TownRequest)
class RISParliamentarianLayout(DefaultLayout):

    @cached_property
    def collection(self) -> RISParliamentarianCollection:
        return RISParliamentarianCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return f'{self.model.first_name} {self.model.last_name}'

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(
                _('Parliamentarians'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this '
                                'parliamentarian?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete parliamentarian'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.collection
                            )
                        )
                    )
                ),
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('New parliamentary group function'),
                            url=self.request.link(
                                self.model, 'new-role'),
                            # change to `new-group-role`
                            attrs={'class': 'new-role'}
                        ),
                        Link(
                            text=_('New commission function'),
                            url=self.request.link(
                                self.model, 'new-commission-role'),
                            attrs={'class': 'new-commission-role'}
                        )
                    ],
                ),
            ]
        return None


class RISParliamentarianRoleLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.role_label

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def parliamentarian_collection(self) -> RISParliamentarianCollection:
        return RISParliamentarianCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(
                _('Parliamentarians'),
                self.request.link(self.parliamentarian_collection)
            ),
            Link(
                self.model.parliamentarian.title,
                self.request.link(self.model.parliamentarian)
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Remove'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to remove this role?'),
                            _('This cannot be undone.'),
                            _('Remove role'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.model.parliamentarian
                            )
                        )
                    )
                )
            ]
        return None


class RISParliamentaryGroupCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Parliamentary groups')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Parliamentary group'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-parliamentary-group'}
                        ),
                    ]
                ),
            ]
        return None


@TownApp.layout(model=RISParliamentaryGroup, request=TownRequest)
class RISParliamentaryGroupLayout(DefaultLayout):

    @cached_property
    def collection(self) -> RISParliamentaryGroupCollection:
        return RISParliamentaryGroupCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.name

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(
                _('Parliamentary groups'),
                self.request.link(self.collection)
            ),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete this '
                                'parliamentary group?'
                            ),
                            _('This cannot be undone.'),
                            _('Delete parliamentary group'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.collection
                            )
                        )
                    )
                )
            ]
        return None


class RISPartyCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Political Parties')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model)),
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Political Party'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-party'},
                        ),
                    ],
                ),
            ]
        return None


class RISCommissionCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Commissions')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Commission'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-commission'}
                        ),
                    ]
                ),
            ]
        return None


@TownApp.layout(model=RISCommission, request=TownRequest)
class RISCommissionLayout(DefaultLayout):

    @cached_property
    def collection(self) -> RISCommissionCollection:
        return RISCommissionCollection(self.request.session)

    @cached_property
    def title(self) -> str:
        return self.model.name

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(_('Commissions'),
                 self.request.class_link(RISCommissionCollection)),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this commission?'),
                            _('This cannot be undone.'),
                            _('Delete commission'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(RISCommissionCollection)
                        )
                    )
                )
            ]
        return None


class PoliticalBusinessCollectionLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _('Political Businesses')

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[LinkGroup] | None:
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('Political Business'),
                            url=self.request.link(self.model, 'new'),
                            attrs={'class': 'new-political-business'}
                        ),
                    ]
                ),
            ]
        return None


@TownApp.layout(model=PoliticalBusiness, request=TownRequest)
class PoliticalBusinessLayout(DefaultLayout):

    @cached_property
    def collection(self) -> PoliticalBusinessCollection:
        return PoliticalBusinessCollection(self.request)

    @cached_property
    def title(self) -> str:
        return self.model.title

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS Settings'), self.ris_overview_url),
            Link(_('Political Businesses'),
                 self.request.class_link(PoliticalBusinessCollection)),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Delete'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete this '
                              'political business?'),
                            _('This cannot be undone.'),
                            _('Delete political business'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                              PoliticalBusinessCollection)
                        )
                    )
                )
            ]
        return None


class RISCommissionMembershipLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return self.model.parliamentarian.title

    @cached_property
    def og_description(self) -> str:
        return self.request.translate(self.title)

    @cached_property
    def commission_collection(self) -> RISCommissionCollection:
        return RISCommissionCollection(self.request.session)

    @cached_property
    def parliamentarian_collection(self) -> RISParliamentarianCollection:
        return RISParliamentarianCollection(self.request.session)

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('RIS settings'), self.ris_overview_url),

            Link(
                _('Parliamentarians'),
                self.request.link(self.parliamentarian_collection)
            ),
            Link(
                self.model.parliamentarian.title,
                self.request.link(self.model.parliamentarian)
            ),
            Link(
                _('Commission membership'),
                self.request.link(self.model)
            )
        ]

    @cached_property
    def editbar_links(self) -> list[Link] | None:
        if self.request.is_manager:
            return [
                Link(
                    text=_('Edit'),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_('Remove'),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to remove this '
                                'commission membership?'
                            ),
                            _('This cannot be undone.'),
                            _('Remove commission membership'),
                            _('Cancel')
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                self.model.commission
                            )
                        )
                    )
                )
            ]
        return None
