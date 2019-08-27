from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


class UploadElectionBaseForm(Form):

    file_format = RadioField(
        _("File format"),
        choices=[],
        validators=[
            InputRequired()
        ],
        default='internal'
    )

    complete = BooleanField(
        label=_("Complete"),
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    results = UploadField(
        label=_("Results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', '!wabsti_c'),
    )

    elected = UploadField(
        label=_("Elected Candidates"),
        validators=[
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    def adjust(self, principal, election):
        """ Adjusts the form to the given principal and election. """

        if principal.domain == 'municipality':
            self.file_format.choices = [
                ('internal', _("OneGov Cloud")),
            ]
        else:
            self.file_format.choices = [
                ('internal', "OneGov Cloud"),
                ('wabsti', "Wabsti"),
            ]

        if election.data_sources:
            self.file_format.choices.append(('wabsti_c', "WabstiCExport"))


class UploadMajorzElectionForm(UploadElectionBaseForm):

    wm_gemeinden = UploadField(
        label='WM_Gemeinden.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    wm_kandidaten = UploadField(
        label='WM_Kandidaten.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    wm_kandidatengde = UploadField(
        label='WM_KandidatenGde.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    wm_wahl = UploadField(
        label="WM_Wahl",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    wmstatic_gemeinden = UploadField(
        label='WMStatic_Gemeinden.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    majority = IntegerField(
        label=_("Absolute majority"),
        depends_on=('file_format', 'wabsti'),  # actually wabsti
        validators=[
            Optional(),
            NumberRange(min=1)
        ]
    )

    def adjust(self, principal, election):
        """ Adjusts the form to the given principal and election. """

        super(UploadMajorzElectionForm, self).adjust(principal, election)

        if principal.domain == 'municipality':
            self.file_format.choices.append(('wabsti_m', "Wabsti"))


class UploadProporzElectionForm(UploadElectionBaseForm):

    connections = UploadField(
        label=_("List connections"),
        validators=[
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    statistics = UploadField(
        label=_("Election statistics"),
        validators=[
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    wp_gemeinden = UploadField(
        label="WP_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wp_kandidaten = UploadField(
        label="WP_Kandidaten",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wp_kandidatengde = UploadField(
        label="WP_KandidatenGde",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wp_listen = UploadField(
        label="WP_Listen",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wp_listengde = UploadField(
        label="WP_ListenGde",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wp_wahl = UploadField(
        label="WP_Wahl",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    wpstatic_gemeinden = UploadField(
        label="WPStatic_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )

    wpstatic_kandidaten = UploadField(
        label="WPStatic_Kandidaten",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True),
        depends_on=('file_format', 'wabsti_c')
    )
