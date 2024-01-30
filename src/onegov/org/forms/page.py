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
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from onegov.page import Page


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

    def get_model(self) -> 'Page':
        return self.model.page


class MovePageForm(Form):
    """ Form to move a page including its subpages. """

    parent_id = ChosenSelectField(
        label=_("Destination"),
        coerce=int,
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    def on_request(self) -> None:
        pages = PageCollection(self.request.session)
        self.parent_id.choices = list(self.iterate_page_tree(pages.roots))

        # adding root element, ids start beyond 0, so 0 means no parent
        self.parent_id.choices.insert(
            0, (0, self.request.translate(_("- Root -")))
        )

    def iterate_page_tree(
        self,
        pages: 'Iterable[Page]',
        indent: str = '',
    ) -> 'Iterator[tuple[int, str]]':
        """
        Iterates over the page tree and lists the elements with ident
        to show the page hierarchy in the choices list
        """
        from onegov.org.models import News

        for page in pages:
            if isinstance(page, News):
                continue  # prevent pages to be moved under a news page

            yield page.id, f'{indent} {page.title}'

            yield from self.iterate_page_tree(
                page.children,
                indent=indent + ' -'
            )

    def validate_parent_id(self, field: ChosenSelectField) -> None:
        """
        As a new destination (parent page) every menu item is valid except
        yourself or a child of yourself.
        """
        if self.parent_id.data:
            new_parent_id = int(self.parent_id.data)

            # prevent selecting yourself as new parent
            if self.model.page_id == new_parent_id:
                raise ValidationError(_("Invalid destination selected"))

            # prevent selecting a child node
            if any(
                choice[0] == new_parent_id
                for choice in self.iterate_page_tree(self.model.page.children)
            ):
                raise ValidationError(_("Invalid destination selected"))

    def update_model(self, model: 'Page') -> None:
        session = self.request.session
        pages = PageCollection(session)

        new_parent_id = None
        new_parent = None
        if self.parent_id.data:
            new_parent_id = self.parent_id.data
            new_parent = pages.by_id(new_parent_id)

        model.name = pages.get_unique_child_name(model.title, new_parent)
        model.parent_id = new_parent_id
