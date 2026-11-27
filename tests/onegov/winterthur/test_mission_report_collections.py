from __future__ import annotations

from datetime import datetime as dt
from decimal import Decimal
from onegov.winterthur.collections import (
    MissionReportCollection,
    MissionReportVehicleCollection,
)
from onegov.winterthur.models import MissionReport, MissionReportVehicle
from sedate import replace_timezone


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _report(**kwargs: object) -> MissionReport:
    defaults: dict[str, object] = dict(
        duration=Decimal('5'), nature='Brand', location='Luzern',
        personnel=10, backup=5,
    )
    defaults.update(kwargs)
    return MissionReport(**defaults)


def test_mission_report_collection_by_id_ignores_year(
    session: Session
) -> None:
    last_year = replace_timezone(dt(dt.now().year - 1, 6, 1), 'Europe/Zurich')
    report = _report(date=last_year)
    session.add(report)
    session.flush()

    missions = MissionReportCollection(session)  # defaults to current year
    # the default query is year-scoped and would not find last year's report
    assert missions.query().count() == 0
    # by_id bypasses the year filter
    assert missions.by_id(report.id) is report


def test_mission_report_collection_include_hidden(session: Session) -> None:
    now = replace_timezone(dt(dt.now().year, 6, 1), 'Europe/Zurich')
    public = _report(date=now)
    hidden = _report(date=now)
    hidden.access = 'private'
    session.add_all((public, hidden))
    session.flush()

    assert MissionReportCollection(session).query_all().count() == 1
    assert MissionReportCollection(
        session, include_hidden=True).query_all().count() == 2


def test_mission_report_collection_equality_and_paging(
    session: Session
) -> None:
    missions = MissionReportCollection(session, year=2020)
    assert missions == MissionReportCollection(session, year=2020)
    assert missions != MissionReportCollection(session, page=1, year=2020)
    assert missions != object()

    assert missions.page_index == 0
    other = missions.page_by_index(2)
    assert other.page == 2
    assert other.year == 2020


def test_mission_report_vehicle_collection_ordering(session: Session) -> None:
    session.add_all((
        MissionReportVehicle(name='Thor', description='Boot'),
        MissionReportVehicle(name='Florian', description='Fahrzeug'),
    ))
    session.flush()

    names = [v.name for v in MissionReportVehicleCollection(session).query()]
    assert names == ['Florian', 'Thor']


def test_mission_report_model_properties() -> None:
    date = replace_timezone(dt(2020, 6, 1, 12, 0), 'Europe/Zurich')
    report = _report(date=date, duration=Decimal('2.5'), nature='Brand')
    assert report.title == 'Brand'
    assert report.readable_duration == '2.5h'
    assert report.local_date.hour == 12


def test_mission_report_vehicle_properties() -> None:
    vehicle = MissionReportVehicle(
        name='Florian 1', description='Fahrzeug',
        website='https://example.org/f1'
    )
    assert vehicle.title == 'Florian 1 - Fahrzeug'
    assert vehicle.readable_website == 'example.org/f1'

    assert MissionReportVehicle(
        name='x', description='y').readable_website is None
