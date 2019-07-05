from io import BytesIO
from PyPDF2 import PdfFileReader


def test_views(client):
    client.login_admin()
    settings = client.get('/module-settings')
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

    # ... sort agencies
    bund = client.get('/organizations').click('Bundesbehörden')
    url = bund.pyquery('ul.children').attr('data-sortable-url')
    url = url.replace('%7Bsubject_id%7D', '2')
    url = url.replace('%7Bdirection%7D', 'below')
    url = url.replace('%7Btarget_id%7D', '3')
    client.put(url)

    bund = client.get('/organizations').click('Bundesbehörden')
    assert [a.text for a in bund.pyquery('ul.children li a')] == [
        'Ständerat', 'Nationalrat',
    ]

    bund.click("Unterorganisationen", href='sort')

    bund = client.get('/organizations').click('Bundesbehörden')
    assert [a.text for a in bund.pyquery('ul.children li a')] == [
        'Nationalrat', 'Ständerat',
    ]

    # ... add memberships
    new_membership = nr.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Mitglied von Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['since'] = "2016"
    new_membership.form['addition'] = "SVP Fraktion"
    new_membership.form['note'] = "seit 2011"
    new_membership.form['prefix'] = "***"
    agency = new_membership.form.submit().follow()

    assert "Mitglied von Zug" in agency
    assert "Aeschi Thomas" in agency
    assert "***" in agency

    membership = agency.click("Mitglied von Zug")
    assert "Mitglied von Zug" in membership
    assert "Aeschi Thomas" in membership
    assert "2016" in membership
    assert "SVP Fraktion" in membership
    assert "seit 2011" in membership

    new_membership = sr.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Standerat für Zug"
    new_membership.form['person_id'].select(text="Eder Joachim")
    agency = new_membership.form.submit().follow()

    assert "Standerat für Zug" in agency
    assert "Eder Joachim" in agency

    # ... edit membership
    edit_membership = agency.click("Standerat für Zug").click("Bearbeiten")
    edit_membership.form['title'] = "Ständerat für Zug"
    edit_membership.form['person_id'].select(text="Eder Joachim")
    agency = edit_membership.form.submit().follow()

    assert "Ständerat für Zug" in agency
    assert "Eder Joachim" in agency

    # ... sort memberships
    new_membership = sr.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Zweiter Ständerat für Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    agency = new_membership.form.submit().follow()

    assert [a.text for a in agency.pyquery('ul.memberships li a')] == [
         'Eder Joachim', 'Ständerat für Zug',
         'Aeschi Thomas', 'Zweiter Ständerat für Zug',
    ]

    agency.click("Mitgliedschaften", href='sort')
    agency = client.get(agency.request.url)
    assert [a.text for a in agency.pyquery('ul.memberships li a')] == [
        'Aeschi Thomas', 'Zweiter Ständerat für Zug',
        'Eder Joachim', 'Ständerat für Zug',
    ]

    agency.click("Zweiter Ständerat für Zug").click("Löschen")

    # ... PDFs
    client.login_editor()
    bund = client.get('/organizations').click("Bundesbehörden")
    bund = bund.click("PDF erstellen").form.submit().follow()

    pdf = bund.click("Organisation als PDF speichern")
    assert pdf.content_type == 'application/pdf'
    assert pdf.content_length

    agencies = client.get('/organizations')
    agencies = agencies.click("PDF erstellen").form.submit().follow()

    pdf = agencies.click("Gesamter Staatskalender als PDF")
    assert pdf.content_type == 'application/pdf'
    assert pdf.content_length

    # Organization filter in peoples view
    people = client.get('/people')
    options = {o.text: o.attrib for o in people.pyquery('option')}
    assert set(options.keys()) == {None, 'Nationalrat', 'Ständerat'}

    people = client.get(options['Nationalrat']['value'])
    assert "Aeschi Thomas" in people
    assert "Eder Joachim" not in people

    people = client.get(options['Ständerat']['value'])
    assert "Aeschi Thomas" not in people
    assert "Eder Joachim" in people

    # Move agencies
    move = sr.click("Verschieben")
    move.form['parent_id'].select(text="- oberste Ebene -")
    sr = move.form.submit().maybe_follow()
    assert "Organisation verschoben" in sr

    move = bund.click("Verschieben")
    move.form['parent_id'].select(text="Ständerat")
    bund = move.form.submit().maybe_follow()
    assert "Organisation verschoben" in bund

    client.get('/organizations').click("Ständerat").click("Eder Joachim")
    client.get('/organizations').click("Ständerat").click("Bundesbehörden")\
        .click("Nationalrat")
    client.get('/organizations').click("Ständerat").click("Bundesbehörden")\
        .click("Nationalrat")
    client.get('/organizations').click("Ständerat").click("Bundesbehörden")\
        .click("Nationalrat").click("Aeschi Thomas")

    # Delete agency
    bund = client.get('/organizations').click("Ständerat")
    agencies = bund.click("Löschen")
    assert "noch keine Organisationen" in client.get('/organizations')


def test_views_hidden(client):
    # Add data
    client.login_editor()

    new_person = client.get('/people').click('Person', href='new')
    new_person.form['first_name'] = 'Thomas'
    new_person.form['last_name'] = 'Aeschi'
    new_person.form['is_hidden_from_public'] = True
    person = new_person.form.submit().follow()
    assert 'Thomas' in person
    assert 'Aeschi' in person
    assert 'Aeschi' in client.get('/people')

    new_agency = client.get('/organizations').click('Organisation', href='new')
    new_agency.form['title'] = 'Bundesbehörden'
    root = new_agency.form.submit().follow()
    assert 'Bundesbehörden' in root

    new_agency = root.click('Organisation', href='new')
    new_agency.form['title'] = 'Nationalrat'
    new_agency.form['is_hidden_from_public'] = True
    child = new_agency.form.submit().follow()
    assert 'Nationalrat' in child
    assert 'Nationalrat' in client.get('/organizations')

    new_membership = root.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Mitglied von Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['is_hidden_from_public'] = True
    agency = new_membership.form.submit().follow()
    assert "Mitglied von Zug" in agency
    assert "Aeschi Thomas" in agency
    root_membership = agency.click("Mitglied von Zug")
    assert "Mitglied von Zug" in root_membership
    assert "Aeschi Thomas" in root_membership

    new_membership = child.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Nationalrat Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['is_hidden_from_public'] = True
    agency = new_membership.form.submit().follow()
    assert "Nationalrat Zug" in agency
    assert "Aeschi Thomas" in agency
    child_membership = agency.click("Nationalrat Zug")
    assert "Nationalrat Zug" in child_membership
    assert "Aeschi Thomas" in child_membership

    hidden = client.get('/').click("Versteckte Inhalte")
    assert "Nationalrat" in hidden
    assert "Mitglied von Zug" in hidden
    assert "Nationalrat Zug" in hidden
    assert "Aeschi Thomas" in hidden

    # Test forbidden views
    client.logout()
    client.get(person.request.url, status=403)
    client.get(child.request.url, status=403)
    client.get(root_membership.request.url, status=403)
    client.get(child_membership.request.url, status=403)

    # Test hiding
    assert "Aeschi" not in client.get('/people')
    assert "Nationalrat" not in client.get('/organizations')
    assert "Versteckte Einträge" not in client.get('/')


def test_view_pdf_settings(client):
    def get_pdf():
        agencies = client.get('/organizations')
        agencies = agencies.click("PDF erstellen").form.submit().follow()

        pdf = agencies.click("Gesamter Staatskalender als PDF")
        reader = PdfFileReader(BytesIO(pdf.body))
        return '\n'.join([
            reader.getPage(page).extractText()
            for page in range(reader.getNumPages())
        ])

    client.login_admin()

    assert client.get('/agency-settings')\
        .form['pdf_layout'].value == 'default'

    assert get_pdf() == '1\nGovikon\n0\nPlaceholder for table of contents\n'

    settings = client.get('/agency-settings')
    settings.form['pdf_layout'] = 'zg'
    settings.form.submit()

    assert get_pdf() == 'Govikon\n0\nPlaceholder for table of contents\n'


def test_view_report_change(client):
    # Add data
    client.login_editor()

    new = client.get('/people').click("Person", href='new')
    new.form['academic_title'] = "Dr."
    new.form['first_name'] = "Nick"
    new.form['last_name'] = "Rivera"
    person = new.form.submit().follow()

    new = client.get('/organizations').click("Organisation", href='new')
    new.form['title'] = "Hospital Springfield"
    agency = new.form.submit().follow()

    new = agency.click("Mitgliedschaft", href='new')
    new.form['title'] = "Doctor"
    new.form['person_id'].select(text="Rivera Nick")

    # Report agency change
    change = agency.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"
    change.form['message'] = "Please add our address."
    change = change.form.submit().follow()
    assert "Vielen Dank für Ihre Eingabe!" in change

    ticket_number = change.pyquery('.ticket-number a')[0].attrib['href']
    ticket = client.get(ticket_number)
    assert "Mutationsmeldung" in ticket
    assert "Hospital Springfield" in ticket
    assert "Please add our address." in ticket
    assert "info@hospital-springfield.com" in ticket
    ticket = ticket.click("Ticket annehmen").follow()
    ticket = ticket.click("Ticket abschliessen").follow()

    agency.click("Löschen")

    ticket = client.get(ticket_number)
    assert "Der hinterlegte Datensatz wurde entfernt." in ticket
    assert "Mutationsmeldung" in ticket
    assert "Hospital Springfield" in ticket
    assert "Please add our address." in ticket
    assert "info@hospital-springfield.com" in ticket

    # Report person change
    change = person.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"
    change.form['message'] = "Dr. Rivera's retired."
    change = change.form.submit().follow()
    assert "Vielen Dank für Ihre Eingabe!" in change

    ticket_number = change.pyquery('.ticket-number a')[0].attrib['href']
    ticket = client.get(ticket_number)
    assert "Mutationsmeldung" in ticket
    assert "Rivera Nick" in ticket
    assert "Dr. Rivera's retired." in ticket
    assert "info@hospital-springfield.com" in ticket
    ticket = ticket.click("Ticket annehmen").follow()
    ticket = ticket.click("Ticket abschliessen").follow()

    person.click("Löschen")

    ticket = client.get(ticket_number)
    assert "Der hinterlegte Datensatz wurde entfernt." in ticket
    assert "Mutationsmeldung" in ticket
    assert "Rivera Nick" in ticket
    assert "Dr. Rivera's retired." in ticket
    assert "info@hospital-springfield.com" in ticket


def test_disable_report_changes(client):
    client.login_admin()

    page = client.get('/people').click("Person", href='new')
    page.form['academic_title'] = "Dr."
    page.form['first_name'] = "Nick"
    page.form['last_name'] = "Rivera"
    page = page.form.submit().follow()

    assert "Mutation melden" in page
    person_url = page.request.url

    page = client.get('/settings').click("Organisationen", index=1)
    page.form['report_changes'] = False
    page.form.submit()

    assert "Mutation melden" not in client.get(person_url)

    page = client.get('/settings').click("Organisationen", index=1)
    page.form['report_changes'] = True
    page.form.submit()

    assert "Mutation melden" in client.get(person_url)
