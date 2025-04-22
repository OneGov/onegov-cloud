from __future__ import annotations

from wtforms import BooleanField

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

    request: OrgRequest

    subscribed_categories = MultiCheckboxField(
        label=_('Categories'),
        description=_('Select newsletter categories your are interested '
                      'in. You will receive the newsletter if it reports '
                      'on at least one of the subscribed categories.'),
        choices=[],
    )

    address = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()]
    )

    confirmed = BooleanField(
        label=_('The subscriber has given consent to receive the newsletter.'),
        validators=[InputRequired()]
    )

    name = HoneyPotField()

    daily_newsletter = BooleanField(
        label=_('Daily newsletter for all categories (only for '
                'news items)'),
        default=False,
    )

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

        if len(choices) == 0:
            self.delete_field('subscribed_categories')

        if not self.request.is_manager:
            self.delete_field('confirmed')

        if self.request.app.org.enable_automatic_newsletters:
            times = self.request.app.org.newsletter_times or []
            self.daily_newsletter.description = self.request.translate(
                _(('If there are any new news items since the last '
                   'sending time you will receive the newsletter at '
                   'the following times: ${joined}:00.')
                , mapping={
                    'joined': ':00, '.join(times)
                })
            )

        else:
            self.delete_field('daily_newsletter')
