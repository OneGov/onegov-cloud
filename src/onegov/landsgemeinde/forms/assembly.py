from __future__ import annotations

from datetime import date, datetime

import pytz
from onegov.form.fields import PanelField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde import _
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import Assembly
from onegov.landsgemeinde.models.assembly import STATES
from onegov.org.forms.fields import HtmlField
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL
from wtforms.validators import ValidationError

from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.landsgemeinde.request import LandsgemeindeRequest


class AssemblyForm(NamedFileForm):

    request: LandsgemeindeRequest

    date = DateField(
        label=_('Date'),
        fieldset=_('General'),
        validators=[InputRequired()],
        default=date.today
    )

    state = RadioField(
        _('State'),
        fieldset=_('General'),
        choices=list(STATES.items()),
        validators=[
            InputRequired()
        ],
        default=next(iter(STATES.keys()))
    )

    extraordinary = BooleanField(
        label=_('Extraordinary'),
        fieldset=_('General'),
    )

    info_video = PanelField(
        text=_('To embed a youtube video first click on the "share" button '
               'then on the "embed" button. Copy the URL of the src '
               'attribute.'),
        fieldset=_('Video'),
        kind='callout'
    )

    video_url = URLField(
        label=_('Video URL'),
        fieldset=_('Video'),
        description=_('The URL to the video of the assembly.'),
        validators=[URL(), Optional()]
    )

    start_time = TimeField(
        label=_('Start time of the livestream'),
        format='%H:%M:%S',
        render_kw={'step': 1},
        fieldset=_('Video'),
        validators=[
            Optional()
        ],
    )

    memorial_pdf = UploadField(
        label=_('Memorial part 1 (PDF)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    memorial_2_pdf = UploadField(
        label=_('Memorial part 2 (PDF)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    memorial_supplement_pdf = UploadField(
        label=_('Supplement to the memorial (PDF)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    protocol_pdf = UploadField(
        label=_('Protocol (PDF)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    audio_mp3 = UploadField(
        label=_('Audio (MP3)'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'audio/mpeg'}),
            FileSizeLimit(600 * 1024 * 1024)
        ]
    )

    audio_zip = UploadField(
        label=_('Memorial as audio for the visually impaired and blind'),
        fieldset=_('Downloads'),
        validators=[
            WhitelistedMimeType({'application/zip'}),
            FileSizeLimit(600 * 1024 * 1024)
        ]
    )

    overview = HtmlField(
        label=_('Text'),
        fieldset=_('Content')
    )

    def on_request(self) -> None:
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data(exclude=['info_video'])
        return data

    def validate_date(self, field: DateField) -> None:
        if field.data:
            session = self.request.session
            query = session.query(Assembly)
            query = query.filter(Assembly.date == field.data)
            if isinstance(self.model, Assembly):
                query = query.filter(Assembly.id != self.model.id)
            if session.query(query.exists()).scalar():
                raise ValidationError(_('Date already used.'))

    def populate_obj(self, obj: Assembly) -> None:  # type:ignore[override]
        super().populate_obj(obj)
        if not obj.start_time and self.state.data == 'ongoing':
            tz = pytz.timezone('Europe/Zurich')
            now = datetime.now(tz=tz).time()
            obj.start_time = now
