from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms import IntegerField
from wtforms import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange


class UploadVoteForm(Form):

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

    file_format = RadioField(
        _("File format"),
        choices=[],
        validators=[
            InputRequired()
        ],
        default='default'
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
                ('wabsti_m', "Wabsti"),
            ]
        else:
            self.file_format.choices = [
                ('default', _("Default")),
                ('internal', "OneGov Cloud"),
                ('wabsti', "Wabsti"),
            ]

        if vote.data_sources:
            self.file_format.choices.append(('wabsti_c', "WabstiCExport"))

        if vote.type == 'complex':
            self.type.choices = [('complex', _("Vote with Counter-Proposal"))]
            self.type.data = 'complex'
        else:
            self.type.choices = [('simple', _("Simple Vote"))]
            self.type.data = 'simple'
