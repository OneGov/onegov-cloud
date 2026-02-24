from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.orm.mixins import ContentMixin
from onegov.file import File
from onegov.org.models import AccessExtension
from sedate import to_timezone
from sqlalchemy import Enum, ForeignKey, Numeric
from sqlalchemy.orm import mapped_column, relationship, Mapped
from uuid import uuid4, UUID


from typing import Literal, TypeAlias

MissionType: TypeAlias = Literal['single', 'multi']
MISSION_TYPES: tuple[MissionType, ...] = ('single', 'multi')


class MissionReportFile(File):
    __mapper_args__ = {'polymorphic_identity': 'mission-report-file'}


class MissionReport(Base, ContentMixin, AccessExtension):

    __tablename__ = 'mission_reports'

    #: the public id of the mission_report
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the date of the report
    date: Mapped[datetime]

    #: how long the mission lasted, in hours
    duration: Mapped[Decimal] = mapped_column(
        Numeric(precision=6, scale=2)
    )

    #: the nature of the mission
    nature: Mapped[str]

    #: the location of the mission
    location: Mapped[str]

    #: actually active personnel
    personnel: Mapped[int]

    #: backup personnel
    backup: Mapped[int]

    #: the Zivilschutz was involved
    civil_defence: Mapped[bool] = mapped_column(default=False)

    #: pictures of the mission
    pictures = associated(MissionReportFile, 'pictures', 'one-to-many')

    # The number of missions on the same site during a day
    mission_count: Mapped[int] = mapped_column(default=1)

    # the mission type
    mission_type: Mapped[MissionType] = mapped_column(
        Enum(*MISSION_TYPES, name='mission_type'),
        default='single'
    )

    used_vehicles: Mapped[list[MissionReportVehicleUse]] = relationship(
        cascade='all, delete-orphan',
        back_populates='mission_report'
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
    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    #: the short id of the vehicle
    name: Mapped[str]

    #: the longer name of the vehicle
    description: Mapped[str]

    #: symbol of the vehicle
    symbol = associated(MissionReportFile, 'symbol', 'one-to-one')

    #: a website describing the vehicle
    website: Mapped[str | None]

    uses: Mapped[list[MissionReportVehicleUse]] = relationship(
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

    mission_report_id: Mapped[UUID] = mapped_column(
        ForeignKey('mission_reports.id'),
        primary_key=True
    )

    mission_report: Mapped[MissionReport] = relationship(
        back_populates='used_vehicles'
    )

    vehicle_id: Mapped[UUID] = mapped_column(
        ForeignKey('mission_report_vehicles.id'),
        primary_key=True
    )

    vehicle: Mapped[MissionReportVehicle] = relationship(
        back_populates='uses'
    )

    # vehicles may be used multiple times in a single mission_report
    count: Mapped[int] = mapped_column(default=1)
