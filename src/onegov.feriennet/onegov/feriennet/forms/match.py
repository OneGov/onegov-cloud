from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import Scoring
from onegov.feriennet import _
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
        scoring = Scoring()

        if self.prefer_in_age_bracket.data:
            scoring.criteria.append(
                PreferInAgeBracket.from_session(session))

        if self.prefer_organiser.data:
            scoring.criteria.append(
                PreferOrganiserChildren.from_session(session))

        if self.prefer_admins.data:
            scoring.criteria.append(
                PreferAdminChildren.from_session(session))

        return scoring

    @property
    def confirm_period(self):
        return self.confirm.data == 'yes' and self.sure.data is True

    def store_to_period(self, period):
        period.data['match-settings'] = {
            k: v for k, v in self.data.items() if k not in (
                'csrf_token',
                'confirm',
                'sure',
            )
        }

    def load_from_period(self, period):
        if 'match-settings' in period.data:
            for key, value in period.data['match-settings'].items():
                if hasattr(self, key):
                    getattr(self, key).data = value
