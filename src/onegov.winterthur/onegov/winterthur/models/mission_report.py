from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.file import File
from onegov.org.models import HiddenFromPublicExtension
from sedate import to_timezone
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import Text
from sqlalchemy.orm import relationship
from uuid import uuid4


class MissionReportFile(File):
    __mapper_args__ = {'polymorphic_identity': 'mission-report-file'}


class MissionReport(Base, ContentMixin, HiddenFromPublicExtension):

    __tablename__ = 'mission_reports'

    #: the public id of the mission_report
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the date of the report
    date = Column(UTCDateTime, nullable=False)

    #: how long the mission lasted, in hours
    duration = Column(Numeric(precision=6, scale=2), nullable=False)

    #: the nature of the mission
    nature = Column(Text, nullable=False)

    #: the location of the mission
    location = Column(Text, nullable=False)

    #: actually active personnel
    personnel = Column(Integer, nullable=False)

    #: backup personnel
    backup = Column(Integer, nullable=False)

    #: the Zivilschutz was involved
    civil_defence = Column(Boolean, nullable=False, default=False)

    #: the vehicle use of the mission report
    used_vehicles = relationship(
        'MissionReportVehicleUse',
        cascade="all, delete-orphan")

    #: pictures of the mission
    pictures = associated(MissionReportFile, 'pictures', 'one-to-many')

    @property
    def title(self):
        return self.nature

    @property
    def readable_duration(self):
        return str(self.duration).rstrip('.0') + 'h'

    @property
    def local_date(self):
        return to_timezone(self.date, 'Europe/Zurich')


class MissionReportVehicle(Base, ContentMixin, HiddenFromPublicExtension):

    __tablename__ = 'mission_report_vehicles'

    #: the public id of the vehicle
    id = Column(UUID, nullable=False, primary_key=True, default=uuid4)

    #: the short id of the vehicle
    name = Column(Text, nullable=False)

    #: the longer name of the vehicle
    description = Column(Text, nullable=False)

    #: symbol of the vehicle
    symbol = associated(MissionReportFile, 'symbol', 'one-to-one')

    #: a website describing the vehicle
    website = Column(Text, nullable=True)

    uses = relationship('MissionReportVehicleUse')

    @property
    def title(self):
        return f'{self.name} - {self.description}'

    @property
    def readable_website(self):
        if self.website:
            return self.website.replace('https://', '').replace('http://', '')


class MissionReportVehicleUse(Base):
    """ Many to many association between vehicles and reports. """

    __tablename__ = 'mission_report_vehicle_usees'

    mission_report_id = Column(
        UUID,
        ForeignKey('mission_reports.id'),
        primary_key=True)

    mission_report = relationship('MissionReport')

    vehicle_id = Column(
        UUID,
        ForeignKey('mission_report_vehicles.id'),
        primary_key=True)

    vehicle = relationship('MissionReportVehicle')

    # vehicles may be used multiple times in a single mission_report
    count = Column(
        Integer,
        nullable=False,
        default=1)
