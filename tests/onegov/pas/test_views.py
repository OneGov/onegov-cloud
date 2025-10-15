import pytest
import json
import transaction
from webtest import Upload

from typing import Any
from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections.commission_membership import (
    PASCommissionMembershipCollection
)


def add_rate_set(settings, delete) -> None:
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
    page.form['commission_official_president_halfday'] = 1
    page.form['commission_official_president_fullday'] = 1
    page.form['study_official_president_halfhour'] = 1
    page.form['commission_official_vice_president_halfday'] = 1
    page.form['commission_official_vice_president_fullday'] = 1
    page.form['study_official_member_halfhour'] = 1
    page.form['shortest_all_president_halfhour'] = 1
    page.form['shortest_all_member_halfhour'] = 1
    page = page.form.submit().follow()
    assert 'CHF 1.-' in page

    page = page.click('Bearbeiten')
    page.form['cost_of_living_adjustment'] = 2
    page = page.form.submit().follow()
    assert '2%' in page
    delete.append(page)


@pytest.mark.flaky(reruns=5, only_rerun=None)
def test_views_manage(client_with_fts):
    client = client_with_fts
    client.login_admin()

    settings = client.get('/').follow().click('PAS Einstellungen')
    delete = []

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

    # parties
    page = settings.click('Parteien')
    page = page.click(href='new')
    page.form['name'] = 'BB'
    page = page.form.submit().follow()
    assert 'BB' in page

    page = page.click('Bearbeiten')
    page.form['name'] = 'AA'
    page = page.form.submit().follow()
    assert 'AA' in page

    delete.append(page)

    # Parliamentarian Group
    page = settings.click('Fraktionen')
    page = page.click(href='new')
    page.form['name'] = 'CC'
    page = page.form.submit().follow()
    assert 'CC' in page

    page = page.click('Bearbeiten')
    page.form['name'] = 'BB'
    page = page.form.submit().follow()
    assert 'BB' in page

    delete.append(page)

    # Parliamentarian
    page = settings.click('Parlamentarier:innen')
    page = page.click(href='new')
    page.form['gender'] = 'male'
    page.form['first_name'] = 'First'
    page.form['last_name'] = 'Last'
    page.form['shipping_method'] = 'a'
    page.form['shipping_address'] = 'Address'
    page.form['shipping_address_zip_code'] = 'ZIP'
    page.form['shipping_address_city'] = 'City'
    page.form['email_primary'] = 'first.last@example.org'
    page = page.form.submit().follow()
    assert 'First Last' in page
    assert ' Das Parlamentsmitglied wurde automatisch für den' in page

    page = page.click('Bearbeiten')
    page.form['gender'] = 'female'
    page = page.form.submit().follow()
    assert 'weiblich' in page

    delete.append(page)

    # Role
    page = page.click(href='new')
    page.form['role'] = 'member'
    page.form['start'] = '2020-01-01'
    page = page.form.submit().follow()
    assert 'Mitglied Parlament' in page

    page = page.click('Mitglied Parlament').click('Bearbeiten')
    page.form['role'] = 'president'
    page = page.form.submit().follow()
    assert 'Präsident:in Parlament' in page

    # Commission
    page = settings.click('Kommissionen')
    page = page.click(href='new')
    page.form['name'] = 'DD'
    page = page.form.submit().follow()
    assert 'DD' in page

    page = page.click('Bearbeiten')
    page.form['name'] = 'CC'
    page = page.form.submit().follow()
    assert 'CC' in page

    delete.append(page)

    # Commission Membership
    page = page.click(href='new-membership')
    page.form['role'] = 'member'
    page.form['start'] = '2020-01-01'
    page = page.form.submit().follow()
    assert 'Mitglied' in page

    page = page.click('Mitglied').click('Bearbeiten')
    page.form['role'] = 'president'
    page = page.form.submit().follow()
    assert 'Präsident:in' in page

    # Attendences
    # ... commission
    page = page.click(href='add-attendence')
    page.form['date'] = '2024-02-02'
    page.form['duration'] = '1'
    page.form['type'] = 'commission'
    page = page.form.submit().follow()
    assert 'Kommissionsitzung hinzugefügt' in page

    # ... attendence
    page = client.get('/').follow().click('Anwesenheiten').click(
        href='new', index=0
    )
    page.form['date'] = '2024-02-03'
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='CC')
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
    assert '2 Resultate' in client.get('/search?q=first')
    assert '1 Resultat' in client.get('/search?q=Q1')

    # Delete
    for page in delete:
        page.click('Löschen')
    assert 'Noch keine Sätze erfasst' in settings.click('Sätze')
    assert 'Noch keine Abrechnungsläufe erfasst' in (
           settings.click('Abrechnungsläufe'))
    assert 'Noch keine Parteien erfasst' in settings.click('Parteien')
    assert 'Noch keine Fraktionen erfasst' in settings.click('Fraktionen')
    assert 'Noch keine Parlamentarier:innen erfasst' in (
           settings.click('Parlamentarier:innen'))


def test_view_upload_json(
    client,
    people_json,
    organization_json,
    memberships_json
):
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
        org_data,
        member_data,
        ppl_data
    ):
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
        assert result.status_code == 200
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


def test_copy_rate_set(client):
    client.login_admin()

    settings = client.get('/').follow().click('PAS Einstellungen')
    delete = []
    add_rate_set(settings, delete)

    page = client.get('/rate-sets')
    page = page.click('Inaktiv')

    href = page.pyquery('a.copy-icon').attr('href')
    href = href.replace('http://localhost', '')
    copy_page = client.get(href)

    # Create new rateset, change just the year other values remain
    copy_page.form['year'] = '2025'
    new_page = copy_page.form.submit().follow()
    assert '2025' in new_page


def test_simple_attendence_add(client):
    client.login_admin()
    settings = client.get('/').follow().click('PAS Einstellungen')
    delete = []

    add_rate_set(settings, delete)

    # Settlement Runs
    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q1'
    page.form['start'] = '2024-01-01'
    page.form['end'] = '2024-03-31'
    page.form['closed'] = False
    page = page.form.submit().follow()

    # parties
    page = settings.click('Parteien')
    page = page.click(href='new')
    page.form['name'] = 'BB'
    page = page.form.submit().follow()
    assert 'BB' in page

    # Parliamentarian
    page = settings.click('Parlamentarier:innen')
    page = page.click(href='new')
    page.form['personnel_number'] = '666999'
    page.form['gender'] = 'male'
    page.form['first_name'] = 'First'
    page.form['last_name'] = 'Last'
    page.form['shipping_method'] = 'a'
    page.form['shipping_address'] = 'Address'
    page.form['shipping_address_zip_code'] = 'ZIP'
    page.form['shipping_address_city'] = 'City'
    page.form['email_primary'] = 'first.last@example.org'
    page = page.form.submit().follow()
    assert 'First Last' in page

    page = page.click('Bearbeiten')
    page.form['gender'] = 'female'
    page = page.form.submit().follow()
    assert 'weiblich' in page

    # Role
    page = page.click(href='new')
    page.form['role'] = 'member'
    page.form['start'] = '2020-01-01'
    page = page.form.submit().follow()
    assert 'Mitglied Parlament' in page

    # Commission
    page = settings.click('Kommissionen')
    page = page.click(href='new')
    page.form['name'] = 'DD'
    page = page.form.submit().follow()
    assert 'DD' in page

    # Commission Membership
    page = page.click(href='new-membership')
    page.form['role'] = 'member'
    page.form['start'] = '2020-01-01'
    page = page.form.submit().follow()
    assert 'Mitglied' in page

    # make president
    # page = page.click('Mitglied').click('Bearbeiten')
    # page.form['role'] = 'president'
    # page = page.form.submit().follow()
    # assert 'Präsident:in' in page

    # Attendences
    # ... commission
    page = page.click(href='add-attendence')
    page.form['date'] = '2024-02-02'
    page.form['duration'] = '1'
    page.form['type'] = 'commission'
    page = page.form.submit().follow()
    assert 'Kommissionsitzung hinzugefügt' in page
    return

    # ... attendence
    page = client.get('/').follow().click('Anwesenheiten').click(
        href='new', index=0
    )
    page.form['date'] = '2024-02-03'
    page.form['duration'] = '2'
    page.form['type'] = 'study'
    page.form['commission_id'].select(text='CC')
    page = page.form.submit().follow()
    assert 'Neue Anwesenheit hinzugefügt' in page


def test_fetch_commissions_parliamentarians_json(client):
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


def test_add_new_user_without_activation_email(client):
    client.login_admin()

    client.app.enable_yubikey = True

    new = client.get('/usermanagement').click('Benutzer', href='new')
    new.form['username'] = 'admin@example.org'

    assert "existiert bereits" in new.form.submit()

    new.form['username'] = 'secondadmin@example.org'
    new.form['role'] = 'admin'

    assert "müssen zwingend einen YubiKey" in new.form.submit()

    new.form['role'] = 'parliamentarian'
    new.form['send_activation_email'] = False
    added = new.form.submit()

    assert "Passwort" in added
    password = added.pyquery('.panel strong').text()

    login = client.spawn().get('/auth/login')
    login.form['username'] = 'secondadmin@example.org'
    login.form['password'] = password
    assert login.form.submit().status_code == 302
