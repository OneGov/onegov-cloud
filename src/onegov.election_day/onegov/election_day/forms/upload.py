from onegov.election_day import _
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.parser.core import FieldDependency
from onegov.form.validators import WhitelistedMimeType, FileSizeLimit
from wtforms import RadioField
from wtforms.validators import DataRequired, InputRequired
from wtforms_components import If, Chain


ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'text/plain'
}

MAX_FILE_SIZE = 5 * 1024 * 1024


class UploadForm(Form):

    type = RadioField(_("Type"), choices=[
        ('simple', _("Simple Vote")),
        ('complex', _("Vote with Counter-Proposal")),
    ], validators=[InputRequired()], default='simple')

    # XXX make this easier with onegov.form
    complex_vote_dependency = FieldDependency('type', 'complex')
    complex_vote_validators = [If(
        complex_vote_dependency.fulfilled,
        Chain((
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ))
    )]
    complex_vote_validators[0].field_flags = ('required', )

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
        label=_("Counter-Proposal"),
        validators=complex_vote_validators,
        render_kw=dict(force_simple=True, **complex_vote_dependency.html_data)
    )

    tie_breaker = UploadField(
        label=_("Tie-Breaker"),
        validators=complex_vote_validators,
        render_kw=dict(force_simple=True, **complex_vote_dependency.html_data)
    )
