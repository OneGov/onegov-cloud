import sedate

from datetime import datetime
from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import Form
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.winterthur import _
from onegov.winterthur.models import MissionReportFile
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.fields.html5 import TimeField
from wtforms.fields.html5 import DecimalField
from wtforms.fields.html5 import IntegerField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


def today():
    return sedate.to_timezone(sedate.utcnow(), 'Europe/Zurich').date()


class MissionReportForm(Form):

    day = DateField(
        _("Date"),
        default=today,
        validators=[InputRequired()])

    time = TimeField(
        _("Time"),
        validators=[InputRequired()])

    duration = DecimalField(
        _("Mission duration (h)"),
        validators=[InputRequired(), NumberRange(0, 10000)])

    nature = TextAreaField(
        _("Mission nature"),
        render_kw={'rows': 4},
        validators=[InputRequired()])

    location = StringField(
        _("Location"),
        validators=[InputRequired()])

    personnel = IntegerField(
        _("Mission personnel"),
        validators=[InputRequired(), NumberRange(0, 10000)])

    backup = IntegerField(
        _("Backup personnel"),
        validators=[InputRequired(), NumberRange(0, 10000)])

    civil_defence = BooleanField(
        _("Civil Defence involvement"))

    @property
    def date(self):
        dt = datetime.combine(self.day.data, self.time.data)
        return sedate.replace_timezone(dt, timezone='Europe/Zurich')

    @date.setter
    def date(self, value):
        dt = sedate.to_timezone(value, 'Europe/Zurich')
        self.day.data = dt.date()
        self.time.data = dt.time()


class MissionReportVehicleForm(Form):

    name = StringField(
        _("Name"),
        validators=[InputRequired()])

    description = StringField(
        _("Description"),
        validators=[InputRequired()])

    symbol = UploadFileWithORMSupport(
        _("Symbol"),
        file_class=MissionReportFile,
        validators=[
            Optional(),
            WhitelistedMimeType(IMAGE_MIME_TYPES_AND_SVG),
            FileSizeLimit(1 * 1024 * 1024)
        ])

    website = URLField(
        _("Website"))
