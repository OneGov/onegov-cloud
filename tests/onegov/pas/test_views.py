import pytest


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
    assert 'Noch keine Abrechnungsläufe erfasst' in \
        settings.click('Abrechnungsläufe')
    assert 'Noch keine Parteien erfasst' in settings.click('Parteien')
    assert 'Noch keine Fraktionen erfasst' in settings.click('Fraktionen')
    assert 'Noch keine Parlamentarier:innen erfasst' in \
        settings.click('Parlamentarier:innen')
    assert 'Keine aktiven Kommissionen' in settings.click('Kommissionen')


def test_settlement_export_views(client, session):
    # Create test data
    rate_set = RateSet(year=2024)
    rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment
    rate_set.plenary_none_president_halfday = 1000
    rate_set.plenary_none_member_halfday = 500
    rate_set.commission_normal_president_initial = 300
    rate_set.commission_normal_member_initial = 200
    rate_set.study_normal_president_halfhour = 100
    rate_set.study_normal_member_halfhour = 80
    session.add(rate_set)

    # Create parties
    party_a = Party(name='Party A')
    party_b = Party(name='Party B')
    session.add_all([party_a, party_b])

    # Create commissions
    commission_a = Commission(name='Commission A', type='normal')
    commission_b = Commission(name='Commission B', type='normal')
    session.add_all([commission_a, commission_b])

    # Create parliamentarians with roles
    pres = Parliamentarian(first_name='Jane', last_name='President')
    pres_role = ParliamentarianRole(
        parliamentarian=pres,
        role='president',
        party=party_a,
        start=date(2024, 1, 1),
    )

    mem = Parliamentarian(first_name='John', last_name='Member')
    mem_role = ParliamentarianRole(
        parliamentarian=mem,
        role='member',
        party=party_b,
        start=date(2024, 1, 1),
    )
    session.add_all([pres, mem, pres_role, mem_role])

    # Create settlement run
    run = SettlementRun(
        name='Q1 2024',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True,
    )
    session.add(run)

    # Create various types of attendences
    attendences = [
        # Plenary attendences
        Attendence(
            parliamentarian=pres,
            date=date(2024, 1, 15),
            duration=240,  # 4 hours
            type='plenary',
        ),
        Attendence(
            parliamentarian=mem,
            date=date(2024, 2, 15),
            duration=240,  # 4 hours
            type='plenary',
        ),
        # Commission attendences
        Attendence(
            parliamentarian=pres,
            date=date(2024, 1, 20),
            duration=180,  # 3 hours
            type='commission',
            commission=commission_a,
        ),
        Attendence(
            parliamentarian=mem,
            date=date(2024, 2, 20),
            duration=180,  # 3 hours
            type='commission',
            commission=commission_a,
        ),
        # Study attendences
        Attendence(
            parliamentarian=pres,
            date=date(2024, 1, 25),
            duration=60,  # 1 hour
            type='study',
            commission=commission_a,
        ),
        Attendence(
            parliamentarian=mem,
            date=date(2024, 2, 25),
            duration=60,  # 1 hour
            type='study',
            commission=commission_a,
        ),
    ]
    session.add_all(attendences)
    session.flush()

    # Login as admin
    client.login_admin()

    # Test accessing the settlement run page
    page = client.get(f'/settlement-run/{run.id}')
    assert page.status_code == 200

    # Test all-parties export
    response = client.get(
        f'/settlement-run/{run.id}/export/all-parties/run-export'
    )
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.content_disposition.startswith('attachment')

    # Test party-specific exports
    for party in [party_a, party_b]:
        response = client.get(
            f'/settlement-run/{run.id}/export/party/{party.id}/run-export'
        )
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert 'attachment' in response.content_disposition
        assert party.name.replace(' ', '_') in response.content_disposition

    # Test commission-specific exports
    for commission in [commission_a, commission_b]:
        response = client.get(
            f'/settlement-run/{run.id}/export/commission/{commission.id}/run-export'
        )
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert 'attachment' in response.content_disposition
        assert (
            commission.name.replace(' ', '_')
            in response.content_disposition
        )

    # Test parliamentarian-specific exports
    for parliamentarian in [pres, mem]:
        response = client.get(
            f'/settlement-run/{run.id}/export/parliamentarian/{parliamentarian.id}/run-export'
        )
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        assert 'attachment' in response.content_disposition
        assert parliamentarian.last_name in response.content_disposition

    # Test that non-admin users can't access exports
    client.logout()

    # Test access denied for non-admin
    response = client.get(
        f'/settlement-run/{run.id}/export/all-parties/run-export'
    )
    assert response.status_code in (
        401,
        403,
    )  # Either unauthorized or forbidden

    response = client.get(
        f'/settlement-run/{run.id}/export/party/{party_a.id}/run-export'
    )
    assert response.status_code in (401, 403)

    response = client.get(
        f'/settlement-run/{run.id}/export/commission/{commission_a.id}/run-export'
    )
    assert response.status_code in (401, 403)

    response = client.get(
        f'/settlement-run/{run.id}/export/parliamentarian/{pres.id}/run-export'
    )
    assert response.status_code in (401, 403)
