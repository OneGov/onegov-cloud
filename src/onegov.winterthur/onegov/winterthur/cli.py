import click
import sedate

from datetime import datetime
from onegov.core.cli import command_group
from onegov.core.csv import CSVFile
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse


cli = command_group()


@cli.command(
    name='import-mission-reports', context_settings={'singular': True})
@click.option('--vehicles-file', type=click.Path(exists=True), required=True)
@click.option('--missions-file', type=click.Path(exists=True), required=True)
@click.option('--no-confirm', is_flag=True, default=False)
def generate_activities(vehicles_file, missions_file, no_confirm):
    """ Imports the existing mission reports. """

    if not no_confirm:
        click.confirm(
            'This will delete all existing missions and vehicles, continue?',
            abort=True
        )

    with open(vehicles_file, 'rb') as f:
        vehicles = tuple(CSVFile(f, expected_headers=(
            'uid', 'name', 'description', 'hidden'
        )))

    with open(missions_file, 'rb') as f:
        missions = tuple(CSVFile(f, expected_headers=(
            'date',
            'alert_time',
            'duration',
            'type',
            'location',
            'personnel',
            'personnel_hq',
            'vehicles',
            'public'
        )))

    def extract_date(mission):
        d = datetime.utcfromtimestamp(int(mission.date))
        d = sedate.replace_timezone(d, 'UTC')

        time = mission.alert_time.replace('.', ':')
        time = time.replace(';', ':')
        time = time.replace('::', ':')

        if ':' in time:
            h, m = (int(v.strip('<>-')) for v in time.split(':'))
        else:
            h = int(time)
            m = 0

        d = d.replace(hour=h)
        d = d.replace(minute=m)

        return sedate.to_timezone(d, 'Europe/Zurich')

    def extract_duration(mission):
        d = mission.duration
        d = d.replace(',', '.')

        if ':' in d:
            hours, minutes = (int(v) for v in d.split(':'))
            return hours + minutes / 60

        return float(d)

    def extract_personnel(value):

        def digits():
            for v in value:
                if v.isdigit():
                    yield v
                else:
                    break

        return int(''.join(digits()))

    def handle_import(request, app):

        for mission in request.session.query(MissionReport):
            request.session.delete(mission)

        for vehicle in request.session.query(MissionReportVehicle):
            request.session.delete(vehicle)

        created_vehicles = {}

        for vehicle in vehicles:
            created = MissionReportVehicle(
                name=vehicle.name,
                description=vehicle.description,
            )

            if vehicle.hidden == '1':
                created.is_hidden_from_public = True

            created_vehicles[vehicle.uid] = created
            request.session.add(created)

        request.session.flush()

        for mission in missions:
            created = MissionReport(
                date=extract_date(mission),
                duration=extract_duration(mission),
                nature=mission.type,
                location=mission.location,
                personnel=extract_personnel(mission.personnel),
                backup=extract_personnel(mission.personnel_hq),
            )

            vehicle_uids = mission.vehicles.split(',')
            vehicle_uids = (v.strip() for v in vehicle_uids)
            vehicle_uids = (v for v in vehicle_uids if v)

            for uid in vehicle_uids:
                created.used_vehicles.append(MissionReportVehicleUse(
                    vehicle=created_vehicles[uid]
                ))

            if mission.public == '0' or mission.hidden == '1':
                created.is_hidden_from_public = True

            if "nicht freischalten" in mission.type.lower():
                created.is_hidden_from_public = True

            request.session.add(created)

        request.session.flush()

    return handle_import
