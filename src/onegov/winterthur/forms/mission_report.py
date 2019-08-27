from onegov.file.utils import IMAGE_MIME_TYPES_AND_SVG
from onegov.form import Form
from onegov.form.fields import TimezoneDateTimeField
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.winterthur import _
from onegov.winterthur.models import MissionReportFile
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields.html5 import DecimalField
from wtforms.fields.html5 import IntegerField
from wtforms.fields.html5 import URLField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


class MissionReportForm(Form):

    date = TimezoneDateTimeField(
        _("Date"),
        timezone='Europe/Zurich',
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
