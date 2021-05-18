from io import BytesIO
from onegov.core.utils import linkify
from onegov.org.models import Organisation
from PyPDF2 import PdfFileReader
from pytest import mark
from tests.onegov.core.test_utils import valid_test_phone_numbers


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
    bund_url = bund.request.url
    assert 'Bundesbehörden' in bund

    tel_nr = valid_test_phone_numbers[0]
    new_agency = bund.click('Organisation', href='new')
    new_agency.form['title'] = 'Nationalrat'
    new_agency.form['portrait'] = f'2016/2019<br>{tel_nr}'
    new_agency.form['export_fields'] = ['membership.title', 'person.title']
    nr = new_agency.form.submit().follow()

    assert 'Nationalrat' in nr
    assert f'2016/2019<br><a href="tel:{tel_nr}">{tel_nr}</a>' in nr

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
    sort = client.get('/organizations').click('Hauptorganisationen sortieren')
    url = sort.pyquery('ul.agencies').attr('data-sortable-url')

    url = url.replace('%7Bsubject_id%7D', '2')
    url = url.replace('%7Bdirection%7D', 'below')
    url = url.replace('%7Btarget_id%7D', '3')
    client.put(url)

    bund = client.get(bund_url)
    assert [a.text for a in bund.pyquery('ul.children li a')] == [
        'Ständerat', 'Nationalrat',
    ]

    bund.click("Unterorganisationen", href='sort')

    bund = client.get(bund_url)
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
        'Eder Joachim', 'Ständerat für Zug', None,
        'Aeschi Thomas', 'Zweiter Ständerat für Zug', None
    ]

    agency.click("Mitgliedschaften", href='sort')
    agency = client.get(agency.request.url)

    assert [a.text for a in agency.pyquery('ul.memberships li a')] == [
        'Aeschi Thomas', 'Zweiter Ständerat für Zug', None,
        'Eder Joachim', 'Ständerat für Zug', None
    ]

    agency.click("Zweiter Ständerat für Zug").click("Löschen")

    # ... PDFs
    client.login_editor()
    bund = client.get(bund_url)
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
    sr_url = sr.request.url
    assert "Organisation verschoben" in sr

    move = bund.click("Verschieben")
    move.form['parent_id'].select(text="Ständerat")
    bund = move.form.submit().maybe_follow()
    assert "Organisation verschoben" in bund
    client.get(sr_url).click("Eder Joachim")
    client.get(sr_url).click("Bundesbehörden")\
        .click("Nationalrat")
    client.get(sr_url).click("Bundesbehörden")\
        .click("Nationalrat")
    client.get(sr_url).click("Bundesbehörden")\
        .click("Nationalrat").click("Aeschi Thomas")

    # Delete agency
    client.login_admin()
    bund = client.get(sr_url)
    agencies = bund.click("Löschen")
    assert "noch keine Organisationen" in client.get('/organizations')


def test_views_hidden(client):
    # Add data
    client.login_editor()

    new_person = client.get('/people').click('Person', href='new')
    new_person.form['first_name'] = 'Thomas'
    new_person.form['last_name'] = 'Aeschi'
    new_person.form['access'] = 'private'
    person = new_person.form.submit().follow()
    assert 'Thomas' in person
    assert 'Aeschi' in person
    assert 'Aeschi' in client.get('/people')

    new_agency = client.get('/organizations').click('Organisation', href='new')
    new_agency.form['title'] = 'Bundesbehörden'
    bund = new_agency.form.submit().follow()
    assert 'Bundesbehörden' in bund

    new_agency = bund.click('Organisation', href='new')
    new_agency.form['title'] = 'Nationalrat'
    new_agency.form['access'] = 'private'
    child = new_agency.form.submit().follow()
    assert 'Nationalrat' in child
    assert 'Nationalrat' in client.get(bund.request.url)

    new_membership = bund.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Mitglied von Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['access'] = 'private'
    agency = new_membership.form.submit().follow()
    assert "Mitglied von Zug" in agency
    assert "Aeschi Thomas" in agency
    root_membership = agency.click("Mitglied von Zug")
    assert "Mitglied von Zug" in root_membership
    assert "Aeschi Thomas" in root_membership

    new_membership = child.click("Mitgliedschaft", href='new')
    new_membership.form['title'] = "Nationalrat Zug"
    new_membership.form['person_id'].select(text="Aeschi Thomas")
    new_membership.form['access'] = 'private'
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

    org = client.app.session().query(Organisation).one()
    assert org.pdf_layout is None
    assert org.page_break_on_level_root_pdf is None
    assert org.page_break_on_level_org_pdf is None
    assert org.report_changes is None
    color = '#7a8367'

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

    assert get_pdf() == '1\nGovikon\n0\nPlaceholder for table of contents\n'

    settings = client.get('/agency-settings')

    # Test default options for pdf rendering
    assert settings.form['pdf_layout'].value == 'default'
    assert settings.form['root_pdf_page_break'].value == '1'
    assert settings.form['orga_pdf_page_break'].value == '1'
    assert settings.form['report_changes'].value == 'y'

    # Todo: Find out why this does not work in the test
    # the field report_changes is Boolean with the same default on
    # the meta_property, the default is applied in populate_obj, and then
    # something weird happens in the test

    # assert settings.form['underline_links'].value == 'n'
    # assert settings.pyquery.find('input[name=link_color]').val() == \
    #        Pdf.default_link_color

    settings.form['pdf_layout'] = 'zg'
    settings.form['root_pdf_page_break'] = '2'
    settings.form['orga_pdf_page_break'] = '2'
    settings.form['report_changes'] = False
    settings.form['underline_links'] = True
    settings.form['link_color'] = color

    page = settings.form.submit().follow()
    assert 'Ihre Änderungen wurden gespeichert' in page

    settings = client.get('/agency-settings')
    assert settings.form['pdf_layout'].value == 'zg'
    assert settings.form['root_pdf_page_break'].value == '2'
    assert settings.form['orga_pdf_page_break'].value == '2'
    assert settings.form['report_changes'].value is None
    assert settings.form['underline_links'].value == 'y'
    assert settings.form['link_color'].value == color

    assert get_pdf() == 'Govikon\n0\nPlaceholder for table of contents\n'


def test_view_report_change(client):
    # Add data
    client.login_admin()

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
    new.form.submit().follow()

    new = client.get('/organizations').click("Organisation", href='new')
    new.form['title'] = "School"
    new.form.submit().follow()

    new = client.get('/usergroups').click("Benutzergruppe", href='new')
    new.form['name'] = "School Editors"
    new.form['users'].select_multiple(texts=["member@example.org"])
    new.form['agencies'].select_multiple(texts=["School"])
    new.form.submit().follow()

    # Report agency change
    change = agency.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"

    long_message = """
    I saw some errors. Check
    - https://mywebsite.com
    Contact me under +41 77 777 77 77
    """.strip()
    linkified = linkify(long_message).replace('\n', '<br>')

    change.form['message'] = long_message
    change = change.form.submit().follow()
    assert "Vielen Dank für Ihre Eingabe!" in change

    agency_ticket_number = change.pyquery('.ticket-number a')[0].attrib['href']
    agency_ticket = client.get(agency_ticket_number)
    assert "Mutationsmeldung" in agency_ticket
    assert "Hospital Springfield" in agency_ticket
    assert linkified in agency_ticket
    assert "info@hospital-springfield.com" in agency_ticket
    agency_ticket = agency_ticket.click("Ticket annehmen").follow()
    agency_ticket = agency_ticket.click("Ticket abschliessen").follow()

    # ... with honeypot filled
    change = agency.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"
    change.form['delay'] = 'abc'
    change.form['message'] = 'xyz'
    change = change.form.submit().maybe_follow()
    assert "Vielen Dank für Ihre Eingabe!" not in change

    # Report person change
    change = person.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"
    change.form['message'] = "Dr. Rivera's retired."
    change = change.form.submit().follow()
    assert "Vielen Dank für Ihre Eingabe!" in change

    person_ticket_number = change.pyquery('.ticket-number a')[0].attrib['href']
    person_ticket = client.get(person_ticket_number)
    assert "Mutationsmeldung" in person_ticket
    assert "Rivera Nick" in person_ticket
    assert "Dr. Rivera's retired." in person_ticket
    assert "info@hospital-springfield.com" in person_ticket
    person_ticket = person_ticket.click("Ticket annehmen").follow()
    person_ticket = person_ticket.click("Ticket abschliessen").follow()

    # ... with honeypot filled
    change = person.click("Mutation melden")
    change.form['email'] = "info@hospital-springfield.com"
    change.form['delay'] = 'abc'
    change.form['message'] = 'xyz'
    change = change.form.submit().maybe_follow()
    assert "Vielen Dank für Ihre Eingabe!" not in change

    # Details not shown if missing permissions
    client.login('member@example.org', 'hunter2')
    client.get(agency_ticket_number, status=403)
    client.get(person_ticket_number, status=403)
    page = client.get('/tickets/ALL/closed')
    assert 'ticket-number-plain' in page
    assert 'ticket-state' not in page

    # Deleted content
    client.login_admin()
    agency.click("Löschen")
    person.click("Löschen")

    ticket = client.get(agency_ticket_number)
    assert "Der hinterlegte Datensatz wurde entfernt." in ticket
    assert "Mutationsmeldung" in ticket
    assert "Hospital Springfield" in ticket
    assert linkified in ticket
    assert "info@hospital-springfield.com" in ticket

    ticket = client.get(person_ticket_number)
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


def test_excel_export_for_editor(client):

    #  Eventually is_manager is true for admin and editor
    client.login_editor()

    # Test pdf is not present
    page = client.get('/people/people-xlsx', expect_errors=True)
    assert page.status == '503 Service Unavailable'

    page = client.get('/people').click('Excel erstellen')
    assert page.status_code == 200
    redirected = page.form.submit().follow()
    assert 'http://localhost/people?page=0' == redirected.request.url

    # Download the file
    page = client.get('/people')
    page = page.click('Download Excel Personen')
    assert page.content_type == \
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def test_excel_export_not_logged_in(client):
    page = client.get('/people')
    assert 'Excel erstellen' not in page

    # Excel creation page
    page = client.get(
        '/people/create-people-xlsx', expect_errors=True).maybe_follow()
    assert page.status == '403 Forbidden'

    # Actual excel itself
    page = client.get(
        '/people/people-xlsx', expect_errors=True).maybe_follow()
    assert page.status == '403 Forbidden'


@mark.flaky(reruns=3)
def test_basic_search(client_with_es):
    client = client_with_es
    client.login_admin()
    new = client.get('/people').click("Person", href='new')
    new.form['academic_title'] = "Dr."
    new.form['first_name'] = "Nick"
    new.form['last_name'] = "Rivera"
    new.form.submit().follow()

    client.app.es_client.indices.refresh(index='_all')

    client = client.spawn()
    client.get('/search?q=Nick')


def test_footer_settings_custom_links(client):
    client.login_admin()

    # footer settings custom links
    settings = client.get('/footer-settings')
    custom_url = 'https://custom.com/1'
    custom_name = 'Custom1'

    settings.form['custom_link_1_name'] = custom_name
    settings.form['custom_link_1_url'] = custom_url
    settings.form['custom_link_2_name'] = 'Custom2'
    settings.form['custom_link_2_url'] = None

    page = settings.form.submit().follow()
    assert f'<a href="{custom_url}">{custom_name}</a>' in page
    assert 'Custom2' not in page


def test_view_user_groups(client):
    client.login_admin()

    manage = client.get('/organizations').click('Organisation', href='new')
    manage.form['title'] = 'Bundesbehörden'
    manage.form.submit()

    manage = client.get('/organizations').click('Organisation', href='new')
    manage.form['title'] = 'Kantonsrat'
    manage.form.submit()

    # create
    manage = client.get('/usergroups').click('Benutzergruppe', href='new')
    manage.form['name'] = 'Gruppe BB'
    manage.form['users'].select_multiple(texts=['editor@example.org'])
    manage.form['agencies'].select_multiple(texts=['Bundesbehörden'])
    page = manage.form.submit().maybe_follow()
    assert 'Gruppe BB' in page
    assert 'editor@example.org' in page
    assert 'Bundesbehörden' in page

    page = client.get('/usermanagement').click('Ansicht', index=1)
    assert 'editor@example.org' in page
    assert 'Gruppe BB' in page

    # modify
    manage = client.get('/usergroups').click('Ansicht').click('Bearbeiten')
    manage.form['name'] = 'Gruppe KR'
    manage.form['users'].select_multiple(texts=['admin@example.org'])
    manage.form['agencies'].select_multiple(texts=['Kantonsrat'])
    page = manage.form.submit().maybe_follow()
    assert 'Gruppe KR' in page
    assert 'admin@example.org' in page
    assert 'editor@example.org' not in page
    assert 'Kantonsrat' in page
    assert 'Bundesbehörden' not in page

    page = client.get('/usermanagement').click('Ansicht', index=0)
    assert 'admin@example.org' in page
    assert 'Gruppe BB' not in page
    assert 'Gruppe KR' in page

    page = client.get('/usermanagement').click('Ansicht', index=1)
    assert 'editor@example.org' in page
    assert 'Gruppe BB' not in page
    assert 'Gruppe KR' not in page

    # delete
    client.get('/usergroups').click('Ansicht').click('Löschen')
    assert 'Alle (0)' in client.get('/usergroups')
