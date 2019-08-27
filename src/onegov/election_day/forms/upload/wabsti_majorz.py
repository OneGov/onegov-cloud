from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.validators import DataRequired


class UploadWabstiMajorzElectionForm(Form):

    wm_gemeinden = UploadField(
        label="WM_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wm_kandidaten = UploadField(
        label="WM_Kandidaten",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wm_kandidatengde = UploadField(
        label="WM_KandidatenGde",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wm_wahl = UploadField(
        label="WM_Wahl",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wmstatic_gemeinden = UploadField(
        label="WMStatic_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )
