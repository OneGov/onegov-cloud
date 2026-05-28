from __future__ import annotations

import datetime
import json
import transaction
import zipfile
from io import BytesIO

from onegov.pas.collections import PartyCollection
from onegov.pas.collections import PASParliamentaryGroupCollection
from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections.commission_membership import (
    PASCommissionMembershipCollection
)
from onegov.pas.models import PASCommissionMembership
from onegov.pas.models import PASParliamentarianRole
from onegov.pas.models import SettlementRun
from onegov.user import UserCollection
from uuid import UUID
from webtest import Upload


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import Client, ExtendedResponse
    from .conftest import TestPasApp


def add_rate_set(
    settings: ExtendedResponse,
    delete: list[ExtendedResponse]
) -> None:
    """Adds a rate set via the UI."""
    page = settings.click('Sätze')
    page = page.click(href='new')
    page.form['year'] = 2024
    page.form['cost_of_living_adjustment'] = 1
    page.form['plenary_none_president_halfday'] = 1
    page.form['plenary_none_member_halfday'] = 1
    page.form['commission_normal_president_initial'] = 1
    page.form['commission_normal_president_additional'] = 1
    page.form['study_normal_president_halfhour'] = 1
    page.form['commission_normal_member_initial'] = 1
    page.form['commission_normal_member_additional'] = 1
    page.form['study_normal_member_halfhour'] = 1
    page.form['commission_intercantonal_president_halfday'] = 1
    page.form['study_intercantonal_president_hour'] = 1
    page.form['commission_intercantonal_member_halfday'] = 1
    page.form['study_intercantonal_member_hour'] = 1
    page.form['shortest_all_president_halfhour'] = 1
    page.form['shortest_all_member_halfhour'] = 1
    page = page.form.submit().follow()
    assert 'CHF 1.-' in page

    page = page.click('Bearbeiten')
    page.form['cost_of_living_adjustment'] = 2
    page = page.form.submit().follow()
    assert '2%' in page
    delete.append(page)


def test_views_manage(client_with_fts: Client[TestPasApp]) -> None:
    client = client_with_fts
    client.login_admin()

    settings = client.get('/').follow().click('PAS Einstellungen')
    delete: list[ExtendedResponse] = []

    add_rate_set(settings, delete)

    # Settlement Runs
    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q1'
    page.form['start'] = '2024-01-01'
    page.form['end'] = '2024-12-31'
    page.form['closed'] = False
    page = page.form.submit().follow()
    assert '31.12.2024' in page

    page = page.click('Bearbeiten')
    page.form['end'] = '2024-03-31'
    page = page.form.submit().follow()
    assert '31.03.2024' in page

    delete.append(page)

    # Create read-only entities programmatically (imported via API)
    session = client.app.session()

    parties = PartyCollection(session)
    parties.add(name='AA')

    parl_groups = PASParliamentaryGroupCollection(session)
    parl_groups.add(name='BB')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='First',
        last_name='Last',
        gender='male',
        shipping_method='a',
        shipping_address='Address',
        shipping_address_zip_code='ZIP',
        shipping_address_city='City',
        email_primary='first.last@example.org',
    )

    session.add(
        PASParliamentarianRole(
            parliamentarian_id=parl.id,
            role='member',
            start=datetime.date(2020, 1, 1),
            meta={'org_type': 'Kantonsrat'},
        )
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='CC')

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2020, 1, 1),
    )

    session.flush()
    transaction.commit()

    # Verify entities are visible
    assert 'AA' in settings.click('Parteien')
    assert 'BB' in settings.click('Fraktionen')
    assert 'First Last' in settings.click('Parlamentarier:innen')
    assert 'CC' in settings.click('Kommissionen')

    # Attendences (still editable via UI)
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-02-02'
    page.form['duration'] = '1'
    page.form['type'] = 'commission'
    page.form['commission_id'].select(text='CC')
    page.form['parliamentarian_id'].select(text='First Last')
    page = page.form.submit().follow()
    assert 'Neue Anwesenheit hinzugefügt' in page

    # ... attendence
    page = client.get('/').follow().click('Anwesenheiten').click(
        href='new', index=0
    )
    page.form['date'] = '2024-02-03'
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='CC')
    page.form['parliamentarian_id'].select(text='First Last')
    page = page.form.submit().follow()
    assert 'Neue Anwesenheit hinzugefügt' in page

    page = page.click('Bearbeiten')
    page.form['duration'] = '0.5'
    page = page.form.submit().follow()
    assert '0.50h' in page

    delete.insert(0, page)

    # ... plenary
    page = client.get('/').follow().click('Anwesenheiten').click(
        href='new', index=1
    )
    page.form['date'] = '2024-02-04'
    page.form['duration'] = '3'
    page = page.form.submit().follow()
    assert 'Plenarsitzung hinzugefügt' in page

    page = client.get('/').follow().click('Anwesenheiten')
    assert '02.02.2024' in page
    assert '03.02.2024' in page
    assert '04.02.2024' in page

    # Changes
    page = client.get('/').follow().click('Aktivitäten')
    assert '02.02.2024' in page
    assert '03.02.2024' in page
    assert '04.02.2024' in page
    assert 'Anwesenheit bearbeitet' in page

    page = page.click(href='/change/', index=0)
    assert 'admin@example.org' in page

    # Test search results
    client = client.spawn()

    assert '0 Resultate' in client.get('/search?q=aa')
    assert '0 Resultate' in client.get('/search?q=bb')
    assert '0 Resultate' in client.get('/search?q=cc')
    assert '0 Resultate' in client.get('/search?q=first')
    assert '0 Resultate' in client.get('/search?q=Q1')

    client.login_admin()

    assert '1 Resultat' in client.get('/search?q=aa')
    assert '1 Resultat' in client.get('/search?q=bb')
    assert '1 Resultat' in client.get('/search?q=cc')
    assert '1 Resultat' in client.get('/search?q=first')
    assert '1 Resultat' in client.get('/search?q=Q1')

    # Delete (only rate set, settlement run, attendence — still editable)
    for page in delete:
        page.click('Löschen')
    assert 'Noch keine Sätze erfasst' in settings.click('Sätze')
    assert 'Noch keine Abrechnungsläufe erfasst' in (
           settings.click('Abrechnungsläufe'))


def test_view_upload_json(
    client: Client[TestPasApp],
    people_json: dict[str, Any],
    organization_json: dict[str, Any],
    memberships_json: dict[str, Any]
) -> None:
    """ Test successful import of all data using fixtures.

    *1. Understanding the Data and Models**

    **people.json**: Contains individual person data (Parliamentarians). Key
         fields are firstName, officialName, primaryEmail, tags, title, id.
         This maps to the Parliamentarian model.

    **organizations.json**:
        The organizationTypeTitle dictates the type of organization.
        - "Kommission":  Maps to Commission model.
        - "Kantonsrat":  This is a special case. It's not a Commission. It
        represents the Parliament itself. We link this as ParliamentarianRole
        directly on the Parliamentarian model with role='member' and associated
        with the Kantonsrat organization.
        - "Fraktion":  Maps to ParliamentaryGroup.
        - "Sonstige": Could be various types. Let's see how these are intended
          to be modeled. We need more clarity on how "Sonstige" is categorized.

    **memberships.json**: Connects person and organization.
        It defines the role within that organization, start, end dates.
        The nested person and organization blocks are crucial for establishing
        relationships.
    """

    client.login_admin()

    # --- Reference: Previously used function for local file testing ---
    # import os
    # def yield_paths():
    #     """ Yields paths in this order: organization, membership, people """
    #     base_path = '/path/to/your/local/json/files' # Adjust this path
    #     yield [base_path + '/organization.json']
    #     membership_count = 7 # Adjust as needed
    #     membership_paths = [
    #         f'{base_path}/memberships_{i}.json'
    #         for i in range(1, membership_count + 1)
    #     ]
    #     assert all(
    #         os.path.exists(path) for path in membership_paths
    #     ), "Some membership paths don't exist"
    #     yield membership_paths
    #
    #     # Yield people paths after validating existence
    #     # Adjust as needed:
    #     people_paths = [f'{base_path}/people_{i}.json' for i in range(1, 3)]
    #     assert all(
    #         os.path.exists(path) for path in people_paths
    #     ), "Some people paths don't exist"
    #     yield people_paths


    # def upload_file(filepath):
    #     with open(filepath, 'rb') as f:
    #         content = f.read()
    #         return Upload(
    #             os.path.basename(filepath),
    #             content,
    #             'application/json'
    #         )

    # # Get all paths
    # paths_generator = yield_paths()

    # org_paths = next(paths_generator)
    # page.form['organizations_source'] = [
    #     upload_file(path) for path in org_paths
    # ]

    # membership_paths = next(paths_generator)
    # page.form['memberships_source'] = [
    #     upload_file(path) for path in membership_paths
    # ]

    # people_paths = next(paths_generator)
    # page.form['people_source'] = [
    #     upload_file(path) for path in people_paths
    # ]


    # --- End Reference ---

    def create_upload_object(
        filename: str, data: dict[str, list[Any]]
    ) -> Upload:
        """Creates a webtest Upload object from a dictionary."""
        content_bytes = json.dumps(data).encode('utf-8')
        return Upload(
            filename,
            content_bytes,
            'application/json'
        )

    def do_upload_procedure(
        org_data: dict[str, Any],
        member_data: dict[str, Any],
        ppl_data: dict[str, Any]
    ) -> ExtendedResponse:
        """Uploads data using Upload objects created from fixtures."""
        page = client.get('/pas-import')

        # Create Upload objects from the fixture data
        # We wrap the list in the expected 'results' structure if needed,
        # matching the fixture structure.
        org_upload = create_upload_object('organization.json', org_data)
        # Assuming memberships_json fixture contains the 'results' list
        memberships_upload = create_upload_object(
            'memberships.json', member_data
        )
        # Assuming people_json fixture contains the 'results' list
        people_upload = create_upload_object('people.json', ppl_data)

        # Assign the Upload objects to the form fields
        # Note: The form expects a list of uploads, even if there's only one.
        page.form['validate_schema'] = False
        page.form['organizations_source'] = [org_upload]
        page.form['memberships_source'] = [memberships_upload]
        page.form['people_source'] = [people_upload]

        # Submit the form
        result = page.form.submit().maybe_follow()

        # Add assertions as needed
        assert result.status_code == 200, f"Import failed: {result.text}"
        return result

    # --- First Import ---
    result1 = do_upload_procedure(
        organization_json, memberships_json, people_json
    )

    # Check the import logs after first import
    logs_page = client.get('/import-logs')
    assert logs_page.status_code == 200
    # Todo: This should validate all columns on all table
    # For example address is not checked here.

    # --- Second Import (Test idempotency) ---
    # Run the import again with the same data, to test robustness
    do_upload_procedure(
        organization_json, memberships_json, people_json
    )

    # Check logs again after second import
    logs_page = client.get('/import-logs')
    assert logs_page.status_code == 200, "Could not load import logs page"
    # Should now have two logs
    assert len(logs_page.pyquery('tbody tr')) == 2
    assert 'Abgeschlossen' in logs_page.pyquery(
        'tbody tr:first-child .import-status'
    ).text()
    assert 'Abgeschlossen' in logs_page.pyquery(
        'tbody tr:last-child .import-status'
    ).text()


def test_copy_rate_set(client: Client[TestPasApp]) -> None:
    client.login_admin()

    settings = client.get('/').follow().click('PAS Einstellungen')
    add_rate_set(settings, [])

    page = client.get('/rate-sets')
    page = page.click('Inaktiv')

    href = page.pyquery('a.copy-icon').attr('href')
    href = href.replace('http://localhost', '')
    copy_page = client.get(href)

    # Create new rateset, change just the year other values remain
    copy_page.form['year'] = '2025'
    new_page = copy_page.form.submit().follow()
    assert '2025' in new_page


def test_simple_attendence_add(client: Client[TestPasApp]) -> None:
    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')

    add_rate_set(settings, [])

    # Settlement Runs
    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q1'
    page.form['start'] = '2024-01-01'
    page.form['end'] = '2024-03-31'
    page.form['closed'] = False
    page = page.form.submit().follow()

    # Create read-only entities programmatically
    session = client.app.session()

    parties = PartyCollection(session)
    parties.add(name='BB')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='First',
        last_name='Last',
        gender='male',
        shipping_method='a',
        shipping_address='Address',
        shipping_address_zip_code='ZIP',
        shipping_address_city='City',
        email_primary='first.last@example.org',
    )

    session.add(
        PASParliamentarianRole(
            parliamentarian_id=parl.id,
            role='member',
            start=datetime.date(2020, 1, 1),
            meta={'org_type': 'Kantonsrat'},
        )
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='DD')

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2020, 1, 1),
    )

    session.flush()
    transaction.commit()

    # Attendences
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-02-02'
    page.form['duration'] = '1'
    page.form['type'] = 'commission'
    page.form['commission_id'].select(text='DD')
    page.form['parliamentarian_id'].select(text='First Last')
    page = page.form.submit().follow()
    assert 'Neue Anwesenheit hinzugefügt' in page

    page = client.get('/').follow().click('Anwesenheiten').click(
        href='new', index=0
    )
    page.form['date'] = '2024-02-03'
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='DD')
    page.form['parliamentarian_id'].select(text='First Last')
    page = page.form.submit().follow()
    assert 'Neue Anwesenheit hinzugefügt' in page


def test_attendance_blocked_outside_any_settlement_run(
    client: Client[TestPasApp],
) -> None:
    """Test that attendance cannot be created outside any settlement run."""

    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')

    add_rate_set(settings, [])

    # Create a settlement run with a specific period
    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q2 2024'
    page.form['start'] = '2024-04-01'
    page.form['end'] = '2024-06-30'
    page.form['closed'] = False
    page = page.form.submit().follow()

    # Create read-only entities programmatically
    session = client.app.session()

    parties = PartyCollection(session)
    parties.add(name='Test Party')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='Test',
        last_name='User',
        gender='male',
        shipping_method='a',
        shipping_address='Address',
        shipping_address_zip_code='ZIP',
        shipping_address_city='City',
        email_primary='test@example.org',
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')

    session.add(
        PASParliamentarianRole(
            parliamentarian_id=parl.id,
            role='member',
            start=datetime.date(2020, 1, 1),
            meta={'org_type': 'Kantonsrat'},
        )
    )

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2020, 1, 1),
    )

    session.flush()
    transaction.commit()

    # TEST 1: Try to create attendance BEFORE settlement run period
    # Should fail - NOT within any settlement run
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-03-15'  # Before Q2 starts
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='Test Commission')
    result = page.form.submit()

    # Form should NOT be submitted (200 status, not redirect)
    assert result.status_code == 200
    assert 'Neue Anwesenheit hinzugefügt' not in result
    assert 'input' in result and 'date' in result

    # TEST 2: Try to create attendance AFTER settlement run period
    # Should fail - NOT within any settlement run
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-07-15'  # After Q2 ends
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='Test Commission')
    result = page.form.submit()

    # Form should NOT be submitted (200 status, not redirect)
    assert result.status_code == 200
    assert 'Neue Anwesenheit hinzugefügt' not in result
    assert 'input' in result and 'date' in result

    # TEST 3: Create attendance WITHIN settlement run period
    # Should succeed
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-05-15'  # Within Q2 period
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='Test Commission')
    page = page.form.submit().follow()

    # Should successfully create attendance
    assert 'Neue Anwesenheit hinzugefügt' in page


def test_fetch_commissions_parliamentarians_json(
    client: Client[TestPasApp]
) -> None:
    """Test the commissions-parliamentarians-json endpoint that the JS
    dropdown uses."""

    session = client.app.session()
    commissions = PASCommissionCollection(session)
    commission1 = commissions.add(name='Commission A')
    commission2 = commissions.add(name='Commission B')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl1 = parliamentarians.add(
        first_name='John',
        last_name='Doe',
    )
    parl2 = parliamentarians.add(
        first_name='Jane',
        last_name='Smith',
    )
    parl3 = parliamentarians.add(
        first_name='Bob',
        last_name='Johnson',
    )

    for p in (parl1, parl2, parl3):
        session.add(PASParliamentarianRole(
            parliamentarian_id=p.id,
            role='member',
            meta={'org_type': 'Kantonsrat'},
        ))

    memberships = PASCommissionMembershipCollection(session)

    # Commission A has John and Jane
    memberships.add(commission_id=commission1.id, parliamentarian_id=parl1.id)
    memberships.add(commission_id=commission1.id, parliamentarian_id=parl2.id)

    # Commission B has Bob
    memberships.add(commission_id=commission2.id, parliamentarian_id=parl3.id)

    session.flush()
    commission1_id = str(commission1.id)
    commission2_id = str(commission2.id)
    parl1_title = parl1.title
    parl2_title = parl2.title
    parl3_title = parl3.title
    parl3_id = str(parl3.id)
    transaction.commit()

    client.login_admin()
    response = client.get('/commissions/commissions-parliamentarians-json')
    assert response.status_code == 200
    assert response.content_type == 'application/json'

    data = response.json

    assert isinstance(data, dict)

    # Commission A should have John and Jane
    assert commission1_id in data
    commission_a_parliamentarians = data[commission1_id]
    assert len(commission_a_parliamentarians) == 2

    parl_names = [p['title'] for p in commission_a_parliamentarians]
    assert parl1_title in parl_names
    assert parl2_title in parl_names

    for parl in commission_a_parliamentarians:
        assert 'id' in parl
        assert 'title' in parl
        assert isinstance(parl['id'], str)  # JS expects string IDs
        assert isinstance(parl['title'], str)

    # Commission B should have Bob
    assert commission2_id in data
    commission_b_parliamentarians = data[commission2_id]
    assert len(commission_b_parliamentarians) == 1
    assert commission_b_parliamentarians[0]['title'] == parl3_title
    assert commission_b_parliamentarians[0]['id'] == parl3_id

    # Test edge cases
    session = client.app.session()
    commissions = PASCommissionCollection(session)
    commission3 = commissions.add(name='Empty Commission')
    session.flush()
    commission3_id = str(commission3.id)

    response2 = client.get('/commissions/commissions-parliamentarians-json')
    data2 = response2.json
    assert commission3_id not in data2

    # Test commission_president role filtering
    # Create a commission president for Commission A only
    session = client.app.session()
    parl_president = parliamentarians.add(
        first_name='Alice',
        last_name='President',
        email_primary='alice.president@example.org',
        zg_username='zgalice',
    )
    session.add(PASParliamentarianRole(
        parliamentarian_id=parl_president.id,
        role='member',
        meta={'org_type': 'Kantonsrat'},
    ))

    # Add president to Commission A (using the ID we saved earlier)
    president_membership = PASCommissionMembership(
        parliamentarian_id=parl_president.id,
        commission_id=UUID(commission1_id),
        role='president'
    )
    session.add(president_membership)

    # Create and configure user
    users = UserCollection(session)
    user = users.by_username('zgalice')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'
    user.active = True

    transaction.commit()

    # Login as commission president
    client.login('zgalice', 'test')

    # Commission president should only see Commission A
    # (where they're president)
    response3 = client.get('/commissions/commissions-parliamentarians-json')
    assert response3.status_code == 200
    data3 = response3.json

    # Should have Commission A (where they're president)
    assert commission1_id in data3
    # John, Jane, and Alice (the president)
    assert len(data3[commission1_id]) == 3

    # Verify Alice, John, and Jane are all present
    parl_titles_in_commission_a = {p['title'] for p in data3[commission1_id]}
    assert 'Alice President' in parl_titles_in_commission_a
    assert parl1_title in parl_titles_in_commission_a
    assert parl2_title in parl_titles_in_commission_a

    # Should NOT have Commission B (where they're not president)
    assert commission2_id not in data3

    # Should NOT have empty Commission 3
    assert commission3_id not in data3


def test_commissions_view_filtered_by_role(
    client: Client[TestPasApp],
) -> None:
    session = client.app.session()

    commissions = PASCommissionCollection(session)
    commission_a = commissions.add(name='Finanzkommission')
    commission_b = commissions.add(name='Bildungskommission')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='Pia',
        last_name='Member',
        email_primary='pia@example.org',
        zg_username='zgpia',
    )
    pres = parliamentarians.add(
        first_name='Alice',
        last_name='President',
        email_primary='alice@example.org',
        zg_username='zgalice',
    )

    session.add(
        PASCommissionMembership(
            parliamentarian_id=parl.id,
            commission_id=commission_a.id,
            role='member',
        )
    )
    session.add(
        PASCommissionMembership(
            parliamentarian_id=pres.id,
            commission_id=commission_a.id,
            role='president',
        )
    )
    session.add(
        PASCommissionMembership(
            parliamentarian_id=pres.id,
            commission_id=commission_b.id,
            role='member',
        )
    )

    users = UserCollection(session)

    user_parl = users.by_username('zgpia')
    assert user_parl is not None
    user_parl.role = 'parliamentarian'
    user_parl.password = 'test'
    user_parl.active = True

    user_pres = users.by_username('zgalice')
    assert user_pres is not None
    user_pres.role = 'commission_president'
    user_pres.password = 'test'
    user_pres.active = True

    transaction.commit()

    # Admin sees all commissions
    client.login_admin()
    page = client.get('/commissions')
    assert 'Finanzkommission' in page
    assert 'Bildungskommission' in page

    # Parliamentarian sees only their commission (A)
    client.login('zgpia', 'test')
    page = client.get('/commissions')
    assert 'Finanzkommission' in page
    assert 'Bildungskommission' not in page

    # Commission president sees both (member of both)
    client.login('zgalice', 'test')
    page = client.get('/commissions')
    assert 'Finanzkommission' in page
    assert 'Bildungskommission' in page


def test_add_new_user_without_activation_email(
    client: Client[TestPasApp]
) -> None:

    client.login_admin()

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'admin@example.org'

    assert "existiert bereits" in new.form.submit()

    new.form['username'] = 'secondadmin@example.org'
    new.form['role'] = 'admin'
    new.form['send_activation_email'] = False
    added = new.form.submit()

    assert "Passwort" in added
    password = added.pyquery('.panel strong').text()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'secondadmin@example.org'
    login.form['password'] = password
    assert login.form.submit().status_code == 302


def test_settlement_run_complete_translation(
    client: Client[TestPasApp],
) -> None:
    """Test that 'Complete' is translated to 'Abgeschlossen' in the
    settlement run view."""
    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')

    add_rate_set(settings, [])

    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q1'
    page.form['start'] = '2024-01-01'
    page.form['end'] = '2024-03-31'
    page.form['closed'] = False
    page = page.form.submit().follow()

    # Create read-only entities programmatically
    session = client.app.session()

    parties = PartyCollection(session)
    parties.add(name='TestParty')

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='Test',
        last_name='Person',
        gender='male',
        shipping_method='a',
        shipping_address='Address',
        shipping_address_zip_code='ZIP',
        shipping_address_city='City',
        email_primary='test.person@example.org',
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='TestCommission')

    session.add(PASParliamentarianRole(
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2020, 1, 1),
        meta={'org_type': 'Kantonsrat'},
    ))

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2020, 1, 1),
    )

    session.flush()
    transaction.commit()

    # Create attendance with abschluss via standalone form
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-02-02'
    page.form['duration'] = '1'
    page.form['type'] = 'commission'
    page.form['commission_id'].select(text='TestCommission')
    page.form['parliamentarian_id'].select(text='Test Person')
    page.form['abschluss'] = True
    page = page.form.submit().follow()

    page = settings.click('Abrechnungsläufe')
    page = page.click('Q1')

    assert '✓ Abgeschlossen' in page
    assert '✓ Complete' not in page


def test_commission_president_bulk_add(
    client: Client[TestPasApp],
) -> None:
    session = client.app.session()
    session.add(
        SettlementRun(
            name='Q1 2024',
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 12, 31),
            active=True,
            closed=False,
        )
    )

    parliamentarians = PASParliamentarianCollection(client.app)
    bob = parliamentarians.add(
        first_name='Bob',
        last_name='Member',
        email_primary='bob.member@example.org',
        zg_username='zgbob',
    )
    alice = parliamentarians.add(
        first_name='Alice',
        last_name='President',
        email_primary='alice.president@example.org',
        zg_username='zgalice',
    )

    for p in (bob, alice):
        session.add(PASParliamentarianRole(
            parliamentarian_id=p.id,
            role='member',
            meta={'org_type': 'Kantonsrat'},
        ))

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finanzkommission')

    session.add(
        PASCommissionMembership(
            parliamentarian_id=bob.id,
            commission_id=commission.id,
            role='member',
        )
    )
    session.add(
        PASCommissionMembership(
            parliamentarian_id=alice.id,
            commission_id=commission.id,
            role='president',
        )
    )

    commission_id = str(commission.id)
    bob_id = str(bob.id)
    alice_id = str(alice.id)

    users = UserCollection(session)
    president_user = users.by_username('zgalice')
    assert president_user is not None
    president_user.role = 'commission_president'
    president_user.password = 'test'
    president_user.active = True
    transaction.commit()

    client.login('zgalice', 'test')

    page = client.get('/attendences')
    assert 'Massenbuchung Kommissionssitzung' in page

    page = client.get('/attendences/new-commission-bulk')
    assert page.status_code == 200
    page.form['date'] = '2024-06-01'
    page.form['type'] = 'commission'
    page.form['duration'] = '2'
    page.form['commission_id'] = commission_id
    page.form['abschluss'] = False
    page.form['parliamentarian_id'] = [bob_id, alice_id]
    page = page.form.submit().maybe_follow()
    assert page.status_code == 200


def test_abschluss_blocks_second_bulk_add(
    client: Client[TestPasApp],
) -> None:
    from onegov.pas.models import Attendence

    session = client.app.session()
    session.add(
        SettlementRun(
            name='Q1 2024',
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 12, 31),
            active=True,
            closed=False,
        )
    )

    parliamentarians = PASParliamentarianCollection(client.app)
    bob = parliamentarians.add(
        first_name='Bob',
        last_name='Member',
        email_primary='bob.member@example.org',
        zg_username='zgbob',
    )
    alice = parliamentarians.add(
        first_name='Alice',
        last_name='President',
        email_primary='alice.president@example.org',
        zg_username='zgalice',
    )

    for p in (bob, alice):
        session.add(
            PASParliamentarianRole(
                parliamentarian_id=p.id,
                role='member',
                meta={'org_type': 'Kantonsrat'},
            )
        )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finanzkommission')

    session.add(
        PASCommissionMembership(
            parliamentarian_id=bob.id,
            commission_id=commission.id,
            role='member',
        )
    )
    session.add(
        PASCommissionMembership(
            parliamentarian_id=alice.id,
            commission_id=commission.id,
            role='president',
        )
    )

    commission_id = str(commission.id)
    bob_id = str(bob.id)
    alice_id = str(alice.id)

    users = UserCollection(session)
    president_user = users.by_username('zgalice')
    assert president_user is not None
    president_user.role = 'commission_president'
    president_user.password = 'test'
    president_user.active = True
    transaction.commit()

    client.login('zgalice', 'test')

    page = client.get('/attendences/new-commission-bulk')
    assert page.status_code == 200
    page.form['date'] = '2024-06-01'
    page.form['type'] = 'commission'
    page.form['duration'] = '2'
    page.form['commission_id'] = commission_id
    page.form['abschluss'] = True
    page.form['parliamentarian_id'] = [bob_id, alice_id]
    page = page.form.submit().maybe_follow()
    assert page.status_code == 200

    session = client.app.session()
    count_after_first = session.query(Attendence).count()
    assert count_after_first == 2

    page = client.get('/attendences/new-commission-bulk')
    assert page.status_code == 200
    page.form['date'] = '2024-07-15'
    page.form['type'] = 'commission'
    page.form['duration'] = '3'
    page.form['commission_id'] = commission_id
    page.form['abschluss'] = False
    page.form['parliamentarian_id'] = [bob_id, alice_id]
    page = page.form.submit()

    assert 'abschluss' in page.text.lower()

    session = client.app.session()
    count_after_second = session.query(Attendence).count()
    assert count_after_second == 2


def test_presidential_allowance_view(client: Client[TestPasApp]) -> None:
    client.login_admin()

    # Step 1: PAS settings shows the Präsidialzulagen card
    settings = client.get('/').follow().click('PAS Einstellungen')
    assert 'Präsidialzulagen' in settings

    # Step 2: Create parliamentarians with president/VP roles
    # and settlement runs
    session = client.app.session()
    parliamentarians = PASParliamentarianCollection(client.app)
    president = parliamentarians.add(
        first_name='Hans',
        last_name='Präsident',
        email_primary='hans.praesident@example.org',
        zg_username='zghans',
    )
    vice = parliamentarians.add(
        first_name='Lisa',
        last_name='Vizepräsidentin',
        email_primary='lisa.vize@example.org',
        zg_username='zglisa',
    )
    session.flush()
    president_id = str(president.id)
    vice_id = str(vice.id)
    session.add(PASParliamentarianRole(
        parliamentarian_id=president.id,
        role='president',
    ))
    session.add(PASParliamentarianRole(
        parliamentarian_id=vice.id,
        role='vice_president',
    ))

    run1 = SettlementRun(
        name='Q1 2026',
        start=datetime.date(2026, 1, 1),
        end=datetime.date(2026, 3, 31),
        active=True,
        closed=False,
    )
    run2 = SettlementRun(
        name='Q2 2026',
        start=datetime.date(2026, 4, 1),
        end=datetime.date(2026, 6, 30),
        active=True,
        closed=False,
    )
    session.add(run1)
    session.add(run2)
    session.flush()
    run1_id = str(run1.id)
    run2_id = str(run2.id)
    transaction.commit()

    pres_value = f'{president_id}:president'
    vice_value = f'{vice_id}:vice_president'

    # Submit allowance for president on run1
    page = client.get('/presidential-allowances/new')
    assert 'Zulage hinzufügen' in page
    page.form['settlement_run'] = run1_id
    page.form['recipient'] = pres_value
    page = page.form.submit().follow()
    assert 'Zulage hinzugefügt' in page
    assert 'Hans Präsident' in page
    assert 'Q1 2026' in page

    # Submit allowance for vice president on run1
    page = client.get('/presidential-allowances/new')
    page.form['settlement_run'] = run1_id
    page.form['recipient'] = vice_value
    page = page.form.submit().follow()
    assert 'Zulage hinzugefügt' in page
    assert 'Lisa Vizepräsidentin' in page

    # Fill run1 to max (4): add 2 more on run1
    for val in (pres_value, vice_value):
        page = client.get('/presidential-allowances/new')
        page.form['settlement_run'] = run1_id
        page.form['recipient'] = val
        page = page.form.submit().follow()
        assert 'Zulage hinzugefügt' in page

    # 5th allowance on run1 should fail (max 4 per run)
    page = client.get('/presidential-allowances/new')
    page.form['settlement_run'] = run1_id
    page.form['recipient'] = pres_value
    result = page.form.submit()
    assert result.status_code == 200
    assert 'Maximum' in result

    # But adding on run2 still works
    page = client.get('/presidential-allowances/new')
    page.form['settlement_run'] = run2_id
    page.form['recipient'] = pres_value
    page = page.form.submit().follow()
    assert 'Zulage hinzugefügt' in page

    # Fill up yearly limit for president (20k = 4 × 5000)
    # Already have 3 president allowances (2 on run1, 1 on run2)
    # Need 1 more to hit limit
    page = client.get('/presidential-allowances/new')
    page.form['settlement_run'] = run2_id
    page.form['recipient'] = pres_value
    page = page.form.submit().follow()
    assert 'Zulage hinzugefügt' in page

    # 5th president allowance should fail (yearly limit)
    page = client.get('/presidential-allowances/new')
    page.form['settlement_run'] = run2_id
    page.form['recipient'] = pres_value
    result = page.form.submit()
    assert result.status_code == 200
    assert 'CHF 20000' in result


def test_abschluss_email_uses_commission_name(
    client: Client[TestPasApp],
) -> None:
    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')
    add_rate_set(settings, [])

    session = client.app.session()
    session.add(
        SettlementRun(
            name='Q1 2024',
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 12, 31),
            active=True,
            closed=False,
        )
    )

    parliamentarians = PASParliamentarianCollection(client.app)
    parl = parliamentarians.add(
        first_name='Max',
        last_name='Muster',
        email_primary='max.muster@example.org',
    )

    session.add(PASParliamentarianRole(
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2024, 1, 1),
        meta={'org_type': 'Kantonsrat'},
    ))

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finanzkommission')

    PASCommissionMembershipCollection(session).add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=datetime.date(2024, 1, 1),
    )

    session.flush()
    transaction.commit()

    # Create attendance without abschluss first
    page = (
        client.get('/')
        .follow()
        .click('Anwesenheiten')
        .click(href='new', index=0)
    )
    page.form['date'] = '2024-06-15'
    page.form['duration'] = '2'
    page.form['type'] = 'commission'
    page.form['commission_id'].select(text='Finanzkommission')
    page.form['parliamentarian_id'].select(text='Max Muster')
    page.form['abschluss'] = False
    page = page.form.submit().follow()

    # Now edit to set abschluss — this triggers the email
    page = page.click('Bearbeiten')
    page.form['abschluss'] = True
    page.form.submit().follow()

    email = client.get_email(0)
    assert email['Subject'] == ('PAS: Abschluss gesetzt für Finanzkommission')
    assert 'Finanzkommission' in email['HtmlBody']
    assert 'Max Muster' in email['HtmlBody']


def test_parliamentarian_pdf_zip_download(
    client: Client[TestPasApp],
) -> None:
    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')
    add_rate_set(settings, [])

    session = client.app.session()
    session.add(
        SettlementRun(
            name='Q1 2024',
            start=datetime.date(2024, 1, 1),
            end=datetime.date(2024, 12, 31),
            active=True,
            closed=False,
        )
    )

    parliamentarians = PASParliamentarianCollection(client.app)
    alice = parliamentarians.add(
        first_name='Alice',
        last_name='Aaberg',
        email_primary='alice@example.org',
    )
    bob = parliamentarians.add(
        first_name='Bob',
        last_name='Baumann',
        email_primary='bob@example.org',
    )

    parties = PartyCollection(session)
    party = parties.add(name='TestPartei')

    session.add(
        PASParliamentarianRole(
            parliamentarian_id=alice.id,
            role='member',
            party=party,
            start=datetime.date(2024, 1, 1),
        )
    )
    session.add(
        PASParliamentarianRole(
            parliamentarian_id=bob.id,
            role='member',
            party=party,
            start=datetime.date(2024, 1, 1),
        )
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='TestKommission')

    PASCommissionMembershipCollection(session).add(
        commission_id=commission.id,
        parliamentarian_id=alice.id,
        role='member',
        start=datetime.date(2024, 1, 1),
    )
    PASCommissionMembershipCollection(session).add(
        commission_id=commission.id,
        parliamentarian_id=bob.id,
        role='member',
        start=datetime.date(2024, 1, 1),
    )

    session.flush()

    # Add attendances for both
    from onegov.pas.models import Attendence

    session.add(
        Attendence(
            parliamentarian=alice,
            commission=commission,
            date=datetime.date(2024, 3, 10),
            duration=120,
            type='commission',
        )
    )
    session.add(
        Attendence(
            parliamentarian=bob,
            commission=commission,
            date=datetime.date(2024, 3, 10),
            duration=120,
            type='commission',
        )
    )
    session.flush()
    transaction.commit()

    # Navigate to settlement run and find ZIP link
    page = settings.click('Abrechnungsläufe')
    page = page.click('Q1 2024')
    assert 'Alle Parlamentarier:innen (ZIP)' in page

    resp = page.click(href='all-parliamentarians-zip')
    assert resp.status_code == 200
    assert resp.content_type == 'application/zip'
    assert resp.content_disposition is not None
    assert '.zip' in resp.content_disposition

    zf = zipfile.ZipFile(BytesIO(resp.body))
    names = zf.namelist()
    assert len(names) == 2
    assert all(n.endswith('.pdf') for n in names)
    assert any('Aaberg' in n for n in names)
    assert any('Baumann' in n for n in names)

    for name in names:
        pdf_bytes = zf.read(name)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:4] == b'%PDF'
