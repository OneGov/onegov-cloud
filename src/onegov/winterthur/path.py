from __future__ import annotations

from datetime import date
from onegov.winterthur.app import WinterthurApp
from onegov.winterthur.collections import AddressCollection
from onegov.winterthur.collections import AddressSubsetCollection
from onegov.winterthur.collections import MissionReportCollection
from onegov.winterthur.collections import MissionReportFileCollection
from onegov.winterthur.collections import MissionReportVehicleCollection
from onegov.winterthur.daycare import DaycareSubsidyCalculator
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.roadwork import RoadworkCollection, Roadwork
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.winterthur.request import WinterthurRequest


@WinterthurApp.path(
    model=AddressCollection,
    path='/streets')
def get_streets_directory(app: WinterthurApp) -> AddressCollection:
    return AddressCollection(app.session())


@WinterthurApp.path(
    model=AddressSubsetCollection,
    path='/streets/{street}')
def get_street_subset(
    app: WinterthurApp,
    street: str
) -> AddressSubsetCollection | None:
    subset = AddressSubsetCollection(app.session(), street=street)
    return subset.exists() and subset or None


@WinterthurApp.path(
    model=RoadworkCollection,
    path='/roadwork')
def get_roadwork_collection(
    app: WinterthurApp,
    letter: str | None = None,
    query: str | None = None
) -> RoadworkCollection:
    return RoadworkCollection(app.roadwork_client, letter=letter, query=query)


@WinterthurApp.path(
    model=Roadwork,
    path='/roadwork/{id}',
    converters={'id': int})
def get_roadwork(app: WinterthurApp, id: int) -> Roadwork | None:
    return RoadworkCollection(app.roadwork_client).by_id(id)


@WinterthurApp.path(
    model=MissionReportCollection,
    path='/mission-reports',
    converters={'year': int, 'page': int})
def get_mission_reports(
    request: WinterthurRequest,
    page: int = 0,
    year: int | None = None
) -> MissionReportCollection:

    year = date.today().year if year == 0 else year
    return MissionReportCollection(
        request.session, page=page,
        include_hidden=request.is_manager,
        year=year)


@WinterthurApp.path(
    model=MissionReportVehicleCollection,
    path='/mission-reports/vehicles')
def get_mission_report_vehicles(
    request: WinterthurRequest
) -> MissionReportVehicleCollection:
    return MissionReportVehicleCollection(request.session)


@WinterthurApp.path(
    model=MissionReport,
    path='/mission-reports/report/{id}',
    converters={'id': UUID})
def get_mission_report(
    request: WinterthurRequest,
    id: UUID
) -> MissionReport | None:
    return get_mission_reports(request).by_id(id)


@WinterthurApp.path(
    model=MissionReportFileCollection,
    path='/mission-reports/report/{id}/images',
    converters={'id': UUID})
def get_mission_report_files(
    request: WinterthurRequest,
    id: UUID
) -> MissionReportFileCollection | None:

    if report := get_mission_report(request, id):
        return MissionReportFileCollection(request.session, report)
    return None


@WinterthurApp.path(
    model=MissionReportVehicle,
    path='/mission-reports/vehicle/{id}',
    converters={'id': UUID})
def get_mission_report_vehicle(
    request: WinterthurRequest,
    id: UUID
) -> MissionReportVehicle | None:
    return get_mission_report_vehicles(request).by_id(id)


@WinterthurApp.path(
    model=DaycareSubsidyCalculator,
    path='/daycare-subsidy-calculator')
def get_daycare_subsidy_calculator(
    request: WinterthurRequest
) -> DaycareSubsidyCalculator:
    return DaycareSubsidyCalculator(request.session)
