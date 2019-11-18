import re
from collections import OrderedDict
from datetime import timedelta

from wtforms import StringField, BooleanField
from wtforms.validators import InputRequired
from wtforms.widgets import TextInput

from onegov.core.utils import linkify
from onegov.form import Form
from onegov.form.fields import HtmlField
from onegov.fsi import _

mapping = OrderedDict({'year': 365, 'month': 30, 'week': 7, 'day': 1})


def string_to_timedelta(value):
    # Incoming model value
    if not value:
        return None

    pattern = r'(\d+)\.?\d?\s?(\w+)'
    g = re.search(pattern, value)
    if not isinstance(g, re.Match) or not g.group():
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
    if not dt or not isinstance(dt, timedelta):
        return None
    remaining = dt.days

    def s_append(key, value):
        return key + 's' if value >= 2 else key

    for unit, divisor in mapping.items():
        count = remaining // divisor
        if count != 0:
            return f"{count} {s_append(unit, count)}"
    return None


class IntervalStringField(StringField):
    """To handle incoming data from python, override process_data.
    Similarly, to handle incoming data from the outside,
    override process_formdata.

    The _value method is called by the TextInput widget to provide
     the value that is displayed in the form. Overriding the process_formdata()
    method processes the incoming form data back into a list of tags.

    """
    widget = TextInput()

    def process_data(self, value):
        print('test')
        super().process_data(value)

    def process_formdata(self, valuelist):
        if valuelist and valuelist[0]:
            self.data = string_to_timedelta(valuelist[0].strip())
        else:
            self.data = None

    def _value(self):
        if self.data is not None:
            return datetime_to_string(self.data)
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
        description=_('Enter all information to the course here'),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 10}
    )

    mandatory_refresh = BooleanField(
        label=_("Refresh mandatory"),
        default=False
    )

    refresh_interval = IntervalStringField(
        label=_('Refresh Interval'),
        description=_('e.g. 5 years of 1 month a')
    )

    def get_useful_data(self, exclude={'csrf_token'}):
        result = super().get_useful_data(exclude)
        if self.description.data:
            result['description'] = linkify(
                self.description.data, escape=False)
        return result

    def apply_model(self, model):
        self.name.data = model.name
        self.description.data = model.description

    def update_model(self, model):
        model.name = self.name.data
        model.description = linkify(self.description.data, escape=False)
