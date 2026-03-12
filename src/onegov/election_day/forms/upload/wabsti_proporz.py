from __future__ import annotations

from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from wtforms.validators import DataRequired


class UploadWabstiProporzElectionForm(Form):

    wp_gemeinden = UploadField(
        label='WP_Gemeinden',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wp_kandidaten = UploadField(
        label='WP_Kandidaten',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wp_kandidatengde = UploadField(
        label='WP_KandidatenGde',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wp_listen = UploadField(
        label='WP_Listen',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wp_listengde = UploadField(
        label='WP_ListenGde',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wp_wahl = UploadField(
        label='WP_Wahl',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wpstatic_gemeinden = UploadField(
        label='WPStatic_Gemeinden',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )

    wpstatic_kandidaten = UploadField(
        label='WPStatic_Kandidaten',
        validators=[
            DataRequired(),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        allowed_mimetypes=ALLOWED_MIME_TYPES,
        render_kw={'force_simple': True}
    )
