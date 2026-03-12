from __future__ import annotations

from onegov.form.fields import PhoneNumberField
from onegov.form.fields import TranslatedSelectField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import (
    ValidPhoneNumber,
    MIME_TYPES_IMAGE
)
from onegov.parliament.models.parliamentarian import GENDERS
from onegov.parliament.models.parliamentarian import SHIPPING_METHODS
from onegov.pas.collections.parliamentarian import (
    PASParliamentarianCollection
)
from onegov.pas import _
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL


from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Collection
    from onegov.pas.models.parliamentarian import PASParliamentarian
    from onegov.pas.app import PasApp


class PASParliamentarianForm(NamedFileForm):

    personnel_number = StringField(
        label=_('Personnel number'),
        fieldset=_('Basic properties'),
    )

    contract_number = StringField(
        label=_('Contract number'),
        fieldset=_('Basic properties'),
    )

    gender = TranslatedSelectField(
        label=_('Gender'),
        fieldset=_('Basic properties'),
        choices=list(GENDERS.items()),
        validators=[InputRequired()],
        default='male'
    )

    first_name = StringField(
        label=_('First name'),
        fieldset=_('Basic properties'),
        validators=[InputRequired()],
    )

    last_name = StringField(
        label=_('Last name'),
        fieldset=_('Basic properties'),
        validators=[InputRequired()],
    )

    picture = UploadField(
        label=_('Picture'),
        fieldset=_('Basic properties'),
        allowed_mimetypes=MIME_TYPES_IMAGE,
    )

    shipping_method = TranslatedSelectField(
        label=_('Shipping method'),
        fieldset=_('Shipping address'),
        choices=list(SHIPPING_METHODS.items()),
        validators=[InputRequired()],
        default='a'
    )

    shipping_address = StringField(
        label=_('Address'),
        fieldset=_('Shipping address'),
        validators=[InputRequired()],
    )

    shipping_address_addition = StringField(
        label=_('Addition'),
        fieldset=_('Shipping address'),
    )

    shipping_address_zip_code = StringField(
        label=_('Zip code'),
        fieldset=_('Shipping address'),
        validators=[InputRequired()],
    )

    shipping_address_city = StringField(
        label=_('City'),
        fieldset=_('Shipping address'),
        validators=[InputRequired()],
    )

    private_address = StringField(
        label=_('Address'),
        fieldset=_('Private address'),
    )

    private_address_addition = StringField(
        label=_('Addition'),
        fieldset=_('Private address'),
    )

    private_address_zip_code = StringField(
        label=_('Zip code'),
        fieldset=_('Private address'),
    )

    private_address_city = StringField(
        label=_('City'),
        fieldset=_('Private address'),
    )

    date_of_birth = DateField(
        label=_('Date of birth'),
        fieldset=_('Additional information'),
        validators=[Optional()],
    )

    date_of_death = DateField(
        label=_('Date of death'),
        fieldset=_('Additional information'),
        validators=[Optional()],
    )

    place_of_origin = StringField(
        label=_('Place of origin'),
        fieldset=_('Additional information'),
    )

    occupation = StringField(
        label=_('Occupation'),
        fieldset=_('Additional information'),
    )

    academic_title = StringField(
        label=_('Academic title'),
        fieldset=_('Additional information'),
    )

    salutation = StringField(
        label=_('Salutation'),
        fieldset=_('Additional information'),
    )

    salutation_for_address = StringField(
        label=_('Salutation used in the address'),
        fieldset=_('Additional information'),
    )

    salutation_for_letter = StringField(
        label=_('Salutation used for letters'),
        fieldset=_('Additional information'),
    )

    forwarding_of_bills = StringField(
        label=_('How bills should be delivered'),
        fieldset=_('Additional information'),
    )

    phone_private = PhoneNumberField(
        label=_('Private phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    phone_mobile = PhoneNumberField(
        label=_('Mobile phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    phone_business = PhoneNumberField(
        label=_('Business phone number'),
        fieldset=_('Additional information'),
        validators=[ValidPhoneNumber()],
        render_kw={'autocomplete': 'tel'}
    )

    email_primary = EmailField(
        label=_('Primary email address'),
        fieldset=_('Additional information'),
        validators=[InputRequired(), Email()]
    )

    email_secondary = EmailField(
        label=_('Secondary email address'),
        fieldset=_('Additional information'),
        validators=[Optional(), Email()]
    )

    website = URLField(
        label=_('Website'),
        fieldset=_('Additional information'),
        validators=[URL(), Optional()]
    )

    remarks = TextAreaField(
        label=_('Remarks'),
        fieldset=_('Additional information'),
    )

    def get_useful_data(
        self,
        exclude: Collection[str] | None = None
    ) -> dict[str, Any]:
        """Do not use to update and instance of a parliamentarian."""
        exclude_set = set(exclude or ())
        exclude_set.add('csrf_token')
        data = super().get_useful_data(
            exclude=exclude_set
        )

        data['email_primary'] = data['email_primary'] or None
        return data

    def update_model(self, model: PASParliamentarian) -> None:
        app = cast('PasApp', self.request.app)
        parliamentarians = PASParliamentarianCollection(app)
        parliamentarians.update_user(model, self.email_primary.data)

        for field_name, field in self._fields.items():
            if field_name in ('csrf_token', 'picture'):
                continue

            if hasattr(model, field_name):
                setattr(model, field_name, field.data)
