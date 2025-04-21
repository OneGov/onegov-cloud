import pytest
import os
from webtest import Upload
from onegov.pas import _


@pytest.mark.flaky(reruns=5)
def test_views_manage(client_with_es):
    client = client_with_es
    client.login_admin()

    settings = client.get('/').click('PAS Einstellungen')
    delete = []

    # Rate Sets
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

    # Legislative Periods
    page = settings.click('Legislaturen')
    page = page.click(href='new')
    page.form['name'] = '2020-2024'
    page.form['start'] = '2020-01-01'
    page.form['end'] = '2023-12-31'
    page = page.form.submit().follow()
    assert '31.12.2023' in page

    page = page.click('Bearbeiten')
    page.form['end'] = '2024-12-31'
    page = page.form.submit().follow()
    assert '31.12.2024' in page

    delete.append(page)

    # Settlement Runs
    page = settings.click('Abrechnungsläufe')
    page = page.click(href='new')
    page.form['name'] = 'Q1'
    page.form['start'] = '2024-01-01'
    page.form['end'] = '2024-12-31'
    page.form['active'] = True
    page = page.form.submit().follow()
    assert '31.12.2024' in page

    page = page.click('Bearbeiten')
    page.form['end'] = '2024-03-31'
    page = page.form.submit().follow()
    assert '31.03.2024' in page

    delete.append(page)

    # Parties
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
    page = client.get('/').click('Anwesenheiten').click(href='new', index=0)
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
    page = client.get('/').click('Anwesenheiten').click(href='new', index=1)
    page.form['date'] = '2024-02-04'
    page.form['duration'] = '3'
    page = page.form.submit().follow()
    assert 'Plenarsitzung hinzugefügt' in page

    page = client.get('/').click('Anwesenheiten')
    assert '02.02.2024' in page
    assert '03.02.2024' in page
    assert '04.02.2024' in page

    # Changes
    page = client.get('/').click('Aktivitäten')
    assert '02.02.2024' in page
    assert '03.02.2024' in page
    assert '04.02.2024' in page
    assert 'Anwesenheit bearbeitet' in page

    page = page.click(href='/change/', index=0)
    assert 'admin@example.org' in page

    # Test search results
    client.app.es_client.indices.refresh(index='_all')
    client = client.spawn()

    assert '0 Resultate' in client.get('/search?q=aa')
    assert '0 Resultate' in client.get('/search?q=bb')
    assert '0 Resultate' in client.get('/search?q=cc')
    assert '0 Resultate' in client.get('/search?q=first')
    assert '0 Resultate' in client.get('/search?q=2020-2024')
    assert '0 Resultate' in client.get('/search?q=Q1')

    client.login_admin()

    assert '1 Resultat' in client.get('/search?q=aa')
    assert '1 Resultat' in client.get('/search?q=bb')
    assert '1 Resultat' in client.get('/search?q=cc')
    assert '1 Resultat' in client.get('/search?q=first')
    assert '1 Resultat' in client.get('/search?q=2020-2024')
    assert '1 Resultat' in client.get('/search?q=Q1')

    # Delete
    for page in delete:
        page.click('Löschen')
    assert 'Noch keine Sätze erfasst' in settings.click('Sätze')
    assert 'Noch keine Legislaturen erfasst' in settings.click('Legislaturen')
    assert 'Noch keine Abrechnungsläufe erfasst' in\
           settings.click('Abrechnungsläufe')
    assert 'Noch keine Parteien erfasst' in settings.click('Parteien')
    assert 'Noch keine Fraktionen erfasst' in settings.click('Fraktionen')
    assert 'Noch keine Parlamentarier:innen erfasst' in\
           settings.click('Parlamentarier:innen')


def test_view_upload_json(client):

    """ Test successful import of all data.

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

    def yield_paths():
        """ Yields paths in this order: organization, membership, people """
        base_path = '/home/cyrill/pasimport/json'
        yield [base_path + '/organization.json']
        membership_count = 7
        membership_paths = [
            f'{base_path}/memberships_{i}.json'
            for i in range(1, membership_count + 1)
        ]
        assert all(
            os.path.exists(path) for path in membership_paths
        ), "Some membership paths don't exist"
        yield membership_paths

        # Yield people paths after validating existence
        people_paths = [f'{base_path}/people_{i}.json' for i in range(1, 3)]
        assert all(
            os.path.exists(path) for path in people_paths
        ), "Some people paths don't exist"
        yield people_paths

    def do_upload_procedure():
        page = client.get('/pas-import')

        def upload_file(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
                return Upload(
                    os.path.basename(filepath),
                    content,
                    'application/json'
                )

        # Get all paths
        paths_generator = yield_paths()

        org_paths = next(paths_generator)
        page.form['organizations_source'] = [
            upload_file(path) for path in org_paths
        ]

        membership_paths = next(paths_generator)
        page.form['memberships_source'] = [
            upload_file(path) for path in membership_paths
        ]
        people_paths = next(paths_generator)
        page.form['people_source'] = [
            upload_file(path) for path in people_paths
        ]

        # Submit the form
        result = page.form.submit().maybe_follow()

        # Add assertions as needed
        assert result.status_code == 200
        return result

    result = do_upload_procedure()

    # Check the import logs
    logs_page = client.get('/import-logs')
    assert logs_page.status_code == 200
    assert 'completed' in logs_page  # Check if the status is shown
    log_detail_link = logs_page.click(_('View Details'), index=0)
    log_detail_page = log_detail_link.follow()
    assert log_detail_page.status_code == 200
    assert 'Import Details' in log_detail_page
    assert 'completed' in log_detail_page.pyquery('.import-status').text()

    # do it again to test that errors / duplicates are gracefully handled.
    result = do_upload_procedure()

    # Check logs again after second import
    logs_page = client.get('/import-logs')
    assert logs_page.status_code == 200
    # Should now have two logs
    assert len(logs_page.pyquery('tbody tr')) == 2
    assert 'completed' in logs_page.pyquery('tbody tr:first-child .import-status').text()
    assert 'completed' in logs_page.pyquery('tbody tr:last-child .import-status').text()
