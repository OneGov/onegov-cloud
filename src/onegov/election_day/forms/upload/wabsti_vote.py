from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.validators import DataRequired


class UploadWabstiVoteForm(Form):

    sg_gemeinden = UploadField(
        label="SG_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    sg_geschaefte = UploadField(
        label="SG_Geschaefte.csv",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )
