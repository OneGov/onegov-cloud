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


class EmailSubscriptionForm(Form):

    email = EmailField(
        label=_("Email Address"),
        description="peter.muster@example.org",
        validators=[
            InputRequired(),
            Email()
        ],
        render_kw={
            'autocomplete': 'email',
        }
    )

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )


class SmsSubscriptionForm(Form):

    phone_number = PhoneNumberField(
        label=_("Phone number"),
        description="+41791112233",
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

    name = HoneyPotField(
        render_kw={
            'autocomplete': 'off'
        }
    )


class SubscribersCleanupForm(Form):

    callout = _(
        'Deactivates or deletes the given subscribers. '
        'The same format is used as for export (only address column).'
    )

    type = RadioField(
        label=_("Type"),
        validators=[
            InputRequired()
        ],
        choices=[
            ('delete', _("Delete")),
            ('deactivate', _("Deactivate")),
        ]
    )

    file = UploadField(
        label=_("File"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        render_kw={'force_simple': True},
    )
