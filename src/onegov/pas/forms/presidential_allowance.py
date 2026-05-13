from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.pas import _
from onegov.pas.models import PASParliamentarianRole, SettlementRun
from onegov.pas.models.presidential_allowance import (
    ALLOWANCE_ROLES,
    MAX_ALLOWANCES_PER_RUN,
    PRESIDENT_QUARTERLY,
    PRESIDENT_YEARLY_ALLOWANCE,
    VICE_PRESIDENT_QUARTERLY,
    VICE_PRESIDENT_YEARLY_ALLOWANCE,
    PresidentialAllowance,
)
from sqlalchemy import extract, func
from uuid import UUID
from wtforms.validators import InputRequired

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

    settlement_run = ChosenSelectField(
        label=_('Settlement run'),
        validators=[InputRequired()],
    )

    recipient = ChosenSelectField(
        label=_('Recipient'),
        validators=[InputRequired()],
    )

    def _settlement_run_choices(self) -> list[Any]:
        runs = (
            self.request.session.query(SettlementRun)
            .filter(SettlementRun.closed.is_(False))
            .order_by(SettlementRun.end.desc())
            .all()
        )
        return [(str(r.id), r.name) for r in runs]

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
        self.settlement_run.choices = self._settlement_run_choices()
        self.recipient.choices = self._role_holder_choices()

    def _yearly_total(self, year: int, role: str) -> int:
        total = (
            self.request.session.query(
                func.coalesce(
                    func.sum(PresidentialAllowance.amount),
                    0,
                )
            )
            .join(SettlementRun)
            .filter(
                extract('year', SettlementRun.end) == year,
                PresidentialAllowance.role == role,
            )
            .scalar()
        )
        return int(total)

    def _count_for_run(self, run_id: UUID) -> int:
        return (
            self.request.session.query(PresidentialAllowance)
            .filter(
                PresidentialAllowance.settlement_run_id == run_id,
            )
            .count()
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

        run_id = UUID(self.settlement_run.data)
        _parl_id, role = self.parsed_recipient
        amount = QUARTERLY_AMOUNTS[role]
        limit = YEARLY_LIMITS[role]

        count = self._count_for_run(run_id)
        if count >= MAX_ALLOWANCES_PER_RUN:
            assert isinstance(self.settlement_run.errors, list)
            self.settlement_run.errors.append(
                _(
                    'Maximum of ${max} allowances per'
                    ' settlement run reached.',
                    mapping={
                        'max': str(MAX_ALLOWANCES_PER_RUN),
                    },
                )
            )
            return False

        run = (
            self.request.session.query(SettlementRun)
            .filter(SettlementRun.id == run_id)
            .one()
        )
        year = run.end.year
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

        return True

    @property
    def parsed_recipient(self) -> tuple[UUID, str]:
        value = self.recipient.data
        parl_id, role = value.rsplit(':', 1)
        return UUID(parl_id), role
