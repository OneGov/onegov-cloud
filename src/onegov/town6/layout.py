import secrets
from collections import namedtuple
from functools import cached_property

from dateutil import rrule
from dateutil.rrule import rrulestr

from onegov.chat import TextModuleCollection
from onegov.core.elements import Block, Confirm, Intercooler, Link, LinkGroup
from onegov.core.static import StaticFile
from onegov.core.utils import linkify, to_html_ul
from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.file import File
from onegov.form import FormCollection, as_internal_id
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.org.elements import QrCodeLink
from onegov.org.exports.base import OrgExport
from onegov.org.layout import (AdjacencyListMixin, DefaultLayoutMixin,
                               DefaultMailLayoutMixin)
from onegov.org.layout import Layout as OrgLayout
from onegov.org.models import (Editor, ExportCollection, ImageFileCollection,
                               ImageSetCollection, News, PageMove,
                               PublicationCollection,
                               ResourceRecipientCollection)
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.org.models.external_link import ExternalLinkCollection
from onegov.org.models.form import submission_deletable
from onegov.org.utils import IMG_URLS
from onegov.page import PageCollection
from onegov.pay import PaymentCollection, PaymentProviderCollection
from onegov.people import PersonCollection
from onegov.qrcode import QrCode
from onegov.reservation import ResourceCollection
from onegov.stepsequence import step_sequences
from onegov.stepsequence.extension import StepsLayoutExtension
from onegov.ticket import TicketCollection
from onegov.ticket.collection import ArchivedTicketsCollection
from onegov.town6 import _
from onegov.town6.theme import user_options
from onegov.user import UserCollection, UserGroupCollection

PartnerCard = namedtuple('PartnerCard', ['url', 'image_url', 'lead'])


class Layout(OrgLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('foundation6')

    @property
    def primary_color(self):
        return self.org.theme_options.get(
            'primary-color-ui', user_options['primary-color-ui'])

    @cached_property
    def font_awesome_path(self):
        return self.request.link(StaticFile(
            'font-awesome5/css/all.min.css',
            version=self.app.version
        ))

    @cached_property
    def sentry_init_path(self):
        static_file = StaticFile.from_application(
            self.app, 'sentry/js/sentry-init.js'
        )
        return self.request.link(static_file)

    @cached_property
    def drilldown_back(self):
        back = self.request.translate(_("back"))
        return '<li class="js-drilldown-back">' \
               f'<a tabindex="0">{back}</a></li>'

    @property
    def on_homepage(self):
        return self.request.url == self.homepage_url

    @property
    def partners(self):
        partner_attrs = [key for key in dir(self.org) if 'partner' in key]
        partner_count = int(len(partner_attrs) / 3)

        return [
            PartnerCard(
                url=getattr(self.org, f'partner_{ix}_url'),
                image_url=getattr(self.org, f'partner_{ix}_img'),
                lead=getattr(self.org, f'partner_{ix}_name'),
            ) for ix in range(1, partner_count + 1)
            if (getattr(self.org, f'partner_{ix}_url')
                or getattr(self.org, f'partner_{ix}_img')
                or getattr(self.org, f'partner_{ix}_name'))
        ]

    @property
    def show_partners(self):
        if self.on_homepage:
            if '<partner' in self.org.homepage_structure:
                # The widget is rendered
                return False
        if self.org.always_show_partners and not self.request.is_admin:
            return True
        return False

    @cached_property
    def search_keybindings_help(self):
        return self.request.translate(
            _('Press ${shortcut} to open Search',
              mapping={'shortcut': 'Ctrl+Shift+F / Ctrl+Shift+S'})
        )

    @cached_property
    def page_collection(self):
        return PageCollection(self.request.session)

    def page_by_path(self, path):
        return self.page_collection.by_path(path)


class DefaultLayout(Layout, DefaultLayoutMixin):

    def __init__(self, model, request):
        super().__init__(model, request)

        # always include the common js files
        self.request.include('common')
        self.request.include('chosen')

        # always include the map components
        self.request.include(self.org.geo_provider)

        if self.request.is_manager:
            self.request.include('sortable')
            self.request.include('websockets')
            self.custom_body_attributes['data-websocket-endpoint'] = \
                self.app.websockets_client_url(request)
            self.custom_body_attributes['data-websocket-schema'] = \
                self.app.schema
            self.custom_body_attributes['data-websocket-channel'] = \
                self.app.websockets_private_channel

        if self.org.open_files_target_blank:
            self.request.include('all_blank')

        self.hide_from_robots()

    def exclude_invisible(self, items):
        items = self.request.exclude_invisible(items)
        if not self.request.is_manager:
            return tuple(i for i in items if i.published)
        return items

    @cached_property
    def top_navigation(self):

        def yield_children(page):
            children = ()
            if not isinstance(page, News):
                children = tuple(
                    yield_children(p)
                    for p in self.exclude_invisible(page.children)
                )
            return (
                page, Link(page.title, self.request.link(page)),
                children
            )

        return tuple(yield_children(page) for page in self.root_pages)

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        return self.exclude_invisible(self.app.root_pages)

    @cached_property
    def sortable_url_template(self):
        return self.csrf_protected_url(
            self.request.link(PageMove.for_url_template())
        )

    def show_label(self, field):
        return True

    @cached_property
    def qr_endpoint(self):
        return self.request.class_link(QrCode)


class DefaultMailLayout(Layout, DefaultMailLayoutMixin):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def macros(self):
        return self.template_loader.mail_macros

    @cached_property
    def contact_html(self):
        """ Returns the contacts html, but instead of breaking it into multiple
        lines (like on the site footer), this version puts it all on one line.

        """

        lines = (l.strip() for l in self.org.meta['contact'].splitlines())
        lines = (l for l in lines if l)

        return linkify(', '.join(lines))


class AdjacencyListLayout(DefaultLayout, AdjacencyListMixin):
    pass


class SettingsLayout(DefaultLayout):
    def __init__(self, model, request, setting=None):
        super().__init__(model, request)

        self.include_editor()
        self.include_code_editor()
        self.request.include('tags-input')

        self.setting = setting

    @cached_property
    def breadcrumbs(self):
        bc = [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Settings"), self.request.link(self.org, 'settings'))
        ]

        if self.setting:
            bc.append(Link(_(self.setting), '#'))

        return bc


class PageLayout(AdjacencyListLayout):

    @cached_property
    def og_image_source(self):
        if not self.model.text:
            return super().og_image_source
        for url in IMG_URLS.findall(self.model.text) or []:
            if self.is_internal(url):
                return url
        return super().og_image_source

    @cached_property
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def sidebar_links(self):
        return tuple(self.get_sidebar(type='topic'))

    @cached_property
    def contact_html(self):
        return self.model.contact_html or to_html_ul(self.org.contact)


class NewsLayout(AdjacencyListLayout):

    @cached_property
    def og_image_source(self):
        if not self.model.text:
            return super().og_image_source
        for url in IMG_URLS.findall(self.model.text) or []:
            if self.is_internal(url):
                return url
        return super().og_image_source

    @cached_property
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def contact_html(self):
        return self.model.contact_html or to_html_ul(
            self.org.contact, convert_dashes=False
        )


class EditorLayout(AdjacencyListLayout):

    def __init__(self, model, request, site_title):
        super().__init__(model, request)
        self.site_title = site_title
        self.include_editor()

    @cached_property
    def breadcrumbs(self):
        links = list(self.get_breadcrumbs(self.model.page))
        links.append(Link(self.site_title, url='#'))

        return links


class FormEditorLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.include_editor()
        self.include_code_editor()


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
class FormSubmissionLayout(StepsLayoutExtension, DefaultLayout):

    def __init__(self, model, request, title=None):
        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title

    @property
    def step_position(self):
        if self.request.view_name in ('send-message',):
            return
        if self.model.__class__.__name__ == 'CustomFormDefinition':
            return 1
        return 2

    @cached_property
    def form(self):
        if hasattr(self.model, 'form'):
            return self.model.form
        else:
            return self.model

    @cached_property
    def breadcrumbs(self):
        collection = FormCollection(self.request.session)

        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Forms"), self.request.link(collection)),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def can_delete_form(self):
        return all(
            submission_deletable(submission, self.request.session)
            for submission in self.form.submissions
        )

    @cached_property
    def editbar_links(self):

        if not self.request.is_manager:
            return

        # only show the edit bar links if the site is the base of the form
        # -> if the user already entered some form data remove the edit bar
        # because it makes it seem like it's there to edit the submission,
        # not the actual form
        if hasattr(self.model, 'form'):
            return

        collection = FormCollection(self.request.session)

        edit_link = Link(
            text=_("Edit"),
            url=self.request.link(self.form, name='edit'),
            attrs={'class': 'edit-link'}
        )

        qr_link = QrCodeLink(
            text=_("QR"),
            url=self.request.link(self.model),
            attrs={'class': 'qr-code-link'}
        )

        if not self.can_delete_form:
            delete_link = Link(
                text=_("Delete"),
                attrs={'class': 'delete-link'},
                traits=(
                    Block(
                        _("This form can't be deleted."),
                        _(
                            "There are submissions associated with the form. "
                            "Those need to be removed first."
                        ),
                        _("Cancel")
                    )
                )
            )

        else:
            delete_link = Link(
                text=_("Delete"),
                url=self.csrf_protected_url(
                    self.request.link(self.form)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to delete this form?"),
                        _("This cannot be undone."),
                        _("Delete form"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.link(collection)
                    )
                )
            )

        export_link = Link(
            text=_("Export"),
            url=self.request.link(self.form, name='export'),
            attrs={'class': 'export-link'}
        )

        change_url_link = Link(
            text=_("Change URL"),
            url=self.request.link(self.form, name='change-url'),
            attrs={'class': 'internal-url'}
        )

        registration_windows_link = LinkGroup(
            title=_("Registration Windows"),
            links=[
                Link(
                    text=_("Add"),
                    url=self.request.link(
                        self.model, 'new-registration-window'
                    ),
                    attrs={'class': 'new-registration-window'}
                ),
                *(
                    Link(
                        text=self.format_date_range(w.start, w.end),
                        url=self.request.link(w),
                        attrs={'class': 'view-link'}
                    ) for w in self.form.registration_windows
                )
            ]
        )

        return [
            edit_link,
            delete_link,
            export_link,
            change_url_link,
            registration_windows_link,
            qr_link
        ]


class FormCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Forms"), '#')
        ]

    @property
    def forms_url(self):
        return self.request.class_link(FormCollection)

    @property
    def external_forms(self):
        return ExternalLinkCollection(self.request.session)

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Form"),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-form'}
                        ),
                        Link(
                            text=_("External form"),
                            url=self.request.link(
                                self.external_forms,
                                query_params={
                                    'to': self.forms_url,
                                    'title': self.request.translate(
                                        _("New external form")),
                                    'type': 'form'
                                },
                                name='new'
                            ),
                            attrs={'class': 'new-form'}
                        )
                    ]
                ),
            ]


class PersonCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("People"), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Person"),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-person'}
                        )
                    ]
                ),
            ]


class PersonLayout(DefaultLayout):

    @cached_property
    def collection(self):
        return PersonCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("People"), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this person?"),
                            _("This cannot be undone."),
                            _("Delete person"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class TicketsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), '#')
        ]


class ArchivedTicketsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), '#')
        ]

    @cached_property
    def editbar_links(self):
        links = []
        if self.request.is_admin:
            text = self.request.translate(_("Delete archived tickets"))
            links.append(
                Link(
                    text=text,
                    url=self.csrf_protected_url(self.request.link(self.model,
                                                                  'delete')),
                    traits=(
                        Confirm(
                            _("Do you really want to delete all archived "
                              "tickets?"),
                            _("This cannot be undone."),
                            _("Delete archived tickets"),
                            _("Cancel"),
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.class_link(
                                ArchivedTicketsCollection, {'handler': 'ALL'}
                            ),
                        ),
                    ),
                    attrs={'class': 'delete-link'},
                )
            )
        return links


class TicketLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('timeline')

    @cached_property
    def collection(self):
        return TicketCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), self.request.link(self.collection)),
            Link(self.model.number, '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:

            # only show the model related links when the ticket is pending
            if self.model.state == 'pending':
                links = self.model.handler.get_links(self.request)
                assert len(links) <= 3, """
                    Models are limited to three model-specific links. Usually
                    a primary single link and a link group containing the
                    other links.
                """
            else:
                links = []

            if self.model.state == 'open':
                links.append(Link(
                    text=_("Accept ticket"),
                    url=self.request.link(self.model, 'accept'),
                    attrs={'class': ('ticket-button', 'ticket-accept')}
                ))

            elif self.model.state == 'pending':
                traits = ()

                if self.model.handler.undecided:
                    traits = (
                        Block(
                            _("This ticket can't be closed."),
                            _(
                                "This ticket requires a decision, but no "
                                "decision has been made yet."
                            ),
                            _("Cancel")
                        ),
                    )

                links.append(Link(
                    text=_("Assign ticket"),
                    url=self.request.link(self.model, 'assign'),
                    attrs={'class': ('ticket-button', 'ticket-assign')}
                ))

                links.append(Link(
                    text=_("Close ticket"),
                    url=self.request.link(self.model, 'close'),
                    attrs={'class': ('ticket-button', 'ticket-close')},
                    traits=traits
                ))

            elif self.model.state == 'closed':
                links.append(Link(
                    text=_("Reopen ticket"),
                    url=self.request.link(self.model, 'reopen'),
                    attrs={'class': ('ticket-button', 'ticket-reopen')}
                ))

                links.append(Link(
                    text=_("Archive ticket"),
                    url=self.request.link(self.model, 'archive'),
                    attrs={'class': ('ticket-button', 'ticket-archive')})
                )
            elif self.model.state == 'archived':
                links.append(Link(
                    text=_('Recover from archive'),
                    url=self.request.link(self.model, 'unarchive'),
                    attrs={'class': ('ticket-button', 'ticket-reopen')}
                ))
                links.append(Link(
                    text=_("Delete Ticket"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model, 'delete')
                    ),
                    attrs={'class': ('ticket-button', 'ticket-delete')},
                ))

            # ticket notes are always enabled
            links.append(
                Link(
                    text=_("New Note"),
                    url=self.request.link(self.model, 'note'),
                    attrs={'class': 'new-note'}
                )
            )
            links.append(
                Link(
                    text=_("PDF"),
                    url=self.request.link(self.model, 'pdf'),
                    attrs={'class': 'ticket-pdf'}
                )
            )
            if self.has_submission_files:
                links.append(
                    Link(
                        text=_("Download files"),
                        url=self.request.link(self.model, 'files'),
                        attrs={'class': 'ticket-files'}
                    )
                )
            if self.request.app.org.gever_endpoint:
                links.append(
                    Link(
                        text=_("Upload to Gever"),
                        url=self.request.link(self.model, 'send-to-gever'),
                        attrs={'class': 'upload'},
                        traits=(
                            Confirm(
                                _("Do you really want to upload this ticket?"),
                                _("This will upload this ticket to the "
                                  "Gever instance, if configured."),
                                _("Upload Ticket"),
                                _("Cancel")
                            )
                        )
                    )
                )
            return links

    @cached_property
    def has_submission_files(self) -> bool:
        submission = getattr(self.model.handler, 'submission', None)
        return submission is not None and bool(submission.files)


class TicketNoteLayout(DefaultLayout):

    def __init__(self, model, request, title, ticket=None):
        super().__init__(model, request)
        self.title = title
        self.ticket = ticket or model

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), self.request.link(
                TicketCollection(self.request.session)
            )),
            Link(self.ticket.number, self.request.link(self.ticket)),
            Link(self.title, '#')
        ]


@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='FormSubmissionLayout')
@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='EventLayout')
@step_sequences.registered_step(
    3, _('Confirmation'),
    cls_before='ReservationLayout')
class TicketChatMessageLayout(StepsLayoutExtension, DefaultLayout):

    def __init__(self, model, request, internal=False):
        super().__init__(model, request)
        self.internal = internal

    @property
    def step_position(self):
        return 3

    @cached_property
    def breadcrumbs(self):
        return self.internal\
            and self.internal_breadcrumbs\
            or self.public_breadcrumbs

    @property
    def internal_breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), self.request.link(
                TicketCollection(self.request.session)
            )),
            Link(self.ticket.number, self.request.link(self.ticket)),
            Link(_("New Message"), '#')
        ]

    @property
    def public_breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Ticket Status"), self.request.link(self.model, 'status')),
            Link(_("New Message"), '#')
        ]


class TextModulesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Text modules"), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Text module"),
                            url=self.request.link(
                                self.model,
                                name='add'
                            ),
                            attrs={'class': 'new-text-module'}
                        )
                    ]
                ),
            ]


class TextModuleLayout(DefaultLayout):

    @cached_property
    def collection(self):
        return TextModuleCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('Text modules'), self.request.link(self.collection)),
            Link(self.model.name, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                "Do you really want to delete this text "
                                "module?"
                            ),
                            _("This cannot be undone."),
                            _("Delete text module"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class ResourcesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.model))
        ]

    @property
    def external_resources(self):
        return ExternalLinkCollection(self.request.session)

    @property
    def resources_url(self):
        return self.request.class_link(ResourceCollection)

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Recipients"),
                    url=self.request.class_link(ResourceRecipientCollection),
                    attrs={'class': 'manage-recipients'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Room"),
                            url=self.request.link(
                                self.model,
                                name='new-room'
                            ),
                            attrs={'class': 'new-room'}
                        ),
                        Link(
                            text=_("Daypass"),
                            url=self.request.link(
                                self.model,
                                name='new-daypass'
                            ),
                            attrs={'class': 'new-daypass'}
                        ),
                        Link(
                            text=_("Resource Item"),
                            url=self.request.link(
                                self.model,
                                name='new-daily-item'
                            ),
                            attrs={'class': 'new-daily-item'}
                        ),
                        Link(
                            text=_("External resource link"),
                            url=self.request.link(
                                self.external_resources,
                                query_params={
                                    'to': self.resources_url,
                                    'title': self.request.translate(
                                        _("New external resource")),
                                    'type': 'resource'
                                },
                                name='new'
                            ),
                            attrs={'class': 'new-resource-link'}
                        )
                    ]
                ),
                Link(
                    text=_("Export All"),
                    url=self.request.link(self.model, name="export-all"),
                ),
            ]


class FindYourSpotLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(
                _("Homepage"), self.homepage_url
            ),
            Link(
                _("Reservations"), self.request.class_link(ResourceCollection)
            ),
            Link(
                _("Find Your Spot"), self.request.link(self.model)
            )
        ]


class ResourceRecipientsLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(
                _("Homepage"), self.homepage_url
            ),
            Link(
                _("Reservations"), self.request.class_link(ResourceCollection)
            ),
            Link(
                _("Notifications"), self.request.link(self.model)
            )
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("E-Mail Recipient"),
                            url=self.request.link(
                                self.model,
                                name='new-recipient'
                            ),
                            attrs={'class': 'new-recipient'}
                        ),
                    ]
                ),
            ]


class ResourceRecipientsFormLayout(DefaultLayout):

    def __init__(self, model, request, title):
        super().__init__(model, request)
        self.title = title

    @cached_property
    def breadcrumbs(self):
        return [
            Link(
                _("Homepage"), self.homepage_url
            ),
            Link(
                _("Reservations"), self.request.class_link(ResourceCollection)
            ),
            Link(
                _("Notifications"), self.request.class_link(
                    ResourceRecipientCollection
                )
            ),
            Link(self.title, '#')
        ]


class ResourceLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

        self.request.include('fullcalendar')

    @cached_property
    def collection(self):
        return ResourceCollection(self.request.app.libres_context)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            if self.model.deletable:
                delete_link = Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this resource?"),
                            _("This cannot be undone."),
                            _("Delete resource"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )

            else:
                delete_link = Link(
                    text=_("Delete"),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Block(
                            _("This resource can't be deleted."),
                            _(
                                "There are existing reservations associated "
                                "with this resource"
                            ),
                            _("Cancel")
                        )
                    )
                )
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                delete_link,
                Link(
                    text=_("Clean up"),
                    url=self.request.link(self.model, 'cleanup'),
                    attrs={'class': ('cleanup-link', 'calendar-dependent')}
                ),
                Link(
                    text=_("Occupancy"),
                    url=self.request.link(self.model, 'occupancy'),
                    attrs={'class': ('occupancy-link', 'calendar-dependent')}
                ),
                Link(
                    text=_("Export"),
                    url=self.request.link(self.model, 'export'),
                    attrs={'class': ('export-link', 'calendar-dependent')}
                ),
                Link(
                    text=_("Subscribe"),
                    url=self.request.link(self.model, 'subscribe'),
                    attrs={'class': 'subscribe-link'}
                ),
                Link(
                    text=_("Rules"),
                    url=self.request.link(self.model, 'rules'),
                    attrs={'class': 'rule-link'}
                )
            ]
        elif self.request.has_role('member'):
            if self.model.occupancy_is_visible_to_members:
                return [
                    Link(
                        text=_("Occupancy"),
                        url=self.request.link(self.model, 'occupancy'),
                        attrs={
                            'class': ('occupancy-link', 'calendar-dependent')}
                    )
                ]


@step_sequences.registered_step(
    1, _("Form"), cls_after='ReservationLayout')
@step_sequences.registered_step(
    2, _("Check"),
    cls_before='ReservationLayout', cls_after='TicketChatMessageLayout')
class ReservationLayout(StepsLayoutExtension, ResourceLayout):
    editbar_links = None

    @property
    def step_position(self):
        """ Note the last step is the ticket status page with step 3. """
        view_name = self.request.view_name
        if view_name == 'form':
            return 1
        if view_name == 'confirmation':
            return 2


class AllocationRulesLayout(ResourceLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model)),
            Link(_("Rules"), '#')
        ]

    @cached_property
    def editbar_links(self):
        return [
            LinkGroup(
                title=_("Add"),
                links=[
                    Link(
                        text=_("Rule"),
                        url=self.request.link(
                            self.model,
                            name='new-rule'
                        ),
                        attrs={'class': 'new-link'}
                    )
                ]
            ),
        ]


class AllocationEditFormLayout(DefaultLayout):
    """ Same as the resource layout, but with different editbar links, because
    there's not really an allocation view, but there are allocation forms.

    """

    @cached_property
    def collection(self):
        return ResourceCollection(self.request.app.libres_context)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.collection)),
            Link(_("Edit allocation"), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            if self.model.availability == 100.0:
                yield Link(
                    _("Delete"),
                    self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this allocation?"),
                            _("This cannot be undone."),
                            _("Delete allocation"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            else:
                yield Link(
                    text=_("Delete"),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Block(
                            _("This resource can't be deleted."),
                            _(
                                "There are existing reservations associated "
                                "with this resource"
                            ),
                            _("Cancel")
                        )
                    )
                )


class EventBaseLayout(DefaultLayout):

    def format_recurrence(self, recurrence):
        """ Returns a human readable version of an RRULE used by us. """

        WEEKDAYS = (_("Mo"), _("Tu"), _("We"), _("Th"), _("Fr"), _("Sa"),
                    _("Su"))

        if recurrence:
            rule = rrulestr(recurrence)

            if getattr(rule, '_freq', None) == rrule.WEEKLY:
                return _(
                    "Every ${days} until ${end}",
                    mapping={
                        'days': ', '.join((
                            self.request.translate(WEEKDAYS[day])
                            for day in rule._byweekday
                        )),
                        'end': rule._until.date().strftime('%d.%m.%Y')
                    }
                )

        return ''

    def event_deletable(self, event):
        tickets = TicketCollection(self.app.session())
        ticket = tickets.by_handler_id(event.id.hex)
        return False if ticket else True


class OccurrencesLayout(EventBaseLayout):

    @property
    def og_description(self):
        return self.request.translate(_("Events"))

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):

        def links():
            if (self.request.is_admin and self.request.app.org.
                    event_filter_type in ['filters', 'tags_and_filters']):
                yield Link(
                    text=_("Configure"),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                )

            if self.request.is_manager:
                yield Link(
                    text=_("Import"),
                    url=self.request.link(self.model, 'import'),
                    attrs={'class': 'import-link'}
                )

                yield Link(
                    text=_("Export"),
                    url=self.request.link(self.model, 'export'),
                    attrs={'class': 'export-link'}
                )

                yield LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Event"),
                            url=self.request.link(self.model, 'enter-event'),
                            attrs={'class': 'new-form'}
                        ),
                    ]
                )

        return list(links())


class OccurrenceLayout(EventBaseLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

    @cached_property
    def collection(self):
        return OccurrenceCollection(self.request.session)

    @property
    def og_description(self):
        return self.model.event.description

    @cached_property
    def og_image(self):
        return self.model.event.image or super().og_image

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.request.link(self.collection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            if self.model.event.source:
                return [
                    Link(
                        text=_("Edit"),
                        attrs={'class': 'edit-link'},
                        traits=(
                            Block(
                                _("This event can't be edited."),
                                _("Imported events can not be edited."),
                                _("Cancel")
                            )
                        )
                    ),
                    Link(
                        text=_("Delete"),
                        url=self.csrf_protected_url(
                            self.request.link(self.model.event, 'withdraw'),
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(
                                _("Do you really want to delete this event?"),
                                _("This cannot be undone."),
                                _("Delete event"),
                                _("Cancel")
                            ),
                            Intercooler(
                                request_method='POST',
                                redirect_after=self.events_url
                            ),
                        )
                    )
                ]

            edit_link = Link(
                text=_("Edit"),
                url=self.request.return_here(
                    self.request.link(self.model.event, 'edit')
                ),
                attrs={'class': 'edit-link'}
            )

            if self.event_deletable(self.model.event):
                delete_link = Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model.event)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this event?"),
                            _("This cannot be undone."),
                            _("Delete event"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.events_url
                        )
                    )
                )
            else:
                delete_link = Link(
                    text=_("Delete"),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Block(
                            _("This event can't be deleted."),
                            _(
                                "To remove this event, go to the ticket "
                                "and reject it."
                            ),
                            _("Cancel")
                        )
                    )
                )

            return [edit_link, delete_link]


@step_sequences.registered_step(1, _('Form'), cls_after='FormSubmissionLayout')
@step_sequences.registered_step(
    2, _('Check'),
    cls_before='EventLayout',
    cls_after='TicketChatMessageLayout'
)
class EventLayout(StepsLayoutExtension, EventBaseLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.events_url),
            Link(self.model.title, self.request.link(self.model)),
        ]

    @property
    def step_position(self):
        if self.request.view_name == 'new':
            return 1
        return 2

    @cached_property
    def editbar_links(self):
        imported_editable = self.request.is_manager and self.model.source
        links = []
        if imported_editable:
            links = [
                Link(
                    text=_("Edit"),
                    attrs={'class': 'edit-link'},
                    traits=(
                        Block(
                            _("This event can't be edited."),
                            _("Imported events can not be edited."),
                            _("Cancel")
                        )
                    )
                )]
        if imported_editable and self.model.state == 'published':
            links.append(
                Link(
                    text=_("Withdraw event"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model, 'withdraw'),
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to withdraw this event?"),
                            _("You can re-publish an imported event later."),
                            _("Withdraw event"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='POST',
                            redirect_after=self.events_url
                        ),
                    )
                )
            )
        if imported_editable and self.model.state == 'withdrawn':
            links.append(
                Link(
                    text=_("Re-publish event"),
                    url=self.request.return_here(
                        self.request.link(self.model, 'publish')),
                    attrs={'class': 'accept-link'}
                )
            )
        if imported_editable:
            return links

        edit_link = Link(
            text=_("Edit"),
            url=self.request.link(self.model, 'edit'),
            attrs={'class': 'edit-link'}
        )
        if self.event_deletable(self.model):
            delete_link = Link(
                text=_("Delete"),
                url=self.csrf_protected_url(
                    self.request.link(self.model)
                ),
                attrs={'class': 'delete-link'},
                traits=(
                    Confirm(
                        _("Do you really want to delete this event?"),
                        _("This cannot be undone."),
                        _("Delete event"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.events_url
                    )
                )
            )
        else:
            delete_link = Link(
                text=_("Delete"),
                attrs={'class': 'delete-link'},
                traits=(
                    Block(
                        _("This event can't be deleted."),
                        _(
                            "To remove this event, go to the ticket "
                            "and reject it."
                        ),
                        _("Cancel")
                    )
                )
            )

        return [edit_link, delete_link]


class NewsletterLayout(DefaultLayout):

    @cached_property
    def collection(self):
        return NewsletterCollection(self.app.session())

    @cached_property
    def recipients(self):
        return RecipientCollection(self.app.session())

    @cached_property
    def is_collection(self):
        return isinstance(self.model, NewsletterCollection)

    @cached_property
    def breadcrumbs(self):

        if self.is_collection and self.view_name == 'new':
            return [
                Link(_("Homepage"), self.homepage_url),
                Link(_("Newsletter"), self.request.link(self.collection)),
                Link(_("New"), '#')
            ]
        elif self.is_collection:
            return [
                Link(_("Homepage"), self.homepage_url),
                Link(_("Newsletter"), '#')
            ]
        else:
            return [
                Link(_("Homepage"), self.homepage_url),
                Link(_("Newsletter"), self.request.link(self.collection)),
                Link(self.model.title, '#')
            ]

    @cached_property
    def editbar_links(self):
        if not self.request.is_manager:
            return

        if self.is_collection:
            return [
                Link(
                    text=_("Subscribers"),
                    url=self.request.link(self.recipients),
                    attrs={'class': 'manage-subscribers'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Newsletter"),
                            url=self.request.link(
                                NewsletterCollection(self.app.session()),
                                name='new'
                            ),
                            attrs={'class': 'new-newsletter'}
                        ),
                    ]
                ),
            ]
        else:
            return [
                Link(
                    text=_("Send"),
                    url=self.request.link(self.model, 'send'),
                    attrs={'class': 'send-link'}
                ),
                Link(
                    text=_("Test"),
                    url=self.request.link(self.model, 'test'),
                    attrs={'class': 'test-link'}
                ),
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete "{}"?'.format(
                                self.model.title
                            )),
                            _("This cannot be undone."),
                            _("Delete newsletter"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class RecipientLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Newsletter"), self.request.link(
                NewsletterCollection(self.app.session())
            )),
            Link(_("Subscribers"), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Import"),
                    url=self.request.link(self.model,
                                          'import-newsletter-recipients'),
                    attrs={'class': 'import-link'},
                ),
                Link(
                    text=_("Export"),
                    url=self.request.link(self.model,
                                          'export-newsletter-recipients'),
                    attrs={'class': 'export-link'},
                ),
            ]


class ImageSetCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Photo Albums"), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Manage images"),
                    url=self.request.link(ImageFileCollection(self.app)),
                    attrs={'class': 'upload'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Photo Album"),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-photo-album'}
                        )
                    ]
                ),
            ]


class ImageSetLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('photoswipe')

    @property
    def collection(self):
        return ImageSetCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Photo Albums"), self.request.link(self.collection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Choose images"),
                    url=self.request.link(self.model, 'select'),
                    attrs={'class': 'select'}
                ),
                Link(
                    text=_("Edit"),
                    url=self.request.link(
                        self.model,
                        name='edit'
                    ),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _('Do you really want to delete "{}"?'.format(
                                self.model.title
                            )),
                            _("This cannot be undone."),
                            _("Delete photo album"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class UserManagementLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Usermanagement"), self.request.class_link(UserCollection))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            links = []

            if self.app.enable_user_registration:
                links.append(
                    Link(
                        text=_("Create Signup Link"),
                        url=self.request.class_link(
                            UserCollection,
                            name='signup-link'
                        ),
                        attrs={'class': 'new-link'}
                    )
                )

            links.append(
                LinkGroup(
                    title=_("Add"),
                    links=(
                        Link(
                            text=_("User"),
                            url=self.request.class_link(
                                UserCollection, name='new'
                            ),
                            attrs={'class': 'new-user'}
                        ),
                    )
                )
            )

        return links


class UserLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Usermanagement"), self.request.class_link(UserCollection)),
            Link(self.model.title, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_admin and not self.model.source:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
            ]


class UserGroupCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('User groups'), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_admin:
            return [
                LinkGroup(
                    title=_('Add'),
                    links=[
                        Link(
                            text=_('User group'),
                            url=self.request.link(
                                self.model,
                                name='new'
                            ),
                            attrs={'class': 'new-user'}
                        )
                    ]
                ),
            ]


class UserGroupLayout(DefaultLayout):

    @cached_property
    def collection(self):
        return UserGroupCollection(self.request.session)

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_('Homepage'), self.homepage_url),
            Link(_('User groups'), self.request.link(self.collection)),
            Link(self.model.name, self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_admin:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _("Do you really want to delete this user group?"),
                            _("This cannot be undone."),
                            _("Delete user group"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(self.collection)
                        )
                    )
                )
            ]


class ExportCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Exports"), self.request.class_link(ExportCollection))
        ]


class PaymentProviderLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Payment Providers"), self.request.class_link(
                PaymentProviderCollection
            ))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_admin:
            return [
                Link(
                    text=_("Payments"),
                    url=self.request.class_link(PaymentCollection),
                    attrs={'class': 'payments'}
                ),
                LinkGroup(
                    title=_("Add"),
                    links=(
                        Link(
                            text=_("Stripe Connect"),
                            url=self.request.class_link(
                                PaymentProviderCollection,
                                name='stripe-connect-oauth'
                            ),
                            attrs={'class': 'new-stripe-connect'}
                        ),
                    )
                )
            ]


class PaymentCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Payments"), self.request.class_link(
                PaymentProviderCollection
            ))
        ]

    @cached_property
    def editbar_links(self):
        links = []

        if self.app.payment_providers_enabled:
            if self.request.is_admin:
                links.append(
                    Link(
                        text=_("Payment Provider"),
                        url=self.request.class_link(PaymentProviderCollection),
                        attrs={'class': 'payment-provider'}
                    )
                )

            links.append(
                Link(
                    text=_("Synchronise"),
                    url=self.request.class_link(
                        PaymentProviderCollection, name='sync'
                    ),
                    attrs={'class': 'sync'}
                )
            )

            links.append(
                Link(
                    text=_("Export"),
                    url=self.request.class_link(OrgExport, {'id': 'payments'}),
                    attrs={'class': 'export-link'}
                )
            )

        return links


class MessageCollectionLayout(DefaultLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('timeline')

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Timeline"), '#')
        ]


class DirectoryCollectionLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        self.include_editor()
        self.include_code_editor()
        self.request.include('iconwidget')

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Directories"), '#')
        ]

    @property
    def og_description(self):
        return self.request.translate(_("Directories"))

    @cached_property
    def editbar_links(self):
        if self.request.is_admin:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Directory"),
                            url=self.request.link(
                                self.model,
                                name='+new'
                            ),
                            attrs={'class': 'new-directory'}
                        )
                    ]
                ),
            ]


class DirectoryEntryBaseLayout(DefaultLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request.include('photoswipe')
        if self.directory.marker_color:
            self.custom_body_attributes['data-default-marker-color']\
                = self.directory.marker_color

        if self.directory.marker_icon:
            self.custom_body_attributes['data-default-marker-icon']\
                = self.directory.marker_icon.encode('unicode-escape')[2:]

    @property
    def directory(self):
        return self.model.directory

    def show_label(self, field):
        return field.id not in self.model.hidden_label_fields

    @cached_property
    def thumbnail_field_id(self):
        if self.directory.configuration.thumbnail:
            return as_internal_id(self.directory.configuration.thumbnail)

    def thumbnail_file_id(self, entry):
        thumbnail = self.thumbnail_field_id
        if not thumbnail:
            return
        value = entry.values.get(thumbnail)
        if isinstance(value, list) and value:
            value = value[0]
        if not isinstance(value, dict):
            return
        return value.get('data', '').lstrip('@')

    def thumbnail_link(self, entry):
        file_id = self.thumbnail_file_id(entry)
        return file_id and self.request.class_link(
            File, {'id': file_id}, name='thumbnail')

    def thumbnail_file(self, entry):
        file_id = self.thumbnail_file_id(entry)
        if not file_id:
            return
        return self.request.session.query(File).filter_by(id=file_id).first()


@step_sequences.registered_step(
    1, _('Form'), cls_after='FormSubmissionLayout'
)
class DirectoryEntryCollectionLayout(StepsLayoutExtension,
                                     DirectoryEntryBaseLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.directory.numbering == 'standard':
            self.custom_body_attributes['data-default-marker-icon'] = 'numbers'
        elif self.directory.numbering == 'custom':
            self.custom_body_attributes['data-default-marker-icon'] = 'custom'

    @property
    def step_position(self):
        return 1

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Directories"), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                ExtendedDirectoryEntryCollection, {
                    'directory_name': self.model.directory_name
                }
            ))
        ]

    @cached_property
    def editbar_links(self):

        export_link = Link(
            text=_("Export"),
            url=self.request.link(self.model, name='+export'),
            attrs={'class': 'export-link'}
        )

        def links():
            qr_link = None
            if self.request.is_admin:
                yield Link(
                    text=_("Configure"),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                )

            if self.request.is_manager:
                yield export_link

                yield Link(
                    text=_("Import"),
                    url=self.request.class_link(
                        ExtendedDirectoryEntryCollection, {
                            'directory_name': self.model.directory_name
                        }, name='+import'
                    ),
                    attrs={'class': 'import-link'}
                )

                qr_link = QrCodeLink(
                    text=_("QR"),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                )

            if self.request.is_admin:
                yield Link(
                    text=_("Delete"),
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
                            _("All entries will be deleted as well!"),
                            _("Delete directory"),
                            _("Cancel")
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
                    text=self.request.translate(_("Change URL")),
                    url=self.request.link(
                        self.model.directory,
                        'change-url'),
                    attrs={'class': 'internal-url'},
                )

            if self.request.is_manager:
                yield LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Entry"),
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

        return list(links())

    def get_pub_link(self, text, filter=None, toggle_active=True):
        filter_data = {}
        classes = []
        if filter:
            filter_data[filter] = True
            if toggle_active and filter in self.request.params:
                classes.append('active')

        return Link(
            text=text,
            url=self.request.class_link(
                ExtendedDirectoryEntryCollection,
                {**filter_data, 'directory_name': self.directory.name}
            ),
            attrs={'class': classes}
        )

    @property
    def publication_filters(self):
        if not self.request.is_logged_in:
            return {}
        if self.request.is_manager:
            return {
                'published_only': _('Published'),
                'upcoming_only': _("Upcoming"),
                'past_only': _("Past"),
            }
        return {
            'published_only': _('Published'),
            'past_only': _("Past"),
        }

    @property
    def publication_filter_title(self):
        default_title = self.request.translate(_("Publication"))
        for filter in self.publication_filters:
            if filter in self.request.params:
                applied_title = self.request.translate(
                    self.publication_filters[filter])
                return f'{default_title}: {applied_title}'
        return f'{default_title}: {self.request.translate(_("Choose filter"))}'

    @property
    def publication_links(self):
        return (
            self.get_pub_link(text, filter_kw)
            for filter_kw, text in self.publication_filters.items()
        )


@step_sequences.registered_step(1, _('Form'), cls_after='FormSubmissionLayout')
class DirectoryEntryLayout(StepsLayoutExtension, DirectoryEntryBaseLayout):

    @property
    def step_position(self):
        return 1

    @cached_property
    def og_image(self):
        return self.thumbnail_file(self.model) or super().og_image

    @property
    def og_description(self):
        return self.directory.lead

    @property
    def thumbnail_field_ids(self):
        return [
            as_internal_id(e) for e in getattr(
                self.model.directory.configuration,
                'show_as_thumbnails', []) or []
        ]

    def field_download_link(self, field):
        url = super().field_download_link(field)
        if field.id in self.thumbnail_field_ids:
            return self.thumbnail_url(url)
        return url

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Directories"), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                ExtendedDirectoryEntryCollection, {
                    'directory_name': self.model.directory.name
                }
            )),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    def linkify(self, text):
        linkified = super().linkify(text)
        return linkified.replace('\\n', '<br>') if linkified else linkified

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                ),
                Link(
                    text=_("Delete"),
                    url=self.csrf_protected_url(
                        self.request.link(self.model)
                    ),
                    attrs={'class': 'delete-link'},
                    traits=(
                        Confirm(
                            _(
                                'Do you really want to delete "${title}"?',
                                mapping={
                                    'title': self.model.title
                                }
                            ),
                            _("This cannot be undone."),
                            _("Delete entry"),
                            _("Cancel")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                ExtendedDirectoryEntryCollection(
                                    self.model.directory)
                            )
                        )
                    )
                ),
                QrCodeLink(
                    text=_("QR"),
                    url=self.request.link(self.model),
                    attrs={'class': 'qr-code-link'}
                )
            ]


class PublicationLayout(DefaultLayout):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request.include('filedigest')

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Publications"), self.request.class_link(
                PublicationCollection
            ))
        ]


class DashboardLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Dashboard"), '#')
        ]


class GeneralFileCollectionLayout(DefaultLayout):
    def __init__(self, model, request):
        """
        The order of assets differ from org where common.js must come first
        including jquery. Here, the foundation6 assets contain jquery and must
        come first.
        """
        super().__init__(model, request)
        request.include('upload')
        request.include('prompt')


class ImageFileCollectionLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)
        request.include('upload')
        request.include('editalttext')


class ExternalLinkLayout(DefaultLayout):

    @property
    def editbar_links(self):
        return [
            Link(
                _("Delete"),
                self.csrf_protected_url(self.request.link(self.model)),
                traits=(
                    Confirm(
                        _("Do you really want to delete this external link?"),
                        _("This cannot be undone."),
                        _("Delete external link"),
                        _("Cancel")
                    ),
                    Intercooler(
                        request_method='DELETE',
                        redirect_after=self.request.class_link(
                            ExternalLinkCollection.target(self.model)
                        )
                    )
                ),
                attrs={'class': ('ticket-delete',)}
            )
        ]


class HomepageLayout(DefaultLayout):

    @property
    def editbar_links(self):
        if self.request.is_manager:
            return [
                Link(
                    _("Edit"),
                    self.request.link(self.model, 'homepage-settings'),
                    attrs={'class': ('edit-link')}
                ),
                Link(
                    _("Sort"),
                    self.request.link(self.model, 'sort'),
                    attrs={'class': ('sort-link')}
                ),
                Link(
                    _("Add"),
                    self.request.link(Editor('new-root', self.model, 'page')),
                    attrs={'class': ('new-page')},
                    classes=(
                        'new-page',
                        'show-new-content-placeholder'
                    ),
                ),
            ]


class ChatLayout(DefaultLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

        token = self.make_websocket_token()

        # Make token available to JavaScript when creating the WebSocket
        # connection.
        self.custom_body_attributes['data-websocket-token'] = token

        # Store the WebSocket token in the session check when the connection is
        # initiated.
        request.browser_session['websocket_token'] = token

    def make_websocket_token(self):
        """
        A user (authenticated or anonymous) attempts to create a chat
        connection. For the connection to succeed, they must present a one-time
        token to the WebSocket server.

        TODO: Add lifespan to the token?
        """
        return secrets.token_hex(16)


class StaffChatLayout(ChatLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('websockets')
        self.request.include('staff-chat')

        self.custom_body_attributes['data-websocket-endpoint'] = \
            self.app.websockets_client_url(request)

        self.custom_body_attributes['data-websocket-schema'] = \
            self.app.schema

    @cached_property
    def breadcrumbs(self):
        bc = [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Chats"), self.request.link(
                self.request.app.org, name='chats'
            ))
        ]

        return bc


class ClientChatLayout(ChatLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
        self.request.include('websockets')
        self.request.include('client-chat')

        self.custom_body_attributes['data-websocket-endpoint'] = \
            self.app.websockets_client_url(request)
        self.custom_body_attributes['data-websocket-schema'] = \
            self.app.schema


class ChatInitiationFormLayout(DefaultLayout):
    def __init__(self, model, request):
        super().__init__(model, request)
