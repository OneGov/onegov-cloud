from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.org import _
from onegov.org.forms.fields import HtmlField
from onegov.org.forms.generic import ChangeAdjacencyListUrlForm
from onegov.page.collection import PageCollection
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import URL


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
        validators=[InputRequired(), URL(require_tld=False)],
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
    """ Form to move a page including its subpages. """

    parent_id = ChosenSelectField(
        label=_("Destination"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        pages = PageCollection(self.request.session)
        self.iterate_page_tree(pages.roots, indent='',
                               page_list=self.parent_id.choices)

        # adding root element
        self.parent_id.choices.insert(
            0, ('root', self.request.translate(_("- Root -")))
        )

    def iterate_page_tree(self, pages, indent='', page_list=None):
        """
        Iterates over the page tree and lists the elements with ident
        to show the page hierarchy in the choices list
        :returns list of tuples(str:id, str:title)
        """
        from onegov.org.models import News

        for page in pages:
            if isinstance(page, News):
                continue  # prevent pages to be moved under a news page

            item = (str(page.id), f'{indent} {page.title}')
            page_list.append(item)

            self.iterate_page_tree(page.children, indent=indent + ' -',
                                   page_list=page_list)

    def ensure_valid_parent(self):
        """
        As a new destination (parent page) every menu item is valid except
        yourself or a child of yourself.
        :return: bool
        """
        if self.parent_id.data and self.parent_id.data.isdigit():
            new_parent_id = int(self.parent_id.data)

            # prevent selecting yourself as new parent
            if self.model.page_id == new_parent_id:
                self.parent_id.errors.append(
                    _("Invalid destination selected"))
                return False

            # prevent selecting a child node
            child_pages = []
            self.iterate_page_tree(self.model.page.children, indent='',
                                   page_list=child_pages)
            if new_parent_id in [int(child[0]) for child in child_pages]:
                self.parent_id.errors.append(
                    _("Invalid destination selected"))
                return False
        return True

    def update_model(self, model):
        session = self.request.session
        pages = PageCollection(session)

        new_parent_id = None
        new_parent = None
        if self.parent_id.data and self.parent_id.data.isdigit():
            new_parent_id = int(self.parent_id.data)
            new_parent = pages.by_id(new_parent_id)

        model.name = pages.get_unique_child_name(model.title, new_parent)
        model.parent_id = new_parent_id
