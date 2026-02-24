from __future__ import annotations

import csv

from datetime import datetime as dt
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from freezegun import freeze_time
from io import StringIO
from onegov.winterthur.collections import MissionReportCollection
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse
from sedate import replace_timezone
from transaction import commit


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from tests.shared.client import Client
    from .conftest import TestApp


def test_mission_report_models(session: Session) -> None:
    date = replace_timezone(dt.now(), timezone='Europe/Zurich')
    reports = {
        'Luzern': MissionReport(
            date=date, duration=Decimal('5'), nature='Brand',
            location='Luzern', personnel=10, backup=5
        ),
        'Kriens': MissionReport(
            date=date, duration=Decimal('10'), nature='Brand',
            location='Kriens', personnel=5, backup=2
        )
    }
    vehicles = {
        'Florian 1': MissionReportVehicle(
            name='Florian 1', description='Tanklöschfahrzeug'
        ),
        'Florian 2': MissionReportVehicle(
            name='Florian 2', description='Tanklöschfahrzeug'
        ),
        'Florian 10': MissionReportVehicle(
            name='Florian 10', description='Personentransporter'
        ),
        'Thor': MissionReportVehicle(name='Thor', description='Boot')
    }
    for report in reports.values():
        session.add(report)
    for vehicle in vehicles.values():
        session.add(vehicle)
    session.flush()

    assert all(report.used_vehicles == [] for report in reports.values())
    assert all(vehicle.uses == [] for vehicle in vehicles.values())

    uses = {
        'Luzern-Florian 1': MissionReportVehicleUse(
            mission_report=reports['Luzern'],
            vehicle=vehicles['Florian 1']
        ),
        'Luzern-Florian 2': MissionReportVehicleUse(
            mission_report=reports['Luzern'],
            vehicle=vehicles['Florian 2']
        ),
        'Luzern-Thor': MissionReportVehicleUse(
            mission_report=reports['Luzern'],
            vehicle=vehicles['Thor']
        ),
        'Kriens-Florian 1': MissionReportVehicleUse(
            mission_report=reports['Kriens'],
            vehicle=vehicles['Florian 1']
        ),
        'Kriens-Florian 10': MissionReportVehicleUse(
            mission_report=reports['Kriens'],
            vehicle=vehicles['Florian 10']
        )
    }
    for obj in uses.values():
        session.add(obj)
    session.flush()

    assert len(reports['Luzern'].used_vehicles) == 3
    assert len(reports['Kriens'].used_vehicles) == 2
    assert len(vehicles['Florian 1'].uses) == 2
    assert len(vehicles['Florian 2'].uses) == 1
    assert len(vehicles['Florian 10'].uses) == 1
    assert len(vehicles['Thor'].uses) == 1

    session.delete(reports['Luzern'])
    session.flush()
    assert session.query(MissionReportVehicle).count() == 4


def test_mission_report_collection(session: Session) -> None:
    date = replace_timezone(dt.now(), timezone='Europe/Zurich')
    missions = MissionReportCollection(session, year=date.year)
    mission_data = dict(
        date=date, duration=5, nature='Brand', mission_type='multi',
        location='Luzern', personnel=10, backup=5, mission_count=5)
    mission = missions.add(**mission_data)
    assert mission.mission_count == 5
    assert mission.mission_type == 'multi'


def test_view_mission_reports(client: Client[TestApp]) -> None:
    session = client.app.session()
    date = replace_timezone(dt.now(), timezone='Europe/Zurich')
    missions = MissionReportCollection(session, year=date.year)
    mission = missions.add(
        date=date, duration=5, nature='Brand',
        location='Luzern', personnel=10, backup=5
    )
    assert mission.mission_count == 1
    assert mission.mission_type == 'single'

    # Test mission count
    assert missions.mission_count() == 1

    last_year = date - relativedelta(years=1)
    mission_2 = missions.add(
        date=last_year, duration=1.5, nature='Brand im Dachstock',
        location='Luzern', personnel=8, backup=5, mission_count=3
    )
    assert mission_2.mission_count == 3

    assert missions.mission_count() == 1  # current year
    assert MissionReportCollection(
        session, year=last_year.year).mission_count() == 3

    new_url = '/mission-reports/+new'
    client.login_admin()
    page = client.get(new_url)

    # leave time unfilled
    page.form['day'] = f'{dt.now().year}-05-05'
    page.form['duration'] = 5
    page.form['nature'] = 'Fire with a lot of smoke'
    page.form['location'] = 'Montreux'
    page.form['personnel'] = 10
    page.form['backup'] = 5

    page = page.form.submit()
    field_error = page.pyquery('.field-time small.error')[0].text
    assert 'Dieses Feld wird benötigt.' in field_error

    # change the mode to multi
    page.form['mission_type'] = 'multi'
    page.form['mission_count'] = 5
    page.form['time'] = '00:00'
    entry = page.form.submit().follow()
    # setting the time for the date to midnight
    assert '00:00' in entry.pyquery('tr td:last-of-type')[1].text
    assert entry.pyquery('#mission-count')[0].text == '5'
    assert entry.pyquery('#mission-type')[0].text == 'Mehrfach-Einsatz'

    # test editing
    edit = entry.click('Bearbeiten')
    edit.form['mission_type'] = 'single'
    edit = edit.form.submit()
    assert 'Die Anzahl Einsätze muss 1 sein bei normalen Einsätzen' in edit

    page = client.get(f'/mission-reports?year={date.year}')
    assert page.pyquery('.total-missions b')[0].text == '5'


@freeze_time('2024-11-12 08:31')
def test_view_mission_report_json(client: Client[TestApp]) -> None:
    session = client.app.session()

    now = replace_timezone(dt.now(), timezone='Europe/Zurich')
    last_week = now - relativedelta(weeks=1, hours=5, minutes=19)
    last_month = now - relativedelta(months=1, hours=1, minutes=10)
    last_year = now - relativedelta(years=1, hours=3, minutes=30)

    missions = MissionReportCollection(session, year=now.year)
    for m in ((now, 2, 'Brand', 'Luzern', 10, 5),
              (last_week, 0.5, 'Rauchmelder', 'Kriens', 3, 2),
              (last_month, 1, 'Kellerbrand', 'Reussbühl', 6, 8)):
        missions.add(
            date=m[0], duration=m[1], nature=m[2],
            location=m[3], personnel=m[4], backup=m[5]
        )
    assert missions.mission_count() == 3
    commit()

    expected_2024 = {
        "name": "Mission Reports",
        "report_count": 3,
        "reports": [
            {
                "date": "12-11-2024",
                "alarm": "08:31",
                "duration": "2h",
                "nature": "Brand",
                "mission_type": "single",
                "mission_count": 1,
                "vehicles": [],
                "vehicles_icons": [],
                "location": "Luzern",
                "personnel_active": 10,
                "personnel_backup": 5,
                "civil_defence_involved": False
            },
            {
                "date": "05-11-2024",
                "alarm": "03:12",
                "duration": "0.5h",
                "nature": "Rauchmelder",
                "mission_type": "single",
                "mission_count": 1,
                "vehicles": [],
                "vehicles_icons": [],
                "location": "Kriens",
                "personnel_active": 3,
                "personnel_backup": 2,
                "civil_defence_involved": False
            },
            {
                "date": "12-10-2024",
                "alarm": "08:21",
                "duration": "1h",
                "nature": "Kellerbrand",
                "mission_type": "single",
                "mission_count": 1,
                "vehicles": [],
                "vehicles_icons": [],
                "location": "Reussbühl",
                "personnel_active": 6,
                "personnel_backup": 8,
                "civil_defence_involved": False
            }
        ]
    }

    response = client.get('/mission-reports/json')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    assert client.get('/mission-reports/json').json == expected_2024
    assert client.get(
        '/mission-reports/json?year=2024').json == expected_2024
    assert client.get('/mission-reports/json?year=2023').json == {
        'name': 'Mission Reports', 'report_count': 0, 'reports': []}
    assert client.get(
        '/mission-reports/json?all=true').json['report_count'] == 3

    # add a mission for last year
    missions.add(
        date=last_year, duration=4.2, nature="Wohnhausbrand",
        location="Tribschen", personnel=20, backup=1, mission_count=2
    )
    assert missions.mission_count() == 3  # current year only
    assert MissionReportCollection(
        session, year=last_year.year).mission_count() == 2
    commit()

    expected_2023 = {
        "name": "Mission Reports",
        "report_count": 1,
        "reports": [
            {
                "date": "12-11-2023",
                "alarm": "05:01",
                "duration": "4.2h",
                "nature": "Wohnhausbrand",
                "mission_type": "single",
                "mission_count": 2,
                "vehicles": [],
                "vehicles_icons": [],
                "location": "Tribschen",
                "personnel_active": 20,
                "personnel_backup": 1,
                "civil_defence_involved": False
            },
        ]
    }

    assert client.get('/mission-reports/json').json == expected_2024
    assert client.get(
        '/mission-reports/json?year=2024').json == expected_2024
    assert client.get(
        '/mission-reports/json?year=2023').json == expected_2023
    assert client.get('/mission-reports/json?year=2022').json == {
        'name': 'Mission Reports', 'report_count': 0, 'reports': []}
    assert client.get(
        '/mission-reports/json?all=true').json['report_count'] == 4

    assert missions.mission_count() == 3
    assert missions.query_current_year().count() == 3
    assert missions.query_all().count() == 4
    assert MissionReportCollection(
        session, year=last_year.year).mission_count() == 2


@freeze_time('2024-11-12 08:31')
def test_view_mission_report_csv(client: Client[TestApp]) -> None:
    session = client.app.session()

    now = replace_timezone(dt.now(), timezone='Europe/Zurich')
    last_week = now - relativedelta(weeks=1, hours=5, minutes=19)
    last_month = now - relativedelta(months=1, hours=1, minutes=10)
    last_year = now - relativedelta(years=1, hours=3, minutes=30)

    missions = MissionReportCollection(session, year=now.year)
    for m in ((now, 2, 'Brand', 'Luzern', 10, 5),
              (last_week, 0.5, 'Rauchmelder', 'Kriens', 3, 2),
              (last_month, 1, 'Kellerbrand', 'Reussbühl', 6, 8),
              (last_year, 4.2, 'Wohnhausbrand', 'Tribschen', 20, 1, 2)):
        missions.add(
            date=m[0], duration=m[1], nature=m[2],
            location=m[3], personnel=m[4], backup=m[5]
        )
    assert missions.mission_count() == 3
    commit()

    response = client.get('/mission-reports/csv')
    assert response.status_code == 200
    assert response.content_type == 'text/csv'

    row_headers = ['date', 'alarm', 'duration', 'nature', 'mission_type',
                   'mission_count', 'vehicles', 'vehicles_icons',
                   'location', 'personnel_active', 'personnel_backup',
                   'civil_defence_involved']
    csv_content = StringIO(response.text)
    reader = csv.reader(csv_content)
    rows = list(reader)

    expected_row_luzern = [
        '12-11-2024', '08:31', '2h', 'Brand', 'single', '1', '',
        '', 'Luzern', '10', '5', 'False'
    ]
    expected_row_kriens = [
        '05-11-2024', '03:12', '0.5h', 'Rauchmelder', 'single', '1', '',
        '', 'Kriens', '3', '2', 'False'
    ]
    expected_row_reussbuehl = [
        '12-10-2024', '08:21', '1h', 'Kellerbrand', 'single', '1', '',
        '', 'Reussbühl', '6', '8', 'False'
    ]
    expected_row_tribschen = [
        '12-11-2023', '05:01', '4.2h', 'Wohnhausbrand', 'single', '1', '',
        '', 'Tribschen', '20', '1', 'False'
    ]

    assert rows[0] == row_headers
    assert rows[1] == expected_row_luzern
    assert rows[2] == expected_row_kriens
    assert rows[3] == expected_row_reussbuehl
    assert len(rows) == 4

    response = client.get('/mission-reports/csv?year=2024')
    csv_content = StringIO(response.text)
    reader = csv.reader(csv_content)
    rows = list(reader)
    assert rows[0] == row_headers
    assert rows[1] == expected_row_luzern
    assert rows[2] == expected_row_kriens
    assert rows[3] == expected_row_reussbuehl
    assert len(rows) == 4

    response = client.get('/mission-reports/csv?year=2023')
    csv_content = StringIO(response.text)
    reader = csv.reader(csv_content)
    rows = list(reader)
    assert rows[0] == row_headers
    assert rows[1] == expected_row_tribschen
    assert len(rows) == 2

    response = client.get('/mission-reports/csv?year=2022')
    csv_content = StringIO(response.text)
    reader = csv.reader(csv_content)
    rows = list(reader)
    assert rows[0] == row_headers
    assert len(rows) == 1

    response = client.get('/mission-reports/csv?all=true')
    csv_content = StringIO(response.text)
    reader = csv.reader(csv_content)
    rows = list(reader)
    assert rows[0] == row_headers
    assert rows[1] == expected_row_luzern
    assert rows[2] == expected_row_kriens
    assert rows[3] == expected_row_reussbuehl
    assert rows[4] == expected_row_tribschen
    assert len(rows) == 5


def test_mission_reports_validating_integer_fields(
    client: Client[TestApp]
) -> None:

    client.login_admin()
    page = client.get('/mission-reports/vehicles/+new')
    page.form['name'] = 'Personentrnasportfahrzeug'
    page.form['description'] = 'Note'
    page.form.submit()
    page = client.get('/mission-reports/+new')
    page.form['day'] = f'{dt.now().year}-05-05'
    page.form['duration'] = 5
    page.form['nature'] = 'Fire with a lot of smoke'
    page.form['location'] = 'Montreux'
    page.form['personnel'] = 10
    page.form['backup'] = 5
    page.form['time'] = '00:00'

    inputs = page.pyquery("input[name^='vehicles']")
    checkbox_vehicle = inputs[0].attrib["name"]
    vehicle_count_input = inputs[1].attrib["name"]

    page.form[checkbox_vehicle] = 'y'
    page.form[vehicle_count_input] = '-1'  # negative integer: disallowed

    page = page.form.submit()
    assert 'Das Formular enthält Fehler' in page
    page.form[vehicle_count_input] = '1'

    page = page.form.submit().follow()
    assert 'Der Einsatzbericht wurde hinzugefügt' in page


def test_mission_reports_validating_integer_fields_multi(
    client: Client[TestApp]
) -> None:

    client.login_admin()
    page = client.get('/mission-reports/vehicles/+new')
    page.form['name'] = 'Personentrnasportfahrzeug'
    page.form['description'] = 'Note'
    page.form.submit()
    page = client.get('/mission-reports/+new')
    page.form['day'] = f'{dt.now().year}-05-05'
    page.form['duration'] = 5
    page.form['nature'] = 'Fire with a lot of smoke'
    page.form['location'] = 'Montreux'
    page.form['personnel'] = 10
    page.form['backup'] = 5
    page.form['time'] = '00:00'

    # change to multi
    page.form['mission_type'] = 'multi'
    page.form['mission_count'] = '-2'  # negative integer: disallowed

    inputs = page.pyquery("input[name^='vehicles']")
    checkbox_vehicle = inputs[0].attrib["name"]
    vehicle_count_input = inputs[1].attrib["name"]

    page.form[checkbox_vehicle] = 'y'
    page.form[vehicle_count_input] = 1

    page = page.form.submit()
    assert 'Das Formular enthält Fehler' in page
    page.form['mission_count'] = 2

    page = page.form.submit().follow()
    assert 'Der Einsatzbericht wurde hinzugefügt' in page
