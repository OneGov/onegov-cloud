import json

from fnmatch import fnmatch
from markupsafe import Markup
from urllib.parse import urlparse

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TagsField
from onegov.form.fields import URLField
from onegov.org import _, log
from onegov.org.forms.fields import HtmlField
from onegov.form.fields import PanelField
from onegov.org.forms.generic import ChangeAdjacencyListUrlForm
from onegov.page.collection import PageCollection
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.widgets import html_params
from wtforms.validators import InputRequired
from wtforms.validators import URL
from wtforms.validators import ValidationError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import (
        Collection, Iterable, Iterator, Mapping, Sequence)
    from onegov.org.models import Topic
    from onegov.org.request import OrgRequest
    from onegov.page import Page
    from wtforms import Field


class PageBaseForm(Form):
    """ Defines the base form for all pages. """
    title = StringField(
        label=_('Title'),
        validators=[InputRequired()],
        render_kw={'autofocus': ''}
    )


class LinkForm(PageBaseForm):
    """ Defines the form for pages with the 'link' trait. """
    url = URLField(
        label=_('URL'),
        default_scheme=None,
        validators=[InputRequired(), URL(require_tld=False)],
        render_kw={'class_': 'image-url file-url internal-url'}
    )

    page_image = StringField(
        label=_('Image'),
        render_kw={'class_': 'image-url'},
        description=_(
            'Will be used as image in the page overview on the parent page')
    )


class PageForm(PageBaseForm):
    """ Defines the form for pages with the 'page' trait. """

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this page is about'),
        render_kw={'rows': 4})

    text = HtmlField(
        label=_('Text'))

    keywords = TagsField(
        label=_('Keywords'),
        description=_(
            'Additional search terms and synonyms for this page. '
            'Helps visitors find this page even if they use different words.'
        )
    )

    lead_when_child = BooleanField(
        label=_('Show the lead if accessing the parent page'),
    )

    def on_request(self) -> None:
        self.request.include('tags-input')


class IframeForm(PageBaseForm):
    """ Defines the form for pages with the 'iframe' trait. """

    lead = TextAreaField(
        label=_('Lead'),
        description=_('Describes what this page is about'),
        render_kw={'rows': 4})

    allowed_domains: list[str] = []

    domain_hint = PanelField(
        text=_('There are currently no allowed domains for iFrames. To enable '
               'domains for iFrames, please contact info@seantis.ch.'),
        kind='callout',
        fieldset=_('URL')
    )

    url = URLField(
        label=_('URL'),
        default_scheme=None,
        validators=[InputRequired(), URL(require_tld=False)],
        fieldset=_('URL')
    )

    height = StringField(
        label=_('Height'),
        description=_('The height of the iFrame in pixels. '
                      'If not set, the iFrame will have a standard height of '
                      '800px.'),
        render_kw={'placeholder': 'auto'},
        fieldset=_('Display')
    )

    as_card = BooleanField(
        label=_('Display as card'),
        description=_('Display the iFrame as a card with a border'),
        fieldset=_('Display')
    )

    def on_request(self) -> None:
        self.allowed_domains = (
            self.request.app.allowed_iframe_domains)  # type: ignore

        for domain in getattr(
            self.request.app.settings.content_security_policy.default,
                'child_src', set()):
            self.allowed_domains.append(domain) if domain != "'self'" else None
        if self.allowed_domains:
            # keep displayed domain order stable
            self.allowed_domains.sort()

            self.domain_hint.text = (
                self.request.translate(
                    _('The following domains are allowed for iFrames:')
                ) + '\n - '
                + '\n - '.join(self.allowed_domains)
                + '\n\n'
                + self.request.translate(
                    _('To allow more domains for iFrames, please contact '
                      'info@seantis.ch.'))
            )

    def validate_url(self, field: URLField) -> None:
        """ Validates the URL against the iFrame allow-list.

        This implements only a subset of CSP source matching: the scheme
        (an ``http`` source also allows ``https``, an empty scheme allows
        any) and the host (with wildcard support, e.g. ``*.vimeo.com``).
        Ports and paths on the allow-list entries are not honoured.
        """

        if not field.data:
            return

        url = urlparse(field.data)
        if url.hostname is None:
            raise ValidationError(
                _('The domain of the URL is not allowed for iFrames.')
            )

        for allowed in self.allowed_domains:
            allowed_url = urlparse(allowed)
            if allowed_url.hostname is None:
                continue
            scheme_matches = (
                not allowed_url.scheme
                or url.scheme == allowed_url.scheme
                # an http source also allows the https upgrade
                or (allowed_url.scheme == 'http' and url.scheme == 'https')
            )
            # CSP child_src entries may use a wildcard host (*.vimeo.com)
            if scheme_matches and fnmatch(url.hostname, allowed_url.hostname):
                return
        raise ValidationError(
            _('The domain of the URL is not allowed for iFrames.')
        )


class ApiTopicPickerWidget:
    """ Renders a hidden input with the selected topic id and a container
    for the topic picker (see ``api-topic-picker.js``). """

    def __call__(self, field: Field, **kwargs: Any) -> Markup:
        kwargs.pop('id', None)
        kwargs['class'] = 'api-topic-picker'
        return Markup('<input type="hidden" {input}><div {picker}></div>').format(
            input=Markup(html_params(  # nosec: B704
                id=field.id, name=field.name, value=field.data or '')),
            picker=Markup(html_params(  # nosec: B704
                data_input=field.id, **kwargs))
        )


API_TOPIC_PICKER_LABELS = {
    'selected': _('Selected topic'),
    'none_selected': _('No topic selected yet'),
    'select': _('Select'),
    'children': _('Subpages'),
    'back': _('Topics'),
    'loading': _('Loading...'),
    'empty': _('No topics found'),
    'more': _('Load more'),
    'error': _('The topics could not be loaded'),
}


class ApiTopicForm(Form):
    """ Defines the form for pages with the 'api' trait.

    Title, lead, text and the sidebar are taken from the linked topic of
    the source organisation (see :mod:`onegov.org.api_source`).

    """

    title = StringField(
        label=_('Title'),
        description=_(
            'Optional. If left empty, the title of the linked topic is used.'),
    )

    api_topic_id = StringField(
        label=_('Linked topic'),
        widget=ApiTopicPickerWidget(),
        validators=[InputRequired()],
    )

    #: the data of the selected topic, fetched during validation
    api_data: dict[str, Any] | None = None

    #: True if the title of the linked topic should be used
    use_source_title = False

    if TYPE_CHECKING:
        request: OrgRequest

    def on_request(self) -> None:
        self.request.include('api-topic-picker')
        self.title.render_kw = {
            'placeholder': self.request.translate(_('Title'))}
        self.api_topic_id.render_kw = {
            'data-api-url': self.request.app.org.api_source_url or '',
            'data-title-input': self.title.id,
            'data-labels': json.dumps({
                key: self.request.translate(label)
                for key, label in API_TOPIC_PICKER_LABELS.items()
            }),
        }

    @property
    def selected_title(self) -> str | None:
        """ The title of the linked topic (shown as placeholder). """
        return self.api_topic_id.render_kw.get('data-selected-title')

    @selected_title.setter
    def selected_title(self, value: str | None) -> None:
        self.api_topic_id.render_kw['data-selected-title'] = value or ''

    def validate_api_topic_id(self, field: StringField) -> None:
        from onegov.org.api_source import (
            ApiLinkForbidden, ApiSourceError, fetch_api_topic,
            register_api_link)

        api_url = self.request.app.org.api_source_url
        if not api_url:
            raise ValidationError(
                _('No API of a source organisation is configured.'))

        if not field.data or not field.data.isdigit():
            raise ValidationError(_('Please select a topic.'))

        try:
            data = fetch_api_topic(api_url, int(field.data))
        except ApiSourceError as exception:
            log.warning(f'Could not fetch API topic: {exception}')
            raise ValidationError(_(
                'The API of the source organisation could not be reached.'
            )) from exception

        if data is None:
            raise ValidationError(
                _('The selected topic is not publicly available.'))

        # the page url is not known yet for new pages, the parent
        # organisation checks if this organisation may link its topics
        try:
            register_api_link(
                api_url,
                int(field.data),
                self.request.link(self.request.app.org).rstrip('/') + '/',
                data['title'],
                dry_run=True
            )
        except ApiLinkForbidden as exception:
            raise ValidationError(_(
                'The source organisation does not allow this organisation '
                'to link its topics.'
            )) from exception
        except ApiSourceError as exception:
            log.warning(f'Could not register API link: {exception}')
            raise ValidationError(_(
                'The API of the source organisation could not be reached.'
            )) from exception

        self.api_data = data
        self.selected_title = data['title']

    def validate(
        self,
        extra_validators: Mapping[str, Sequence[Any]] | None = None
    ) -> bool:
        result = super().validate(extra_validators)
        if result and not self.title.data and self.api_data:
            # the page needs a title (e.g. for the url), it is kept in sync
            # with the source as long as no custom title is set
            self.title.data = self.api_data['title']
            self.use_source_title = True
        return result

    def populate_obj(  # type:ignore[override]
        self,
        obj: Topic,
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        from onegov.org.api_source import (
            ApiSourceError, apply_api_topic, register_api_link,
            unregister_api_link)

        previous_topic_id = obj.api_topic_id
        super().populate_obj(
            obj,
            exclude={'api_topic_id', 'title', *(exclude or ())},
            include=include
        )
        assert self.api_topic_id.data is not None
        obj.api_topic_id = int(self.api_topic_id.data)
        obj.api_use_source_title = self.use_source_title
        obj.title = self.title.data  # type:ignore[assignment]

        api_url = self.request.app.org.api_source_url
        assert api_url is not None
        apply_api_topic(obj, api_url, self.api_data)

        # tell the source organisation which page links its topic
        url = self.request.link(obj)
        if previous_topic_id and previous_topic_id != obj.api_topic_id:
            unregister_api_link(api_url, previous_topic_id, url)
        try:
            register_api_link(api_url, obj.api_topic_id, url, obj.title)
        except ApiSourceError as exception:
            log.warning(f'Could not register API link {url}: {exception}')

    def process_obj(self, obj: Topic) -> None:  # type:ignore[override]
        super().process_obj(obj)
        if obj.api_topic_id:
            self.api_topic_id.data = str(obj.api_topic_id)
        self.selected_title = obj.meta.get('api_source_title') or obj.title
        if obj.api_use_source_title:
            self.title.data = ''


class PageUrlForm(ChangeAdjacencyListUrlForm):

    def get_model(self) -> Page:
        return self.model.page


class MovePageForm(Form):
    """ Form to move a page including its subpages. """

    parent_id = ChosenSelectField(
        label=_('Destination'),
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
            0, (0, self.request.translate(_('- Root -')))
        )

    def iterate_page_tree(
        self,
        pages: Iterable[Page],
        indent: str = '',
    ) -> Iterator[tuple[int, str]]:
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
                raise ValidationError(_('Invalid destination selected'))

            # prevent selecting a child node
            if any(
                choice[0] == new_parent_id
                for choice in self.iterate_page_tree(self.model.page.children)
            ):
                raise ValidationError(_('Invalid destination selected'))

    def update_model(self, model: Page) -> None:
        session = self.request.session
        pages = PageCollection(session)

        new_parent_id = None
        new_parent = None
        if self.parent_id.data:
            new_parent_id = self.parent_id.data
            new_parent = pages.by_id(new_parent_id)

        model.name = pages.get_unique_child_name(model.title, new_parent)
        model.parent_id = new_parent_id
