from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional


ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'text/plain',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
    'application/octet-stream',
    'application/zip'
}

MAX_FILE_SIZE = 10 * 1024 * 1024


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
                ('sesam', "SESAM"),
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
        depends_on=('file_format', 'wabsti'),  # actually wabsti OR sesam
        validators=[
            Optional(),
            NumberRange(min=1)
        ]
    )


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


class UploadElectionPartyResultsForm(Form):

    parties = UploadField(
        label=_("Party results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )


class UploadVoteForm(Form):

    file_format = RadioField(
        _("File format"),
        choices=[],
        validators=[
            InputRequired()
        ],
        default='default'
    )

    type = RadioField(
        _("Type"),
        choices=[
            ('simple', _("Simple Vote")),
            ('complex', _("Vote with Counter-Proposal")),
        ],
        validators=[
            InputRequired()
        ],
        default='simple'
    )

    proposal = UploadField(
        label=_("Proposal / Results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', '!wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    counter_proposal = UploadField(
        label=_("Counter Proposal"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'default', 'type', 'complex'),
        render_kw=dict(force_simple=True)
    )

    tie_breaker = UploadField(
        label=_("Tie-Breaker"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'default', 'type', 'complex'),
        render_kw=dict(force_simple=True)
    )

    sg_gemeinden = UploadField(
        label="SG_Gemeinden.csv",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    sg_geschaefte = UploadField(
        label="SG_Geschaefte.csv",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw=dict(force_simple=True)
    )

    vote_number = IntegerField(
        label=_("Vote number"),
        depends_on=('file_format', 'wabsti'),
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    def adjust(self, principal, vote):
        """ Adjusts the form to the given principal and vote. """

        if principal.domain == 'municipality':
            self.file_format.choices = [
                ('default', _("Default")),
                ('internal', "OneGov Cloud"),
            ]
        else:
            self.file_format.choices = [
                ('default', _("Default")),
                ('internal', "OneGov Cloud"),
                ('wabsti', "Wabsti"),
            ]

        if vote.data_sources:
            self.file_format.choices.append(('wabsti_c', "WabstiCExport"))

        if (vote.meta or {}).get('vote_type', 'simple') == 'complex':
            self.type.choices = [('complex', _("Vote with Counter-Proposal"))]
            self.type.data = 'complex'
        else:
            self.type.choices = [('simple', _("Simple Vote"))]
            self.type.data = 'simple'


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


class UploadWabstiProporzElectionForm(Form):

    wp_gemeinden = UploadField(
        label="WP_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wp_kandidaten = UploadField(
        label="WP_Kandidaten",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wp_kandidatengde = UploadField(
        label="WP_KandidatenGde",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wp_listen = UploadField(
        label="WP_Listen",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wp_listengde = UploadField(
        label="WP_ListenGde",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wp_wahl = UploadField(
        label="WP_Wahl",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wpstatic_gemeinden = UploadField(
        label="WPStatic_Gemeinden",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )

    wpstatic_kandidaten = UploadField(
        label="WPStatic_Kandidaten",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )


class UploadRestForm(Form):

    type = RadioField(
        _("Type"),
        choices=[
            ('vote', _("Vote")),
            ('election', _("Election")),
            ('parties', _("Party results")),
        ],
        validators=[
            InputRequired()
        ],
        default='vote'
    )

    id = StringField(
        label=_("Identifier"),
        validators=[
            InputRequired()
        ]
    )

    results = UploadField(
        label=_("Results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw=dict(force_simple=True)
    )
