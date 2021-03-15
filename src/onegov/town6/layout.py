from collections import namedtuple

from cached_property import cached_property
from dateutil.rrule import rrulestr
from dateutil import rrule

from onegov.core.utils import linkify
from onegov.directory import DirectoryCollection
from onegov.event import OccurrenceCollection
from onegov.form import FormCollection, as_internal_id
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.org.models import (
    ResourceRecipientCollection, ImageFileCollection, ImageSetCollection,
    ExportCollection, PublicationCollection, PageMove
)
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from onegov.pay import PaymentProviderCollection, PaymentCollection
from onegov.people import PersonCollection
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from onegov.town6 import _
from onegov.core.elements import Link, Block, Confirm, Intercooler, LinkGroup
from onegov.core.static import StaticFile
from onegov.town6.theme import user_options
from onegov.org.layout import (
    Layout as OrgLayout, AdjacencyListMixin,
    DefaultLayoutMixin, DefaultMailLayoutMixin,
)
from onegov.user import UserCollection

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
        ]

    @property
    def show_partners(self):
        if self.on_homepage or self.request.is_admin:
            return False
        if '<partner' not in self.org.homepage_structure:
            return False
        if not self.org.always_show_partners:
            return False
        return True

    @cached_property
    def search_keybindings_help(self):
        return self.request.translate(
            _('Press ${shortcut} to open Search',
              mapping={'shortcut': 'Ctrl+Shift+F / Ctrl+Shift+S'})
        )


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

        self.hide_from_robots()

    @cached_property
    def top_navigation(self):
        def yield_children(page):
            return (
                page.id, Link(page.title, self.request.link(page)),
                tuple(yield_children(p) for p in
                      self.request.exclude_invisible(page.children))
            )
        return tuple(yield_children(page) for page in self.root_pages)

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        return self.request.exclude_invisible(self.app.root_pages)

    @cached_property
    def sortable_url_template(self):
        return self.csrf_protected_url(
            self.request.link(PageMove.for_url_template())
        )

    def show_label(self, field):
        return True


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
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def sidebar_links(self):
        return tuple(self.get_sidebar(type='topic'))

    @cached_property
    def contact_html(self):
        return self.model.contact_html or '<ul><li>{}</li></ul>'.format(
            '</li><li>'.join(linkify(self.org.contact).splitlines())
        )


class NewsLayout(AdjacencyListLayout):

    @cached_property
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def contact_html(self):
        return self.model.contact_html or '<ul><li>{}</li></ul>'.format(
            '</li><li>'.join(linkify(self.org.contact).splitlines())
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


class FormSubmissionLayout(DefaultLayout):

    def __init__(self, model, request, title=None):
        super().__init__(model, request)
        self.include_code_editor()
        self.title = title or self.form.title

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

        if self.form.has_submissions(with_state='complete'):
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

        return [edit_link, delete_link, export_link, registration_windows_link]


class FormCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Forms"), '#')
        ]

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
                assert len(links) <= 2, """
                    Models are limited to two model-specific links. Usually
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
                        Confirm(
                            _("Do you really want to close this ticket?"),
                            _(
                                "This ticket requires a decision, but no "
                                "decision has been made yet."
                            ),
                            _("Close ticket"),
                            _("Cancel")
                        ),
                    )

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

            return links


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


class TicketChatMessageLayout(DefaultLayout):

    def __init__(self, model, request, internal=False):
        super().__init__(model, request)
        self.internal = internal

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


class ResourcesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.model))
        ]

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
                        )
                    ]
                ),
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


class ReservationLayout(ResourceLayout):
    editbar_links = None


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

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_manager:
            return (
                Link(
                    text=_("Export"),
                    url=self.request.link(self.model, 'export'),
                    attrs={'class': 'export-link'}
                ),
            )


class OccurrenceLayout(EventBaseLayout):

    def __init__(self, model, request):
        super().__init__(model, request)

    @cached_property
    def collection(self):
        return OccurrenceCollection(self.request.session)

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
                                _("This event can't be editet."),
                                _("Imported events can not be editet."),
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


class EventLayout(EventBaseLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.events_url),
            Link(self.model.title, self.request.link(self.model)),
        ]

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
                            _("This event can't be editet."),
                            _("Imported events can not be editet."),
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
                    url=self.request.link(self.model, 'export'),
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


class DirectoryEntryCollectionLayout(DirectoryEntryBaseLayout):

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

            if not self.request.is_logged_in:
                yield export_link

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
            return dict(
                published_only=_('Published'),
                upcoming_only=_("Upcoming"),
                past_only=_("Past"),
            )
        return dict(
            published_only=_('Published'),
            past_only=_("Past"),
        )

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


class DirectoryEntryLayout(DirectoryEntryBaseLayout):

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
                )
            ]

    def include_code_editor(self):
        super().include_code_editor()
        self.request.include('form-length-counter')


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
