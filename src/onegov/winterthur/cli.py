from __future__ import annotations

import os

import click
import json
import sedate
import shutil

from datetime import datetime
from decimal import Decimal
from onegov.core.cli import command_group
from onegov.core.crypto import random_token
from onegov.core.csv import CSVFile
from onegov.directory import DirectoryEntry
from onegov.file import File
from onegov.file.utils import as_fileintent
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportFile
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.csv import DefaultRow
    from onegov.winterthur.app import WinterthurApp
    from onegov.winterthur.request import WinterthurRequest


cli = command_group()


@cli.command(
    name='import-mission-reports', context_settings={'singular': True})
@click.option('--vehicles-file', type=click.Path(exists=True), required=True)
@click.option('--missions-file', type=click.Path(exists=True), required=True)
@click.option('--no-confirm', is_flag=True, default=False)
def import_mission_reports(
    vehicles_file: str,
    missions_file: str,
    no_confirm: bool
) -> Callable[[WinterthurRequest, WinterthurApp], None]:
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

    def extract_date(mission: DefaultRow) -> datetime:
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

    def extract_duration(mission: DefaultRow) -> Decimal:
        d = mission.duration
        d = d.replace(',', '.')

        if ':' in d:
            hours, minutes = (int(v) for v in d.split(':'))
            return Decimal(hours + minutes) / Decimal(60)

        return Decimal(d)

    def extract_personnel(value: str) -> int:

        def digits() -> Iterator[str]:
            for v in value:
                if v.isdigit():
                    yield v
                else:
                    break

        return int(''.join(digits()))

    def is_hidden(mission: DefaultRow) -> bool:
        if mission.public == '0':
            return True

        if mission.hidden == '1':
            return True

        if mission.hide == '1':
            return True

        if 'nicht freischalten' in mission.type.lower():
            return True

        return False

    def handle_import(
        request: WinterthurRequest,
        app: WinterthurApp
    ) -> None:

        for mission_obj in request.session.query(MissionReport):
            request.session.delete(mission_obj)

        for vehicle_obj in request.session.query(MissionReportVehicle):
            request.session.delete(vehicle_obj)

        created_vehicles = {}

        for vehicle in vehicles:
            vehicle_obj = MissionReportVehicle(
                name=vehicle.name,
                description=vehicle.description,
            )

            if vehicle.hidden == '1':
                vehicle_obj.access = 'private'

            created_vehicles[vehicle.uid] = vehicle_obj
            request.session.add(vehicle_obj)

        request.session.flush()

        for mission in missions:
            mission_obj = MissionReport(
                date=extract_date(mission),
                duration=extract_duration(mission),
                nature=mission.type,
                location=mission.location,
                personnel=extract_personnel(mission.personnel),
                backup=extract_personnel(mission.personnel_hq),
                meta={'access': is_hidden(mission) and 'private' or 'public'}
            )

            vehicle_uids = (
                uid
                for v in mission.vehicles.split(',')
                if (uid := v.strip())
            )

            for uid in vehicle_uids:
                mission_obj.used_vehicles.append(MissionReportVehicleUse(
                    vehicle=created_vehicles[uid]
                ))

            request.session.add(mission_obj)

        request.session.flush()

    return handle_import


@cli.command(
    name='export-mission-vehicles', context_settings={'singular': True})
@click.option('--export-file', type=click.Path(exists=False), required=True)
def export_mission_vehicles(
    export_file: str
) -> Callable[[WinterthurRequest, WinterthurApp], None]:
    """ Exports the mission vehicles (with symbols, but without usage) into
    a ZIP file for consumption with the 'import-mission-vehicles' command.

    """

    def handle_export(
        request: WinterthurRequest,
        app: WinterthurApp
    ) -> None:

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
def import_mission_vehicles(
    import_file: str,
    replace: bool,
    match: bool
) -> Callable[[WinterthurRequest, WinterthurApp], None]:
    """ Imports the mission vehicles created by the export-mission-vehicles
    command.

    """

    def handle_import(
        request: WinterthurRequest,
        app: WinterthurApp
    ) -> None:

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
                vehicle = (
                    request.session.query(MissionReportVehicle)
                    .filter_by(name=data[id]['name'])
                    .first()
                )

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


@cli.command(
    name='analyze-directories', context_settings={'singular': True})
@click.option('--log-file', help='Path if a logfile is wanted')
@click.option('--dry-run', is_flag=True, default=False)
def analyze_directories(
    log_file: str | None,
    dry_run: bool
) -> Callable[[WinterthurRequest, WinterthurApp], None]:
    """ Spots missing depot directories of file in directory entries and
    fixes full-path filenames that come from Upload via IE11. """

    missing_folders = []
    db_entry_missing = []
    file_names_changed = []

    def is_full_path(file_name: str) -> bool:
        return ':\\' in file_name

    def fix_file_name(file_name: str) -> str:
        return file_name.rsplit('\\', 1)[-1]

    def handle_analyze_entries(
        request: WinterthurRequest,
        app: WinterthurApp
    ) -> None:

        assert request.app.depot_storage_path is not None
        for entry in request.session.query(DirectoryEntry).all():
            for field in entry.directory.file_fields:
                field_data = entry.content['values'][field.id]
                file_data = field_data.get('data', '')
                if not file_data:
                    continue
                file_id = file_data.lstrip('@')
                file = request.session.query(File).filter_by(
                    id=file_id).first()

                if not file:
                    db_entry_missing.append(file_id)
                    continue

                if is_full_path(file.name):
                    new_name = fix_file_name(file.name)
                    if not dry_run:
                        file.name = new_name
                    else:
                        click.secho(f'Change {file.name} to {new_name}')
                    file_names_changed.append(file_id)

                file_path = os.path.join(
                    request.app.depot_storage_path,
                    file.reference['path']
                )
                if not os.path.exists(file_path):
                    data = (
                        file_path,
                        f'/directories/{entry.directory.name}/{entry.name}',
                        entry.created
                    )
                    missing_folders.append(data)

        if not any((missing_folders, file_names_changed)):
            click.secho('Nothing changed')
            return

        log_data = '\n'.join((
            'MISSING FOLDER PATH, URL FRAGMENT, ENTRY CREATED',
            *(f'{p},{u},{created!s}' for p, u, created in missing_folders),
        ))

        log_filenames = '\n'.join((
            '--- CHANGED FILENAMES ---',
            *file_names_changed
        ))

        if log_file:
            with open(log_file, 'w') as f:
                click.secho(f'Writing log file to {log_file}')
                f.write(log_data)
            click.secho(log_filenames)
        else:
            click.secho(log_data)
            click.secho(log_filenames)

    return handle_analyze_entries
