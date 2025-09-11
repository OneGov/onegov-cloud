from __future__ import annotations

import json

from onegov.form.fields import PhoneNumberField
from onegov.form.fields import TranslatedSelectField
from onegov.form.fields import UploadField
from onegov.form.forms import NamedFileForm
from onegov.form.validators import ValidPhoneNumber
from onegov.org import _
from onegov.parliament.models.parliamentarian import GENDERS
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import Email
from wtforms.validators import InputRequired
from wtforms.validators import Optional
from wtforms.validators import URL

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.parliament.models.parliamentarian import Parliamentarian


class ParliamentarianForm(NamedFileForm):
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
    )

    party = StringField(
        label=_('Party'),
        fieldset=_('Basic properties'),
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

    # just commented as not used but still as column in the database
    # date_of_death = DateField(
    #     label=_('Date of death'),
    #     fieldset=_('Additional information'),
    #     validators=[Optional()],
    # )

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

    interest_ties = StringField(
        label=_('Interest ties'),
        fieldset=_('Interest ties'),
        render_kw={'class_': 'many many-interest-ties'}
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.interest_tie_errors: dict[int, str] = {}

    def on_request(self) -> None:
        pass

    def process_obj(self, obj: Parliamentarian) -> None:  # type:ignore[override]
        super().process_obj(obj)

        parliamentarian: Parliamentarian = obj
        interest_ties = parliamentarian.interests or {'rows': []}
        self.interest_ties.data = self.interest_ties_to_json(interest_ties)

    def populate_obj(
        self,
        obj: object,
        *args: Any, **kwargs: Any
    ) -> None:
        super().populate_obj(
            obj,
            exclude={'interest_ties'}
        )

        if hasattr(obj, 'interests'):
            interests = obj.interests
            interests['rows'] = self.json_to_interest_ties(
                self.interest_ties.data)
            if not interests.get('headers'):
                interests['headers'] = ['Interessenbindung', 'Kategorie']
            obj.interests = interests

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        data = super().get_useful_data()
        data.pop('interest_ties')
        return data

    def interest_ties_to_json(
        self,
        interest_ties: dict[str, Any]
    ) -> str:
        cats = [self.request.translate(_('No categories defined'))]

        interest_tie_cats = self.request.app.org.ris_interest_tie_categories  # type:ignore[attr-defined]
        if interest_tie_cats:
            cats = [
                i.strip() for i in
                interest_tie_cats.split(';')
                if i
            ]

        return json.dumps({
            'labels': {
                'interest_tie': self.request.translate(_('Interest tie')),
                'category': self.request.translate(_('Category')),
                'add': self.request.translate(_('Add')),
                'remove': self.request.translate(_('Remove')),
            },
            'categories': {
                val: val for val in cats
            },
            'values': [
                {
                    'interest_tie': tie['Interessenbindung'],
                    'category': tie['Kategorie'],
                    'error': self.interest_tie_errors.get(ix, '')
                } for ix, tie in enumerate(interest_ties['rows'])
            ]
        })

    def json_to_interest_ties(
        self,
        text: str | None
    ) -> list[dict[str, str]]:
        if not text:
            return []

        return [
            {
                'Interessenbindung': value['interest_tie'],
                'Kategorie': value['category']
            }
            for value in json.loads(text).get('values', [])
            if value['interest_tie'] and value['category']
        ]
