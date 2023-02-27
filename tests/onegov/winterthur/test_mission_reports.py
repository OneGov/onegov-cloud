from datetime import datetime as dt
from onegov.winterthur.collections import MissionReportCollection
from onegov.winterthur.models import MissionReport
from onegov.winterthur.models import MissionReportVehicle
from onegov.winterthur.models import MissionReportVehicleUse
from sedate import replace_timezone
from tests.shared import Client as BaseClient


class Client(BaseClient):
    skip_n_forms = 1


def test_mission_report_models(session):
    date = replace_timezone(dt.now(), timezone='Europe/Zurich')
    reports = {
        'Luzern': MissionReport(
            date=date, duration=5, nature='Brand',
            location='Luzern', personnel=10, backup=5
        ),
        'Kriens': MissionReport(
            date=date, duration=10, nature='Brand',
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
    for obj in reports.values():
        session.add(obj)
    for obj in vehicles.values():
        session.add(obj)
    session.flush()

    assert all([report.used_vehicles == [] for report in reports.values()])
    assert all([vehicle.uses == [] for vehicle in vehicles.values()])

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


def test_mission_report_collection(session):
    date = replace_timezone(dt.now(), timezone='Europe/Zurich')
    missions = MissionReportCollection(session, year=date.year)
    mission_data = dict(
        date=date, duration=5, nature='Brand', mission_type='multi',
        location='Luzern', personnel=10, backup=5, mission_count=5)
    mission = missions.add(**mission_data)
    assert mission.mission_count == 5
    assert mission.mission_type == 'multi'


def test_view_mission_reports(winterthur_app):
    session = winterthur_app.session()
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

    new_url = '/mission-reports/+new'
    client = Client(winterthur_app)
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


def test_mission_reports_validating_integer_fields(winterthur_app):

    client = Client(winterthur_app)
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


def test_mission_reports_validating_integer_fields_multi(winterthur_app):

    client = Client(winterthur_app)
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
