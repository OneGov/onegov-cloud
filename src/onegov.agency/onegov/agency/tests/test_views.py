from io import BytesIO


def test_views(client):
    client.login_admin()
    settings = client.get('/settings')
    settings.form['hidden_people_fields'] = ['academic_title', 'born']
    settings.form.submit()
    client.logout()

    # Test people
    # ... add
    client.login_editor()

    people = client.get('/people')
    assert "Keine Personen gefunden" in people

    new_person = people.click('Person', href='new')
    new_person.form['academic_title'] = 'lic.oec.HSG Harvard'
    new_person.form['first_name'] = 'Thomas'
    new_person.form['last_name'] = 'Aeschi'
    new_person.form['political_party'] = 'SVP'
    new_person.form['born'] = '1979'
    person = new_person.form.submit().follow()

    assert 'lic.oec.HSG Harvard' in person
    assert 'Thomas' in person
    assert 'Aeschi' in person
    assert 'SVP' in person
    assert '1979' in person

    new_person = people.click('Person', href='new')
    new_person.form['first_name'] = 'Joachim'
    new_person.form['last_name'] = 'Elder'
    new_person.form['political_party'] = 'FDP'
    person = new_person.form.submit().follow()

    assert 'Joachim' in person
    assert 'Elder' in person
    assert 'FDP' in person

    # ... edit
    edit_person = person.click('Bearbeiten')
    edit_person.form['first_name'] = 'Joachim'
    edit_person.form['last_name'] = 'Eder'
    edit_person.form['political_party'] = 'FDP'
    person = edit_person.form.submit().follow()

    assert 'Joachim' in person
    assert 'Eder' in person
    assert 'FDP' in person

    # ... check hidden fields
    client.logout()
    people = client.get('/people')
    assert "Aeschi Thomas" in people
    assert "Eder Joachim" in people

    person = people.click("Aeschi Thomas")
    assert 'lic.oec.HSG Harvard' not in person
    assert 'Thomas' in person
    assert 'Aeschi' in person
    assert 'SVP' in person
    assert '1979' not in person

    # ... letter filter
    people = client.get('/people').click('A', href='letter=A')
    assert "Aeschi Thomas" in people
    assert "Eder Joachim" not in people

    people = client.get('/people').click('E', href='letter=E')
    assert "Aeschi Thomas" not in people
    assert "Eder Joachim" in people

    # Test agencies
    # ... add agency
    client.login_editor()

    agencies = client.get('/organizations')
    assert "noch keine Organisationen" in agencies

    new_agency = agencies.click('Organisation', href='new')
    new_agency.form['title'] = 'Bundesbehörden'
    bund = new_agency.form.submit().follow()

    assert 'Bundesbehörden' in bund

    new_agency = bund.click('Organisation', href='new')
    new_agency.form['title'] = 'Nationalrat'
    new_agency.form['portrait'] = '2016/2019\nZug'
    new_agency.form['export_fields'] = ['membership.title', 'person.title']
    nr = new_agency.form.submit().follow()

    assert 'Nationalrat' in nr
    assert '<p>2016/2019<br>Zug</p>' in nr

    new_agency = bund.click('Organisation', href='new')
    new_agency.form['title'] = 'Standerat'
    new_agency.form['portrait'] = '2016/2019\nZug'
    new_agency.form['export_fields'] = ['person.last_name']
    sr = new_agency.form.submit().follow()

    assert 'Standerat' in sr

    # ... edit agency
    edit_agency = sr.click('Bearbeiten')
    edit_agency.form['title'] = 'Ständerat'
    edit_agency.form['portrait'] = '2016/2019\nZug'
    edit_agency.form['export_fields'] = ['person.last_name']
    sr = edit_agency.form.submit().follow()

    assert 'Ständerat' in sr

    # ... add memberships
    new_membership = nr.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Mitglied von Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['since'] = "2016"
    membership = new_membership.form.submit().follow()

    assert "Mitglied von Zug" in membership
    assert "Aeschi Thomas" in membership

    new_membership = sr.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Standerat für Zug"
    new_membership.form['person_id'].select(text="Eder Joachim")
    membership = new_membership.form.submit().follow()

    assert "Standerat für Zug" in membership
    assert "Eder Joachim" in membership

    # ... edit membership
    edit_membership = membership.click("Standerat für Zug").click("Bearbeiten")
    edit_membership.form['title'] = "Ständerat für Zug"
    edit_membership.form['person_id'].select(text="Eder Joachim")
    membership = edit_membership.form.submit().follow()

    assert "Ständerat für Zug" in membership
    assert "Eder Joachim" in membership

    # ... PDFs
    client.login_editor()
    bund = client.get('/organizations').click("Bundesbehörden")
    bund = bund.click("PDF erstellen").form.submit().follow()

    pdf = bund.click("Organisation als PDF speichern")
    assert pdf.content_type == 'application/pdf'
    assert pdf.content_length

    client.app.root_pdf = BytesIO(pdf.body)

    agencies = client.get('/organizations')
    pdf = agencies.click("Gesamter Staatskalender als PDF")
    pdf = bund.click("Organisation als PDF speichern")
    assert pdf.content_type == 'application/pdf'
    assert pdf.content_length

    # ... XLSX Export
    xlsx = client.get('/export-agencies')
    assert xlsx.content_type == (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    assert xlsx.content_length

    # Organization filter in peoples view
    people = client.get('/people')
    options = {o.text: o.attrib for o in people.pyquery('option')}
    assert set(options.keys()) == {'-', 'Nationalrat', 'Ständerat'}

    people = client.get(options['Nationalrat']['value'])
    assert "Aeschi Thomas" in people
    assert "Eder Joachim" not in people

    people = client.get(options['Ständerat']['value'])
    assert "Aeschi Thomas" not in people
    assert "Eder Joachim" in people

    # Delete agency
    bund = client.get('/organizations').click("Bundesbehörden")
    agencies = bund.click("Löschen")
    assert "noch keine Organisationen" in client.get('/organizations')
