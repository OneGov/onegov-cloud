from onegov.activity.matching import PreferAdminChildren
from onegov.activity.matching import PreferInAgeBracket
from onegov.activity.matching import PreferOrganiserChildren
from onegov.activity.matching import Scoring
from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import BooleanField


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

    def store_to_period(self, period):
        period.data['match-settings'] = {
            k: v for k, v in self.data.items() if k != 'csrf_token'
        }

    def load_from_period(self, period):
        if 'match-settings' in period.data:
            for key, value in period.data['match-settings'].items():
                if hasattr(self, key):
                    getattr(self, key).data = value
