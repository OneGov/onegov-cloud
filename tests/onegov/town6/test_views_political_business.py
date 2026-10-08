import pytest

from datetime import date
from freezegun import freeze_time
from markupsafe import Markup
from onegov.org.models import Meeting, MeetingItem, RISParliamentarian
from onegov.org.models.political_business import (
    PoliticalBusiness,
    PoliticalBusinessParticipation,
)
from sedate import utcnow
from transaction import commit

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conftest import Client


@pytest.mark.parametrize('access', ['public', 'secret', 'private', 'member'])
def test_political_business_access(client: Client, access: str) -> None:
    client.login_admin()
    settings = client.get('/module-activation-settings')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    page = client.get('/political-businesses/new')
    assert page.form['access'].value == 'public'
    page.form['title'] = 'Restricted Business'
    page.form['political_business_type'] = 'postulate'
    page.form['status'] = 'beantwortet'
    page.form['entry_date'] = '2037-01-01'
    page.form['access'] = access
    page = page.form.submit().follow()
    url = page.request.path

    edit = page.click('Bearbeiten')
    assert edit.form['access'].value == access

    client.logout()
    page = client.get('/political-businesses')
    assert ('Restricted Business' in page) == (access == 'public')
    assert ('2037' in page) == (access == 'public')
    client.get(url, status=200 if access in ('public', 'secret') else 404)

    client.login_member()
    page = client.get('/political-businesses')
    assert ('Restricted Business' in page) == (access in ('public', 'member'))
    client.get(url, status=404 if access == 'private' else 200)

    client.logout()
    client.login_editor()
    page = client.get('/political-businesses')
    assert 'Restricted Business' in page
    assert '2037' in page
    page = client.get(url).click('Bearbeiten')
    assert page.form['access'].value == access
    page.form['access'] = 'public'
    page.form.submit().follow()
    client.logout()
    assert 'Restricted Business' in client.get('/political-businesses')
    client.get(url)


def test_private_business_hidden_from_related_pages(client: Client) -> None:
    client.app.org.ris_enabled = True
    person = RISParliamentarian(first_name='Anna', last_name='Example')
    business = PoliticalBusiness(
        title='Private Business',
        political_business_type='postulate',
        status='beantwortet',
        entry_date=date(2037, 1, 1),
        meta={'access': 'private', 'self_id': 'private-business'},
        participants=[
            PoliticalBusinessParticipation(
                parliamentarian=person,
                participant_type='First signatory',
            )
        ],
    )
    meeting = Meeting(
        title='Public Meeting',
        start_datetime=utcnow(),
        address=Markup('Town Hall'),
        meeting_items=[
            MeetingItem(
                title='Linked private item',
                number='1',
                political_business=business,
            ),
            MeetingItem(
                title='Imported private item',
                number='2',
                political_business_link_id='private-business',
            ),
            MeetingItem(title='Public agenda item', number='3'),
        ],
    )
    session = client.app.session()
    session.add(meeting)
    session.flush()
    meeting_url = f'/meeting/{meeting.id.hex}'
    person_url = f'/parliamentarian/{person.id.hex}'
    commit()

    page = client.get(meeting_url)
    assert 'Linked private item' not in page
    assert 'Imported private item' not in page
    assert 'Public agenda item' in page
    assert 'Private Business' not in client.get(person_url)
    page = client.get(meeting_url + '/export')
    assert 'Linked private item' not in page
    assert 'Imported private item' not in page

    client.login_editor()
    page = client.get(meeting_url)
    assert 'Linked private item' in page
    assert 'Imported private item' in page
    assert 'Private Business' in client.get(person_url)


def test_political_businesses(client_with_fts: Client) -> None:
    client = client_with_fts
    client.login_admin().follow()

    # ris views not enabled
    assert client.get('/political-businesses', status=404)
    assert client.get('/political-businesses/new', status=404)

    # enable ris
    settings = client.get('/module-activation-settings')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    # add parliamentary groups first
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Für ein schöneres Luzern'
    page = page.form.submit().follow()
    assert 'Für ein schöneres Luzern' in page

    page = client.get('/parliamentary-groups/new')
    page.form['name'] = 'Oberfraktion'
    page = page.form.submit().follow()
    assert 'Oberfraktion' in page

    # add parliamentarians
    new = client.get('/parliamentarians/new')
    new.form['first_name'] = 'Bau'
    new.form['last_name'] = 'Mann'
    new.form['email_primary'] = 'bau.mann@example.org'
    page = new.form.submit().follow()
    assert 'Bau' in page
    assert 'Mann' in page

    # add parliamentarian role
    role = page.click('Neue Fraktionsfunktion')
    options = role.form['parliamentary_group_id'].options
    id = next(
        (opt[0] for opt in options if opt[2] == 'Für ein schöneres Luzern'))
    role.form['parliamentary_group_id'] = id
    role.form['parliamentary_group_role'] = 'member'
    role.form.submit().follow()

    with freeze_time('2025-11-04 8:00'):
        page = client.get('/political-businesses')
        assert 'Es wurden noch keine politischen Geschäfte erfasst' in page

        page = page.click('Politisches Geschäft')
        title = 'How many congressmen does it take to change a light bulb?'
        page.form['title'] = title
        page.form['number'] = '25.10'
        page.form['political_business_type'] = 'inquiry'
        page.form['entry_date'] = '2025-10-02'
        page.form['status'] = 'pendent_legislative'
        page.form['chronology'] = 'Schriftlich beantwortet am 03.11.2025'
        options = page.form['parliamentary_groups'].options
        page.form['parliamentary_groups'] = [o[0] for o in options]
        page = page.form.submit().follow()
        assert title in page
        keywords = ['Für ein schöneres Luzern', 'Oberfraktion',
                    'Geschäftsart', 'Anfrage', 'Status', 'Pendent Legislative',
                    'Einreichungs-/Publikationsdatum', '02.10.2025',
                    'Chronologie', 'Schriftlich beantwortet am 03.11.2025']
        for keyword in keywords:
            assert keyword in page

        # edit adding author
        edit = page.click('Bearbeiten')
        options = edit.form['participants-0-parliamentarian_id'].options
        id = next(
            (opt[0] for opt in options if opt[2] == 'Mann Bau'))
        edit.form['participants-0-parliamentarian_id'] = id
        edit.form['participants-0-participant_type'] = 'First signatory'
        page = edit.form.submit().follow()
        assert 'Erstunterzeichner' in page
        keywords = ['Verfasser/Beteiligte', 'Mann', 'Bau', 'Erstunterzeichner',
                    'Fraktion', 'Geschäftsart', 'Anfrage',
                    'Status', 'Pendent Legislative',
                    'Einreichungs-/Publikationsdatum', '02.10.2025']
        for keyword in keywords:
            assert keyword in page
        assert 'Dokumente' not in page

        # test business overview and filters
        page = client.get('/political-businesses')
        keywords = [
            'Politische Geschäfte', '02.10.2025',
            'How many congressmen does it take to change a light bulb?',
            'Geschäftsart', 'Anfrage (1)',
            'Status', 'Pendent Legislative (1)', 'Jahr', '2025 (1)']
        for keyword in keywords:
            assert keyword in page

        # test search
        assert '02.10.2025' in client.get('/political-businesses?q=light')
        assert '02.10.2025' not in client.get('/political-businesses?q=bogus')

        # test malicious search
        assert '02.10.2025' not in client.get(
            '/political-businesses?q=----------------------------------light'
        )

        # out-of-range year and invalid status/type params must not error
        # and must not filter out valid results
        assert '02.10.2025' in client.get(
            '/political-businesses?years=843169290')
        assert '02.10.2025' in client.get(
            '/political-businesses?status=bogus')
        assert '02.10.2025' in client.get(
            '/political-businesses?types=mabis')

    # delete businesses
    (client.get('/political-businesses')
     .click('ow many congressmen does it take to change a light bulb?')
     .click('Löschen'))
    assert "Es wurden noch keine politischen Geschäfte erfasst" in client.get(
        "/political-businesses"
    )

    # delete parliamentarian
    client.get('/parliamentarians').click('Mann Bau').click('Löschen')
    assert (
        "Keine Filterergebnisse gefunden oder noch keine "
        "Parlamentarier erfasst"
        in client.get("/parliamentarians")
    )

    # delete parliamentary groups
    (client.get('/parliamentary-groups')
     .click('Für ein schöneres Luzern').click('Löschen'))
    (client.get('/parliamentary-groups')
     .click('Oberfraktion').click('Löschen'))
    groups = client.get('/parliamentary-groups')
    assert 'Noch keine Fraktionen erfasst' in groups
