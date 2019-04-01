import json

from cached_property import cached_property
from datetime import date, datetime, timedelta
from dateutil import rrule
from dateutil.rrule import rrulestr
from onegov.event.models import EventFile
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import CoordinatesField
from onegov.org import _
from sedate import replace_timezone, to_timezone
from wtforms import RadioField, StringField, TextAreaField, validators
from wtforms.fields.html5 import DateField, EmailField
from wtforms_components import TimeField


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

    timezone = 'Europe/Zurich'

    email = EmailField(
        label=_("Submitter"),
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

    image = UploadFileWithORMSupport(
        label=_("Image"),
        description="Foobar",
        file_class=EventFile,
        validators=[
            validators.Optional(),
            WhitelistedMimeType({
                'image/gif',
                'image/jpeg',
                'image/png'
            }),
            FileSizeLimit(1 * 1024 * 1024)
        ]
    )

    location = StringField(
        label=_("Venue"),
        description=_("Castle garden"),
        validators=[validators.InputRequired()]
    )

    organizer = StringField(
        label=_("Organizer"),
        description=_("Music society"),
        validators=[validators.InputRequired()]
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

    repeat = RadioField(
        label=_("Repeat"),
        default='without',
        choices=(
            ('without', _("Without")),
            ('weekly', _("Weekly")),
            ('dates', _("On additional dates"))
        )
    )

    weekly = MultiCheckboxField(
        label=_("Repeats itself every"),
        choices=WEEKDAYS,
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'},
        depends_on=('repeat', 'weekly')
    )

    end_date = DateField(
        label=_("Until date"),
        validators=[validators.Optional()],
        depends_on=('repeat', 'weekly')
    )

    dates = TextAreaField(
        label=_("Dates"),
        depends_on=('repeat', 'dates'),
        render_kw={'class_': 'many many-dates'},
    )

    @property
    def start(self):
        return replace_timezone(
            datetime(
                self.start_date.data.year,
                self.start_date.data.month,
                self.start_date.data.day,
                self.start_time.data.hour,
                self.start_time.data.minute
            ),
            self.timezone
        )

    @property
    def end(self):
        end_date = self.start_date.data

        if self.end_time.data <= self.start_time.data:
            end_date += timedelta(days=1)

        return replace_timezone(
            datetime(
                end_date.year,
                end_date.month,
                end_date.day,
                self.end_time.data.hour,
                self.end_time.data.minute
            ),
            self.timezone
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_errors = {}

    def on_request(self):
        self.request.include('common')
        self.request.include('many')

        if not self.dates.data:
            self.dates.data = self.dates_to_json(None)

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

        if self.repeat.data == 'weekly':
            if self.weekly.data and self.start_date.data:
                weekday = WEEKDAYS[self.start_date.data.weekday()][0]
                if weekday not in self.weekly.data:
                    message = _(
                        "The weekday of the start date must be selected.")
                    self.weekly.errors.append(message)
                    result = False

            if self.weekly.data and not self.end_date.data:
                message = _(
                    "Please set and end date if the event is recurring.")
                self.end_date.errors.append(message)
                result = False

            if self.end_date.data and not self.weekly.data:
                message = _(
                    "Please select a weekday if the event is recurring.")
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
        model.timezone = self.timezone
        model.start = self.start
        model.end = self.end

        if self.repeat.data == 'without':
            self.recurrence = None
        elif self.repeat.data == 'weekly':
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
        elif self.repeat.data == 'dates':
            model.recurrence = '\n'.join(
                f"RDATE:{d.strftime('%Y%m%dT000000Z')}"
                for d in self.parsed_dates
            )
        else:
            raise NotImplementedError

    def process_obj(self, model):
        """ Stores the page values on the form. """

        super().process_obj(model)

        self.start_time.data = model.localized_start.time()
        self.end_time.data = model.localized_end.time()
        self.start_date.data = model.localized_start.date()

        if model.recurrence:
            last_occurrence = model.occurrence_dates(localize=True)[-1]
            self.end_date.data = last_occurrence.date()

            rule = rrulestr(model.recurrence)

            if getattr(rule, '_freq', None) == rrule.WEEKLY:
                self.repeat.data = 'weekly'
                self.dates.data = self.dates_to_json(None)
                self.weekly.data = [
                    WEEKDAYS[day][0] for day in rule._byweekday
                ]
            else:
                self.repeat.data = 'dates'
                self.dates.data = self.dates_to_json(tuple(rule))
        elif self.errors.get('weekly'):
            self.dates.data = self.dates_to_json(None)
            self.repeat.data = 'weekly'
        else:
            self.dates.data = self.dates_to_json(None)
            self.repeat.data = 'without'

        if model.meta:
            self.email.data = model.meta.get('submitter_email')

    @cached_property
    def parsed_dates(self):
        return self.json_to_dates(self.dates.data)

    def json_to_dates(self, text=None):
        result = []

        for value in json.loads(text or '{}').get('values', []):
            result.append(date(*map(int, value['date'].split('-'))))

        return result

    def dates_to_json(self, dates=None):
        dates = dates or []

        return json.dumps({
            'labels': {
                'date': self.request.translate(_("Date")),
                'add': self.request.translate(_("Add")),
                'remove': self.request.translate(_("Remove")),
            },
            'values': [
                {
                    'date': d.strftime('%Y-%m-%d'),
                    'error': self.date_errors.get(ix, "")
                } for ix, d in enumerate(dates)
            ]
        })
