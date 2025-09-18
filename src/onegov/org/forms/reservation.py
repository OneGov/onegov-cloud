from __future__ import annotations

from datetime import date, time, timedelta
from functools import cached_property
from uuid import UUID
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange
from wtforms.validators import Regexp

from onegov.core.csv import convert_list_of_list_of_dicts_to_xlsx
from onegov.core.custom import json
from onegov.form import Form
from onegov.form.fields import (
    ChosenSelectField, DurationField, MultiCheckboxField, TimeField)
from onegov.org import _
from onegov.org.forms.util import KABA_CODE_RE
from onegov.org.forms.util import WEEKDAYS


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Callable, Iterable, Sequence
    from onegov.org.request import OrgRequest
    from onegov.reservation import Resource
    from typing import TypeAlias
    from .allocation import DateContainer

    StrKeyFunc: TypeAlias = Callable[[str], SupportsRichComparison]

# include all fields used below so we can filter them out
# when we merge this form with the custom form definition
RESERVED_FIELDS: list[str] = ['email', 'ticket_tag']


class ReservationForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    reserved_fields = RESERVED_FIELDS

    ticket_tag = ChosenSelectField(
        label=_('Tag'),
        choices=(),
        render_kw={},
    )

    email = EmailField(
        label=_('E-Mail'),
        validators=[InputRequired(), Email()]
    )

    def on_request(self) -> None:
        if not (self.request.is_manager or self.request.is_supporter):
            self.delete_field('ticket_tag')
            return

        choices = self.ticket_tag.choices = [
            (tag, tag)
            for item in self.request.app.org.ticket_tags
            for tag in (item.keys() if isinstance(item, dict) else (item,))
        ]
        if not choices:
            self.delete_field('ticket_tag')

        choices.insert(0, ('', ''))

        self.css_class = 'resettable'

        auto_fill_data = {
            tag: filtered_meta
            for item in self.request.app.org.ticket_tags
            if isinstance(item, dict)
            for tag, meta in item.items()
            if (filtered_meta := {
                field.id: value
                for key, value in meta.items()
                # only include pre-fill data for the fields we render
                # since some of the data may not be public
                for field in self
                # FIXME: This is technically incorrect for IntegerRangeField
                #        with a price, since the price is displayed in the
                #        label, but since this is a very unlikely combination
                #        of features, we punt on this for now. This should
                #        handle everything else correctly.
                if key == field.label.text
                if field.id != 'ticket_tag'
            })
        }
        if auto_fill_data:
            self.ticket_tag.render_kw[
                'data_auto_fill'] = json.dumps(auto_fill_data)


class ReservationAdjustmentForm(Form):

    # NOTE: Currently we don't allow adjusting a reservation
    #       to a different allocation, so it's impossible to
    #       change the date, but once we do support that we
    #       may want to add a date field here

    start_time = TimeField(
        label=_('Starting at'),
        description=_('HH:MM'),
        validators=[InputRequired()],
        fieldset=_('Time'),
    )

    end_time = TimeField(
        label=_('Ending at'),
        description=_('HH:MM'),
        validators=[InputRequired()],
        fieldset=_('Time'),
    )


class AddReservationForm(Form):

    date = DateField(
        label=_('Date'),
        description=_('HH:MM'),
        validators=[InputRequired()],
        fieldset=_('Date'),
    )

    whole_day = RadioField(
        label=_('Whole day'),
        choices=[
            ('yes', _('Yes')),
            ('no', _('No'))
        ],
        default='no',
        fieldset=_('Time'),
    )

    start_time = TimeField(
        label=_('Starting at'),
        description=_('HH:MM'),
        fieldset=_('Time'),
        validators=[InputRequired()],
        depends_on=('whole_day', 'no')
    )

    end_time = TimeField(
        label=_('Ending at'),
        description=_('HH:MM'),
        fieldset=_('Time'),
        validators=[InputRequired()],
        depends_on=('whole_day', 'no')
    )

    quota_room = IntegerField(
        label=_('Quota'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Time'),
        default=1,
        depends_on=('whole_day', 'no')
    )

    quota_other = IntegerField(
        label=_('Quota'),
        validators=[
            InputRequired(),
            NumberRange(1, 999)
        ],
        fieldset=_('Time'),
        default=1,
    )

    def apply_resource(self, resource: Resource) -> None:
        if resource.type == 'room':
            self.delete_field('quota_other')
        else:
            self.delete_field('start_time')
            self.delete_field('end_time')
            self.delete_field('whole_day')
            self.delete_field('quota_room')

    @property
    def quota(self) -> IntegerField:
        return self.quota_room if 'quota_room' in self else self.quota_other


class KabaEditForm(Form):

    key_code = StringField(
        label=_('Key Code'),
        validators=[
            InputRequired(),
            Regexp(
                KABA_CODE_RE,
                message=_(
                    'Invalid Kaba Code. '
                    'Needs to be a 4 to 6 digit number code.'
                )
            )
        ],
    )

    key_code_lead_time = IntegerField(
        label=_('Lead Time'),
        validators=[InputRequired(), NumberRange(0, 1440)],
        render_kw={
            'step': 5,
            'long_description': _('In minutes'),
        },
    )

    key_code_lag_time = IntegerField(
        label=_('Lag Time'),
        validators=[InputRequired(), NumberRange(0, 1440)],
        render_kw={
            'step': 5,
            'long_description': _('In minutes'),
        },
    )


class FindYourSpotForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    duration = DurationField(
        label=_('I am looking to make a reservation lasting'),
        default=timedelta(hours=1),
        validators=[DataRequired()],
        render_kw={
            'placeholder': 'HH:MM',
        }
    )

    weekdays = MultiCheckboxField(
        label=_('On Weekday(s)'),
        choices=WEEKDAYS,
        coerce=int,
        default=[v for v, l in WEEKDAYS[:5]],
        validators=[InputRequired()],
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        })

    start = DateField(
        label=_('From'),
        validators=[InputRequired()])

    end = DateField(
        label=_('Until'),
        validators=[InputRequired()])

    start_time = TimeField(
        label=_('Earliest Start'),
        description=_('HH:MM'),
        default=time(7),
        validators=[DataRequired()],
        render_kw={
            'step': 300,
        })

    end_time = TimeField(
        label=_('Latest End'),
        description=_('HH:MM'),
        default=time(22),
        validators=[DataRequired()],
        render_kw={
            'step': 300,
        })

    rooms = MultiCheckboxField(
        label=_('Rooms'),
        choices=(),
        coerce=lambda v: UUID(v) if isinstance(v, str) else v,
        validators=[InputRequired()],
        render_kw={
            'prefix_label': False,
            'class_': 'oneline-checkboxes'
        })

    on_holidays = RadioField(
        label=_('On holidays'),
        choices=(
            ('yes', _('Yes')),
            ('no', _('No'))
        ),
        default='no')

    during_school_holidays = RadioField(
        label=_('During school holidays'),
        choices=(
            ('yes', _('Yes')),
            ('no', _('No'))
        ),
        default='no')

    auto_reserve_available_slots = RadioField(
        label=_('Automatically reserve the first available slot'),
        description=_('You will be able to change individual choices'),
        choices=(
            ('for_every_room', _('Yes, for every selected room and day')),
            ('for_every_day', _('Yes, for every selected day')),
            ('for_first_day', _('Yes, for the first available selected day')),
            ('no', _('No'))
        ),
        validators=[InputRequired()],
        default='no')

    def on_request(self) -> None:
        if not self.request.app.org.holidays:
            self.delete_field('on_holidays')
        if not self.request.app.org.has_school_holidays:
            self.delete_field('during_school_holidays')
        if not self.request.POST:
            # by default search one week from now
            self.start.data = date.today()
            self.end.data = self.start.data + timedelta(days=7)

    def apply_rooms(self, rooms: Sequence[Resource]) -> None:
        if len(rooms) < 2:
            # no need to filter
            self.delete_field('rooms')
            # the first and second choice are the same
            # when there is only one room
            choices = self.auto_reserve_available_slots.choices
            assert isinstance(choices, list)
            self.auto_reserve_available_slots.choices = choices[1:]
            return

        self.rooms.choices = [(room.id, room.title) for room in rooms]
        if not self.request.POST:
            # select all rooms by default
            self.rooms.data = [room.id for room in rooms]

    def ensure_future_start(self) -> bool | None:
        if self.start.data:
            if self.start.data < date.today():
                assert isinstance(self.start.errors, list)
                self.start.errors.append(_('Start date in past'))
                return False
        return None

    def ensure_start_before_end(self) -> bool | None:
        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                assert isinstance(self.start.errors, list)
                self.start.errors.append(_('Start date before end date'))
                return False
        return None

    def ensure_start_before_end_time_and_valid_duration(self) -> bool | None:
        start = self.start_time.data
        end = self.end_time.data
        if start and end:
            if (
                start.hour > end.hour
                or (
                    start.hour == end.hour
                    and start.minute >= end.minute
                )
            ):
                assert isinstance(self.start_time.errors, list)
                self.start_time.errors.append(_('Start time before end time'))
                return False

            if duration := self.duration.data:
                max_duration = timedelta(
                        hours=end.hour - start.hour,
                        minutes=start.minute - end.minute
                )
                if duration > max_duration:
                    assert isinstance(self.duration.errors, list)
                    self.duration.errors.append(_(
                        'Duration is longer than the range between '
                        'start and end time'
                    ))
        return None

    @cached_property
    def exceptions(self) -> DateContainer:
        if not hasattr(self, 'request'):
            return ()

        if not self.on_holidays:
            return ()

        if self.on_holidays.data == 'yes':
            return ()

        return self.request.app.org.holidays

    @cached_property
    def ranged_exceptions(self) -> Sequence[tuple[date, date]]:
        if not hasattr(self, 'request'):
            return ()

        if not self.during_school_holidays:
            return ()

        if self.during_school_holidays.data == 'yes':
            return ()

        return tuple(self.request.app.org.school_holidays)

    def is_excluded(self, date: date) -> bool:
        if date in self.exceptions:
            return True

        if date.weekday() not in (self.weekdays.data or ()):
            return True

        for start, end in self.ranged_exceptions:
            if start <= date <= end:
                return True
        return False


class ExportToExcelWorksheets(Form):
    """ A form providing the export of multiple reservations into Worksheets
    """

    @property
    def format(self) -> str:
        return 'xlsx'

    def as_multiple_export_response(
        self,
        keys: Sequence[StrKeyFunc | None] | None,
        results: Sequence[Iterable[dict[str, Any]]],
        titles: Sequence[str]
    ) -> bytes:

        return convert_list_of_list_of_dicts_to_xlsx(
            results, titles_list=titles, key_list=keys
        )
