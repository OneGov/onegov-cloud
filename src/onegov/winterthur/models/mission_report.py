from __future__ import annotations

from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.types import UUID, UTCDateTime
from onegov.file import File
from onegov.org.models import AccessExtension
from sedate import to_timezone
from sqlalchemy import (
    Boolean, Column, ForeignKey, Integer, Numeric, Text, Enum
)
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from datetime import datetime
    from decimal import Decimal
    from typing import TypeAlias

    MissionType: TypeAlias = Literal['single', 'multi']

MISSION_TYPES: tuple[MissionType, ...] = ('single', 'multi')


class MissionReportFile(File):
    __mapper_args__ = {'polymorphic_identity': 'mission-report-file'}


class MissionReport(Base, ContentMixin, AccessExtension):

    __tablename__ = 'mission_reports'

    #: the public id of the mission_report
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the date of the report
    date: Column[datetime] = Column(UTCDateTime, nullable=False)

    #: how long the mission lasted, in hours
    duration: Column[Decimal] = Column(
        Numeric(precision=6, scale=2),
        nullable=False
    )

    #: the nature of the mission
    nature: Column[str] = Column(Text, nullable=False)

    #: the location of the mission
    location: Column[str] = Column(Text, nullable=False)

    #: actually active personnel
    personnel: Column[int] = Column(Integer, nullable=False)

    #: backup personnel
    backup: Column[int] = Column(Integer, nullable=False)

    #: the Zivilschutz was involved
    civil_defence: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    #: pictures of the mission
    pictures = associated(MissionReportFile, 'pictures', 'one-to-many')

    # The number of missions on the same site during a day
    mission_count: Column[int] = Column(Integer, nullable=False, default=1)

    # the mission type
    mission_type: Column[MissionType] = Column(
        Enum(*MISSION_TYPES, name='mission_type'),  # type:ignore[arg-type]
        nullable=False,
        default='single'
    )

    used_vehicles: relationship[list[MissionReportVehicleUse]] = (
        relationship(
            'MissionReportVehicleUse',
            cascade='all, delete-orphan',
            back_populates='mission_report'
        )
    )

    @property
    def title(self) -> str:
        return self.nature

    @property
    def readable_duration(self) -> str:
        return str(self.duration).rstrip('.0') + 'h'

    @property
    def local_date(self) -> datetime:
        return to_timezone(self.date, 'Europe/Zurich')


class MissionReportVehicle(Base, ContentMixin, AccessExtension):

    __tablename__ = 'mission_report_vehicles'

    #: the public id of the vehicle
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: the short id of the vehicle
    name: Column[str] = Column(Text, nullable=False)

    #: the longer name of the vehicle
    description: Column[str] = Column(Text, nullable=False)

    #: symbol of the vehicle
    symbol = associated(MissionReportFile, 'symbol', 'one-to-one')

    #: a website describing the vehicle
    website: Column[str | None] = Column(Text, nullable=True)

    uses: relationship[list[MissionReportVehicleUse]] = relationship(
        'MissionReportVehicleUse',
        back_populates='vehicle'
    )

    @property
    def title(self) -> str:
        return f'{self.name} - {self.description}'

    @property
    def readable_website(self) -> str | None:
        if self.website:
            return (self.website.removeprefix('http://')
                                .removeprefix('https://'))
        return None


class MissionReportVehicleUse(Base):
    """ Many to many association between vehicles and reports. """

    __tablename__ = 'mission_report_vehicle_usees'

    mission_report_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('mission_reports.id'),
        primary_key=True
    )

    mission_report: relationship[MissionReport] = relationship(
        MissionReport,
        back_populates='used_vehicles'
    )

    vehicle_id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey('mission_report_vehicles.id'),
        primary_key=True
    )

    vehicle: relationship[MissionReportVehicle] = relationship(
        MissionReportVehicle,
        back_populates='uses'
    )

    # vehicles may be used multiple times in a single mission_report
    count = Column(
        Integer,
        nullable=False,
        default=1
    )
