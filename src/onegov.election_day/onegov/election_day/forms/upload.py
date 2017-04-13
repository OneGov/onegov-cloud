from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import WhitelistedMimeType, FileSizeLimit
from wtforms import BooleanField, IntegerField, RadioField
from wtforms.validators import (
    DataRequired, InputRequired, NumberRange, Optional
)


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
        choices=[
            ('internal', _("OneGov Cloud")),
            ('wabsti', _("Wabsti")),
            ('sesam', _("SESAM")),
        ],
        validators=[
            InputRequired()
        ],
        default='internal'
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

    elected = UploadField(
        label=_("Elected Candidates"),
        validators=[
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    complete = BooleanField(
        label=_("Complete"),
        depends_on=('file_format', 'wabsti'),
        render_kw=dict(force_simple=True)
    )

    def adjust(self, principal):
        """ Adjusts the form to the given principal """

        if principal.domain == 'municipality':
            self.file_format.choices = [
                choice for choice in self.file_format.choices
                if choice[0] != 'wabsti' and choice[0] != 'sesam'
            ]


class UploadMajorzElectionForm(UploadElectionBaseForm):

    majority = IntegerField(
        label=_("Absolute majority"),
        depends_on=('file_format', '!internal'),
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
        choices=[
            ('default', _("Default")),
            ('wabsti', _("Wabsti")),
            ('internal', _("OneGov Cloud")),
        ],
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
        depends_on=('file_format', '!internal'),
        default='simple'
    )

    proposal = UploadField(
        label=_("Proposal"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True}
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

    vote_number = IntegerField(
        label=_("Vote number"),
        depends_on=('file_format', 'wabsti'),
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    def adjust(self, principal, vote):
        """ Adjusts the form to the given principal and vote.

        - Wabsti format is removed if it is a communal instance.
        - The vote type (simple/complex) is copied from the vote

        """

        if principal.domain == 'municipality':
            self.file_format.choices = [
                ('default', _("Default")),
                ('internal', _("OneGov Cloud")),
            ]
        else:
            self.file_format.choices = [
                ('default', _("Default")),
                ('wabsti', _("Wabsti")),
                ('internal', _("OneGov Cloud")),
            ]

        if (vote.meta or {}).get('vote_type', 'simple') == 'complex':
            self.type.choices = [('complex', _("Vote with Counter-Proposal"))]
            self.type.data = 'complex'
        else:
            self.type.choices = [('simple', _("Simple Vote"))]
            self.type.data = 'simple'
