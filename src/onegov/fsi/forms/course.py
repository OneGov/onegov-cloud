from __future__ import annotations

import re

from collections import OrderedDict
from datetime import timedelta
from onegov.core.utils import linkify, _email_regex
from onegov.form import Form
from onegov.form.fields import HtmlField
from onegov.fsi import _
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.widgets import TextInput


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.fsi.models import Course


mapping = OrderedDict({'year': 365, 'month': 30, 'week': 7, 'day': 1})


def string_to_timedelta(value: str | None) -> timedelta | None:
    # Incoming model value
    if not value:
        return None

    pattern = r'(\d+)\.?\d?\s?(\w+)'
    g = re.search(pattern, value)
    if g is None or not g.group():
        return None

    count = g.group(1)
    unit = g.group(2)
    normalized_unit = unit.removesuffix('s')

    if multiplier := mapping.get(normalized_unit):
        days = int(count) * multiplier
        return timedelta(days=days)
    else:
        raise AssertionError(f'unit {unit} not in allowed units')


def timedelta_to_string(td: timedelta | None) -> str:
    if not td or not isinstance(td, timedelta):
        return ''

    remaining = td.days
    for unit, divisor in mapping.items():
        count = remaining // divisor
        if count:
            return f"{count} {unit}{'s' if count >= 2 else ''}"
    return ''


def months_from_timedelta(td: timedelta | None) -> int | None:
    if td:
        assert isinstance(td, timedelta)
        return td.days // 30
    return 0


def months_to_timedelta(integer: int | None) -> timedelta | None:
    if integer:
        assert isinstance(integer, int)
        return timedelta(days=integer * 30)
    return None


class IntervalStringField(StringField):
    """To handle incoming data from python, override process_data.
    Similarly, to handle incoming data from the outside,
    override process_formdata.

    The _value method is called by the TextInput widget to provide
    the value that is displayed in the form. Overriding the process_formdata()
    method processes the incoming form data back into a list of tags.

    """
    data: timedelta | None  # type:ignore[assignment]

    widget = TextInput()

    def process_formdata(self, valuelist: list[Any]) -> None:
        if (
            valuelist
            and isinstance(valuelist[0], str)
            and (value := valuelist[0].strip())
        ):
            self.data = string_to_timedelta(value)
        else:
            self.data = None

    def _value(self) -> str:
        if self.data is not None:
            return timedelta_to_string(self.data)
        else:
            return ''


class CourseForm(Form):
    # Course info
    name = StringField(
        label=_('Short Description'),
        validators=[
            InputRequired()
        ]
    )

    description = HtmlField(
        label=_('Description'),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 10}
    )

    mandatory_refresh = BooleanField(
        label=_('Refresh mandatory'),
        default=False
    )

    refresh_interval = IntegerField(
        label=_('Refresh Interval (years)'),
        description=_('Number of years'),
        depends_on=('mandatory_refresh', 'y'),
        default=6,
        validators=[
            Optional()
        ],
    )

    hidden_from_public = BooleanField(
        label=_('Hidden'),
        default=False,
    )

    evaluation_url = StringField(
        label=_('Evaluation URL'),
        description=_('URL to the evaluation form'),
        validators=[
            Optional()
        ]
    )

    def get_useful_data(
        self,
        exclude: Collection[str] | None = None
    ) -> dict[str, Any]:

        result = super().get_useful_data(exclude)
        if self.description.data:
            result['description'] = linkify(self.description.data)
        if not self.mandatory_refresh.data:
            result['refresh_interval'] = None
        return result

    def ensure_refresh_interval(self) -> bool:
        if self.mandatory_refresh.data and not self.refresh_interval.data:
            self.refresh_interval.errors = [
                _('Not a valid integer value')
            ]
            return False
        return True

    def apply_model(self, model: Course) -> None:
        self.name.data = model.name
        self.description.data = model.description
        self.mandatory_refresh.data = model.mandatory_refresh
        self.refresh_interval.data = model.refresh_interval
        self.hidden_from_public.data = model.hidden_from_public
        self.evaluation_url.data = model.evaluation_url

    def update_model(self, model: Course) -> None:
        assert self.name.data is not None
        model.name = self.name.data
        model.description = linkify(self.description.data)
        model.mandatory_refresh = self.mandatory_refresh.data
        model.hidden_from_public = self.hidden_from_public.data
        model.evaluation_url = self.evaluation_url.data
        if not self.mandatory_refresh.data:
            model.refresh_interval = None
        else:
            model.refresh_interval = self.refresh_interval.data


class InviteCourseForm(Form):
    attendees = TextAreaField(
        label=_('Attendees'),
        description=_('Paste a list of email addresses.'),
        render_kw={'rows': 20},
    )

    # FIXME: Why are we completely changing what get_useful_data does here?
    #        This should be its own method really...
    def get_useful_data(  # type:ignore[override]
        self,
        exclude: Collection[str] | None = None
    ) -> tuple[str, ...]:
        string = self.attendees.data or ''
        return tuple(t[0] for t in _email_regex.findall(string))
