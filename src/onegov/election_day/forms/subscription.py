from __future__ import annotations

from datetime import date
from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import PhoneNumberField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import ValidPhoneNumber
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import EmailField
from wtforms.fields import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.request import ElectionDayRequest


class SubscriptionForm(Form):

    request: ElectionDayRequest

    domain = RadioField(
        label=_('Type'),
        choices=(
            ('canton', _('Cantonal')),
            ('municipality', _('Communal')),
        ),
        default='canton',
        validators=[
            InputRequired()
        ]
    )

    domain_segment = RadioField(
        label=_('Municipality'),
        validators=[
            InputRequired()
        ],
        depends_on=('domain', 'municipality'),
    )

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )

    def on_request(self) -> None:
        principal = self.request.app.principal
        if principal.segmented_notifications:
            self.domain_segment.choices = [
                (entity, entity)
                for entity in sorted(
                    principal.get_entities(date.today().year)
                )
            ]
        else:
            self.delete_field('domain')
            self.delete_field('domain_segment')


class EmailSubscriptionForm(SubscriptionForm):

    email = EmailField(
        label=_('Email Address'),
        description='peter.muster@example.org',
        validators=[
            InputRequired(),
            Email()
        ],
        render_kw={
            'autocomplete': 'email',
        }
    )


class SmsSubscriptionForm(SubscriptionForm):

    phone_number = PhoneNumberField(
        label=_('Phone number'),
        description='+41791112233',
        validators=[
            InputRequired(),
            ValidPhoneNumber(country_whitelist={
                'CH', 'AT', 'DE', 'FR', 'IT', 'LI'
            })
        ],
        render_kw={
            'autocomplete': 'tel',
        }
    )


class SubscribersCleanupForm(Form):

    callout = _(
        'Deactivates or deletes the given subscribers. '
        'The same format is used as for export (only address column).'
    )

    type = RadioField(
        label=_('Type'),
        validators=[
            InputRequired()
        ],
        choices=[
            ('delete', _('Delete')),
            ('deactivate', _('Deactivate')),
        ]
    )

    file = UploadField(
        label=_('File'),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
    )
