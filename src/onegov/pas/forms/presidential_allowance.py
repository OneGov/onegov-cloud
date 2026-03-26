from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.pas import _
from onegov.pas.models import PASParliamentarianRole, SettlementRun
from onegov.pas.models.presidential_allowance import (
    ALLOWANCE_ROLES,
    PRESIDENT_QUARTERLY,
    PRESIDENT_YEARLY_ALLOWANCE,
    VICE_PRESIDENT_QUARTERLY,
    VICE_PRESIDENT_YEARLY_ALLOWANCE,
    PresidentialAllowance,
)
from uuid import UUID
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired, NumberRange

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any


YEARLY_LIMITS: dict[str, int] = {
    'president': PRESIDENT_YEARLY_ALLOWANCE,
    'vice_president': VICE_PRESIDENT_YEARLY_ALLOWANCE,
}

QUARTERLY_AMOUNTS: dict[str, int] = {
    'president': PRESIDENT_QUARTERLY,
    'vice_president': VICE_PRESIDENT_QUARTERLY,
}


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

    recipient = ChosenSelectField(
        label=_('Recipient'),
        validators=[InputRequired()],
    )

    def _role_holder_choices(self) -> list[Any]:
        today = date.today()
        choices: list[tuple[str, str]] = []
        for role_key, role_label in ALLOWANCE_ROLES.items():
            roles = (
                self.request.session.query(PASParliamentarianRole)
                .filter(
                    PASParliamentarianRole.role == role_key,
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
            translated = self.request.translate(role_label)
            for r in roles:
                value = f'{r.parliamentarian_id}:{role_key}'
                label = f'{r.parliamentarian.title} ({translated})'
                choices.append((value, label))
        return choices

    def on_request(self) -> None:
        self.recipient.choices = self._role_holder_choices()

        if self.submitted(self.request):
            return

        self.year.data = self.year.data or date.today().year

    @property
    def current_settlement_run(
        self,
    ) -> SettlementRun | None:
        return (
            self.request.session.query(SettlementRun)
            .filter(SettlementRun.closed.is_(False))
            .order_by(SettlementRun.end.desc())
            .first()
        )

    def _yearly_total(self, year: int, role: str) -> int:
        total = (
            self.request.session.query(PresidentialAllowance)
            .filter(
                PresidentialAllowance.year == year,
                PresidentialAllowance.role == role,
            )
            .with_entities(PresidentialAllowance.amount)
            .all()
        )
        return sum(row[0] for row in total)

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

        _parl_id, role = self.parsed_recipient
        amount = QUARTERLY_AMOUNTS[role]
        limit = YEARLY_LIMITS[role]
        existing = self._yearly_total(year, role)

        if existing + amount > limit:
            role_label = self.request.translate(ALLOWANCE_ROLES[role])
            remaining = limit - existing
            assert isinstance(self.recipient.errors, list)
            self.recipient.errors.append(
                _(
                    'Yearly limit for ${role} is CHF'
                    ' ${limit}. Already allocated:'
                    ' CHF ${existing}. Remaining:'
                    ' CHF ${remaining}.',
                    mapping={
                        'role': role_label,
                        'limit': str(limit),
                        'existing': str(existing),
                        'remaining': str(remaining),
                    },
                )
            )
            return False

        existing_quarter = (
            self.request.session.query(PresidentialAllowance)
            .filter(
                PresidentialAllowance.year == year,
                PresidentialAllowance.quarter == quarter,
                PresidentialAllowance.role == role,
            )
            .first()
        )
        if existing_quarter is not None:
            assert isinstance(self.quarter.errors, list)
            self.quarter.errors.append(
                _(
                    'Allowance for Q${quarter}'
                    ' ${year} already exists'
                    ' for this role',
                    mapping={
                        'quarter': str(quarter),
                        'year': str(year),
                    },
                )
            )
            return False

        return True

    @property
    def parsed_recipient(self) -> tuple[UUID, str]:
        value = self.recipient.data
        parl_id, role = value.rsplit(':', 1)
        return UUID(parl_id), role
