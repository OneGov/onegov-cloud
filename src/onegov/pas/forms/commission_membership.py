from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.pas import _
from onegov.pas.collections import CommissionCollection
from onegov.pas.collections import ParliamentarianCollection
from onegov.pas.models.commission_membership import ROLES
from wtforms.fields import DateField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class CommissionMembershipForm(Form):

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
    )

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Function'),
        choices=list(ROLES.items()),
        validators=[InputRequired()],
        default='member'
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        default=date.today
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    def on_request(self) -> None:
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in CommissionCollection(self.request.session).query()
        ]
        self.parliamentarian_id.choices = [
            (parliamentarian.id, parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(self.request.session).query()
        ]
