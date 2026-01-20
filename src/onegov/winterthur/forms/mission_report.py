from __future__ import annotations

import sedate

from datetime import date, datetime
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import Form
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.winterthur import _
from onegov.winterthur.models import MissionReportFile
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import TimeField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional
from wtforms.validators import URL


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.winterthur.request import WinterthurRequest


def today() -> date:
    return sedate.to_timezone(sedate.utcnow(), 'Europe/Zurich').date()


class MissionReportForm(Form):

    request: WinterthurRequest

    day = DateField(
        _('Date'),
        default=today,
        validators=[InputRequired()])

    time = TimeField(
        _('Time'),
        validators=[InputRequired()]
    )

    duration = DecimalField(
        _('Mission duration (h)'),
        validators=[InputRequired(), NumberRange(0, 10000)])

    mission_type = RadioField(
        _('Mission type'),
        choices=[
            ('single', _('Single')),
            ('multi', _('Multi'))
        ],
        default='single',
        validators=[InputRequired()]
    )

    mission_count = IntegerField(
        _('Mission count'),
        validators=[NumberRange(0, 10000)],
        depends_on=('mission_type', 'multi'),
        default=1
    )

    nature = TextAreaField(
        _('Mission nature'),
        render_kw={'rows': 4},
        validators=[InputRequired()])

    location = StringField(
        _('Location'),
        validators=[InputRequired()])

    personnel = IntegerField(
        _('Mission personnel'),
        validators=[InputRequired(), NumberRange(0, 10000)])

    backup = IntegerField(
        _('Backup personnel'),
        validators=[InputRequired(), NumberRange(0, 10000)])

    civil_defence = BooleanField(
        _('Civil Defence involvement'))

    @property
    def date(self) -> datetime:
        assert self.day.data is not None
        assert self.time.data is not None
        dt = datetime.combine(self.day.data, self.time.data)
        return sedate.replace_timezone(dt, timezone='Europe/Zurich')

    @date.setter
    def date(self, value: datetime) -> None:
        dt = sedate.to_timezone(value, 'Europe/Zurich')
        self.day.data = dt.date()
        self.time.data = dt.time()

    def on_request(self) -> None:
        if self.request.app.hide_civil_defence_field:
            self.delete_field('civil_defence')

    def ensure_correct_mission_count(self) -> bool | None:
        if self.mission_type.data == 'single':
            assert self.mission_count.data is not None
            if self.mission_count.data > 1:
                assert isinstance(self.mission_count.errors, list)
                self.mission_count.errors.append(
                    _('Mission count must be one for single mission')
                )
                return False
        return None


class MissionReportVehicleForm(Form):

    name = StringField(
        _('Name'),
        validators=[InputRequired()])

    description = StringField(
        _('Description'),
        validators=[InputRequired()])

    symbol = UploadFileWithORMSupport(
        _('Symbol'),
        file_class=MissionReportFile,
        validators=[
            Optional(),
            WhitelistedMimeType(IMAGE_MIME_TYPES_AND_SVG),
            FileSizeLimit(1 * 1024 * 1024)
        ])

    website = URLField(
        _('Website'),
        validators=[URL(), Optional()]
    )
