from onegov.form import Form
from onegov.form.fields import HoneyPotField, MultiCheckboxField
from onegov.org import _
from onegov.org.utils import extract_categories_and_subcategories
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.request import OrgRequest
    from wtforms.fields.choices import _Choice


class SignupForm(Form):

    request: 'OrgRequest'

    address = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()]
    )

    subscribed_categories = MultiCheckboxField(
        label=_('Categories'),
        description=_('Select newsletter categories your are interested '
                      'in. You will receive the newsletter if it reports '
                      'on at least one of the subscribed categories.'),
        choices=[],
    )

    name = HoneyPotField()

    def on_request(self) -> None:
        categories, subcategories = extract_categories_and_subcategories(
            self.request.app.org.newsletter_categories)

        data: list[str] = []
        choices: list[_Choice] = []
        for cat, sub in zip(categories, subcategories):
            data.append(cat)
            choices.append((cat, cat))
            data.extend(sub)
            choices.extend((s, f'\xa0\xa0\xa0{s}') for s in sub)

        self.subscribed_categories.choices = choices
        self.subscribed_categories.data = data
