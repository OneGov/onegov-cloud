from datetime import date, datetime
from dateutil import rrule
from onegov.form import Form, with_options
from onegov.form.fields import MultiCheckboxField, MultiCheckboxWidget
from onegov.town import _
from sedate import replace_timezone, to_timezone
from wtforms import BooleanField, StringField, TextAreaField, validators
from wtforms_components import TimeField
from wtforms.fields.html5 import DateField
from wtforms.widgets import TextArea


# todo: Where do we store the available tags?
TAGS = [(tag, tag) for tag in ('Fest', 'Freizeit', 'Politik', 'Sport')]

WEEKDAYS = (
    ("MO", _("Mo")),
    ("TU", _("Tu")),
    ("WE", _("We")),
    ("TH", _("Th")),
    ("FR", _("Fr")),
    ("SA", _("Sa")),
    ("SU", _("Su")),
)


class EventForm(Form):
    """ Defines the form for all events. """

    title = StringField(
        label=_("Title"),
        description=_("The title of this event."),
        validators=[validators.InputRequired()]
    )

    description = TextAreaField(
        label=_("Description"),
        description=_("The description of this event."),
        widget=with_options(TextArea, rows=12)
    )

    location = StringField(
        label=_("Location"),
        description=_("A description of the location of this event.")
    )

    tags = MultiCheckboxField(
        label=_("Tags"),
        choices=TAGS,
    )

    start_time = TimeField(
        label=_("From"),
        validators=[validators.InputRequired()]
    )

    end_time = TimeField(
        label=_("To"),
        validators=[validators.InputRequired()]
    )

    start_date = DateField(
        label=_("Date"),
        validators=[validators.InputRequired()],
        default=date.today
    )

    weekly = MultiCheckboxField(
        label=_("Repeats itself every"),
        choices=WEEKDAYS,
        widget=with_options(
            MultiCheckboxWidget,
            prefix_label=False,
            class_='oneline-checkboxes'
        )
    )

    end_date = DateField(
        label=_("... until"),
        validators=[validators.Optional()]
    )

    def validate(self):
        """ Make sure a valid RRULE can be generated with the given fields.

        Might be better to group weekly and end_date in an enclosure,
        see See `<http://wtforms.readthedocs.org/en/latest/fields.html\
        #field-enclosures`_.

        """
        result = super(EventForm, self).validate()

        if self.start_time.data and self.end_time.data:
            if self.start_time.data > self.end_time.data:
                message = _("The end time must be later than the start time.")
                self.end_time.errors.append(message)
                result = False

        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                message = _("The end date must be later than the start date.")
                self.end_date.errors.append(message)
                result = False

        if self.weekly.data and self.start_date.data:
            weekday = WEEKDAYS[self.start_date.data.weekday()][0]
            if weekday not in self.weekly.data:
                message = _("The weekday of the start date must be selected.")
                self.weekly.errors.append(message)
                result = False

        if self.weekly.data and not self.end_date.data:
            message = _("Please set and end date if the event is recurring.")
            self.end_date.errors.append(message)
            result = False

        if self.end_date.data and not self.weekly.data:
            message = _(
                "Please select a type of recurrence if the event is recurring."
            )
            self.end_date.errors.append(message)
            result = False

        return result

    def update_model(self, model):
        """ Stores the form values on the page. """

        # clear the recurrence to avoid updating all occurrences too much
        model.recurrence = ''

        model.title = self.title.data
        model.content = {
            'description': self.description.data
        }
        model.location = self.location.data
        model.tags = ', '.join(self.tags.data)
        model.timezone = 'Europe/Zurich'
        model.start = replace_timezone(
            datetime(
                self.start_date.data.year,
                self.start_date.data.month,
                self.start_date.data.day,
                self.start_time.data.hour,
                self.start_time.data.minute
            ),
            model.timezone
        )
        model.end = replace_timezone(
            datetime(
                self.start_date.data.year,
                self.start_date.data.month,
                self.start_date.data.day,
                self.end_time.data.hour,
                self.end_time.data.minute
            ),
            model.timezone
        )
        if self.weekly.data and self.end_date.data:
            until_date = to_timezone(
                replace_timezone(
                    datetime(
                        self.end_date.data.year,
                        self.end_date.data.month,
                        self.end_date.data.day,
                        self.end_time.data.hour,
                        self.end_time.data.minute
                    ), model.timezone
                ), 'UTC'
            )
            model.recurrence = (
                "RRULE:FREQ=WEEKLY;WKST=MO;BYDAY={0};UNTIL={1}".format(
                    ','.join(self.weekly.data),
                    until_date.strftime('%Y%m%dT%H%M%SZ')
                )
            )

    def apply_model(self, model):
        """ Stores the page values on the form. """

        self.title.data = model.title
        self.description.data = model.description
        self.location.data = model.location
        self.tags.data = model.display_tags
        self.start_time.data = model.localized_start.time()
        self.end_time.data = model.localized_end.time()
        self.start_date.data = model.localized_start.date()
        if model.recurrence:
            last_occurrence = model.occurrence_dates(localize=True)[-1]
            self.end_date.data = last_occurrence.date()

            rule = rrule.rrulestr(model.recurrence)
            if rule._freq == rrule.WEEKLY:
                self.weekly.data = [
                    WEEKDAYS[day][0] for day in rule._byweekday
                ]
