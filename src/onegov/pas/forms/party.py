from onegov.form import Form
from onegov.org.forms.fields import HtmlMarkupField
from onegov.pas import _
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class PartyForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()],
    )

    start = DateField(
        label=_('Start'),
        validators=[Optional()],
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    portrait = HtmlMarkupField(
        label=_('Portrait'),
    )

    description = HtmlMarkupField(
        label=_('Description'),
    )
