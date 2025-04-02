import pytest


@pytest.mark.flaky(reruns=5, only_rerun=None)
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

    # elasticsearch
    assert '0 Resultate' in client.get('/search?q=aa')
    assert '0 Resultate' in client.get('/search?q=bb')
    assert '0 Resultate' in client.get('/search?q=cc')
    assert '0 Resultate' in client.get('/search?q=first')
    assert '0 Resultate' in client.get('/search?q=2020-2024')
    assert '0 Resultate' in client.get('/search?q=Q1')
    # postgres
    assert '0 Resultate' in client.get('/search-postgres?q=aa')
    assert '0 Resultate' in client.get('/search-postgres?q=bb')
    assert '0 Resultate' in client.get('/search-postgres?q=cc')
    assert '0 Resultate' in client.get('/search-postgres?q=first')
    assert '0 Resultate' in client.get('/search-postgres?q=2020-2024')
    assert '0 Resultate' in client.get('/search-postgres?q=Q1')

    client.login_admin()

    # elasticsearch
    assert '1 Resultat' in client.get('/search?q=aa')
    assert '1 Resultat' in client.get('/search?q=bb')
    assert '1 Resultat' in client.get('/search?q=cc')
    assert '1 Resultat' in client.get('/search?q=first')
    assert '1 Resultat' in client.get('/search?q=2020-2024')
    assert '1 Resultat' in client.get('/search?q=Q1')
    # postgres
    assert '1 Resultat' in client.get('/search-postgres?q=aa')
    assert '1 Resultat' in client.get('/search-postgres?q=bb')
    assert '1 Resultat' in client.get('/search-postgres?q=cc')
    assert '1 Resultat' in client.get('/search-postgres?q=first')
    assert '1 Resultat' in client.get('/search-postgres?q=2020-2024')
    assert '1 Resultat' in client.get('/search-postgres?q=Q1')

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
