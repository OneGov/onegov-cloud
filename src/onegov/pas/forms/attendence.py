from __future__ import annotations

import datetime

from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import MultiCheckboxField
from onegov.pas import _
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.models import SettlementRun
from onegov.pas.models.attendence import TYPES
from wtforms.fields import DateField
from wtforms.fields import FloatField
from wtforms.fields import RadioField
from wtforms.validators import InputRequired

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.request import CoreRequest
    from onegov.pas.models import Attendence
    from typing import Any


class SettlementRunBoundMixin:

    if TYPE_CHECKING:
        # forward declaration of required attributes
        date: DateField
        request: CoreRequest

    def ensure_date(self) -> bool:
        if self.date.data:
            query = self.request.session.query(SettlementRun)
            query = query.filter(
                SettlementRun.active == True,
                SettlementRun.start <= self.date.data,
                SettlementRun.end >= self.date.data,
            )
            if not query.first():
                assert isinstance(self.date.errors, list)
                self.date.errors.append(
                    _('No within an active settlement run.')
                )
                return False

        return True


class AttendenceForm(Form, SettlementRunBoundMixin):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    type = RadioField(
        label=_('Type'),
        choices=list(TYPES.items()),
        validators=[InputRequired()],
        default='plenary'
    )

    parliamentarian_id = ChosenSelectField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
        depends_on=('type', '!plenary'),
    )

    def ensure_commission(self) -> bool:
        if (
            self.type.data
            and self.type.data != 'plenary'
            and self.commission_id.data
            and self.parliamentarian_id.data
        ):
            collection = PASParliamentarianCollection(self.request.session)
            parliamentarian = collection.by_id(self.parliamentarian_id.data)
            if parliamentarian:
                commission_ids = [
                    str(membership.commission_id)
                    for membership in parliamentarian.commission_memberships
                ]
                if self.commission_id.data not in commission_ids:
                    assert isinstance(self.commission_id.errors, list)
                    self.commission_id.errors.append(
                        _('Parliamentarian is not in this commission.')
                    )
                    return False

        return True

    def process_obj(self, obj: Attendence) -> None:  # type:ignore
        super().process_obj(obj)
        self.duration.data = obj.duration / 60

    def populate_obj(  # type: ignore[override]
        self,
        obj: Attendence,  # type: ignore[override]
        exclude: Collection[str] | None = None,
        include: Collection[str] | None = None
    ) -> None:
        super().populate_obj(obj, exclude, include)
        obj.commission_id = obj.commission_id or None
        obj.duration *= 60
        if obj.type == 'plenary':
            obj.commission_id = None

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['commission_id'] = result.get('commission_id') or None
        if result.get('type', '') == 'plenary':
            result['commission_id'] = None
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(self.request.session).query()
        ]
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in PASCommissionCollection(self.request.session).query()
        ]
        self.commission_id.choices.insert(0, ('', '-'))


class AttendenceAddForm(AttendenceForm):

    def on_request(self) -> None:
        super().on_request()
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian in PASParliamentarianCollection(
                self.request.session, [True]).query()
        ]


class AttendenceAddPlenaryForm(Form, SettlementRunBoundMixin):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (str(parliamentarian.id), parliamentarian.title)
            for parliamentarian
            in PASParliamentarianCollection(
                self.request.session, [True]).query()
        ]
        self.parliamentarian_id.data = [
            choice[0] for choice in self.parliamentarian_id.choices
        ]


class AttendenceAddCommissionBulkForm(Form, SettlementRunBoundMixin):
    """ Kind of like AttendenceAddPlenaryForm but for commissions. """

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    commission_id = ChosenSelectField(
        label=_('Commission'),
        validators=[InputRequired()],
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
        choices=[]  # are set with in custom.js
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['duration'] = int(60 * (result.get('duration') or 0))
        result['type'] = 'commission'
        return result

    def on_request(self) -> None:
        self.commission_id.choices = [
            (commission.id, commission.title)
            for commission
            in PASCommissionCollection(self.request.session).query()
        ]
        self.parliamentarian_id.data = [
            choice[0] for choice in self.parliamentarian_id.choices
        ]


class AttendenceAddCommissionForm(Form, SettlementRunBoundMixin):

    date = DateField(
        label=_('Date'),
        validators=[InputRequired()],
        default=datetime.date.today
    )

    duration = FloatField(
        label=_('Duration in hours'),
        validators=[InputRequired()],
    )

    type = RadioField(
        label=_('Type'),
        choices=[
            (key, value) for key, value in TYPES.items() if key != 'plenary'
        ],
        validators=[InputRequired()],
        default='commission'
    )

    parliamentarian_id = MultiCheckboxField(
        label=_('Parliamentarian'),
        validators=[InputRequired()],
    )

    def get_useful_data(self) -> dict[str, Any]:  # type:ignore[override]
        result = super().get_useful_data()
        result['commission_id'] = self.model.id
        result['duration'] = int(60 * (result.get('duration') or 0))
        return result

    def on_request(self) -> None:
        self.parliamentarian_id.choices = [
            (
                str(membership.parliamentarian.id),
                membership.parliamentarian.title
            )
            for membership in self.model.memberships
        ]
        self.parliamentarian_id.data = [
            choice[0] for choice in self.parliamentarian_id.choices
        ]
