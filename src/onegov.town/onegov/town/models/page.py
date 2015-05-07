from onegov.core import utils
from onegov.form import Form, with_options
from onegov.page import Page
from onegov.town import _
from onegov.town.const import NEWS_PREFIX, TRAIT_MESSAGES
from onegov.town.utils import sanitize_html
from sqlalchemy import desc
from sqlalchemy.orm import object_session
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


class TraitInfo(object):
    """" Typically used as a mixin for Pages, this class provides
    access to the trait related methods.

    """

    @property
    def trait(self):
        """ Gets the trait of the page. """
        return self.meta.get('trait')

    @trait.setter
    def trait(self, trait):
        """ Sets the trait of the page. """
        self.meta['trait'] = trait

    @property
    def trait_messages(self):
        """ Returns all trait_messages. """
        return TRAIT_MESSAGES

    @property
    def allowed_subtraits(self):
        """ Returns a list of traits that this page may contain. """
        raise NotImplementedError

    def is_supported_trait(trait):
        """ Returns true if the given trait is supported by this type This
        doesn't mean that the trait may be added to this page, it serves
        as a simple sanity check, returning True if the combination of the
        type and the trait make any sense at all.

        """
        raise NotImplementedError

    def get_form_class(self, trait):
        """ Returns the form class for the given trait. """
        raise NotImplementedError


class Topic(Page, TraitInfo):
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

    def get_form_class(self, trait):
        if trait == 'link':
            return LinkForm

        if trait == 'page':
            return PageForm

        raise NotImplementedError


class News(Page, TraitInfo):
    __mapper_args__ = {'polymorphic_identity': 'news'}

    @property
    def absorb(self):
        return utils.lchop(self.path, NEWS_PREFIX).lstrip('/')

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

    def get_form_class(self, trait):
        if trait == 'news':
            return PageForm

        raise NotImplementedError

    @property
    def news_query(self):
        query = object_session(self).query(News)
        query = query.filter(Page.parent == self)
        query = query.order_by(desc(Page.created))

        return query


class PageForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(_("Title"), [validators.InputRequired()])


class LinkForm(PageForm):
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


class PageForm(PageForm):
    """ Defines the form for pages with the 'page' trait. """
    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this page is about"),
        widget=with_options(TextArea, rows=4))

    text = TextAreaField(
        label=_(u"Text"),
        widget=with_options(TextArea, class_='editor'),
        filters=[sanitize_html])

    def get_page(self, page):
        """ Stores the form values on the page. """
        page.title = self.title.data
        page.content = {
            'lead': self.lead.data,
            'text': self.text.data
        }

    def set_page(self, page):
        """ Stores the page values on the form. """
        self.title.data = page.title
        self.lead.data = page.content.get('lead', '')
        self.text.data = page.content.get('text', '')
