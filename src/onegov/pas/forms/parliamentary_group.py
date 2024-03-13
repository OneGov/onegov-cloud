from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.pas import _
from onegov.pas.layouts import DefaultLayout
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class ParliamentaryGroupForm(Form):

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

    description = HtmlField(
        label=_('Description')
    )

    def on_request(self) -> None:
        DefaultLayout(self.model, self.request)  # type:ignore[arg-type]
        self.request.include('redactor')
        self.request.include('editor')
