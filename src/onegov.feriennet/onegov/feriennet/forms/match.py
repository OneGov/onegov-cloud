from onegov.feriennet import _
from onegov.feriennet.utils import scoring_from_match_settings
from onegov.form import Form
from wtforms.fields import BooleanField, RadioField


class MatchForm(Form):

    prefer_in_age_bracket = BooleanField(
        label=_("Children in the right age"),
        fieldset=_("Prefer the following children:"),
        default=False)

    prefer_organiser = BooleanField(
        label=_("Children of organisers"),
        fieldset=_("Prefer the following children:"),
        default=False)

    prefer_admins = BooleanField(
        label=_("Children of administrators"),
        fieldset=_("Prefer the following children:"),
        default=False)

    confirm = RadioField(
        label=_("Confirm matching:"),
        default='no',
        choices=[
            ('no', _("No, preview only")),
            ('yes', _("Yes, confirm matching"))
        ]
    )

    sure = BooleanField(
        label=_("I know the wishlist-phase ends as a result."),
        default=False,
        depends_on=('confirm', 'yes')
    )

    def scoring(self, session):
        return scoring_from_match_settings(session, self.match_settings)

    @property
    def confirm_period(self):
        return self.confirm.data == 'yes' and self.sure.data is True

    @property
    def match_settings(self):
        return {
            k: v for k, v in self.data.items() if k not in (
                'csrf_token',
                'confirm',
                'sure',
            )
        }

    def store_to_period(self, period):
        period.data['match-settings'] = self.match_settings

    def load_from_period(self, period):
        if 'match-settings' in period.data:
            for key, value in period.data['match-settings'].items():
                if hasattr(self, key):
                    getattr(self, key).data = value
