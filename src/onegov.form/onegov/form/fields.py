from wtforms import StringField, SelectMultipleField, widgets
from wtforms.widgets import html5 as html5_widgets


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class TimeField(StringField):
    widget = html5_widgets.TimeInput
