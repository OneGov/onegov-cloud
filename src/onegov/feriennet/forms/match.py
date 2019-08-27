from onegov.activity.matching.score import PreferAdminChildren
from onegov.activity.matching.score import PreferOrganiserChildren
from onegov.activity.matching.score import PreferGroups
from onegov.activity.matching.score import Scoring
from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import BooleanField, RadioField


class MatchForm(Form):

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

        # always prefer groups
        scoring.criteria.append(PreferGroups.from_session(session))

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

    def process_scoring(self, scoring):
        classes = {criterium.__class__ for criterium in scoring.criteria}
        self.prefer_organiser.data = PreferOrganiserChildren in classes
        self.prefer_admins.data = PreferAdminChildren in classes
