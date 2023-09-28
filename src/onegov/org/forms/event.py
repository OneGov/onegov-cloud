import json
import transaction

from functools import cached_property
from datetime import date, datetime, timedelta
from dateutil import rrule
from dateutil.parser import parse
from dateutil.rrule import rrulestr
from itertools import chain

from onegov.core.csv import convert_excel_to_csv
from onegov.core.csv import CSVFile
from onegov.event.collections import EventCollection, OccurrenceCollection
from onegov.event.models import EventFile
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.fields import TimeField
from onegov.form.fields import UploadField
from onegov.form.fields import UploadFileWithORMSupport
from onegov.form.validators import (
    FileSizeLimit, ValidPhoneNumber, ValidFilterFormDefinition)
from onegov.form.validators import WhitelistedMimeType
from onegov.gis import CoordinatesField
from onegov.org import _
from onegov.ticket import TicketCollection
from sedate import replace_timezone, to_timezone
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence


TAGS = [
    _("Art"),
    _("Cinema"),
    _("Concert"),
    _("Congress"),
    _("Culture"),
    _("Dancing"),
    _("Education"),
    _("Exhibition"),
    _("Gastronomy"),
    _("Health"),
    _("Library"),
    _("Literature"),
    _("Market"),
    _("Meetup"),
    _("Misc"),
    _("Music School"),
    _("Music"),
    _("Party"),
    _("Politics"),
    _("Reading"),
    _("Religion"),
    _("Sports"),
    _("Talk"),
    _("Theater"),
    _("Tourism"),
    _("Toy Library"),
    _("Tradition"),
    _("Youth"),
    _("Elderly"),
]

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

    on_request_include: 'Sequence[str]' = ('common', 'many')

    timezone = 'Europe/Zurich'

    email = EmailField(
        label=_("Submitter"),
        description="max.muster@example.org",
        validators=[InputRequired(), Email()]
    )

    title = StringField(
        label=_("Title"),
        description=_("Concerto in the castle garden"),
        validators=[InputRequired()]
    )

    description = TextAreaField(
        label=_("Description"),
        description=_("Enjoy a concerto in the castle garden."),
        render_kw={'rows': 12}
    )

    image = UploadFileWithORMSupport(
        label=_("Image"),
        file_class=EventFile,
        validators=[
            Optional(),
            WhitelistedMimeType({
                'image/gif',
                'image/jpeg',
                'image/png'
            }),
            FileSizeLimit(5 * 1024 * 1024)
        ]
    )

    pdf = UploadFileWithORMSupport(
        label=_("Additional Information (PDF)"),
        file_class=EventFile,
        validators=[
            Optional(),
            WhitelistedMimeType({
                'application/pdf',
            }),
            FileSizeLimit(5 * 1024 * 1024)
        ]
    )

    location = StringField(
        label=_("Venue"),
        description="Pilatusstrasse 3, 6000 Luzern",
        validators=[InputRequired()]
    )

    price = TextAreaField(
        label=_("Price"),
        description=_("10 CHF for adults"),
        render_kw={'rows': 2}
    )

    organizer = StringField(
        label=_("Organizer"),
        description=_("Music society"),
        validators=[InputRequired()]
    )

    organizer_email = EmailField(
        label=_("Organizer E-Mail address"),
        description=_("Shown as contact E-Mail address"),
        validators=[Optional(), Email()]
    )

    organizer_phone = StringField(
        label=_("Organizer phone number"),
        description=_("Shown as contact phone number"),
        validators=[Optional(), ValidPhoneNumber()]
    )

    external_event_url = StringField(
        label=_("External event URL"),
        description="https://www.example.ch",
    )

    coordinates = CoordinatesField(
        label=_("Coordinates"),
        description=_("The marker can be moved by dragging it with the mouse"),
        render_kw={'data-map-type': 'marker'}
    )

    tags = MultiCheckboxField(
        label=_("Tags"),
        choices=[(tag, tag) for tag in TAGS],
    )

    start_date = DateField(
        label=_("Date"),
        validators=[InputRequired()],
        default=date.today
    )

    start_time = TimeField(
        label=_("From"),
        description="18:00",
        validators=[InputRequired()]
    )

    end_time = TimeField(
        label=_("To"),
        description="19:15",
        validators=[InputRequired()]
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
        validators=[Optional()],
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

    def populate_submitter(self):
        if self.request.is_logged_in:
            self.email.data = self.request.current_username

    def on_request(self):
        if self.tags:
            if self.custom_tags():
                self.tags.choices = [(tags, tags) for tags in
                                     self.custom_tags()]

            for include in self.on_request_include:
                self.request.include(include)
            self.sort_tags()

        if not self.dates.data:
            self.dates.data = self.dates_to_json(None)
        if not self.email.data:
            self.populate_submitter()

    def custom_tags(self):
        return self.request.app.custom_event_tags

    def sort_tags(self):
        self.tags.choices.sort(key=lambda c: self.request.translate(c[1]))

    def validate(self):
        """ Make sure a valid RRULE can be generated with the given fields.

        Might be better to group weekly and end_date in an enclosure,
        see See http://wtforms.readthedocs.org/en/latest/fields.html
        #field-enclosures.

        """
        result = super().validate()

        if self.start_date.data and self.end_date.data:
            if self.start_date.data > self.end_date.data:
                self.end_date.errors.append(
                    _("The end date must be later than the start date.")
                )
                result = False

        if self.repeat.data == 'weekly':
            if self.weekly.data and self.start_date.data:
                weekday = WEEKDAYS[self.start_date.data.weekday()][0]
                if weekday not in self.weekly.data:
                    self.weekly.errors.append(
                        _("The weekday of the start date must be selected.")
                    )
                    result = False

            if self.weekly.data and not self.end_date.data:
                self.end_date.errors.append(
                    _("Please set and end date if the event is recurring.")
                )
                result = False

            if self.end_date.data and not self.weekly.data:
                self.weekly.errors.append(
                    _("Please select a weekday if the event is recurring.")
                )
                result = False

        if self.repeat.data == 'dates':
            try:
                assert self.json_to_dates(self.dates.data)
            except (AssertionError, ValueError):
                self.repeat.errors.append(_("Invalid dates."))
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

        if self.request.app.org.event_filter_type in ['filters',
                                                      'tags_and_filters']:
            filter_keywords = dict()
            for field in self.request.app.org.event_filter_fields:
                form_field = getattr(self, field.id)
                filter_keywords[field.id] = form_field.data

            if filter_keywords:
                model.filter_keywords = filter_keywords
                for occ in model.occurrences:
                    occ.filter_keywords = filter_keywords

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

        if model.filter_keywords:
            keywords = model.filter_keywords

            for field in self.request.app.org.event_filter_fields:
                form_field = getattr(self, field.id, None)

                if form_field is None:
                    continue

                form_field.data = keywords[field.id] if (
                    field.id in keywords) else None

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


class EventImportForm(Form):

    clear = BooleanField(
        label=_("Clear"),
        description=_(
            "Delete imported events before importing. This does not delete "
            "otherwise imported events and submitted events."
        ),
        default=False
    )

    dry_run = BooleanField(
        label=_("Dry Run"),
        description=_("Do not actually import the events."),
        default=False
    )

    file = UploadField(
        label=_("Import"),
        validators=[
            DataRequired(),
            WhitelistedMimeType({
                'application/excel',
                'application/vnd.ms-excel',
                (
                    'application/'
                    'vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
                'application/vnd.ms-office',
                'application/octet-stream',
                'application/zip',
                'text/csv',
                'text/plain',
            }),
            FileSizeLimit(10 * 1024 * 1024)
        ],
        render_kw=dict(force_simple=True)
    )

    @property
    def headers(self):
        return {
            'title': self.request.translate(_("Title")),
            'description': self.request.translate(_("Description")),
            'location': self.request.translate(_("Venue")),
            'price': self.request.translate(_("Price")),
            'organizer': self.request.translate(_("Organizer")),
            'organizer_email': self.request.translate(_("Organizer E-Mail "
                                                        "address")),
            'organizer_phone': self.request.translate(_("Organizer phone "
                                                        "number")),
            'external_event_url': self.request.translate(
                _("External event URL")),
            'tags': self.request.translate(_("Tags")),
            'start': self.request.translate(_("From")),
            'end': self.request.translate(_("To")),
        }

    def custom_tags(self):
        return self.request.app.custom_event_tags

    def run_export(self):
        occurrences = OccurrenceCollection(self.request.session)
        headers = self.headers

        def get(occurrence, attribute):
            if attribute in ('start', 'end'):
                attribute = f'localized_{attribute}'
            result = (
                getattr(occurrence, attribute, None)
                or getattr(occurrence.event, attribute, None)
            )
            if isinstance(result, datetime):
                result = result.strftime("%d.%m.%Y %H:%M")
            if attribute == 'tags':
                result = [self.request.translate(_(tag)) for tag in result]
                result = ', '.join(result)
            result = result or ''
            result = result.strip()
            return result

        result = []
        for occurrence in occurrences.query():
            result.append({
                title: get(occurrence, attribute)
                for attribute, title in headers.items()
            })

        return result

    def run_import(self):
        headers = self.headers
        session = self.request.session
        events = EventCollection(session)
        all_tags = chain(
            TAGS,
            self.custom_tags() or []
        )
        tags = {
            self.request.translate(tag): tag for tag in all_tags
        }
        tickets = TicketCollection(session)

        if self.clear.data:
            for event in events.query():
                if event.source:
                    continue
                if tickets.by_handler_id(event.id.hex):
                    continue
                session.delete(event)

        csvfile = convert_excel_to_csv(self.file.file)
        try:
            csv = CSVFile(csvfile, expected_headers=headers.values())
        except Exception:
            error_string = _('Expected header line with the following '
                             'columns:')
            return 0, ['0 - {} {}'.format(error_string,
                                          list(headers.values()))]
        lines = list(csv.lines)
        columns = {
            key: csv.as_valid_identifier(value)
            for key, value in headers.items()
        }

        def get(line, column, attribute):
            result = getattr(line, column)
            if attribute in ('start', 'end'):
                result = parse(result, dayfirst=True)
            if attribute == 'tags':
                result = result.split(', ')
                result = [tags.get(tag, None) for tag in result]
                result = [tag for tag in result if tag]
            return result

        count = 0
        errors = []
        for number, line in enumerate(lines, start=1):
            try:
                kwargs = {
                    attribute: get(line, column, attribute)
                    for attribute, column in columns.items()
                }
                kwargs['timezone'] = 'Europe/Zurich'
                event = events.add(**kwargs)
                event.meta['submitter_email'] = self.request.current_username
                event.submit()
                event.publish()
                count += 1
            except Exception:
                errors.append(str(number))

        if self.dry_run.data or errors:
            transaction.abort()

        return count, errors


class EventConfigurationForm(Form):
    """ Form to configure filters for events view. """

    definition = TextAreaField(
        label=_("Definition"),
        fieldset=_("General"),
        validators=[
            InputRequired(),
            ValidFilterFormDefinition(
                require_email_field=False,
                require_title_fields=False,
                reserved_fields={name for name, _ in
                                 EventForm()._unbound_fields}
            )
        ],
        render_kw={'rows': 32, 'data-editor': 'form'})

    keyword_fields = TextAreaField(
        label=_("Filters"),
        fieldset=_("Display"),
        render_kw={
            'class_': 'formcode-select',
            'data-fields-include': 'radio,checkbox'
        })
