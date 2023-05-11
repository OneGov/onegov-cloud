from datetime import date
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde import _
from onegov.landsgemeinde.forms.file import NamedFileForm
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import Assembly
from onegov.org.forms.fields import HtmlField
from wtforms.fields import DateField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


class AssemblyForm(NamedFileForm):

    date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    memorial_pdf = UploadField(
        label=_("Memorial (PDF)"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    protocol_pdf = UploadField(
        label=_("Protocol (PDF)"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(100 * 1024 * 1024)
        ]
    )

    audio_mp3 = UploadField(
        label=_("Audio (MP3)"),
        validators=[
            WhitelistedMimeType({'audio/mpeg'}),
            FileSizeLimit(600 * 1024 * 1024)
        ]
    )

    overview = HtmlField(
        label=_("Text")
    )

    def on_request(self):
        DefaultLayout(self.model, self.request)
        self.request.include('redactor')
        self.request.include('editor')

    def validate_date(self, field):
        if field.data:
            query = self.request.session.query(Assembly)
            query = query.filter(Assembly.date == field.data)
            if isinstance(self.model, Assembly):
                query = query.filter(Assembly.id != self.model.id)
            if query.first():
                raise ValidationError(_('Date already used.'))
