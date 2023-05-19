from datetime import date
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.landsgemeinde import _
from onegov.landsgemeinde.layouts import DefaultLayout
from onegov.landsgemeinde.models import Assembly
from onegov.org.forms.fields import HtmlField
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError
from onegov.landsgemeinde.models.assembly import STATES


class AssemblyForm(NamedFileForm):

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
        default=list(STATES.keys())[0]
    )

    extraordinary = BooleanField(
        label=_('Extraordinary'),
        fieldset=_('General'),
    )

    video_url = URLField(
        label=_('Video URL'),
        fieldset=_('General')
    )
    extraordinary = BooleanField(
        label=_('Extraordinary'),
        fieldset=_('General'),
    )

    memorial_pdf = UploadField(
        label=_('Memorial (PDF)'),
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
        label=_('Audio (ZIP)'),
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
