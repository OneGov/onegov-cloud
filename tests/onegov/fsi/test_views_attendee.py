from __future__ import annotations

from onegov.fsi.models.course_attendee import external_attendee_org
from onegov.user import User


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client, FsiScenario


def test_course_attendee_collection(client: Client) -> None:
    view = '/fsi/attendees'
    client.get(view, status=403)
    client.login_member()
    client.get(view, status=403)


def test_attendee_details(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()

    planner = session.query(User).filter_by(  # type: ignore[union-attr]
        username='admin@example.org').first().attendee

    attendee = session.query(User).filter_by(  # type: ignore[union-attr]
        username='member@example.org').first().attendee

    client.login_member()
    client.get(f'/fsi/attendee/{planner.id}', status=403)
    # can see his own
    client.get(f'/fsi/attendee/{attendee.id}')

    # ca see all others
    client.login_editor()
    client.get(f'/fsi/attendee/{planner.id}', status=200)


def test_edit_attendee(client_with_db: Client) -> None:
    client = client_with_db
    session = client.app.session()

    attendee = session.query(User).filter_by(  # type: ignore[union-attr]
        username='member@example.org').first().attendee

    client.login_member()
    client.get(f'/fsi/attendee/{attendee.id}', status=200)

    # Assure permission Secret
    client.login_member()
    client.get(f'/fsi/attendee/{attendee.id}/edit', status=403)

    client.login_editor()
    client.get(f'/fsi/attendee/{attendee.id}/edit', status=403)

    client.login_admin()
    new = client.get(f'/fsi/attendee/{attendee.id}/edit')
    assert not new.form.fields.get('organisation')
    new.form['first_name'] = 'New FN'
    new.form['last_name'] = 'New LN'
    page = new.form.submit().follow()
    assert 'New FN' in page


def test_add_edit_external_attendee(
    client: Client,
    scenario: FsiScenario
) -> None:
    # Add an external to have multiple choices in organisations
    real_org = 'AA'
    scenario.add_attendee(external=True, organisation=real_org)

    session = client.app.session()
    editor = session.query(User).filter_by(role='editor').first()
    assert editor is not None
    # Add an attendee with permissions
    scenario.add_attendee(user_id=editor.id, permissions=[real_org])
    scenario.commit()

    view = '/fsi/attendees/add-external'
    client.login_member()
    client.get(view, status=403)

    client.login_editor()
    new = client.get('/fsi/attendees/').click('Externen Teilnehmer hinzufügen')
    options = [opt[2] for opt in new.form['organisation'].options]

    # Limit options to his permissions
    assert options == [external_attendee_org, real_org]

    assert new.form['organisation'].value == external_attendee_org
    new.form['first_name'] = 'New FN'
    new.form['last_name'] = 'New LN'
    new.form['email'] = 'external@example.org'

    page = new.form.submit().follow()
    assert 'Neuer externer Teilnehmer hinzugefügt' in page
    assert 'external@example.org' in page
    assert external_attendee_org in page

    # Edit by logging in as admin
    admin = client.spawn()
    admin.login_admin()
    page = admin.get(page.request.url).click('Profil bearbeiten')
    assert page.form['organisation'].value == external_attendee_org
    page.form['organisation'] = real_org
    page = page.form.submit().follow()
    assert real_org in page

    # Test adding twice
    page = client.get(view)
    page.form['first_name'] = 'Duplicate FN'
    page.form['last_name'] = 'Duplicate LN'
    page.form['email'] = 'external@example.org'
    page = page.form.submit()
    assert 'Ein Teilnehmer mit dieser E-Mail existiert bereits' in page
