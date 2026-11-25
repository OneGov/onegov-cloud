from datetime import date
from onegov.pas.custom import has_user_set_abschluss_for_commission
from onegov.pas.models import (
    Attendence,
    PASCommissionMembership,
    SettlementRun,
)
from onegov.pas.i18n import _
from onegov.pas.utils import is_parliamentarian
from functools import cached_property
from onegov.town6.request import TownRequest

from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID
    from onegov.pas.app import PasApp
    from onegov.pas.models import PASParliamentarian


AppT = TypeVar('AppT', bound='PasApp', default='PasApp', covariant=True)


class PasRequest(TownRequest[AppT]):

    @cached_property
    def is_parliamentarian(self) -> bool:
        return is_parliamentarian(self.current_user)

    @cached_property
    def has_commission_president_role(self) -> bool:
        user = self.current_user
        if not user:
            return False
        return user.role == 'commission_president'

    @cached_property
    def current_parliamentarian(self) -> PASParliamentarian | None:
        if (self.current_user
            and hasattr(self.current_user, 'parliamentarian')
            and self.current_user.parliamentarian):
            return self.current_user.parliamentarian
        return None

    def warn_no_parliamentarian(self) -> bool:
        if (
            self.current_user
            and self.current_user.role
            in ('parliamentarian', 'commission_president')
            and not self.current_parliamentarian
        ):
            self.warning(
                _(
                    'Your user account is not linked '
                    'to a parliamentarian record. '
                    'Please contact an administrator.'
                )
            )
            return True
        return False

    def can_edit_commission_attendance(
        self,
        attendance_date: date,
        commission_id: UUID | None,
        parliamentarian_id: UUID,
    ) -> bool:
        if self.is_admin:
            return True
        president = self.current_parliamentarian
        if not self.has_commission_president_role or president is None:
            return False
        if commission_id is None:
            return False
        if not any(
            membership.commission_id == commission_id
            for membership in president.commission_memberships_on(
                on_date=date.today(), role='president'
            )
        ):
            return False
        memberships = self.session.query(PASCommissionMembership).filter_by(
            commission_id=commission_id,
            parliamentarian_id=parliamentarian_id,
        )
        if not any(m.is_active_on(date.today()) for m in memberships):
            return False
        run = (
            self.session.query(SettlementRun)
            .filter(
                SettlementRun.start <= attendance_date,
                SettlementRun.end >= attendance_date,
            )
            .first()
        )
        if run is None or run.closed:
            return False
        return not any(
            has_user_set_abschluss_for_commission(
                self.session, person_id, commission_id, attendance_date
            )
            for person_id in {president.id, parliamentarian_id}
        )

    def can_edit_attendence(self, attendence: Attendence) -> bool:
        if self.is_admin:
            return True
        records = (
            self.session.query(Attendence)
            .filter_by(bulk_edit_id=attendence.bulk_edit_id)
            .all()
            if attendence.bulk_edit_id
            else [attendence]
        )
        return all(
            record.type != 'plenary'
            and self.can_edit_commission_attendance(
                record.date, record.commission_id, record.parliamentarian_id
            )
            for record in records
        )
