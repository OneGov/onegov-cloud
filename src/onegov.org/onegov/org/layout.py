import babel.dates

from cached_property import cached_property
from datetime import timedelta
from onegov.core.layout import ChameleonLayout
from onegov.core.crypto import RANDOM_TOKEN_LENGTH
from onegov.event import OccurrenceCollection
from onegov.form import FormSubmissionFile, render_field
from onegov.org import utils
from onegov.ticket import TicketCollection
from onegov.town.models import (
    GeneralFileCollection,
    ImageFile,
    ImageFileCollection,
    PersonMove,
    Search,
    SiteCollection
)
from onegov.town.models.extensions import PersonLinkExtension
from onegov.user import Auth


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
    def primary_color(self):
        raise NotImplementedError

    @cached_property
    def default_map_view(self):
        raise NotImplementedError

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
    def bottom_links(self):
        """ A list of links shown at the absolute bottom. Use this for
        links like administration, statistics, source-code.

        """
        return None

    @cached_property
    def editbar_links(self):
        """ A of :class:`onegov.org.elements.LinkGroup` classes. Each of them
        will be shown in the top editbar, with the group title being the
        dropdown title.
        """
        return None

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
        return self.request.link(
            Auth.from_app(self.app, self.request.transform(self.request.path)),
            name='login'
        )

    @cached_property
    def logout_url(self):
        """ Returns the logout url for the current page. """
        return self.request.link(
            Auth.from_app(self.app, self.request.transform(self.request.path)),
            name='logout'
        )

    @cached_property
    def events_url(self):
        return self.request.link(
            OccurrenceCollection(self.request.app.session())
        )

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
            return self.request.link(
                FormSubmissionFile(id=field.data['data'].lstrip('@')))

    @cached_property
    def move_person_url_template(self):
        assert isinstance(self.model, PersonLinkExtension)

        implementation = PersonMove.get_implementation(self.model)
        move = implementation.for_url_template(self.model)

        return self.csrf_protected_url(self.request.link(move))

    def get_user_color(self, username):
        return utils.get_user_color(username)

    def format_time_range(self, start, end):
        return utils.format_time_range(start, end)

    def format_timedelta(self, delta):
        return babel.dates.format_timedelta(
            delta=delta,
            locale=self.request.locale
        )

    def format_seconds(self, seconds):
        return self.format_timedelta(timedelta(seconds=seconds))
