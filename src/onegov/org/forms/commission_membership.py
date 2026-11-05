from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import TranslatedSelectField
from onegov.form.utils import coerce_uuid
from onegov.parliament.collections import CommissionCollection
from onegov.parliament.collections import ParliamentarianCollection
from onegov.parliament.models.commission_membership import ROLES
from onegov.town6 import _
from wtforms.fields import DateField
from wtforms.fields import SelectChoice
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class CommissionMembershipForm(Form):

    commission_id = ChosenSelectField(
        label=_('Commission'),
        choices=lambda form, field: [
            SelectChoice(commission.id.hex, commission.title)
            for commission
            in CommissionCollection(form.request.session).query()
        ],
        coerce=coerce_uuid,
        validators=[InputRequired()],
    )

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        choices=lambda form, field: [
            SelectChoice(parliamentarian.id.hex, parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(form.request.session).query()
        ],
        coerce=coerce_uuid,
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Function'),
        choices=[
            SelectChoice(value, label)
            for value, label in ROLES.items()
        ],
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


class CommissionMembershipAddForm(Form):

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        choices=lambda form, field: [
            SelectChoice(parliamentarian.id.hex, parliamentarian.title)
            for parliamentarian
            in ParliamentarianCollection(form.request.session, [True]).query()
        ],
        coerce=coerce_uuid,
        validators=[InputRequired()],
    )

    role = TranslatedSelectField(
        label=_('Function'),
        choices=[
            SelectChoice(value, label)
            for value, label in ROLES.items()
        ],
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
