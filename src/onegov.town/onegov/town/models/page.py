from onegov.form import Form, with_options
from onegov.page import Page
from onegov.town import _
from onegov.town.utils import sanitize_html
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import URLField
from wtforms.widgets import TextArea


#: Contains the messages that differ for each trait (the handling of all traits
#: is the same). New traits need to adapt the same messages as the others.
trait_messages = {
    'link': dict(
        name=_("Link"),
        new_page_title=_("New Link"),
        new_page_added=_("Added a new link"),
        edit_page_title=_("Edit Link"),
        delete_message=_("The link was deleted"),
        delete_button=_("Delete link"),
        delete_question=_(
            "Do you really want to delete the link \"${title}\"?"),
    ),
    'page': dict(
        name=_("Topic"),
        new_page_title=_("New Topic"),
        new_page_added=_("Added a new topic"),
        edit_page_title=_("Edit Topic"),
        delete_message=_("The topic was deleted"),
        delete_button=_("Delete topic"),
        delete_question=_(
            "Do you really want to delete the topic \"${title}\"?"),
    )
}


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
        return trait_messages


class Topic(Page, TraitInfo):
    __mapper_args__ = {'polymorphic_identity': 'topic'}

    @property
    def allowed_subtraits(self):
        """ Returns a list of traits that this page may contain. """
        if self.trait == 'link':
            return tuple()

        if self.trait == 'page':
            return ('page', 'link')

        raise NotImplementedError

    @staticmethod
    def is_supported_trait(trait):
        """ Returns true if the given trait is supported by this type (this
        doesn't mean that the trait may be added to this page, it serves
        as a simple sanity check, returning True if the combination of the
        type and the trait make any sense at all.

        """
        return trait in {'link', 'page'}

    @property
    def deletable(self):
        """ Returns true if this page may be deleted. """
        return self.parent is not None

    def get_form_class(self, trait):
        """ Returns the form class for the given trait. """
        if trait == 'link':
            return LinkForm

        if trait == 'page':
            return PageForm

        raise NotImplementedError


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
