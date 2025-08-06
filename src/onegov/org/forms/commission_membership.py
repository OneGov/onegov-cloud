from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.parliament.models.commission_membership import ROLES
from onegov.pas import _
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
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
        validators=[Optional()],
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
            in PASCommissionCollection(self.request.session).query()
        ]
        self.parliamentarian_id.choices = [
            (parliamentarian.id, parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(self.request.session).query()
        ]


class CommissionMembershipAddForm(CommissionMembershipForm):

    def on_request(self) -> None:
        self.delete_field('commission_id')
        self.parliamentarian_id.choices = [
            (parliamentarian.id, parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(self.request.session, True).query()
        ]
