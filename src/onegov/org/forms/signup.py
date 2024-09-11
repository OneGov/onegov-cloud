from onegov.form import Form
from onegov.form.fields import HoneyPotField, MultiCheckboxField
from onegov.org import _
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired

from onegov.org.utils import extract_categories_and_subcategories


class SignupForm(Form):

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
            self.request.app.org.newsletter_categories)  # type: ignore
        choices: list[tuple[str, str]] = []

        for cat, sub in zip(categories, subcategories):
            choices.append((cat, cat))
            for s in sub:
                choices.append((f'{s}', f'\xa0\xa0\xa0{s}'))

        self.subscribed_categories.choices = (
            choices)  # type: ignore[assignment]
        self.subscribed_categories.data = [c for c, _ in choices]
