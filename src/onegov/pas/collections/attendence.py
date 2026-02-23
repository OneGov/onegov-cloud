from __future__ import annotations

from sqlalchemy import desc, or_
from sqlalchemy.orm import joinedload

from onegov.core.collection import GenericCollection
from onegov.pas.models import (
    Attendence,
    PASParliamentarian,
    PASParliamentarianRole,
    SettlementRun,
)

from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Query, Session
    from onegov.pas.request import PasRequest


class AttendenceCollection(GenericCollection[Attendence]):
    def __init__(
        self,
        session: Session,
        settlement_run_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        type: str | None = None,
        parliamentarian_id: str | None = None,
        commission_id: str | None = None,
        party_id: str | None = None,  # New parameter
    ):
        super().__init__(session)
        self.settlement_run_id = settlement_run_id
        self.date_from = date_from
        self.date_to = date_to
        self.type = type
        self.parliamentarian_id = parliamentarian_id
        self.commission_id = commission_id
        self.party_id = party_id

    @property
    def model_class(self) -> type[Attendence]:
        return Attendence

    def query(self) -> Query[Attendence]:
        query = super().query()

        # Eagerly load related data to prevent N+1 queries
        query = query.options(
            joinedload(Attendence.parliamentarian).joinedload(PASParliamentarian.roles),
            joinedload(Attendence.commission)
        )

        if self.settlement_run_id:
            settlement_run = self.session.get(
                SettlementRun,
                self.settlement_run_id
            )
            if settlement_run:
                query = query.filter(
                    Attendence.date >= settlement_run.start,
                    Attendence.date <= settlement_run.end,
                    )

        if self.date_from:
            query = query.filter(Attendence.date >= self.date_from)
        if self.date_to:
            query = query.filter(Attendence.date <= self.date_to)
        if self.type:
            query = query.filter(Attendence.type == self.type)
        if self.parliamentarian_id:
            query = query.filter(
                Attendence.parliamentarian_id == self.parliamentarian_id
            )
        if self.commission_id:
            query = query.filter(
                Attendence.commission_id == self.commission_id
            )

        # Check for any overlap in party membership period
        if self.party_id:
            query = (
                query.join(Attendence.parliamentarian)
                .join(PASParliamentarian.roles)
                .filter(
                    PASParliamentarianRole.party_id == self.party_id,
                    or_(
                        PASParliamentarianRole.start.is_(None),
                        PASParliamentarianRole.start <= Attendence.date
                    ),
                    or_(
                        PASParliamentarianRole.end.is_(None),
                        PASParliamentarianRole.end >= Attendence.date
                    )
                )
            )

        return query.order_by(desc(Attendence.date))

    def for_filter(
        self,
        settlement_run_id: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        type: str | None = None,
        parliamentarian_id: str | None = None,
        commission_id: str | None = None,
        party_id: str | None = None,  # New parameter
    ) -> Self:
        return self.__class__(
            self.session,
            settlement_run_id=settlement_run_id,
            date_from=date_from,
            date_to=date_to,
            type=type,
            parliamentarian_id=parliamentarian_id,
            commission_id=commission_id,
            party_id=party_id,
        )

    def by_party(
        self,
        party_id: str,
        start_date: date,
        end_date: date
    ) -> Self:
        """
        Filter attendances by party membership during a period.
        Returns attendances where the parliamentarian belonged to the party
        at any point during the period.
        """
        return self.for_filter(
            settlement_run_id=self.settlement_run_id,
            date_from=start_date,
            date_to=end_date,
            type=self.type,
            parliamentarian_id=self.parliamentarian_id,
            commission_id=self.commission_id,
            party_id=party_id,
        )

    def for_parliamentarian(self, parliamentarian_id: str) -> Self:
        """Returns attendances for a specific parliamentarian only."""
        return self.for_filter(parliamentarian_id=parliamentarian_id)

    def for_commission_president(
        self,
        parliamentarian_id: str,
        active_commission_ids: list[str]
    ) -> Query[Attendence]:
        """
        Returns attendances for a commission president:
        - Their own attendances
        - Attendances of members in commissions they preside over
        """
        query = self.query()
        return query.filter(
            (Attendence.parliamentarian_id == parliamentarian_id) |
            (Attendence.commission_id.in_(active_commission_ids))
        )

    def view_for_parliamentarian(
        self, request: PasRequest
    ) -> list[Attendence]:
        """
        Returns filtered attendances based on user role and permissions.
        This encapsulates the filtering logic previously in the view.
        """
        user = request.current_user

        if not request.is_parliamentarian:
            # Admins see all attendances
            return self.query().all()

        if not (user and hasattr(user, 'parliamentarian') and
                user.parliamentarian):
            return []

        parliamentarian = user.parliamentarian

        if user.role == 'commission_president':
            from datetime import date
            # Commission presidents see own + commission members' attendances
            # We have to check all but usually president of just one
            active_presidencies = [
                cm.commission_id
                for cm in parliamentarian.commission_memberships
                if (cm.role == 'president' and
                    (cm.end is None or cm.end >= date.today()))
            ]

            if active_presidencies:
                return self.for_commission_president(
                    str(parliamentarian.id),
                    active_presidencies
                ).all()
            else:
                # Fallback to own attendances only
                return self.for_parliamentarian(
                    str(parliamentarian.id)
                ).query().all()
        else:
            # Regular parliamentarians see only their own attendances
            return self.for_parliamentarian(
                str(parliamentarian.id)
            ).query().all()
