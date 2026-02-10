from __future__ import annotations

from onegov.core.collection import GenericCollection, Pagination
from onegov.translator_directory.models.time_report import (
    TranslatorTimeReport,
)
from onegov.user import UserGroup
from sqlalchemy import desc


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp
    from onegov.translator_directory.request import TranslatorAppRequest
    from sqlalchemy.orm import Query
    from typing import Self


class TimeReportCollection(
    GenericCollection[TranslatorTimeReport], Pagination[TranslatorTimeReport]
):

    batch_size = 20

    def __init__(
        self,
        app: TranslatorDirectoryApp,
        page: int = 0,
        archive: bool = False,
    ) -> None:
        super().__init__(app.session())
        self.app = app
        self.page = page
        self.archive = archive

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, self.__class__)
            and self.page == other.page
            and self.archive == other.archive
        )

    def query(self) -> Query[TranslatorTimeReport]:
        q = self.session.query(TranslatorTimeReport)
        if self.archive:
            q = q.filter(TranslatorTimeReport.exported == True)
        else:
            q = q.filter(TranslatorTimeReport.exported == False)
        return q.order_by(desc(TranslatorTimeReport.assignment_date))

    @property
    def page_index(self) -> int:
        return self.page

    def subset(self) -> Query[TranslatorTimeReport]:
        return self.query()

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.app, index, self.archive)

    def _get_user_finanzstelles(
        self, request: TranslatorAppRequest
    ) -> list[str]:
        """Get finanzstelles where user is listed as accountant.

        Returns finanzstelles regardless of admin status - if an admin
        is in a user group with finanzstelle, that should be honored.
        """
        if not request.current_user:
            return []

        user_finanzstelles = []
        groups = (
            self.session.query(UserGroup)
            .filter(UserGroup.meta['finanzstelle'].astext.isnot(None))
            .all()
        )

        for group in groups:
            accountant_emails = group.meta.get('accountant_emails', [])
            if request.current_user.username in accountant_emails:
                finanzstelle = group.meta.get('finanzstelle')
                if finanzstelle:
                    user_finanzstelles.append(finanzstelle)

        return user_finanzstelles

    def _apply_finanzstelle_filter(
        self,
        query: Query[TranslatorTimeReport],
        request: TranslatorAppRequest,
    ) -> Query[TranslatorTimeReport]:
        """Apply finanzstelle filter based on user's group membership.

        If user is in finanzstelle groups: filter by those finanzstelles.
        If user is not in any groups but is admin: show all (no filter).
        """
        user_finanzstelles = self._get_user_finanzstelles(request)
        if user_finanzstelles:
            query = query.filter(
                TranslatorTimeReport.finanzstelle.in_(user_finanzstelles)
            )
        return query

    def for_accounting_export(
        self, request: TranslatorAppRequest | None = None
    ) -> Query[TranslatorTimeReport]:
        """Query confirmed but not yet exported time reports.

        Filters by user's finanzstelle groups if they are in any.
        If user is in finanzstelle groups (admin or not): filter applied.
        If user is admin but not in any groups: show all.
        """
        query = (
            self.session.query(TranslatorTimeReport)
            .filter(TranslatorTimeReport.status == 'confirmed')
            .filter(TranslatorTimeReport.exported == False)
        )

        if not request:
            return query

        return self._apply_finanzstelle_filter(query, request)
