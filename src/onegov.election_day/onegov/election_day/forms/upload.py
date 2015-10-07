from onegov.election_day import _
from onegov.form import Form, with_options
from onegov.form.fields import UploadField
from onegov.form.parser.core import FieldDependency
from onegov.form.widgets import UploadWidget
from wtforms import RadioField
from wtforms.validators import DataRequired, InputRequired
from wtforms_components import If


class UploadForm(Form):

    type = RadioField(_("Type"), choices=[
        ('simple', _("Simple Vote")),
        ('complex', _("Vote with Counter-Proposal")),
    ], validators=[InputRequired()])

    # XXX make this easier with onegov.form
    complex_vote_depencdency = FieldDependency('type', 'complex')
    complex_vote_validators = [If(
        complex_vote_depencdency.fulfilled,
        DataRequired()
    )]
    complex_vote_validators[0].field_flags = ('required', )

    proposal = UploadField(
        label=_("Proposal"),
        validators=[DataRequired()]
    )

    counter_proposal = UploadField(
        label=_("Counter-Proposal"),
        validators=complex_vote_validators,
        widget=with_options(UploadWidget, **complex_vote_depencdency.html_data)
    )

    tie_breaker = UploadField(
        label=_("Tie-Breaker"),
        validators=complex_vote_validators,
        widget=with_options(UploadWidget, **complex_vote_depencdency.html_data)
    )
