import click
import json
import sedate
import shutil

from datetime import datetime
from onegov.core.cli import command_group
from onegov.core.crypto import random_token
from onegov.core.csv import CSVFile
from onegov.file.utils import as_fileintent
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportFile
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile


cli = command_group()


@cli.command(
    name='import-mission-reports', context_settings={'singular': True})
@click.option('--vehicles-file', type=click.Path(exists=True), required=True)
@click.option('--missions-file', type=click.Path(exists=True), required=False)
@click.option('--no-confirm', is_flag=True, default=False)
def import_mission_reports(vehicles_file, missions_file, no_confirm):
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
        d = sedate.replace_timezone(d, 'Europe/Zurich')

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

        return d

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

    def is_hidden(mission):
        if mission.public == '0':
            return True

        if mission.hidden == '1':
            return True

        if mission.hide == '1':
            return True

        if "nicht freischalten" in mission.type.lower():
            return True

        return False

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
                meta={'is_hidden_from_public': is_hidden(mission)}
            )

            vehicle_uids = mission.vehicles.split(',')
            vehicle_uids = (v.strip() for v in vehicle_uids)
            vehicle_uids = (v for v in vehicle_uids if v)

            for uid in vehicle_uids:
                created.used_vehicles.append(MissionReportVehicleUse(
                    vehicle=created_vehicles[uid]
                ))

            request.session.add(created)

        request.session.flush()

    return handle_import


@cli.command(
    name='export-mission-vehicles', context_settings={'singular': True})
@click.option('--export-file', type=click.Path(exists=False), required=True)
def export_mission_vehicles(export_file):
    """ Exports the mission vehicles (with symbols, but without usage) into
    a ZIP file for consumption with the 'import-mission-vehicles' command.

    """

    def handle_export(request, app):
        temp = TemporaryDirectory()
        path = Path(temp.name)
        data = {}

        for vehicle in request.session.query(MissionReportVehicle):
            record = data[str(vehicle.id)] = {
                'name': vehicle.name,
                'description': vehicle.description,
                'website': vehicle.website,
                'filename': None
            }

            if vehicle.symbol:
                symbols = (path / 'symbols')
                symbols.mkdir(exist_ok=True)

                record['filename'] = vehicle.symbol.name

                with (symbols / str(vehicle.id)).open('wb') as f:
                    shutil.copyfileobj(vehicle.symbol.reference.file, f)

        with (path / 'data.json').open('w') as f:
            json.dump(data, f, sort_keys=True, indent=4)

        shutil.make_archive(export_file.rstrip('.zip'), 'zip', path)

    return handle_export


@cli.command(
    name='import-mission-vehicles', context_settings={'singular': True})
@click.option('--import-file', type=click.Path(exists=True), required=True)
@click.option('--replace', is_flag=True, default=False)
@click.option('--match', is_flag=True, default=False)
def import_mission_vehicles(import_file, replace, match):
    """ Imports the mission vehicles created by the export-mission-vehicles
    command.

    """

    def handle_import(request, app):
        temp = TemporaryDirectory()
        path = Path(temp.name)
        data = {}

        zip = ZipFile(import_file)
        zip.extractall(path)

        with (path / 'data.json').open('r') as f:
            data = json.load(f)

        existing = {
            str(v.id): v for v in request.session.query(MissionReportVehicle)
        }

        for id in data:

            if id in existing and replace:
                request.session.delete(existing[id])
                request.session.flush()

            if id in existing and not replace:
                continue

            vehicle = None

            if match:
                vehicle = request.session.query(MissionReportVehicle)\
                    .filter_by(name=data[id]['name'])\
                    .first()

            if not vehicle:
                vehicle = MissionReportVehicle(id=id)

            vehicle.name = data[id]['name']
            vehicle.description = data[id]['description']
            vehicle.website = data[id]['website']

            symbol_path = path / 'symbols' / str(id)

            if symbol_path.exists():
                filename = data[id]['filename']

                with symbol_path.open('rb') as f:
                    vehicle.symbol = MissionReportFile(
                        id=random_token(),
                        name=filename,
                        reference=as_fileintent(
                            content=f,
                            filename=filename
                        )
                    )

            request.session.add(vehicle)

    return handle_import
