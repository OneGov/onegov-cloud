from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.pas import _
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.models import PASParliamentarianRole, SettlementRun
from uuid import UUID
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired, NumberRange

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any


class PresidentialAllowanceForm(Form):

    year = IntegerField(
        label=_('Year'),
        validators=[InputRequired()],
    )

    quarter = IntegerField(
        label=_('Quarter'),
        validators=[
            InputRequired(), NumberRange(min=1, max=4)
        ],
    )

    president_id = ChosenSelectField(
        label=_('President'),
        validators=[InputRequired()],
    )

    vice_president_id = ChosenSelectField(
        label=_('Vice president'),
        validators=[InputRequired()],
    )

    def _role_holder_choices(
        self, role: str
    ) -> list[Any]:
        today = date.today()
        roles = (
            self.request.session.query(PASParliamentarianRole)
            .filter(
                PASParliamentarianRole.role == role,
                (
                    PASParliamentarianRole.start.is_(None)
                    | (PASParliamentarianRole.start <= today)
                ),
                (
                    PASParliamentarianRole.end.is_(None)
                    | (PASParliamentarianRole.end >= today)
                ),
            )
            .order_by(PASParliamentarianRole.start.desc())
            .all()
        )
        return [
            (
                str(r.parliamentarian_id),
                r.parliamentarian.title,
            )
            for r in roles
        ]

    def on_request(self) -> None:
        self.president_id.choices = (
            self._role_holder_choices('president')
        )
        self.vice_president_id.choices = (
            self._role_holder_choices('vice_president')
        )

        if self.submitted(self.request):
            return

        self.year.data = self.year.data or date.today().year

        collection = PresidentialAllowanceCollection(
            self.request.session
        )
        next_q = collection.next_quarter(self.year.data)
        self.quarter.data = self.quarter.data or next_q or 1

    @property
    def current_settlement_run(self) -> SettlementRun | None:
        return (
            self.request.session.query(SettlementRun)
            .filter(SettlementRun.closed.is_(False))
            .order_by(SettlementRun.end.desc())
            .first()
        )

    def validate(
        self,
        extra_validators: (
            Mapping[str, Sequence[Any]] | None
        ) = None,
    ) -> bool:
        result = super().validate(extra_validators)
        if not result:
            return False

        year = self.year.data
        quarter = self.quarter.data
        assert year is not None
        assert quarter is not None

        collection = PresidentialAllowanceCollection(
            self.request.session
        )
        if collection.quarter_exists(year, quarter):
            assert isinstance(self.quarter.errors, list)
            self.quarter.errors.append(
                _(
                    'Allowance for Q${quarter} ${year}'
                    ' already exists',
                    mapping={
                        'quarter': str(quarter),
                        'year': str(year),
                    },
                )
            )
            return False

        return True

    @property
    def president_uuid(self) -> UUID:
        return UUID(self.president_id.data)

    @property
    def vice_president_uuid(self) -> UUID:
        return UUID(self.vice_president_id.data)
