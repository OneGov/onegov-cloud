from onegov.core.compat import zip_longest

from cached_property import cached_property
from onegov.page import Page, PageCollection
from onegov.town import _
from onegov.town.elements import Link
from onegov.town.model import ImageCollection, Town
from morepath.security import NO_IDENTITY


class Layout(object):
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

    def __init__(self, model, request):
        self.model = model
        self.request = request

        # always include the common js files
        self.request.include('common')

    @cached_property
    def town(self):
        return self.app.session().query(Town).first()

    @cached_property
    def app(self):
        """ Returns the application behind the request. """
        return self.request.app

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
    def template_loader(self):
        """ Returns the chameleon template loader. """
        return self.app.registry._template_loaders['.pt']

    @cached_property
    def base(self):
        """ Returns the layout, which defines the base layout of all town
        pages. See ``templates/layout.pt``.

        """
        return self.template_loader['layout.pt']

    @cached_property
    def macros(self):
        """ Returns the macros, which offer often used html constructs.
        See ``templates/macros.pt``.

        """
        return self.template_loader['macros.pt']

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
    def bottom_links(self):
        """ A list of links shown at the absolute bottom. Use this for
        links like administration, statistics, source-code.

        """
        return None

    @cached_property
    def is_logged_in(self):
        """ Returns True if the current request is logged in at all. """
        return self.request.identity is not NO_IDENTITY

    @cached_property
    def current_role(self):
        """ Returns the user-role of the current request, if logged in.
        Otherwise, None is returned.

        """
        return self.is_logged_in and self.request.identity.role or None

    def chunks(self, iterable, n, fillvalue=None):
        """ Iterates through an iterable, returning chunks with the given size.

        For example::

            chunks('ABCDEFG', 3, 'x') --> ABC DEF Gxx

        """

        args = [iter(iterable)] * n
        return zip_longest(fillvalue=fillvalue, *args)

    @cached_property
    def image_upload_url(self):
        return self.request.link(ImageCollection(self.app), name='upload')


class DefaultLayout(Layout):
    """ The defaut layout meant for the public facing parts of the site. """

    @cached_property
    def root_pages(self):
        roots = PageCollection(self.app.session()).query().filter(
            Page.parent_id == None,
            Page.meta != None
        )
        return [r for r in roots.all() if r.meta.get('type') == 'town-root']

    @cached_property
    def top_navigation(self):
        return tuple(
            Link(r.title, self.request.link(r)) for r in self.root_pages
        )

    @cached_property
    def bottom_links(self):
        links = []

        links.append(Link(_(u'Homepage'), self.request.link(self.town)))

        if not self.is_logged_in:
            links.append(Link(
                _(u'Login'), self.request.link(self.town, 'login')
            ))
        else:
            links.append(Link(
                _(u'Logout'), self.request.link(self.town, 'logout')
            ))
            links.append(Link(
                _(u'Settings'), self.request.link(self.town, 'settings')
            ))
            links.append(Link(
                _(u'Images'), self.request.link(ImageCollection(self.app))
            ))

        links.append(Link(u'OneGov', 'http://www.onegov.ch'))
        links.append(Link(u'Seantis GmbH', 'https://www.seantis.ch'))

        return links
