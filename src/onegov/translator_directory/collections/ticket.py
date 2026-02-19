from __future__ import annotations

from onegov.org.models.ticket import (
    FilteredTicketCollection,
    FilteredArchivedTicketCollection,
)
from onegov.ticket import Ticket
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.user import UserGroup
from sqlalchemy import and_, or_
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Query

    from onegov.translator_directory.request import TranslatorAppRequest


class TimeReportTicketFilterMixin:
    """Mixin for filtering tickets by finanzstelle."""

    session: Any
    request: Any

    def _apply_finanzstelle_filter(
        self, query: Query[Ticket]
    ) -> Query[Ticket]:
        """Filter TimeReportTickets by finanzstelle, leave other tickets
        unaffected.
        """
        user_finanzstelles = []
        groups = (
            self.session.query(UserGroup)
            .filter(UserGroup.meta['finanzstelle'].astext.isnot(None))
            .all()
        )

        for group in groups:
            accountant_emails = group.meta.get('accountant_emails', [])
            if (
                self.request
                and self.request.current_user
                and self.request.current_user.username in accountant_emails
            ):
                finanzstelle = group.meta.get('finanzstelle')
                if finanzstelle:
                    user_finanzstelles.append(finanzstelle)

        if not user_finanzstelles:
            return query

        time_report_ids = (
            self.session.query(TranslatorTimeReport.id)
            .filter(TranslatorTimeReport.finanzstelle.in_(user_finanzstelles))
            .all()
        )
        time_report_id_strs = [str(tr_id[0]) for tr_id in time_report_ids]

        query = query.filter(
            or_(
                Ticket.handler_code != 'TRP',
                and_(
                    Ticket.handler_code == 'TRP',
                    Ticket.handler_data['handler_data'][
                        'time_report_id'
                    ].astext.in_(time_report_id_strs),
                ),
            )
        )

        return query


class TimeReportFilteredTicketCollection(
    TimeReportTicketFilterMixin, FilteredTicketCollection
):
    """Ticket collection that filters TimeReportTickets by finanzstelle.

    Non-admin users can only see tickets for time reports where they are
    listed as an accountant in the associated finanzstelle user group.
    """

    def __init__(
        self,
        session: Any,
        page: int = 0,
        state: str = 'open',
        handler: str = 'ALL',
        group: str | None = None,
        owner: str = '*',
        submitter: str = '*',
        term: str | None = None,
        extra_parameters: dict[str, Any] | None = None,
        request: TranslatorAppRequest | None = None,
    ) -> None:
        super().__init__(
            session,
            page,
            state,  # type: ignore[arg-type]
            handler,
            group,
            owner,
            submitter,
            term,
            extra_parameters,
            request,
        )

    def subset(self) -> Query[Ticket]:
        query = super().subset()

        if (
            not self.request
            or (not self.request.current_user)
        ):
            return query

        query = self._apply_finanzstelle_filter(query)
        return query


class TimeReportFilteredArchivedTicketCollection(
    TimeReportTicketFilterMixin, FilteredArchivedTicketCollection
):
    """Archived ticket collection that filters TimeReportTickets by
    finanzstelle.

    Non-admin users can only see archived tickets for time reports where
    they are listed as an accountant in the associated finanzstelle user
    group.
    """

    def __init__(
        self,
        session: Any,
        page: int = 0,
        state: str = 'archived',
        handler: str = 'ALL',
        group: str | None = None,
        owner: str = '*',
        submitter: str = '*',
        term: str | None = None,
        extra_parameters: dict[str, Any] | None = None,
        request: TranslatorAppRequest | None = None,
    ) -> None:
        super().__init__(
            session,
            page,
            state,  # type: ignore[arg-type]
            handler,
            group,
            owner,
            submitter,
            term,
            extra_parameters,
            request,
        )

    def subset(self) -> Query[Ticket]:
        query = super().subset()

        if (
            not self.request
            or (not self.request.current_user)
        ):
            return query

        query = self._apply_finanzstelle_filter(query)
        return query
