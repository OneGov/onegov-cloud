from onegov.form.forms import NamedFileForm
from onegov.pas import _
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class ParliamentarianForm(NamedFileForm):

    first_name = StringField(
        label=_('First name'),
        validators=[InputRequired()],
    )

    last_name = StringField(
        label=_('Last name'),
        validators=[InputRequired()],
    )
