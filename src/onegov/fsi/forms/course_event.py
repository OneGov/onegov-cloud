import re
from collections import OrderedDict
from datetime import timedelta

from wtforms import SelectField
from onegov.form.fields import TimezoneDateTimeField

from wtforms import StringField, RadioField
from wtforms.validators import InputRequired

from onegov.form.fields import HtmlField
from onegov.fsi import _
from onegov.form import Form
from onegov.fsi.models.course_event import course_status_choices

mapping = OrderedDict({'year': 365, 'month': 30, 'week': 7, 'day': 1})


def string_to_timedelta(value):
    # Incoming model value
    pattern = r'(\d)+\s?(\w+)'
    g = re.search(pattern, value)
    assert g.group()
    count = g.group(1)
    unit = g.group(2)

    units = tuple(mapping.keys()) + tuple(f'{v}s' for v in mapping.keys())

    if unit in units:
        unit_ = unit[:-1] if unit[-1] == 's' else unit
        return timedelta(days=mapping[unit_])
    else:
        print(f'unit {unit} not in allowed units')
    return None


def datetime_to_string(value):
    assert isinstance(value, timedelta)
    remaining = timedelta.days
    divisor = tuple(mapping.values())[0]

    result = ''

    def s_append(key, value):
        return key + 's' if value >= 2 else key

    for key, divisor in mapping.items():
        div = remaining // divisor
        if div != 0:
            result += f" {div} {s_append(key, div)} "
            remaining = remaining % divisor
    return result.strip()

# class IntervalField(StringField):
#     """Prototype for a timedelta field"""
#
#     def process_data(self, value):
#
#
#     def process_formdata(self, valuelist):
#         if valuelist:
#             self.data = valuelist[0]
#         elif self.data is None:
#             self.data = ''
#

class CourseEventForm(Form):

    # Course info
    name = StringField(
        label=_('Short Description'),
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

    presenter_name = StringField(
        label=_('Presenter'),
        render_kw={'size': 5},
        description=_('Full name of the presenter'),
        validators=[
            InputRequired()
        ]
    )

    presenter_company = StringField(
        label=_('Company'),
        description='Presenters company',
        render_kw={'size': 5},
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

    refresh_interval = StringField(
        label=_('Refresh Interval')
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

    status = SelectField(
        label=_('Status'),
        render_kw={'size': 2},
        choices=course_status_choices()
    )

    def apply_model(self, model):
        self.name.data = model.name
        self.presenter_name.data = model.presenter_name
        self.presenter_company = model.presenter_company
        self.description = model.description
        self.mandatory_refresh = model.mandatory_refresh
        self.hidden_from_public = model.hidden_from_public

        self.start = model.start
        self.end = model.end
        self.min_attendees = model.min_attendees
        self.max_attendees = model.max_attendee
        self.status = model.status
        self.refresh_interval = datetime_to_string(model.refresh_interval)

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
        model.refresh_interval = string_to_timedelta(self.refresh_interval)



# class CourseEventForm(Form):

#     start = TimezoneDateTimeField(
#         label=_('Course Start'),
#         render_kw={'size': 4}
#     )
#
#     end = TimezoneDateTimeField(
#         label=_('Course End')
#     )