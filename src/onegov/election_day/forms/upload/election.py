from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Election
    from onegov.election_day.models import Municipality


class UploadElectionBaseForm(Form):

    file_format = RadioField(
        _('File format'),
        choices=[
            ('internal', 'OneGov Cloud'),
        ],
        validators=[
            InputRequired()
        ],
        default='internal'
    )

    results = UploadField(
        label=_('Results'),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', '!wabsti_c'),
    )

    def adjust(
        self,
        principal: Canton | Municipality,
        election: Election
    ) -> None:
        """ Adjusts the form to the given principal and election. """

        assert hasattr(election, 'data_sources')
        if election.data_sources:
            self.file_format.choices = [
                ('internal', 'OneGov Cloud'),
                ('wabsti_c', 'WabstiCExport')
            ]


class UploadMajorzElectionForm(UploadElectionBaseForm):

    wm_gemeinden = UploadField(
        label='WM_Gemeinden.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    wm_kandidaten = UploadField(
        label='WM_Kandidaten.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    wm_kandidatengde = UploadField(
        label='WM_KandidatenGde.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    wm_wahl = UploadField(
        label='WM_Wahl',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    wmstatic_gemeinden = UploadField(
        label='WMStatic_Gemeinden.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )


class UploadProporzElectionForm(UploadElectionBaseForm):

    wp_gemeinden = UploadField(
        label='WP_Gemeinden',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wp_kandidaten = UploadField(
        label='WP_Kandidaten',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wp_kandidatengde = UploadField(
        label='WP_KandidatenGde',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wp_listen = UploadField(
        label='WP_Listen',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wp_listengde = UploadField(
        label='WP_ListenGde',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wp_wahl = UploadField(
        label='WP_Wahl',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    wpstatic_gemeinden = UploadField(
        label='WPStatic_Gemeinden',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )

    wpstatic_kandidaten = UploadField(
        label='WPStatic_Kandidaten',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
        depends_on=('file_format', 'wabsti_c')
    )
