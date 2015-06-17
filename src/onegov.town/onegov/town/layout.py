from cached_property import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.form import FormCollection, FormSubmissionFile, render_field
from onegov.page import Page, PageCollection
from onegov.town import _
from onegov.town.elements import Link, LinkGroup
from onegov.town.models import ImageCollection


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

    def __init__(self, model, request):
        super(Layout, self).__init__(model, request)

        # always include the common js files
        self.request.include('common')

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
    def homepage_url(self):
        """ Returns the url to the main page. """
        return self.request.link(self.app.town)

    def render_field(self, field):
        """ Alias for ``onegov.form.render_field``. """
        return render_field(field)

    def field_download_link(self, field):
        if not field.type == 'UploadField':
            return None

        if field.data.get('data', '').startswith('@'):
            return self.request.link(
                FormSubmissionFile(id=field.data['data'].lstrip('@')))


class DefaultLayout(Layout):
    """ The defaut layout meant for the public facing parts of the site. """

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        query = PageCollection(self.app.session()).query()
        query = query.filter(Page.parent_id == None)

        return query.all()

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
                Link(_(u'Images'), request.link(ImageCollection(self.app))),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]
        elif request.current_role == 'admin':
            return [
                Link(_(u'Logout'), request.link(self.town, 'logout')),
                Link(_(u'Images'), request.link(ImageCollection(self.app))),
                Link(_(u'Settings'), request.link(self.town, 'einstellungen')),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]
        else:
            return [
                Link(_(u'Login'), request.link(self.town, 'login')),
                Link(u'OneGov Cloud', 'http://www.onegovcloud.ch'),
                Link(u'Seantis GmbH', 'https://www.seantis.ch')
            ]


class PageLayout(DefaultLayout):
    """ The default layout, extended with the navigation of page objects. """

    @cached_property
    def breadcrumbs(self):
        return self.get_page_breadcrumbs(self.model)

    def get_page_breadcrumbs(self, page):
        links = [Link(_("Homepage"), self.homepage_url)]

        for ancestor in page.ancestors:
            links.append(Link(ancestor.title, self.request.link(ancestor)))

        links.append(Link(page.title, self.request.link(page)))

        return links

    @cached_property
    def sidebar_links(self):
        links = []

        for page in self.model.siblings.filter(Page.type == 'topic').all():
            if page != self.model:
                links.append(
                    Link(page.title, self.request.link(page))
                )
            else:
                links.append(
                    Link(page.title, self.request.link(page), active=True)
                )

                for page in self.model.children:
                    links.append(
                        Link(
                            page.title,
                            self.request.link(page),
                            classes=('childpage', )
                        )
                    )

                links.append(
                    Link("...", '#', classes=('new-content-placeholder',))
                )

        return links


class NewsLayout(PageLayout):
    sidebar_links = None


class EditorLayout(PageLayout):
    sidebar_links = None

    def __init__(self, model, request, site_title):
        super(EditorLayout, self).__init__(model, request)
        self.site_title = site_title

        self.request.include('redactor')
        self.request.include('redactor_theme')
        self.request.include('editor')

    @cached_property
    def breadcrumbs(self):
        links = self.get_page_breadcrumbs(self.model.page)
        links.append(Link(self.site_title, url='#'))
        return links


class FormEditorLayout(DefaultLayout):
    def __init__(self, model, request):
        super(FormEditorLayout, self).__init__(model, request)

        self.request.include('redactor')
        self.request.include('redactor_theme')
        self.request.include('editor')
        self.request.include('code_editor')


class FormSubmissionLayout(DefaultLayout):

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
            Link(self.form.title, '#')
        ]

    @cached_property
    def editbar_links(self):

        if not self.request.is_logged_in:
            return

        collection = FormCollection(self.request.app.session())

        edit_link = Link(
            text=_("Edit"),
            url=self.request.link(self.form, name='bearbeiten'),
            classes=('edit-form', )
        )

        if self.form.type == 'builtin':
            delete_link = Link(
                text=_("Delete"),
                url=self.request.link(self.form),
                request_method='DELETE',
                classes=('confirm', 'delete-form'),
                attributes={
                    'data-confirm': _("This form can't be deleted."),
                    'data-confirm-extra': _(
                        "This is a builtin-form. "
                        "Builtin-forms can't be deleted."
                    ),
                    'data-confirm-no': _("Cancel"),
                    'redirect-after': self.request.link(collection)
                }
            )

        elif self.form.has_submissions(with_state='complete'):
            delete_link = Link(
                text=_("Delete"),
                url=self.request.link(self.form),
                request_method='DELETE',
                classes=('confirm', 'delete-form'),
                attributes={
                    'data-confirm': _("This form can't be deleted."),
                    'data-confirm-extra': _(
                        "The are submissions associated with the form. "
                        "Those need to be removed first."
                    ),
                    'data-confirm-no': _("Cancel"),
                    'redirect-after': self.request.link(collection)
                }
            )
        else:
            delete_link = Link(
                text=_("Delete"),
                url=self.request.link(self.form),
                request_method='DELETE',
                classes=('confirm', 'delete-form'),
                attributes={
                    'data-confirm': _(
                        "Do you really want to delete this form?"),
                    'data-confirm-yes': _("Delete form"),
                    'data-confirm-no': _("Cancel"),
                    'redirect-after': self.request.link(collection)
                }
            )

        return [
            LinkGroup(
                title=_("Form"),
                links=[
                    edit_link,
                    delete_link
                ]
            ),
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
