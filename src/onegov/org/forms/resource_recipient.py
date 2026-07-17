from __future__ import annotations

import re

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField, TagsField
from onegov.org import _
from onegov.reservation import Resource, ResourceCollection
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import BooleanField
from wtforms.validators import InputRequired, Email


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest


_TIME_RE = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')

WEEKDAYS = (
    ('MO', _('Mo')),
    ('TU', _('Tu')),
    ('WE', _('We')),
    ('TH', _('Th')),
    ('FR', _('Fr')),
    ('SA', _('Sa')),
    ('SU', _('Su')),
)


class ResourceRecipientForm(Form):

    if TYPE_CHECKING:
        request: OrgRequest

    name = StringField(
        label=_('Name'),
        fieldset='Empfänger',
        description='Peter Muster',
        validators=[InputRequired()]
    )

    address = EmailField(
        label=_('E-Mail'),
        fieldset='Empfänger',
        description='peter.muster@example.org',
        validators=[InputRequired(), Email()]
    )

    new_reservations = BooleanField(
        label=_('New Reservations'),
        fieldset=_('Notifications *'),
        description=_('For each new reservation, a notification will be sent '
                      'to the above recipient.'),
    )

    daily_reservations = BooleanField(
        label=_('Daily Reservations'),
        fieldset=_('Notifications *'),
        description=_("On each day selected below, a notification with the "
                      "day's reservations will be sent to the recipient "
                      "above."),
    )

    customer_messages = BooleanField(
        label=_('Customer Messages'),
        fieldset=_('Notifications *'),
        description=_('Each time a customer adds a message to the ticket for '
                      'a reservation, a notification is sent to the recipient '
                      'above.'),
    )

    internal_notes = BooleanField(
        label=_('Internal Notes'),
        fieldset=_('Notifications *'),
        description=_('Each time a new note is added to the ticket for a '
                      'reservation, a notification is sent to the recipient '
                      'above.'),
    )

    rejected_reservations = BooleanField(
        label=_('Rejected Reservations'),
        fieldset=_('Notifications *'),
        description=_('If a reservation is cancelled, a notification will '
                      'be sent to the above recipient.'),
    )

    cancellation_requests = BooleanField(
        label=_('Cancellation Requests'),
        fieldset=_('Notifications *'),
        description=_('When a customer requests to cancel a reservation, a '
                      'notification will be sent to the above recipient.'),
    )

    send_on = MultiCheckboxField(
        label=_('Send on'),
        fieldset='Tage und Ressourcen',
        choices=WEEKDAYS,
        default=[key for key, value in WEEKDAYS],
        validators=[InputRequired()],
        depends_on=('daily_reservations', 'y'),
        render_kw={'prefix_label': False, 'class_': 'oneline-checkboxes'}
    )

    daily_reservations_times = TagsField(
        label=_('Delivery Times'),
        fieldset='Tage und Ressourcen',
        description=_('e.g. 07:05'),
        depends_on=('daily_reservations', 'y'),
    )

    resources = MultiCheckboxField(
        label=_('Resources'),
        fieldset='Tage und Ressourcen',
        validators=[InputRequired()],
        choices=None
    )

    def ensure_valid_delivery_times(self) -> bool | None:
        if not self.daily_reservations.data:
            return None

        times = self.daily_reservations_times.data
        if not times:
            self.daily_reservations_times.errors.append(  # type: ignore[attr-defined]
                _('Please enter at least one delivery time.')
            )
            return False

        for t in times:
            m = _TIME_RE.match(t)
            if not m:
                self.daily_reservations_times.errors.append(  # type: ignore[attr-defined]
                    _('Invalid time "${time}". Use HH:MM format (e.g. 06:00).',
                      mapping={'time': t})
                )
                return False
            if int(m.group(2)) % 5 != 0:
                self.daily_reservations_times.errors.append(  # type: ignore[attr-defined]
                    _('Minutes must be a multiple of 5 (e.g. 06:10, 16:35).')
                )
                return False

        return None

    def ensure_at_least_one_notification(self) -> bool | None:
        if not (
            self.new_reservations.data
            or self.daily_reservations.data
            or self.customer_messages.data
            or self.internal_notes.data
            or self.rejected_reservations.data
            or self.cancellation_requests.data
        ):
            self.request.alert(_('Please add at least one notification.'))
            return False
        return None

    def on_request(self) -> None:
        if not self.request.POST and not self.daily_reservations_times.data:
            self.daily_reservations_times.data = ['06:00']  # legacy default

        default_group = self.request.translate(_('General'))

        self.resources.choices = [
            (resource_id.hex, f'{group or default_group} - {title}')
            for group, title, resource_id in (
                ResourceCollection(self.request.app.libres_context).query()
                .with_entities(Resource.group, Resource.title, Resource.id)
                .order_by(Resource.group, Resource.name)
                .tuples()
            )
        ]
