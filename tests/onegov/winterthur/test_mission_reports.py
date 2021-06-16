from onegov.winterthur.collections import MissionReportCollection
from tests.shared import Client as BaseClient
from sedate import replace_timezone
from datetime import datetime as dt

from tests.shared.utils import open_in_browser


class Client(BaseClient):
    skip_first_form = True


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
    page.form['day'] = '2021-05-05'
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


