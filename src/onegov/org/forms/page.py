from onegov.core.security import Private
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import ChangeAdjacencyListUrlForm
from onegov.page.collection import PageCollection
from unidecode import unidecode
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(
        label=_("Title"),
        validators=[InputRequired()],
        render_kw={'autofocus': ''}
    )


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(
        label=_("URL"),
        validators=[InputRequired()],
        render_kw={'class_': 'image-url file-url internal-url'}
    )

    page_image = StringField(
        label=_("Image"),
        render_kw={'class_': 'image-url'},
        description=_(
            'Will be used as image in the page overview on the parent page')
    )


class PageForm(PageBaseForm):
    """ Defines the form for pages with the 'page' trait. """

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_("Text"))

    lead_when_child = BooleanField(
        label=_('Show the lead if accessing the parent page'),
        description=_("(Redesign only)")
    )


class PageUrlForm(ChangeAdjacencyListUrlForm):

    def get_model(self):
        return self.model.page


class MovePageForm(Form):
    """ Form to move a page including its sub pages. """

    parent_id = ChosenSelectField(
        label=_("Destination"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        self.request.include('common')
        self.request.include('chosen')

        pages = PageCollection(self.request.session)
        self.iterate_page_tree(pages.roots, indent='',
                               page_list=self.parent_id.choices)

        # adding root element
        if self.request.has_permission(pages, Private):
            self.parent_id.choices.insert(
                0, ('root', self.request.translate(_("- Root -")))
            )

    def iterate_page_tree(self, pages, indent='', page_list=None):
        """
        Iterates over the page tree and lists the elements with ident
        to show the page hierarchy in the choices list
        """
        for page in pages:
            if self.request.has_permission(page, Private):
                item = (str(page.id), f'{indent} {unidecode(page.title)}')
                page_list.append(item)

            self.iterate_page_tree(page.children, indent=indent + ' -',
                                   page_list=page_list)

    def update_model(self, model):
        session = self.request.session
        agencies = PageCollection(session)

        parent_id = None
        parent = None
        if self.parent_id.data and self.parent_id.data.isdigit():
            parent_id = int(self.parent_id.data)
            parent = agencies.by_id(parent_id)
        model.name = agencies.get_unique_child_name(model.title, parent)
        model.parent_id = parent_id

    def apply_model(self, model):

        def remove(item):
            item = (str(item.id), item.title)
            if item in self.parent_id.choices:
                self.parent_id.choices.remove(item)

        def remove_with_children(item):
            remove(item)
            for child in item.children:
                remove_with_children(child)

        if model.parent:
            remove(model.parent)
        else:
            self.parent_id.choices.pop(0)
        remove_with_children(model)
