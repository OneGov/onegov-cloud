from __future__ import annotations

from sqlalchemy import desc, or_

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

        if self.settlement_run_id:
            settlement_run = self.session.query(SettlementRun).get(
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
