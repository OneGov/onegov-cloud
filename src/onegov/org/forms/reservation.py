from datetime import date, time, timedelta
from functools import cached_property
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField, TimeField
from onegov.org import _
from uuid import UUID
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.validators import DataRequired, Email, InputRequired
from onegov.org.forms.allocation import WEEKDAYS
from onegov.core.csv import convert_list_of_list_of_dicts_to_xlsx

# include all fields used below so we can filter them out
# when we merge this form with the custom form definition
RESERVED_FIELDS = ['email']


class ReservationForm(Form):
    reserved_fields = RESERVED_FIELDS

    email = EmailField(
        label=_("E-Mail"),
        validators=[InputRequired(), Email()]
    )


class FindYourSpotForm(Form):
    start = DateField(
        label=_("From"),
        validators=[InputRequired()])

    end = DateField(
        label=_("Until"),
        validators=[InputRequired()])

    start_time = TimeField(
        label=_("Start"),
        description=_("HH:MM"),
        default=time(7),
        validators=[DataRequired()])

    end_time = TimeField(
        label=_("End"),
        description=_("HH:MM"),
        default=time(22),
        validators=[DataRequired()])

    rooms = MultiCheckboxField(
        label=_("Rooms"),
        choices=tuple(),
        coerce=lambda v: UUID(v) if isinstance(v, str) else v,
        validators=[InputRequired()],
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        })

    weekdays = MultiCheckboxField(
        label=_("Weekdays"),
        choices=WEEKDAYS,
        coerce=int,
        default=[v for v, l in WEEKDAYS[:5]],
        validators=[InputRequired()],
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        })

    on_holidays = RadioField(
        label=_("On holidays"),
        choices=(
            ('yes', _("Yes")),
            ('no', _("No"))
        ),
        default='no')

    during_school_holidays = RadioField(
        label=_("During school holidays"),
        choices=(
            ('yes', _("Yes")),
            ('no', _("No"))
        ),
        default='no')

    def on_request(self):
        if not self.request.app.org.holidays:
            self.delete_field('on_holidays')
        if not self.request.app.org.has_school_holidays:
            self.delete_field('during_school_holidays')
        if not self.request.POST:
            # by default search one week from now
            self.start.data = date.today()
            self.end.data = self.start.data + timedelta(days=7)

    def apply_rooms(self, rooms):
        if len(rooms) < 2:
            # no need to filter
            self.delete_field('rooms')
            return

        self.rooms.choices = tuple((room.id, room.title) for room in rooms)
        if not self.request.POST:
            # select all rooms by default
            self.rooms.data = [room.id for room in rooms]

    def ensure_future_start(self):
        if self.start.data:
            if self.start.data < date.today():
                self.start.errors.append(_("Start date in past"))
                return False

    def ensure_start_before_end(self):
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                self.start.errors.append(_("Start date before end date"))
                return False

    def ensure_start_time_before_end_time(self):
        start = self.start_time.data
        end = self.end_time.data
        if start and end:
            if (start.hour > end.hour
                or (start.hour == end.hour
                    and start.minute >= end.minute)):
                self.start_time.errors.append(_("Start time before end time"))
                return False

    @cached_property
    def exceptions(self):
        if not hasattr(self, 'request'):
            return ()

        if not self.on_holidays:
            return ()

        if self.on_holidays.data == 'yes':
            return ()

        return self.request.app.org.holidays

    @cached_property
    def ranged_exceptions(self):
        if not hasattr(self, 'request'):
            return ()

        if not self.during_school_holidays:
            return ()

        if self.during_school_holidays.data == 'yes':
            return ()

        return tuple(self.request.app.org.school_holidays)

    def is_excluded(self, date):
        if date in self.exceptions:
            return True

        # weekdays is required so we don't need to handle None
        if date.weekday() not in self.weekdays.data:
            return True

        for start, end in self.ranged_exceptions:
            if start <= date <= end:
                return True
        return False


class ExportToExcelWorksheets(Form):
    """ A form providing the export of multiple reservations into Worksheets
    """

    @property
    def format(self):
        return 'xlsx'

    def as_multiple_export_response(self, keys, results, titles):

        return convert_list_of_list_of_dicts_to_xlsx(results,
                                                     titles_list=titles,
                                                     key_list=keys)
