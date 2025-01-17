from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import DateTimeLocalField
from onegov.form.validators import UniqueColumnValue
from onegov.gazette import _
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.models import IssueName
from onegov.gazette.validators import UnusedColumnKeyValue
from sedate import standardize_date
from sedate import to_timezone
from wtforms.fields import DateField
from wtforms.fields import HiddenField
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gazette.request import GazetteRequest


class IssueForm(Form):

    request: GazetteRequest

    number = IntegerField(
        label=_('Number'),
        validators=[
            InputRequired(),
            NumberRange(min=1)
        ]
    )

    date_ = DateField(
        label=_('Date'),
        validators=[
            InputRequired()
        ]
    )

    deadline = DateTimeLocalField(
        label=_('Deadline'),
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

    def validate(self) -> bool:  # type:ignore[override]
        if self.date_.data and self.number.data:
            self.name.data = str(
                IssueName(self.date_.data.year, self.number.data)
            )
        return super().validate()

    def on_request(self) -> None:
        self.timezone.data = self.request.app.principal.time_zone

    def update_model(self, model: Issue) -> None:
        assert self.number.data is not None
        model.number = self.number.data
        assert self.date_.data is not None
        model.date = self.date_.data
        model.deadline = self.deadline.data
        model.name = str(IssueName(model.date.year, model.number))
        # Convert the deadline from the local timezone to UTC
        if model.deadline:
            # FIXME: This seems very fragile, how are we ensuring
            #        that timezone is actually set? Should we default
            #        to UTC if we didn't get one?
            assert self.timezone.data is not None
            model.deadline = standardize_date(
                model.deadline,
                self.timezone.data
            )

    def apply_model(self, model: Issue) -> None:
        self.number.data = model.number
        self.name.data = model.name
        self.date_.data = model.date
        self.deadline.data = model.deadline
        # Convert the deadline from UTC to the local timezone
        if self.deadline.data:
            # FIXME: This is even more dubious, since it's even less
            #        likely that the timezone is set, sedate happens
            #        to actually work with `to_timezone(dt, None)`
            #        but I don't think its supposed to
            self.deadline.data = to_timezone(
                self.deadline.data,
                self.timezone.data  # type:ignore[arg-type]
            ).replace(tzinfo=None)
        if model.in_use:
            self.number.render_kw = {'readonly': True}
