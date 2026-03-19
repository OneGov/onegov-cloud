from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.pas import _
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.models import SettlementRun
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any


class PresidentialAllowanceForm(Form):

    year = IntegerField(
        label=_('Year'),
        validators=[InputRequired()],
        default=date.today().year,
    )

    def on_request(self) -> None:
        if not self.submitted(self.request):
            self.year.data = self.year.data or date.today().year

    @property
    def current_settlement_run(self) -> SettlementRun | None:
        """Return the most recent open settlement run."""
        return (
            self.request.session.query(SettlementRun)
            .filter(SettlementRun.closed.is_(False))
            .order_by(SettlementRun.end.desc())
            .first()
        )

    def validate(
        self,
        extra_validators: Mapping[str, Sequence[Any]] | None = None,
    ) -> bool:
        result = super().validate(extra_validators)
        if not result:
            return False

        collection = PresidentialAllowanceCollection(self.request.session)
        if not collection.can_add(
            self.year.data  # type:ignore[arg-type]
        ):
            assert isinstance(self.year.errors, list)
            self.year.errors.append(
                _('Maximum of 4 allowances per year already reached')
            )
            return False

        return True
