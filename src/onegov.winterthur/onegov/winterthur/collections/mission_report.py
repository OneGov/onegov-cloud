import sedate

from datetime import datetime
from onegov.core.collection import GenericCollection, Pagination
from onegov.org.models.file import ImageFileCollection
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportFile
from onegov.winterthur.models import MissionReportVehicle
from sqlalchemy import and_, or_, desc


class MissionReportFileCollection(ImageFileCollection):

    def __init__(self, session, report):
        super().__init__(session)
        self.type = 'mission-report-file'
        self.report = report

    @property
    def id(self):
        return self.report.id

    @property
    def association(self):
        return MissionReportFile.registered_links['linked_mission_reports']

    def add(self, *args, **kwargs):
        file = super().add(*args, **kwargs)
        self.report.pictures.append(file)

        return file

    def query(self):
        query = super().query()
        table = self.association.table

        query = query.filter(MissionReportFile.id.in_(
            self.session.query(table)
                .with_entities(table.c.missionreportfile_id)
                .filter(table.c.mission_reports_id == self.report.id)
                .subquery()
        ))

        return query


class MissionReportCollection(GenericCollection, Pagination):

    def __init__(self, session, page=0, include_hidden=False):
        self.session = session
        self.page = page
        self.include_hidden = include_hidden

    @property
    def model_class(self):
        return MissionReport

    def __eq__(self, other):
        return self.page == other.page

    def query(self):
        query = super().query()

        if not self.include_hidden:
            query = query.filter(or_(
                MissionReport.meta['is_hidden_from_public'] == False,
                MissionReport.meta['is_hidden_from_public'] == None
            ))

        return query.order_by(desc(MissionReport.date))

    def subset(self):
        return self.query()

    @property
    def page_index(self):
        return self.page

    def page_by_index(self, index):
        return self.__class__(self.session, page=index)

    def mission_count(self, year):
        """ The mission count, including hidden missions. """

        timezone = 'Europe/Zurich'

        start = sedate.replace_timezone(datetime(year, 1, 1), timezone)
        end = sedate.replace_timezone(datetime(year + 1, 1, 1), timezone)

        return super().query().filter(and_(
            start <= MissionReport.date, MissionReport.date < end
        )).count()


class MissionReportVehicleCollection(GenericCollection):

    @property
    def model_class(self):
        return MissionReportVehicle

    def query(self):
        return super().query().order_by(MissionReportVehicle.name)
