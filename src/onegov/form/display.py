""" Contains renderers to display form fields. """
from __future__ import annotations


import humanize
import re

from markupsafe import escape, Markup
from onegov.core.markdown import render_untrusted_markdown
from onegov.form import log
from translationstring import TranslationString
from wtforms.widgets.core import html_params

from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from abc import abstractmethod
    from collections.abc import Callable
    from wtforms import Field

_R = TypeVar('_R', bound='BaseRenderer')

__all__ = ('render_field',)


class Registry:
    """ Keeps track of all the renderers and the types they are registered for,
    making sure each renderer is only instantiated once.

    """
    renderer_map: dict[str, BaseRenderer]

    def __init__(self) -> None:
        self.renderer_map = {}

    def register_for(self, *types: str) -> Callable[[type[_R]], type[_R]]:
        """ Decorator to register a renderer. """
        def wrapper(renderer: type[_R]) -> type[_R]:
            instance = renderer()

            for type in types:
                self.renderer_map[type] = instance

            return renderer
        return wrapper

    def render(self, field: Field) -> Markup:
        """ Renders the given field with the correct renderer. """
        if not field.data:
            return Markup('')

        renderer = self.renderer_map.get(field.type)

        if renderer is None:
            log.warning(f'No renderer found for {field.type}')
            return Markup('')
        else:
            return renderer(field)


registry = Registry()

# public interface
render_field = registry.render


class BaseRenderer:
    """ Provides utility functions for all renderers. """

    if TYPE_CHECKING:
        # forward declare that Renderer needs to be callable
        @abstractmethod
        def __call__(self, field: Field) -> Markup: ...

    def escape(self, text: str) -> Markup:
        return escape(text)

    def translate(self, field: Field, text: str) -> str:
        if isinstance(text, TranslationString):
            return field.gettext(text)

        return text


@registry.register_for(
    'StringField',
    'TextAreaField',
)
class StringFieldRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        if field.render_kw:
            if field.render_kw.get('data-editor') == 'markdown':
                return render_untrusted_markdown(field.data)

        return self.escape(field.data or '').replace('\n', Markup('<br>'))


@registry.register_for('PasswordField')
class PasswordFieldRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        return Markup('*' * len(field.data))  # nosec: B704


@registry.register_for('EmailField')
class EmailFieldRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        params = {'href': f'mailto:{field.data}'}
        return Markup(  # nosec: B704
            f'<a {html_params(**params)}>{{email}}</a>'
        ).format(email=field.data)


@registry.register_for('URLField')
class URLFieldRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        params = {'href': field.data}
        return Markup(  # nosec: B704
            f'<a {html_params(**params)}>{{url}}</a>'
        ).format(url=field.data)


@registry.register_for('VideoURLField')
class VideoURLFieldRenderer(BaseRenderer):
    """
    Renders a video url. Embeds the video if in case of vimeo or
    youtube otherwise just displays the url as a link.
    """

    video_template = Markup("""
        <div class="video">
            <div class="videowrapper">
                <iframe allow="fullscreen" frameborder="0" src="{url}"
                sandbox="allow-scripts allow-same-origin
                allow-presentation" referrerpolicy="no-referrer"></iframe>
            </div>
        </div>
    """)
    url_template = Markup('<a href="{url}">{url}</a>')

    def __call__(self, field: Field) -> Markup:
        url = None
        data = field.data

        # youtube
        if any(x in data for x in ['youtube', 'youtu.be']):
            url = self.ensure_youtube_embedded_url(data)

        # vimeo
        if any(x in data for x in ['vimeo']):
            url = self.ensure_vimeo_embedded_url(data)

        if url:
            return self.video_template.format(url=url)

        # for non-vimeo and non-youtube sources we just display the url
        return self.url_template.format(url=data)

    @staticmethod
    def ensure_youtube_embedded_url(url: str) -> str | None:
        pattern = re.compile(
            r'(?:https?://)?(?:www\.)?(?:m\.)?'
            r'(?:youtube|youtu|youtube-nocookie)\.(?:com|be)/'
            r'(?:watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        match = re.match(pattern, url)
        if match:
            video_id = match.group(1)
            return (f'https://www.youtube.com/embed/'
                    f'{video_id}?rel=0&autoplay=0&mute=1')
        return None

    @staticmethod
    def ensure_vimeo_embedded_url(url: str) -> str | None:
        pattern = re.compile(
            r'(?:https?://)?(?:www\.)?'
            r'(?:player\.)?vimeo\.com\/(?:channels\/('
            r'?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|video\/|)(\d+)('
            r'?:|\/\?)')
        match = re.match(pattern, url)
        if match:
            video_id = match.group(1)
            return (f'https://player.vimeo.com/video/{video_id}?muted=1'
                    f'&autoplay=0')
        return None


@registry.register_for('DateField')
class DateFieldRenderer(BaseRenderer):
    # XXX we assume German here currently - should this change we'd have
    # to add a date format to the request and pass it here - which should
    # be doable with little work (not necessary for now)
    date_format = '%d.%m.%Y'

    def __call__(self, field: Field) -> Markup:
        return self.escape(field.data.strftime(self.date_format))


@registry.register_for('DateTimeLocalField')
class DateTimeLocalFieldRenderer(DateFieldRenderer):
    date_format = '%d.%m.%Y %H:%M'


@registry.register_for('TimezoneDateTimeField')
class TimezoneDateTimeFieldRenderer(DateFieldRenderer):
    date_format = '%d.%m.%Y %H:%M %Z'


@registry.register_for('TimeField')
class TimeFieldRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        return Markup(  # nosec: B704
            f'{field.data.hour:02d}:{field.data.minute:02d}'
        )


@registry.register_for('UploadField')
class UploadFieldRenderer(BaseRenderer):

    def __call__(self, field: Field) -> Markup:
        return Markup('{filename} ({size})').format(
            filename=field.data['filename'],
            size=humanize.naturalsize(field.data['size'])
        )


@registry.register_for('UploadMultipleField')
class UploadMultipleFieldRenderer(BaseRenderer):

    def __call__(self, field: Field) -> Markup:
        return Markup('<br>').join(
            Markup('<i class="far fa-file-pdf"></i> {filename} ({'
                   'size})').format(
                filename=data['filename'],
                size=humanize.naturalsize(data['size'])
            ) for data in field.data if data
        )


@registry.register_for('RadioField')
class RadioFieldRenderer(BaseRenderer):

    def __call__(self, field: Field) -> Markup:
        choices = dict(field.choices)  # type:ignore[attr-defined]
        return self.escape('✓ ' + self.translate(
            field, choices.get(field.data, '?')
        ))


@registry.register_for('MultiCheckboxField')
class MultiCheckboxFieldRenderer(BaseRenderer):

    def __call__(self, field: Field) -> Markup:
        choices = {value: f'? ({value})' for value in field.data}
        choices.update(field.choices)  # type:ignore[attr-defined]
        return Markup('<br>').join(
            f'✓ {self.translate(field, choices[value])}'
            for value in field.data
        )


@registry.register_for('CSRFTokenField', 'HiddenField')
class NullRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        return Markup('')


@registry.register_for('DecimalField')
class DecimalRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        return Markup(f'{field.data:.2f}')  # nosec: B704


@registry.register_for('IntegerField')
class IntegerRenderer(BaseRenderer):
    def __call__(self, field: Field) -> Markup:
        return Markup(f'{int(field.data)}')  # nosec: B704
