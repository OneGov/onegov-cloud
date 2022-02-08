from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.form.fields import PhoneNumberField
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import InputRequired


class EmailSubscriptionForm(Form):

    email = StringField(
        label=_("Email"),
        validators=[
            InputRequired(),
            Email()
        ]
    )

    name = HoneyPotField()


class SmsSubscriptionForm(Form):

    phone_number = PhoneNumberField(
        label=_("Phone number"),
        description="+41791112233",
        validators=[
            InputRequired(),
        ],
    )

    name = HoneyPotField()


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
        render_kw=dict(force_simple=True),
    )
