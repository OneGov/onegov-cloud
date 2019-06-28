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


@WinterthurApp.path(
    model=AddressCollection,
    path='/streets')
def get_streets_directory(app):
    return AddressCollection(app.session())


@WinterthurApp.path(
    model=AddressSubsetCollection,
    path='/streets/{street}')
def get_street_subset(app, street):
    subset = AddressSubsetCollection(app.session(), street=street)
    return subset.exists() and subset or None


@WinterthurApp.path(
    model=RoadworkCollection,
    path='/roadwork')
def get_roadwork_collection(app, letter=None, query=None):
    return RoadworkCollection(app.roadwork_client, letter=letter, query=query)


@WinterthurApp.path(
    model=Roadwork,
    path='/roadwork/{id}',
    converters=dict(id=int))
def get_roadwork(app, id):
    return RoadworkCollection(app.roadwork_client).by_id(id)


@WinterthurApp.path(
    model=MissionReportCollection,
    path='/mission-reports')
def get_mission_reports(request, page=0, year=date.today().year):
    year = str(year).isdigit() and int(year) or date.today().year

    return MissionReportCollection(
        request.session, page=page,
        include_hidden=request.is_manager,
        year=year)


@WinterthurApp.path(
    model=MissionReportVehicleCollection,
    path='/mission-reports/vehicles')
def get_mission_report_vehicles(request):
    return MissionReportVehicleCollection(request.session)


@WinterthurApp.path(
    model=MissionReport,
    path='/mission-reports/report/{id}',
    converters=dict(id=UUID))
def get_mission_report(request, id):
    return get_mission_reports(request).by_id(id)


@WinterthurApp.path(
    model=MissionReportFileCollection,
    path='/mission-reports/report/{id}/images',
    converters=dict(id=UUID))
def get_mission_report_files(request, id):
    report = get_mission_report(request, id)

    if report:
        return MissionReportFileCollection(request.session, report)


@WinterthurApp.path(
    model=MissionReportVehicle,
    path='/mission-reports/vehicle/{id}',
    converters=dict(id=UUID))
def get_mission_report_vehicle(request, id):
    return get_mission_report_vehicles(request).by_id(id)


@WinterthurApp.path(
    model=DaycareSubsidyCalculator,
    path='/daycare-subsidy-calculator')
def get_daycare_subsidy_calculator(request):
    return DaycareSubsidyCalculator(request.session)
