import re
from collections import OrderedDict
from datetime import timedelta

from wtforms import SelectField
from onegov.form.fields import TimezoneDateTimeField, ChosenSelectField

from wtforms import StringField, RadioField
from wtforms.validators import InputRequired

from onegov.form.fields import HtmlField
from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.models.course_event import course_status_choices

mapping = OrderedDict({'year': 365, 'month': 30, 'week': 7, 'day': 1})


def string_to_timedelta(value):
    # Incoming model value
    pattern = r'(\d+)\.?\d?\s?(\w+)'
    g = re.search(pattern, value)
    if not g.group():
        return None
    count = g.group(1)
    unit = g.group(2)

    units = tuple(mapping.keys()) + tuple(f'{v}s' for v in mapping.keys())

    if unit in units:
        unit_ = unit[:-1] if unit[-1] == 's' else unit
        days = int(count) * mapping[unit_]
        return timedelta(days=days)
    else:
        raise AssertionError(f'unit {unit} not in allowed units')


def datetime_to_string(dt):
    assert isinstance(dt, timedelta)
    remaining = dt.days

    def s_append(key, value):
        return key + 's' if value >= 2 else key

    for unit, divisor in mapping.items():
        count = remaining // divisor
        if count != 0:
            return f"{count} {s_append(unit, count)}"


class CourseEventForm(Form):

    # Course info
    name = StringField(
        label=_('Short Description'),
        render_kw={'size': 4},
        validators=[
            InputRequired()
        ]
    )

    presenter_name = StringField(
        label=_('Presenter'),
        render_kw={'size': 4},
        description=_('Full name of the presenter'),
        validators=[
            InputRequired()
        ]
    )

    presenter_company = StringField(
        label=_('Company'),
        description='Presenters company',
        render_kw={'size': 4},
        validators=[
            InputRequired()
        ]
    )

    description = HtmlField(
        label=_("Description"),
        render_kw={'rows': 10, 'size': 8},
        validators=[
            InputRequired()
        ]
    )

    mandatory_refresh = RadioField(
        label=_("Refresh mandatory"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 2},
        description=_(
            "Define if this course has a refresh. The refresh"
        )
    )

    hidden_from_public = RadioField(
        label=_("Hidden"),
        choices=(
            (1, _("Yes")),
            (0, _("No")),
        ),
        coerce=bool,
        render_kw={'size': 2}
    )

    refresh_interval = StringField(
        label=_('Refresh Interval'),
        render_kw={'size': 2}
    )

    # Course Event info
    start = TimezoneDateTimeField(
        label=_('Course Start'),
        timezone='Europe/Zurich',
        render_kw={'size': 2},
        validators=[
            InputRequired()
        ]
    )

    end = TimezoneDateTimeField(
        label=_('Course End'),
        timezone='Europe/Zurich',
        render_kw={'size': 2},
        validators=[
            InputRequired()
        ]
    )

    min_attendees = StringField(
        label=_('Attendees min'),
        render_kw={'size': 2},
        validators=[
            InputRequired()
        ]
    )

    max_attendees = StringField(
        label=_('Attendees max'),
        render_kw={'size': 2},
        validators=[
            InputRequired()
        ]
    )

    status = ChosenSelectField(
        label=_('Status'),
        render_kw={'size': 2},
        choices=course_status_choices()
    )

    def apply_model(self, model):
        self.name.data = model.name
        self.presenter_name.data = model.presenter_name
        self.presenter_company.data = model.presenter_company
        self.description.data = model.description
        self.mandatory_refresh.data = model.mandatory_refresh
        self.hidden_from_public.data = model.hidden_from_public

        self.start.data = model.start
        self.end.data = model.end
        self.min_attendees.data = model.min_attendees
        self.max_attendees.data = model.max_attendees
        self.status.data = model.status
        self.refresh_interval.data = datetime_to_string(model.refresh_interval)

    def update_model(self, model):
        model.name = self.name.data
        model.presenter_name = self.presenter_name.data
        model.presenter_company = self.presenter_company.data
        model.description = self.description.data
        model.mandatory_refresh = self.mandatory_refresh.data
        model.hidden_from_public = self.hidden_from_public.data

        model.start = self.start.data
        model.end = self.end.data
        model.min_attendees = self.min_attendees.data
        model.max_attendees = self.max_attendees.data
        model.status = self.status.data
        model.refresh_interval = string_to_timedelta(
            self.refresh_interval.data)
        model.hidden_from_public = self.hidden_from_public.data
