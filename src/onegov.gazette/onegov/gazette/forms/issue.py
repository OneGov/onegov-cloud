from onegov.form import Form
from onegov.form.validators import UniqueColumnValue
from onegov.gazette import _
from onegov.gazette.fields import DateTimeLocalField
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import IssueName
from onegov.gazette.validators import UnusedColumnKeyValue
from sedate import standardize_date
from sedate import to_timezone
from wtforms import HiddenField
from wtforms import IntegerField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange


class IssueForm(Form):

    number = IntegerField(
        label=_("Number"),
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    date_ = DateField(
        label=_("Date"),
        validators=[
            InputRequired()
        ]
    )

    deadline = DateTimeLocalField(
        label=_("Deadline"),
        validators=[
            InputRequired()
        ]
    )

    timezone = HiddenField()

    name = HiddenField(
        validators=[
            UniqueColumnValue(Issue),
            UnusedColumnKeyValue(GazetteNotice._issues)
        ]
    )

    def validate(self):
        if self.date_.data and self.number.data:
            self.name.data = str(
                IssueName(self.date_.data.year, self.number.data)
            )
        return super().validate()

    def on_request(self):
        self.timezone.data = self.request.app.principal.time_zone

    def update_model(self, model):
        model.number = self.number.data
        model.date = self.date_.data
        model.deadline = self.deadline.data
        model.name = str(IssueName(model.date.year, model.number))
        # Convert the deadline from the local timezone to UTC
        if model.deadline:
            model.deadline = standardize_date(
                model.deadline, self.timezone.data
            )

    def apply_model(self, model):
        self.number.data = model.number
        self.name.data = model.name
        self.date_.data = model.date
        self.deadline.data = model.deadline
        # Convert the deadline from UTC to the local timezone
        if self.deadline.data:
            self.deadline.data = to_timezone(
                self.deadline.data, self.timezone.data
            ).replace(tzinfo=None)
        if model.in_use:
            self.number.render_kw = {'readonly': True}
