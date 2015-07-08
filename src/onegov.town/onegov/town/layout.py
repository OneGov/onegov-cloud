from cached_property import cached_property
from onegov.core.layout import ChameleonLayout
from onegov.core.static import StaticFile
from onegov.form import FormCollection, FormSubmissionFile, render_field
from onegov.page import Page, PageCollection
from onegov.people import PersonCollection
from onegov.town import _
from onegov.town.elements import DeleteLink, Link, LinkGroup
from onegov.town.models import FileCollection
from onegov.town.models import ImageCollection, Thumbnail
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
    def homepage_url(self):
        """ Returns the url to the main page. """
        return self.request.link(self.app.town)

    @cached_property
    def login_url(self):
        """ Returns the login url for the current page. """
        return '{}?to={}'.format(
            self.request.link(self.town, 'login'),
            self.request.transform(self.request.path)
        )

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


class DefaultLayout(Layout):
    """ The defaut layout meant for the public facing parts of the site. """

    @cached_property
    def breadcrumbs(self):
        """ Returns the breadcrumbs for the current page. """
        return [Link(_("Homepage"), self.homepage_url)]

    @cached_property
    def root_pages(self):
        query = PageCollection(self.app.session()).query()
        query = query.order_by(desc(Page.type), Page.name)
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
        query = query.order_by(self.model.__class__.name)

        for item in self.request.exclude_invisible(query.all()):
            url = self.request.link(item)

            if item != self.model:
                yield Link(item.title, url, model=item)
            else:
                yield Link(item.title, url, model=item, active=True)

                children = sorted(
                    self.request.exclude_invisible(self.model.children),
                    key=lambda c: c.name
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

        self.request.include('redactor')
        self.request.include('redactor_theme')
        self.request.include('editor')

    @cached_property
    def breadcrumbs(self):
        links = list(self.get_breadcrumbs(self.model.page))
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
