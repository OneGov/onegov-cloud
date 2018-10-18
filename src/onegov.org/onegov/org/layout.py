import babel.dates
import re

from babel import Locale
from cached_property import cached_property
from datetime import date, datetime, time, timedelta
from dateutil import rrule
from dateutil.rrule import rrulestr
from decimal import Decimal
from onegov.core.crypto import RANDOM_TOKEN_LENGTH
from onegov.core.i18n import SiteLocale
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.core.utils import linkify
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryEntryCollection
from onegov.event import OccurrenceCollection
from onegov.file import File
from onegov.form import FormCollection, render_field
from onegov.newsletter import NewsletterCollection, RecipientCollection
from onegov.org import _
from onegov.org import utils
from onegov.org.models import ExportCollection
from onegov.org.models import GeneralFileCollection
from onegov.org.models import ImageFile
from onegov.org.models import ImageFileCollection
from onegov.org.models import ImageSetCollection
from onegov.org.models import News
from onegov.org.models import PageMove
from onegov.org.models import PersonMove
from onegov.org.models import PublicationCollection
from onegov.org.models import ResourceRecipientCollection
from onegov.org.models import Search
from onegov.org.models import SiteCollection
from onegov.org.models.extensions import PersonLinkExtension
from onegov.org.new_elements import Block, Confirm, Intercooler
from onegov.org.new_elements import Link, LinkGroup
from onegov.org.theme.org_theme import user_options
from onegov.pay import PaymentCollection, PaymentProviderCollection
from onegov.people import PersonCollection
from onegov.reservation import ResourceCollection
from onegov.ticket import TicketCollection
from onegov.user import Auth, UserCollection
from onegov.user.utils import password_reset_url
from sedate import to_timezone


capitalised_name = re.compile(r'[A-Z]{1}[a-z]+')


class Layout(ChameleonLayout):
    """ Contains methods to render a page inheriting from layout.pt.

    All pages inheriting from layout.pt rely on this class being present
    as 'layout' variable::

     @OrgApp.html(model=Example, template='example.pt', permission=Public)
        def view_example(self, request):
            return { 'layout': DefaultLayout(self, request) }

    It is meant to be extended for different parts of the site. For example,
    the :class:`DefaultLayout` includes the top navigation defined by
    onegov.page.

    It's possible though to have a different part of the website use a
    completely different top navigation. For that, a new Layout class
    inheriting from this one should be added.

    """

    date_long_without_year_format = 'E d. MMMM'
    datetime_long_without_year_format = 'E d. MMMM HH:mm'
    event_format = 'EEEE, d. MMMM YYYY'

    def __init__(self, *args, **kwargs):
        # overrides body attributes set in the layout template
        self.custom_body_attributes = {}

        super().__init__(*args, **kwargs)

    @property
    def name(self):
        """ Takes the class name of the layout and generates a name which
        can be used as a class. """

        return '-'.join(
            token.lower() for token in capitalised_name.findall(
                self.__class__.__name__
            )
        )

    @property
    def org(self):
        """ An alias for self.request.app.org. """
        return self.request.app.org

    @property
    def primary_color(self):
        return self.org.theme_options.get(
            'primary-color', user_options['primary-color'])

    @cached_property
    def default_map_view(self):
        return self.org.default_map_view or {
            'lon': 8.30576869173879,
            'lat': 47.05183585,
            'zoom': 12
        }

    @cached_property
    def svg(self):
        return self.template_loader['svg.pt']

    @cached_property
    def font_awesome_path(self):
        return self.request.link(StaticFile(
            f'font-awesome/css/font-awesome.min.css',
            version=self.app.version
        ))

    def static_file_path(self, path):
        return self.request.link(StaticFile(path, version=self.app.version))

    @cached_property
    def page_id(self):
        """ Returns the unique page id of the rendered page. Used to have
        a useful id in the body element for CSS/JS.

        """
        page_id = self.request.path_info
        page_id = page_id.lstrip('/')
        page_id = page_id.replace('/', '-')
        page_id = page_id.replace('+', '')
        page_id = page_id.rstrip('-')

        return 'page-' + (page_id or 'root')

    @cached_property
    def body_classes(self):
        """ Yields a list of body classes used on the body. """

        if self.request.is_logged_in:
            yield 'is-logged-in'
            yield 'role-{}'.format(self.request.current_role)
        else:
            yield 'is-logged-out'

        yield self.name

    @cached_property
    def top_navigation(self):
        """ Returns a list of :class:`onegov.org.elements.Link` objects.
        Those links are used for the top navigation.

        If nothing is returned, no top navigation is displayed.

        """
        return None

    @cached_property
    def breadcrumbs(self):
        """ Returns a list of :class:`onegov.org.elements.Link` objects.
        Those links are used for the breadcrumbs.

        If nothing is returned, no top breadcrumbs are displayed.

        """
        return None

    @cached_property
    def sidebar_links(self):
        """ A list of links shown in the sidebar, used for navigation. """
        return None

    @cached_property
    def editbar_links(self):
        """ A of :class:`onegov.org.elements.LinkGroup` classes. Each of them
        will be shown in the top editbar, with the group title being the
        dropdown title.
        """
        return None

    @cached_property
    def locales(self):
        to = self.request.url

        def get_name(locale):
            return Locale.parse(locale).get_language_name().capitalize()

        def get_link(locale):
            return self.request.link(SiteLocale(locale, to))

        return [
            (get_name(locale), get_link(locale))
            for locale in sorted(self.app.locales)
        ]

    @cached_property
    def file_upload_url(self):
        """ Returns the url to the file upload action. """
        url = self.request.link(GeneralFileCollection(self.app), name='upload')
        return self.csrf_protected_url(url)

    @cached_property
    def file_upload_json_url(self):
        """ Adds the json url for file uploads. """
        url = self.request.link(
            GeneralFileCollection(self.app), name='upload.json'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def file_list_url(self):
        """ Adds the json url for file lists. """
        return self.request.link(GeneralFileCollection(self.app), name='json')

    @cached_property
    def image_upload_url(self):
        """ Returns the url to the image upload action. """
        url = self.request.link(ImageFileCollection(self.app), name='upload')
        return self.csrf_protected_url(url)

    @cached_property
    def image_upload_json_url(self):
        """ Adds the json url for image uploads. """
        url = self.request.link(
            ImageFileCollection(self.app), name='upload.json'
        )
        return self.csrf_protected_url(url)

    @cached_property
    def image_list_url(self):
        """ Adds the json url for image lists. """
        return self.request.link(ImageFileCollection(self.app), name='json')

    @cached_property
    def sitecollection_url(self):
        """ Adds the json url for internal links lists. """
        return self.request.link(SiteCollection(self.app.session()))

    @cached_property
    def homepage_url(self):
        """ Returns the url to the main page. """
        return self.request.link(self.app.org)

    @cached_property
    def search_url(self):
        """ Returns the url to the search page. """
        return self.request.link(Search(self.request, None, None))

    @cached_property
    def suggestions_url(self):
        """ Returns the url to the suggestions json view. """
        return self.request.link(Search(self.request, None, None), 'suggest')

    @cached_property
    def events_url(self):
        return self.request.link(
            OccurrenceCollection(self.request.session)
        )

    @cached_property
    def news_url(self):
        return self.request.class_link(News, {'absorb': ''})

    @cached_property
    def newsletter_url(self):
        return self.request.class_link(NewsletterCollection)

    def login_to_url(self, to, skip=False):
        auth = Auth.from_request(self.request, to=to, skip=skip)
        return self.request.link(auth, 'login')

    def export_formatter(self, format):
        """ Returns a formatter function which takes a value and returns
        the value ready for export.

        """

        def is_daterange_list(value, datetype):
            if isinstance(value, (list, tuple)):
                return all(is_daterange(v, datetype) for v in value)

            return False

        def is_daterange(value, datetype):
            if isinstance(value, (list, tuple)):
                if len(value) == 2:
                    if all(isinstance(v, datetype) for v in value):
                        return True

            return False

        def default(value):
            if isinstance(value, Decimal):
                return float(value)
            if isinstance(value, (date, datetime)):
                return value.isoformat()
            if hasattr(value, 'domain'):
                return self.request.translator(value)
            if isinstance(value, str):
                return "\n".join(value.splitlines())  # normalize newlines
            if isinstance(value, (list, tuple)):
                return tuple(formatter(v) for v in value)

            return value

        if format in ('xlsx', 'csv'):
            def formatter(value):
                if is_daterange_list(value, (date, datetime)):
                    return '\n'.join(formatter(v) for v in value)
                if is_daterange(value, datetime):
                    return ' - '.join(
                        self.format_date(v, 'datetime') for v in value)
                if is_daterange(value, date):
                    return ' - '.join(
                        self.format_date(v, 'date') for v in value)
                if isinstance(value, datetime):
                    return self.format_date(value, 'datetime')
                if isinstance(value, date):
                    return self.format_date(value, 'date')
                if isinstance(value, (list, tuple)):
                    return '\n'.join(formatter(v) for v in value)
                if isinstance(value, bool):
                    value = value and _("Yes") or _("No")
                return default(value)
        else:
            formatter = default

        return formatter

    def thumbnail_url(self, url):
        """ Takes the given url and returns the thumbnail url for it.

        Uses some rough heuristic to determine if a url is actually served
        by onegov.file or not. May possibly fail.

        """
        if '/storage/' not in url:
            return url

        image_id = url.split('/storage/')[-1]

        # image file ids are generated from the random_token function
        if len(image_id) == RANDOM_TOKEN_LENGTH:
            return self.request.class_link(
                ImageFile, {'id': image_id}, name='thumbnail')
        else:
            return url

    def include_editor(self):
        self.request.include('redactor')
        self.request.include('editor')

    def include_code_editor(self):
        self.request.include('code_editor')

    def render_field(self, field):
        """ Alias for ``onegov.form.render_field``. """
        return render_field(field)

    def field_download_link(self, field):
        if not field.type == 'UploadField':
            return None

        if field.data.get('data', '').startswith('@'):
            return self.request.class_link(File, {
                'id': field.data['data'].lstrip('@')
            })

    @cached_property
    def move_person_url_template(self):
        assert isinstance(self.model, PersonLinkExtension)

        implementation = PersonMove.get_implementation(self.model)
        move = implementation.for_url_template(self.model)

        return self.csrf_protected_url(self.request.link(move))

    def get_user_color(self, username):
        return utils.get_user_color(username)

    def get_user_title(self, username):
        user = UserCollection(self.request.session).by_username(username)
        return user and user.title or username

    def to_timezone(self, date, timezone):
        return to_timezone(date, timezone)

    def format_time_range(self, start, end):
        time_range = utils.render_time_range(start, end)

        if time_range in ('00:00 - 24:00', '00:00 - 23:59'):
            return self.request.translate(_("all day"))

        return time_range

    def format_date_range(self, start, end):
        if start == end:
            return self.format_date(start, 'date')
        else:
            return ' - '.join((
                self.format_date(start, 'date'),
                self.format_date(end, 'date')
            ))

    def format_datetime_range(self, start, end, with_year=False):

        if start.date() == end.date():
            show_single_day = True
        elif (end - start) <= timedelta(hours=23) and end.time() < time(6, 0):
            show_single_day = True
        else:
            show_single_day = False

        if show_single_day:
            fmt = with_year and 'date_long' or 'date_long_without_year'

            return ' '.join((
                self.format_date(start, fmt),
                self.format_time_range(start, end)
            ))
        else:
            fmt = with_year and 'datetime_long' or 'datetime_long_without_year'

            return ' - '.join((
                self.format_date(start, fmt),
                self.format_date(end, fmt)
            ))

    def format_timedelta(self, delta):
        return babel.dates.format_timedelta(
            delta=delta,
            locale=self.request.locale
        )

    def format_seconds(self, seconds):
        return self.format_timedelta(timedelta(seconds=seconds))

    def password_reset_url(self, user):
        if not user:
            return

        return password_reset_url(
            user,
            self.request,
            self.request.class_link(Auth, name='reset-password')
        )


class DefaultLayout(Layout):
    """ The defaut layout meant for the public facing parts of the site. """

    def __init__(self, model, request):
        super().__init__(model, request)

        # always include the common js files
        self.request.include('common')

        if self.request.is_manager:
            self.request.include('sortable')

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        return self.request.exclude_invisible(self.app.root_pages)

    @cached_property
    def top_navigation(self):
        return tuple(
            Link(r.title, self.request.link(r)) for r in self.root_pages
        )

    @cached_property
    def elements(self):
        return self.template_loader['elements.pt']


class DefaultMailLayout(Layout):
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

    def unsubscribe_link(self, username):
        return '{}?token={}'.format(
            self.request.link(self.org, name='unsubscribe'),
            self.request.new_url_safe_token(
                data={'user': username},
                salt='unsubscribe'
            )
        )


class AdjacencyListLayout(DefaultLayout):
    """ Provides layouts for for models inheriting from
    :class:`onegov.core.orm.abstract.AdjacencyList`

    """

    @cached_property
    def sortable_url_template(self):
        return self.csrf_protected_url(
            self.request.link(PageMove.for_url_template())
        )

    def get_breadcrumbs(self, item):
        """ Yields the breadcrumbs for the given adjacency list item. """

        yield Link(_("Homepage"), self.homepage_url)

        for ancestor in item.ancestors:
            yield Link(ancestor.title, self.request.link(ancestor))

        yield Link(item.title, self.request.link(item))

    def get_sidebar(self, type=None):
        """ Yields the sidebar for the given adjacency list item. """
        query = self.model.siblings.filter(self.model.__class__.type == type)
        items = self.request.exclude_invisible(query.all())

        for item in items:
            if item != self.model:
                yield Link(item.title, self.request.link(item), model=item)
            else:
                children = (
                    Link(c.title, self.request.link(c), model=c) for c
                    in self.request.exclude_invisible(self.model.children)
                )

                yield LinkGroup(
                    title=item.title,
                    links=tuple(children),
                    model=item
                )


class PageLayout(AdjacencyListLayout):

    @cached_property
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))

    @cached_property
    def sidebar_links(self):
        return tuple(self.get_sidebar(type='topic'))


class NewsLayout(AdjacencyListLayout):

    @cached_property
    def breadcrumbs(self):
        return tuple(self.get_breadcrumbs(self.model))


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
                        )
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
                        _("Delete form")
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
                            _("Delete person")
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

            # if we have a payment, add pamyent links
            if self.model.state == 'pending':
                payment = self.model.handler.payment

                if payment and payment.source == 'manual':
                    links.extend(self.get_manual_payment_links(payment))
                if payment and payment.source == 'stripe_connect':
                    links.extend(self.get_stripe_payment_links(payment))

            if self.model.state == 'open':
                links.append(Link(
                    text=_("Accept ticket"),
                    url=self.request.link(self.model, 'accept'),
                    attrs={'class': ('ticket-button', 'ticket-accept')}
                ))

            elif self.model.state == 'pending':
                links.append(Link(
                    text=_("Close ticket"),
                    url=self.request.link(self.model, 'close'),
                    attrs={'class': ('ticket-button', 'ticket-close')}
                ))

            elif self.model.state == 'closed':
                links.append(Link(
                    text=_("Reopen ticket"),
                    url=self.request.link(self.model, 'reopen'),
                    attrs={'class': ('ticket-button', 'ticket-reopen')}
                ))

            # muting/unmuting is always enabled
            if self.model.muted:
                links.append(
                    Link(
                        text=_("Enable E-Mails"),
                        url=self.request.link(self.model, 'unmute'),
                        attrs={'class': 'unmute'}
                    )
                )
            else:
                links.append(
                    Link(
                        text=_("Disable E-Mails"),
                        url=self.request.link(self.model, 'mute'),
                        attrs={'class': 'mute'}
                    )
                )

            # ticket notes are always enabled
            links.append(
                Link(
                    text=_("New Note"),
                    url=self.request.link(self.model, 'note'),
                    attrs={'class': 'new-note'}
                )
            )

            return links

    def get_manual_payment_links(self, payment):
        if payment.state == 'open':
            yield Link(
                text=_("Mark as paid"),
                url=self.csrf_protected_url(
                    self.request.link(payment, 'mark-as-paid'),
                ),
                attrs={'class': 'mark-as-paid'},
                traits=(
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.url,
                    ),
                )
            )
        else:
            yield Link(
                text=_("Mark as unpaid"),
                url=self.csrf_protected_url(
                    self.request.link(payment, 'mark-as-unpaid'),
                ),
                attrs={'class': 'mark-as-unpaid'},
                traits=(
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.url,
                    ),
                )
            )

    def get_stripe_payment_links(self, payment):
        if payment.state == 'open':
            yield Link(
                text=_("Capture Payment"),
                url=self.csrf_protected_url(
                    self.request.link(payment, 'capture')
                ),
                attrs={'class': 'payment-capture'},
                traits=(
                    Confirm(
                        _("Do you really want capture the payment?"),
                        _(
                            "This usually happens automatically, so there is "
                            "no reason not do capture the payment."
                        ),
                        _("Capture payment")
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.url
                    ),
                )
            )
        elif payment.state == 'paid':
            amount = '{:02f} {}'.format(payment.amount, payment.currency)

            yield Link(
                text=_("Refund Payment"),
                url=self.csrf_protected_url(
                    self.request.link(payment, 'refund')
                ),
                attrs={'class': 'payment-refund'},
                traits=(
                    Confirm(
                        _("Do you really want to refund ${amount}?", mapping={
                            'amount': amount
                        }),
                        _("This cannot be undone."),
                        _("Refund ${amount}", mapping={
                            'amount': amount
                        })
                    ),
                    Intercooler(
                        request_method='POST',
                        redirect_after=self.request.url
                    )
                )
            )


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
                            _("Delete resource")
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
                            )
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
                )
            ]


class ReservationLayout(ResourceLayout):
    editbar_links = None


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
                            _("Delete allocation")
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
                            )
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
                                _("Imported events can not be editet.")
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
                                _("Delete event")
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
                            _("Delete event")
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
                            )
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
        if self.request.is_manager:
            if self.model.source:
                return [
                    Link(
                        text=_("Edit"),
                        attrs={'class': 'edit-link'},
                        traits=(
                            Block(
                                _("This event can't be editet."),
                                _("Imported events can not be editet.")
                            )
                        )
                    ),
                    Link(
                        text=_("Delete"),
                        url=self.csrf_protected_url(
                            self.request.link(self.model, 'withdraw'),
                        ),
                        attrs={'class': 'delete-link'},
                        traits=(
                            Confirm(
                                _("Do you really want to delete this event?"),
                                _("This cannot be undone."),
                                _("Delete event")
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
                            _("Delete event")
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
                            )
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
                            _("Delete photo album")
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
        if self.request.is_admin:
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

        if self.directory.marker_color:
            self.custom_body_attributes['data-default-marker-color']\
                = self.directory.marker_color

        if self.directory.marker_icon:
            self.custom_body_attributes['data-default-marker-icon']\
                = self.directory.marker_icon.encode('unicode-escape')[2:]

    @property
    def directory(self):
        return self.model.directory


class DirectoryEntryCollectionLayout(DirectoryEntryBaseLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Directories"), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                DirectoryEntryCollection, {
                    'directory_name': self.model.directory_name
                }
            ))
        ]

    @cached_property
    def editbar_links(self):

        def links():

            if self.request.is_admin:
                yield Link(
                    text=_("Configure"),
                    url=self.request.link(self.model, '+edit'),
                    attrs={'class': 'edit-link'}
                )

            if self.request.is_manager:
                yield Link(
                    text=_("Export"),
                    url=self.request.class_link(
                        DirectoryEntryCollection, {
                            'directory_name': self.model.directory_name
                        }, name='+export'
                    ),
                    attrs={'class': 'export-link'}
                )

                yield Link(
                    text=_("Import"),
                    url=self.request.class_link(
                        DirectoryEntryCollection, {
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
                            _("Delete directory")
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

        return list(links())


class DirectoryEntryLayout(DirectoryEntryBaseLayout):

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Directories"), self.request.class_link(
                DirectoryCollection
            )),
            Link(_(self.model.directory.title), self.request.class_link(
                DirectoryEntryCollection, {
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
                            _("Delete entry")
                        ),
                        Intercooler(
                            request_method='DELETE',
                            redirect_after=self.request.link(
                                DirectoryEntryCollection(self.model.directory)
                            )
                        )
                    )
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
