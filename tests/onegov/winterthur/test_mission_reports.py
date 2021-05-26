from onegov.winterthur.collections import MissionReportCollection
from tests.shared import Client as BaseClient
from sedate import replace_timezone
from datetime import datetime as dt



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
