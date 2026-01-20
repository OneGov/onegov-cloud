from __future__ import annotations

from datetime import datetime, time
from markupsafe import Markup

from onegov.form import render_field
from onegov.form.display import VideoURLFieldRenderer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from wtforms import Field
    from wtforms.fields.choices import _Choice
else:
    Field = object


class MockField(Field):

    def __init__(
        self,
        type: str,
        data: Any,
        choices: list[_Choice] | None = None
    ) -> None:

        self.type = type
        self.data = data
        self.render_kw = None  # type: ignore[assignment]

        if choices is not None:
            self.choices = choices
        else:
            if isinstance(data, str):
                self.choices = [(data, data)]
            elif isinstance(data, list):
                self.choices = [(c, c) for c in data]


def test_render_textfields() -> None:
    assert render_field(MockField('StringField', 'asdf')) == 'asdf'
    assert render_field(MockField('StringField', '<b>')) == '&lt;b&gt;'

    assert render_field(MockField('TextAreaField', 'asdf')) == 'asdf'
    assert render_field(MockField('TextAreaField', '<b>')) == '&lt;b&gt;'
    assert render_field(
        MockField('TextAreaField', '<script>alert(document.cookie)</script>')
    ) == '&lt;script&gt;alert(document.cookie)&lt;/script&gt;'


def test_render_password() -> None:
    assert render_field(MockField('PasswordField', '123')) == '***'
    assert render_field(MockField('PasswordField', '1234')) == '****'
    assert render_field(MockField('PasswordField', '12345')) == '*****'


def test_render_date_field() -> None:
    assert render_field(
        MockField('DateField', datetime(1984, 4, 6))
    ) == '06.04.1984'
    assert render_field(
        MockField('DateTimeLocalField', datetime(1984, 4, 6))
    ) == '06.04.1984 00:00'
    assert render_field(MockField('TimeField', time(10, 0))) == '10:00'


def test_render_upload_field() -> None:
    assert render_field(MockField('UploadField', {
        'filename': '<b.txt>', 'size': 1000
    })) == '&lt;b.txt&gt; (1.0 kB)'


def test_render_upload_multiple_field() -> None:
    icon_html = '<i class="far fa-file-pdf"></i>'
    assert (
        render_field(
            MockField(
                'UploadMultipleField',
                [
                    {'filename': 'a.txt', 'size': 3000},
                    {},  # deleted file will not be rendered
                    {'filename': 'c.txt', 'size': 2000},
                    {'filename': 'b>.txt', 'size': 1000},
                ],
            )
        )
        == f'{icon_html} a.txt (3.0 kB)<br>{icon_html} c.txt (2.0 kB)<br>'
        f'{icon_html} b&gt;.txt (1.0 kB)'
    )


def test_render_radio_field() -> None:
    assert render_field(MockField('RadioField', 'selected')) == '✓ selected'


def test_render_multi_checkbox_field() -> None:
    assert render_field(MockField('MultiCheckboxField', [])) == ''
    assert render_field(
        MockField('MultiCheckboxField', ['a', 'b'])
    ) == '✓ a<br>✓ b'
    assert render_field(
        MockField('MultiCheckboxField', ['c'], [('a', 'a')])
    ) == '✓ ? (c)'


def test_render_video_url_field() -> None:
    # youtube
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    expected_url: str = Markup.escape(
        'https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0&autoplay=0&mute=1'
    )
    result = render_field(MockField('VideoURLField', url))
    assert isinstance(result, Markup)
    assert result == VideoURLFieldRenderer.video_template.format(
        url=expected_url)

    # vimeo
    url = 'https://vimeo.com/76979871'
    expected_url = 'https://player.vimeo.com/video/76979871?muted=1&autoplay=0'
    result = render_field(MockField('VideoURLField', url))
    assert isinstance(result, Markup)
    assert result == VideoURLFieldRenderer.video_template.format(
        url=expected_url)

    # other
    url = 'https://www.other.com/video/12345'
    expected_url = Markup.escape('https://www.other.com/video/12345')
    result = render_field(MockField('VideoURLField', url))
    assert isinstance(result, Markup)
    assert result == VideoURLFieldRenderer.url_template.format(
        url=expected_url)

    # empty
    url = ''
    result = render_field(MockField('VideoURLField', url))
    assert isinstance(result, Markup)
    assert result == Markup('')


def test_video_url_field_renderer_youtube_regex() -> None:
    renderer = VideoURLFieldRenderer()

    valid_urls = [
        'https://www.youtube.com/watch?v=DFYRQ_zQ-gk&feature=featured',
        'https://www.youtube.com/watch?v=DFYRQ_zQ-gk',
        'www.youtube.com/watch?v=DFYRQ_zQ-gk',
        'https://youtube.com/watch?v=DFYRQ_zQ-gk',
        'youtube.com/watch?v=DFYRQ_zQ-gk',
        'https://m.youtube.com/watch?v=DFYRQ_zQ-gk',
        'http://m.youtube.com/watch?v=DFYRQ_zQ-gk',
        'm.youtube.com/watch?v=DFYRQ_zQ-gk',
        'https://www.youtube.com/v/DFYRQ_zQ-gk?fs=1&hl=en_US',
        'http://www.youtube.com/v/DFYRQ_zQ-gk?fs=1&hl=en_US',
        'www.youtube.com/v/DFYRQ_zQ-gk?fs=1&hl=en_US',
        'youtube.com/v/DFYRQ_zQ-gk?fs=1&hl=en_US',
        'https://www.youtube.com/embed/DFYRQ_zQ-gk?autoplay=1',
        'https://www.youtube.com/embed/DFYRQ_zQ-gk',
        'http://www.youtube.com/embed/DFYRQ_zQ-gk',
        'www.youtube.com/embed/DFYRQ_zQ-gk',
        'https://youtube.com/embed/DFYRQ_zQ-gk',
        'http://youtube.com/embed/DFYRQ_zQ-gk',
        'youtube.com/embed/DFYRQ_zQ-gk',
        'https://www.youtube-nocookie.com/embed/DFYRQ_zQ-gk?autoplay=1',
        'https://www.youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'http://www.youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'www.youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'https://youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'http://youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'youtube-nocookie.com/embed/DFYRQ_zQ-gk',
        'https://youtu.be/DFYRQ_zQ-gk?t=120',
        'https://youtu.be/DFYRQ_zQ-gk',
        'http://youtu.be/DFYRQ_zQ-gk',
        'youtu.be/DFYRQ_zQ-gk',
        'https://www.youtube.com/HamdiKickProduction?v=DFYRQ_zQ-gk',
        'https://www.youtube.com/live/sMbxjePPmkw?feature=share'
    ]

    for url in valid_urls:
        result = renderer.ensure_youtube_embedded_url(url)
        assert result is not None

    invalid_urls = [
        '',
        'www.youtube.com/watch?v=None',
        'https://vimeo.com/123456789',
        'https://www.mytube.com/watch?v=dQw4w9WgXcQ',
        'https://www.invalid.com/watch?v=dQw4w9WgXcQ',
        'www.youtube.ch/watch/v=DFYRQ_zQ-gk',
    ]
    for url in invalid_urls:
        result = renderer.ensure_youtube_embedded_url(url)
        assert result is None


def test_video_url_field_renderer_vimeo_regex() -> None:

    renderer = VideoURLFieldRenderer()

    valid_urls = [
        'vimeo.com/123456789',
        'vimeo.com/channels/mychannel/123456789',
        'vimeo.com/groups/shortfilms/videos/123456789',
        'player.vimeo.com/video/123456789',
        'http://vimeo.com/123456789',
        'https://vimeo.com/123456789',
        'https://vimeo.com/channels/mychannel/123456789',
        'https://vimeo.com/groups/shortfilms/videos/123456789',
        'https://www.player.vimeo.com/video/123456789',
    ]

    for url in valid_urls:
        result = renderer.ensure_vimeo_embedded_url(url)
        assert result is not None

    invalid_urls = [
        '',
        'https://www.youtube.com/watch?v=DFYRQ_zQ-gk',
        'https://www.invalid.com/123456789',
        'vimeo.ch/123456789',
    ]

    for url in invalid_urls:
        result = renderer.ensure_vimeo_embedded_url(url)
        assert result is None
