from datetime import timedelta
from uuid import uuid4

from sedate import utcnow

from tests.shared.utils import open_in_browser


def test_audit_for_course(client, scenario):
    """
    Story:
    For a course with refresh interval, an admin checks the list of attendees.
    This list contains when the attendee last visited this course during an
    event.

    The editor might do the same. He can see all attendees he is permitted
    to by attendee.permissions which match attendee.organisation

    """

    # Test what happens if no course is publicly available
    client.login_admin()
    url = f'/fsi/audit'
    page = client.get(url)
    options = [opt[2] for opt in page.form['course_id'].options]
    assert options == ['Keine']
    # Course options should be hidden but there
    org_options = [opt[2] for opt in page.form['organisations'].options]
    assert org_options == ['Keine']

    # Adds data
    scenario.add_course(
        refresh_interval=timedelta(days=2*365), mandatory_refresh=True)
    scenario.commit()
    scenario.refresh()
    course = scenario.latest_course
    now = utcnow()
    for ix in range(2):
        scenario.add_course_event(
            course,
            start=now + timedelta(days=30*ix)
        )
    scenario.commit()
    scenario.refresh()

    # Test that course input form vanishes if only one course is not hidden
    page = client.get(url)
    options = [opt[2] for opt in page.form['course_id'].options]
    assert options == [scenario.latest_course.name]
    # Test if a course was chosen automatically
    assert page.form['course_id'].value == str(scenario.latest_course.id)

    # add 21 attendee members
    for org in ('ZZW', 'ZHW', 'UBV'):
        for i in range(7):
            scenario.add_attendee(
                role='member',
                organisation=org,
                username=f'{uuid4().hex}.manila@quine.ch'
            )

    scenario.commit()
    scenario.refresh()
    editor = scenario.first_user('editor')
    editor.permissions = ['UBV', 'ZHW']

    scenario.commit()
    scenario.refresh()

    page = client.get(url)
    assert page.form['organisations'].value is None

    # Test pagination
    assert page.pyquery('ul.pagination > li.current > a')[0].text == "1"
    page = page.click('2', index=-1)
    assert page.pyquery('ul.pagination > li.current > a')[0].text == "2"
    assert page.form['organisations'].value is None

    # Test reset of pagination upon choosing letter
    page = page.click('M', index=-1)
    # Test reset of page when filtering with last name
    assert page.pyquery('ul.pagination > li.current > a')[0].text == "1"

    page.form['organisations'].data = ['ZZW']
    page = page.form.submit()
    assert page.form['organisations'].value == ['ZZW']
    assert page.pyquery('ul.pagination > li.current > a')[0].text == "1"
