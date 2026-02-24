from __future__ import annotations

import sedate

from datetime import datetime, date
from onegov.core.collection import GenericCollection, Pagination
from onegov.org.models.file import BaseImageFileCollection
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportFile
from onegov.winterthur.models import MissionReportVehicle
from sqlalchemy import and_, or_, desc, func


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.abstract.associable import RegisteredLink
    from sqlalchemy.orm import Query, Session
    from typing import Self
    from typing import TypeVar
    from uuid import UUID

    T = TypeVar('T')


class MissionReportFileCollection(BaseImageFileCollection[MissionReportFile]):

    def __init__(self, session: Session, report: MissionReport):
        super().__init__(
            session,
            type='mission-report-file',
            allow_duplicates=False
        )
        self.report = report

    @property
    def id(self) -> UUID:
        return self.report.id

    @property
    def association(self) -> RegisteredLink:
        assert MissionReportFile.registered_links is not None
        return MissionReportFile.registered_links['linked_mission_reports']

    if not TYPE_CHECKING:
        # NOTE: We don't want to change the signature of add, but we also
        #       don't want to duplicate it, so we just skip type checking
        #       the implementation, since it is trivial
        def add(self, *args, **kwargs):
            file = super().add(*args, **kwargs)
            self.report.pictures.append(file)

            return file

    def query(self) -> Query[MissionReportFile]:
        query = super().query()
        table = self.association.table

        query = query.filter(MissionReportFile.id.in_(
            self.session.query(table)
                .with_entities(table.c.missionreportfile_id)
                .filter(table.c.mission_reports_id == self.report.id)
                .scalar_subquery()
        ))

        return query


class MissionReportCollection(
    GenericCollection[MissionReport],
    Pagination[MissionReport]
):

    def __init__(
        self,
        session: Session,
        page: int = 0,
        include_hidden: bool = False,
        year: int | None = None
    ) -> None:
        self.session = session
        self.page = page
        self.include_hidden = include_hidden
        self.year = year or date.today().year

    @property
    def model_class(self) -> type[MissionReport]:
        return MissionReport

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.page == other.page

    def by_id(
        self,
        id: UUID  # type:ignore[override]
    ) -> MissionReport | None:
        # use the parent to get a report by id, so the date filter is
        # not included, which is not desirable on this lookup
        return super().query().filter(self.primary_key == id).first()

    def query(self) -> Query[MissionReport]:
        # default behavior is to show the current year
        return self.query_current_year()

    def query_all(self) -> Query[MissionReport]:
        query = super().query()

        if not self.include_hidden:
            query = query.filter(or_(
                MissionReport.meta['access'] == 'public',
                MissionReport.meta['access'] == None
            ))

        return query.order_by(desc(MissionReport.date))

    def query_current_year(self) -> Query[MissionReport]:
        return self.filter_by_year(self.query_all())

    def subset(self) -> Query[MissionReport]:
        return self.query()

    @property
    def page_index(self) -> int:
        return self.page

    def page_by_index(self, index: int) -> Self:
        return self.__class__(self.session, page=index, year=self.year)

    def filter_by_year(self, query: Query[T]) -> Query[T]:
        timezone = 'Europe/Zurich'

        start = sedate.replace_timezone(datetime(self.year, 1, 1), timezone)
        end = sedate.replace_timezone(datetime(self.year + 1, 1, 1), timezone)

        return query.filter(and_(
            start <= MissionReport.date, MissionReport.date < end
        ))

    def mission_count(self) -> int | None:
        """ The mission count, including hidden missions. """
        query = self.filter_by_year(super().query())
        return query.with_entities(
            func.sum(MissionReport.mission_count)).scalar()


class MissionReportVehicleCollection(GenericCollection[MissionReportVehicle]):

    @property
    def model_class(self) -> type[MissionReportVehicle]:
        return MissionReportVehicle

    def query(self) -> Query[MissionReportVehicle]:
        return super().query().order_by(MissionReportVehicle.name)
