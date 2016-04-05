from datetime import date, datetime, timedelta
from dateutil import rrule
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.town import _
from onegov.gis import CoordinatesField
from sedate import replace_timezone, to_timezone
from wtforms import StringField, TextAreaField, validators
from wtforms_components import TimeField
from wtforms.fields.html5 import DateField, EmailField


TAGS = [(tag, tag) for tag in (
    _("Exhibition"),
    _("Gastronomy"),
    _("Health"),
    _("Cinema"),
    _("Congress"),
    _("Concert"),
    _("Art"),
    _("Literature"),
    _("Market"),
    _("Music"),
    _("Party"),
    _("Politics"),
    _("Religion"),
    _("Sports"),
    _("Dancing"),
    _("Theater"),
    _("Meetup"),
    _("Talk"),
)]

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

    email = EmailField(
        label=_("E-Mail"),
        description="max.muster@example.org",
        validators=[validators.InputRequired(), validators.Email()]
    )

    title = StringField(
        label=_("Title"),
        description=_("Concerto in the castle garden"),
        validators=[validators.InputRequired()]
    )

    description = TextAreaField(
        label=_("Description"),
        description=_("Enjoy a concerto in the castle garden."),
        render_kw={'rows': 12}
    )

    location = StringField(
        label=_("Location"),
        description=_("Castle garden")
    )

    coordinates = CoordinatesField(
        label=_("Coordinates"),
        description=_("The marker can be moved by dragging it with the mouse"),
        render_kw={'data-map-type': 'marker'}
    )

    tags = MultiCheckboxField(
        label=_("Tags"),
        choices=TAGS,
    )

    start_date = DateField(
        label=_("Date"),
        validators=[validators.InputRequired()],
        default=date.today
    )

    start_time = TimeField(
        label=_("From"),
        description="18:00",
        validators=[validators.InputRequired()]
    )

    end_time = TimeField(
        label=_("To"),
        description="19:15",
        validators=[validators.InputRequired()]
    )

    weekly = MultiCheckboxField(
        label=_("Repeats itself every"),
        choices=WEEKDAYS,
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'}
    )

    end_date = DateField(
        label=_("Until date"),
        validators=[validators.Optional()]
    )

    def validate(self):
        """ Make sure a valid RRULE can be generated with the given fields.

        Might be better to group weekly and end_date in an enclosure,
        see See http://wtforms.readthedocs.org/en/latest/fields.html
        #field-enclosures.

        """
        result = super().validate()

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
            message = _("Please select a weekday if the event is recurring.")
            self.weekly.errors.append(message)
            result = False

        return result

    def populate_obj(self, model):
        """ Stores the form values on the model. """

        super().populate_obj(model, exclude={
            'start_date',
            'start_time',
            'end_date',
            'end_time',
            'weekly',
            'email',
        })

        # clear the recurrence to avoid updating all occurrences too much
        model.recurrence = ''

        model.meta = model.meta or {}
        model.meta['submitter_email'] = self.email.data
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
        end_date = self.start_date.data
        if self.end_time.data <= self.start_time.data:
            end_date += timedelta(days=1)

        model.end = replace_timezone(
            datetime(
                end_date.year,
                end_date.month,
                end_date.day,
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

    def process(self, *args, **kwargs):
        """ Stores the page values on the form. """

        super().process(*args, **kwargs)

        if 'obj' in kwargs:
            model = kwargs['obj']

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

            if model.meta:
                self.email.data = model.meta.get('submitter_email')
