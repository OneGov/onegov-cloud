from datetime import timedelta

from sedate import utcnow


def test_audit_for_course(client, scenario):
    """
    Story:
    For a course with refresh interval, an admin checks the list of attendees.
    This list contains when the attendee last visited this course during an
    event.

    The editor might do the same. He can see all attendees he is permitted
    to by attendee.permissions which match attendee.organisation

    """
    # assert scenario.session == client.app.session()
    scenario.add_course(
        refresh_interval=timedelta(days=2*365), mandatory_refresh=True)
    scenario.commit()
    scenario.refresh()
    course = scenario.latest_course
    now = utcnow()
    for ix in range(2):
        scenario.add_course_event(
            course_id=course.id,
            start=now + timedelta(days=30*ix)
        )

    for org in ('ZZW', 'ZHW', 'UBV'):
        scenario.add_attendee(role='member', organisation=org)

    editor = scenario.first_user('editor')
    editor.permissions = ['UBV', 'ZHW']

    scenario.commit()
    scenario.refresh()

    client.login_admin()
    url = f'/fsi/audit?course_id={scenario.latest_course.id}'
    page = client.get(url)
    client = client.spawn()
    client.login_editor()
    page = client.get(url)


