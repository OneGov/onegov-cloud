from onegov.core import utils
from onegov.core.utils import sanitize_html
from onegov.form import Form, with_options
from onegov.page import Page
from onegov.town import _
from onegov.town.models.traitinfo import TraitInfo
from onegov.town.models.mixins import (
    ContactContentMixin,
    HiddenMetaMixin,
    PeopleContentMixin,
)
from onegov.town.utils import mark_images
from sqlalchemy import desc
from sqlalchemy.orm import undefer, object_session
from wtforms import BooleanField, StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


def extend_form(form_class, request, extensions):
    for extension in extensions:
        form_class = extension(form_class, request)

    return form_class


class Topic(Page, TraitInfo,
            HiddenMetaMixin, PeopleContentMixin, ContactContentMixin):
    __mapper_args__ = {'polymorphic_identity': 'topic'}

    @property
    def deletable(self):
        """ Returns true if this page may be deleted. """
        return self.parent is not None

    @property
    def editable(self):
        return True

    @property
    def allowed_subtraits(self):
        if self.trait == 'link':
            return tuple()

        if self.trait == 'page':
            return ('page', 'link')

        raise NotImplementedError

    def is_supported_trait(self, trait):
        return trait in {'link', 'page'}

    def get_form_class(self, trait, request):
        if trait == 'link':
            return LinkForm

        if trait == 'page':
            return extend_form(PageForm, request, (
                self.extend_form_with_contact,
                self.extend_form_with_people,
            ))

        raise NotImplementedError


class News(Page, TraitInfo,
           HiddenMetaMixin, PeopleContentMixin, ContactContentMixin):
    __mapper_args__ = {'polymorphic_identity': 'news'}

    @property
    def absorb(self):
        return utils.lchop(self.path, 'aktuelles').lstrip('/')

    @property
    def deletable(self):
        return self.parent is not None

    @property
    def editable(self):
        return self.parent is not None

    @property
    def allowed_subtraits(self):
        # only allow one level of news
        if self.parent is None:
            return ('news', )
        else:
            return tuple()

    def is_supported_trait(self, trait):
        return trait in {'news'}

    def get_form_class(self, trait, request):
        if trait == 'news':
            return extend_form(PageForm, request, (
                self.extend_form_with_contact,
                self.extend_form_with_people,
            ))

        raise NotImplementedError

    @property
    def news_query(self):
        query = object_session(self).query(News)
        query = query.filter(Page.parent == self)
        query = query.order_by(desc(Page.created))
        query = query.options(undefer('created'))
        query = query.options(undefer('content'))

        return query


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(_("Title"), [validators.InputRequired()])


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(_("URL"), [validators.InputRequired()])

    def get_page(self, page):
        """ Stores the form values on the page. """
        page.title = self.title.data
        page.content = {'url': self.url.data}

    def set_page(self, page):
        """ Stores the page values on the form. """
        self.title.data = page.title
        self.url.data = page.content.get('url')


class PageForm(PageBaseForm):
    """ Defines the form for pages with the 'page' trait. """
    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html, mark_images])

    is_hidden_from_public = BooleanField(
        label=_("Hide from the public")
    )

    def get_page(self, page):
        """ Stores the form values on the page. """
        page.title = self.title.data
        page.is_hidden_from_public = self.is_hidden_from_public.data
        page.content = {
            'lead': self.lead.data,
            'text': self.text.data
        }

    def set_page(self, page):
        """ Stores the page values on the form. """
        self.title.data = page.title
        self.is_hidden_from_public.data = page.is_hidden_from_public
        self.lead.data = page.content.get('lead', '')
        self.text.data = page.content.get('text', '')
