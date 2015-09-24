import arrow

from cached_property import cached_property
from dateutil import rrule
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.event import OccurrenceCollection
from onegov.form import FormCollection, FormSubmissionFile, render_field
from onegov.libres import ResourceCollection
from onegov.page import Page, PageCollection
from onegov.people import PersonCollection
from onegov.ticket import TicketCollection
from onegov.town import _
from onegov.town.elements import DeleteLink, Link, LinkGroup
from onegov.town.models import (
    FileCollection,
    ImageCollection,
    Search,
    SiteCollection,
    Thumbnail
)
from purl import URL
from sqlalchemy import desc


class Layout(ChameleonLayout):
    """ Contains methods to render a page inheriting from layout.pt.

    All pages inheriting from layout.pt rely on this class being present
    as 'layout' variable::

     @TownApp.html(model=Example, template='example.pt', permission=Public)
        def view_example(self, request):
            return { 'layout': DefaultLayout(self, request) }

    It is meant to be extended for different parts of the site. For example,
    the :class:`DefaultLayout` includes the top navigation defined by
    onegov.page.

    It's possible though to have a different part of the website use a
    completely different top navigation. For that, a new Layout class
    inheriting from this one should be added.

    """

    @property
    def town(self):
        """ An alias for self.request.app.town. """
        return self.request.app.town

    @cached_property
    def font_awesome_path(self):
        static_file = StaticFile.from_application(
            self.app, 'font-awesome/css/font-awesome.min.css')

        return self.request.link(static_file)

    @cached_property
    def page_id(self):
        """ Returns the unique page id of the rendered page. Used to have
        a useful id in the body element for CSS/JS.

        """
        page_id = self.request.path_info
        page_id = page_id.lstrip('/')
        page_id = page_id.replace('/', '-')
        page_id = page_id.rstrip('-')

        return page_id or 'root'

    @cached_property
    def top_navigation(self):
        """ Returns a list of :class:`onegov.town.elements.Link` objects.
        Those links are used for the top navigation.

        If nothing is returned, no top navigation is displayed.

        """
        return None

    @cached_property
    def breadcrumbs(self):
        """ Returns a list of :class:`onegov.town.elements.Link` objects.
        Those links are used for the breadcrumbs.

        If nothing is returned, no top breadcrumbs are displayed.

        """
        return None

    @cached_property
    def sidebar_links(self):
        """ A list of links shown in the sidebar, used for navigation. """
        return None

    @cached_property
    def bottom_links(self):
        """ A list of links shown at the absolute bottom. Use this for
        links like administration, statistics, source-code.

        """
        return None

    @cached_property
    def editbar_links(self):
        """ A of :class:`onegov.town.elements.LinkGroup` classes. Each of them
        will be shown in the top editbar, with the group title being the
        dropdown title.
        """
        return None

    @cached_property
    def file_upload_url(self):
        """ Returns the url to the file upload action. """
        url = self.request.link(FileCollection(self.app), name='upload')
        return self.csrf_protected_url(url)

    @cached_property
    def file_upload_json_url(self):
        """ Adds the json url for file uploads. """
        url = self.request.link(FileCollection(self.app), name='upload.json')
        return self.csrf_protected_url(url)

    @cached_property
    def file_list_url(self):
        """ Adds the json url for file lists. """
        return self.request.link(FileCollection(self.app), name='json')

    @cached_property
    def image_upload_url(self):
        """ Returns the url to the image upload action. """
        url = self.request.link(ImageCollection(self.app), name='upload')
        return self.csrf_protected_url(url)

    @cached_property
    def image_upload_json_url(self):
        """ Adds the json url for image uploads. """
        url = self.request.link(ImageCollection(self.app), name='upload.json')
        return self.csrf_protected_url(url)

    @cached_property
    def image_list_url(self):
        """ Adds the json url for image lists. """
        return self.request.link(ImageCollection(self.app), name='json')

    @cached_property
    def sitecollection_url(self):
        """ Adds the json url for internal links lists. """
        return self.request.link(SiteCollection(self.app.session()))

    @cached_property
    def homepage_url(self):
        """ Returns the url to the main page. """
        return self.request.link(self.app.town)

    @cached_property
    def search_url(self):
        """ Returns the url to the search page. """
        return self.request.link(Search(self.request, None, None))

    @cached_property
    def suggestions_url(self):
        """ Returns the url to the suggestions json view. """
        return self.request.link(Search(self.request, None, None), 'suggest')

    @cached_property
    def open_tickets_url(self):
        return self.request.link(
            TicketCollection(self.request.app.session(), state='open'))

    @cached_property
    def pending_tickets_url(self):
        return self.request.link(
            TicketCollection(self.request.app.session(), state='pending'))

    @cached_property
    def closed_tickets_url(self):
        return self.request.link(
            TicketCollection(self.request.app.session(), state='closed'))

    @cached_property
    def login_url(self):
        """ Returns the login url for the current page. """
        return '{}?to={}'.format(
            self.request.link(self.town, 'login'),
            self.request.transform(self.request.path)
        )

    @cached_property
    def events_url(self):
        return self.request.link(
            OccurrenceCollection(self.request.app.session())
        )

    def include_editor(self):
        self.request.include('redactor')
        self.request.include('redactor_theme')
        self.request.include('editor')

    def include_code_editor(self):
        self.request.include('code_editor')

    def thumbnail_url(self, url):
        """ Takes the given url and returns the thumbnail url for it, if it
        exists. Otherwise returns the url as is.

        """
        thumbnail = Thumbnail.from_url(url)

        if self.request.app.filestorage.exists(thumbnail.path):
            return self.request.link(thumbnail)
        else:
            return url

    def render_field(self, field):
        """ Alias for ``onegov.form.render_field``. """
        return render_field(field)

    def field_download_link(self, field):
        if not field.type == 'UploadField':
            return None

        if field.data.get('data', '').startswith('@'):
            return self.request.link(
                FormSubmissionFile(id=field.data['data'].lstrip('@')))


class DefaultMailLayout(Layout):
    """ A special layout for creating HTML E-Mails. """

    @cached_property
    def base(self):
        return self.template_loader['mail_layout.pt']

    @cached_property
    def macros(self):
        return self.template_loader['mail_macros.pt']


class DefaultLayout(Layout):
    """ The defaut layout meant for the public facing parts of the site. """

    def __init__(self, model, request):
        super(Layout, self).__init__(model, request)

        # always include the common js files
        self.request.include('common')
        self.request.include('common_css')

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        query = PageCollection(self.app.session()).query()
        query = query.order_by(desc(Page.type), Page.title)
        query = query.filter(Page.parent_id == None)

        return self.request.exclude_invisible(query.all())

    @cached_property
    def top_navigation(self):
        return tuple(
            Link(r.title, self.request.link(r)) for r in self.root_pages
        )

    @cached_property
    def bottom_links(self):

        request = self.request

        if request.current_role == 'editor':
            return [
                Link(_(u'Logout'), request.link(self.town, 'logout')),
                Link(_(u'Files'), request.link(FileCollection(self.app))),
                Link(_(u'Images'), request.link(ImageCollection(self.app))),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]
        elif request.current_role == 'admin':
            return [
                Link(_(u'Logout'), request.link(self.town, 'logout')),
                Link(_(u'Files'), request.link(FileCollection(self.app))),
                Link(_(u'Images'), request.link(ImageCollection(self.app))),
                Link(_(u'Settings'), request.link(self.town, 'einstellungen')),
                Link(_(u'Tickets'), request.link(TicketCollection(
                    self.app.session()
                ))),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]
        else:
            return [
                Link(_(u'Login'), self.login_url),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]


class AdjacencyListLayout(DefaultLayout):
    """ Provides layouts for for models inheriting from
    :class:`onegov.core.orm.abstract.AdjacencyList`

    """

    def get_breadcrumbs(self, item):
        """ Yields the breadcrumbs for the given adjacency list item. """

        yield Link(_("Homepage"), self.homepage_url)

        for ancestor in item.ancestors:
            yield Link(ancestor.title, self.request.link(ancestor))

        yield Link(item.title, self.request.link(item))

    def get_sidebar(self, type=None):
        """ Yields the sidebar for the given adjacency list item. """
        query = self.model.siblings.filter(self.model.__class__.type == type)
        query = query.order_by(self.model.__class__.title)

        for item in self.request.exclude_invisible(query.all()):
            url = self.request.link(item)

            if item != self.model:
                yield Link(item.title, url, model=item)
            else:
                yield Link(item.title, url, model=item, active=True)

                children = sorted(
                    self.request.exclude_invisible(self.model.children),
                    key=lambda c: c.title
                )

                for item in children:
                    yield Link(
                        text=item.title,
                        url=self.request.link(item),
                        classes=('childpage', ),
                        model=item
                    )

                yield Link("...", "#", classes=('new-content-placeholder', ))


class PageLayout(AdjacencyListLayout):

    @cached_property
    def breadcrumbs(self):
        return list(self.get_breadcrumbs(self.model))

    @cached_property
    def sidebar_links(self):
        return list(self.get_sidebar(type='topic'))


class NewsLayout(AdjacencyListLayout):

    @cached_property
    def breadcrumbs(self):
        return list(self.get_breadcrumbs(self.model))


class EditorLayout(AdjacencyListLayout):

    def __init__(self, model, request, site_title):
        super(EditorLayout, self).__init__(model, request)
        self.site_title = site_title
        self.include_editor()

    @cached_property
    def breadcrumbs(self):
        links = list(self.get_breadcrumbs(self.model.page))
        links.append(Link(self.site_title, url='#'))

        return links


class FormEditorLayout(DefaultLayout):

    def __init__(self, model, request):
        super(FormEditorLayout, self).__init__(model, request)
        self.include_editor()
        self.include_code_editor()


class FormSubmissionLayout(DefaultLayout):

    def __init__(self, model, request, title=None):
        super(FormSubmissionLayout, self).__init__(model, request)
        self.title = title or self.form.title

    @cached_property
    def form(self):
        if hasattr(self.model, 'form'):
            return self.model.form
        else:
            return self.model

    @cached_property
    def breadcrumbs(self):
        collection = FormCollection(self.request.app.session())

        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Forms"), self.request.link(collection)),
            Link(self.title, '#')
        ]

    @cached_property
    def editbar_links(self):

        if not self.request.is_logged_in:
            return

        # only show the edit bar links if the site is the base of the form
        # -> if the user already entered some form data remove the edit bar
        # because it makes it seem like it's there to edit the submission,
        # not the actual form
        if hasattr(self.model, 'form'):
            return

        collection = FormCollection(self.request.app.session())

        edit_link = Link(
            text=_("Edit"),
            url=self.request.link(self.form, name='bearbeiten'),
            classes=('edit-link', )
        )

        if self.form.type == 'builtin':
            delete_link = DeleteLink(
                text=_("Delete"),
                url=self.request.link(self.form),
                confirm=_("This form can't be deleted."),
                extra_information=_(
                    "This is a builtin-form. "
                    "Builtin-forms can't be deleted."
                )
            )

        elif self.form.has_submissions(with_state='complete'):
            delete_link = DeleteLink(
                text=_("Delete"),
                url=self.request.link(self.form),
                confirm=_("This form can't be deleted."),
                extra_information=_(
                    "The are submissions associated with the form. "
                    "Those need to be removed first."
                )
            )

        else:
            delete_link = DeleteLink(
                text=_("Delete"),
                url=self.request.link(self.form),
                confirm=_("Do you really want to delete this form?"),
                yes_button_text=_("Delete form"),
                redirect_after=self.request.link(collection)
            )

        return [
            edit_link, delete_link
        ]


class FormCollectionLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Forms"), '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_logged_in:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Form"),
                            url=self.request.link(
                                self.model,
                                name='neu'
                            ),
                            classes=('new-form', )
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
        if self.request.is_logged_in:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Person"),
                            url=self.request.link(
                                self.model,
                                name='neu'
                            ),
                            classes=('new-person', )
                        )
                    ]
                ),
            ]


class PersonLayout(DefaultLayout):

    @cached_property
    def collection(self):
        return PersonCollection(self.request.app.session())

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("People"), self.request.link(self.collection)),
            Link(_(self.model.title), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_logged_in:
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'bearbeiten'),
                    classes=('edit-link', )
                ),
                DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_(
                        "Do you really want to delete this person?"),
                    yes_button_text=_("Delete person"),
                    redirect_after=self.request.link(self.collection)
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

    @cached_property
    def collection(self):
        return TicketCollection(self.request.app.session())

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Tickets"), self.request.link(self.collection)),
            Link(self.model.number, '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_logged_in:

            # only show the model related links when the ticket is pending
            if self.model.state == 'pending':
                links = self.model.handler.get_links(self.request)
            else:
                links = []

            if self.model.state == 'open':
                links.append(Link(
                    text=_("Accept ticket"),
                    url=self.request.link(self.model, 'accept'),
                    classes=('ticket-action', 'ticket-accept'),
                ))

            elif self.model.state == 'pending':
                links.append(Link(
                    text=_("Close ticket"),
                    url=self.request.link(self.model, 'close'),
                    classes=('ticket-action', 'ticket-close'),
                ))

            elif self.model.state == 'closed':
                links.append(Link(
                    text=_("Reopen ticket"),
                    url=self.request.link(self.model, 'reopen'),
                    classes=('ticket-action', 'ticket-reopen'),
                ))

            return links


class ResourcesLayout(DefaultLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Reservations"), self.request.link(self.model))
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_logged_in:
            return [
                LinkGroup(
                    title=_("Add"),
                    links=[
                        Link(
                            text=_("Room"),
                            url=self.request.link(
                                self.model,
                                name='neuer-raum'
                            ),
                            classes=('new-room', )
                        ),
                        Link(
                            text=_("Daypass"),
                            url=self.request.link(
                                self.model,
                                name='neue-tageskarte'
                            ),
                            classes=('new-daypass', )
                        )
                    ]
                ),
            ]


class ResourceLayout(DefaultLayout):

    def __init__(self, model, request):
        super(ResourceLayout, self).__init__(model, request)

        self.request.include('fullcalendar')
        self.request.include('fullcalendar_css')

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
        if self.request.is_logged_in:
            if self.model.deletable(self.request.app.libres_context):
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_("Do you really want to delete this resource?"),
                    yes_button_text=_("Delete resource"),
                    redirect_after=self.request.link(self.collection)
                )

            else:
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_("This resource can't be deleted."),
                    extra_information=_(
                        "There are existing reservations associated "
                        "with this resource"
                    )
                )
            return [
                Link(
                    text=_("Edit"),
                    url=self.request.link(self.model, 'bearbeiten'),
                    classes=('edit-link', )
                ),
                delete_link,
                Link(
                    text=_("Clean up"),
                    url=self.request.link(self.model, 'cleanup'),
                    classes=('cleanup-link', )
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
        if self.request.is_logged_in:
            if self.model.availability == 100.0:
                yield DeleteLink(
                    _("Delete"),
                    self.request.link(self.model),
                    confirm=_("Do you really want to delete this allocation?"),
                    yes_button_text=_("Delete allocation"),
                    redirect_after=self.request.link(self.collection)
                )
            else:
                yield DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_("This resource can't be deleted."),
                    extra_information=_(
                        "There are existing reservations associated "
                        "with this resource"
                    ),
                    redirect_after=self.request.link(self.collection)
                )


class EventBaseLayout(DefaultLayout):

    weekday_format = 'dddd'
    month_format = 'MMMM'
    event_format = 'dddd, D. MMMM YYYY, HH:mm'

    def format_date(self, date, format):
        """ Takes a datetime and formats it.

        This overrides :meth:`onegov.core.Layout.format_date` since we want to
        display the date in the timezone given by the event, not a fixed one.

        """
        if format in ('date', 'time', 'datetime'):
            return date.strftime(getattr(self, format + '_format'))

        if format in ('weekday', 'month', 'smonth', 'event'):
            return arrow.get(date).format(
                getattr(self, format + '_format'),
                locale=self.request.locale
            )

    def format_recurrence(self, recurrence):
        """ Returns a human readable version of an RRULE used by us. """

        WEEKDAYS = (_("Mo"), _("Tu"), _("We"), _("Th"), _("Fr"), _("Sa"),
                    _("Su"))

        if recurrence:
            rule = rrule.rrulestr(recurrence)
            if rule._freq == rrule.WEEKLY:
                return _(
                    u"Every ${days} until ${end}",
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


class OccurrenceLayout(EventBaseLayout):

    @cached_property
    def collection(self):
        return OccurrenceCollection(self.request.app.session())

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Events"), self.request.link(self.collection)),
            Link(self.model.title, '#')
        ]

    @cached_property
    def editbar_links(self):
        if self.request.is_logged_in:
            edit_url = URL(self.request.link(self.model.event, 'bearbeiten'))
            edit_url = edit_url.query_param(
                'return-to', self.request.link(self.model.event)
            )
            edit_link = Link(
                text=_("Edit"),
                url=edit_url.as_string(),
                classes=('edit-link', )
            )

            if self.event_deletable(self.model.event):
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model.event),
                    confirm=_("Do you really want to delete this event?"),
                    yes_button_text=_("Delete event"),
                    redirect_after=self.events_url
                )
            else:
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model.event),
                    confirm=_("This event can't be deleted."),
                    extra_information=_(
                        "To remove this event, go to the ticket and reject it."
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
        if self.request.is_logged_in:
            edit_link = Link(
                text=_("Edit"),
                url=self.request.link(self.model, 'bearbeiten'),
                classes=('edit-link', )
            )
            if self.event_deletable(self.model):
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_("Do you really want to delete this event?"),
                    yes_button_text=_("Delete event"),
                    redirect_after=self.events_url
                )
            else:
                delete_link = DeleteLink(
                    text=_("Delete"),
                    url=self.request.link(self.model),
                    confirm=_("This event can't be deleted."),
                    extra_information=_(
                        "To remove this event, go to the ticket and reject it."
                    )
                )

            return [edit_link, delete_link]
