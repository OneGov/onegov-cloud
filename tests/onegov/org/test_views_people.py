from uuid import UUID
from markupsafe import Markup
from onegov.core.request import CoreRequest
from onegov.org.models import Topic
from onegov.org.views.people import person_functions_by_organization
from onegov.people import Person


def test_people_view(client):
    client.login_admin()
    settings = client.get('/people-settings')
    settings.form['hidden_people_fields'] = ['academic_title', 'profession']
    settings.form['organisation_hierarchy'] = """
    - Organisation 1:
    """

    assert 'Ungültiges Format.' in settings.form.submit()

    settings.form['organisation_hierarchy'] = """
    - Organisation 1
    - Organisation 2:
      - Sub-Organisation 2.1
      - Sub-Organisation 2.2
    """
    settings.form.submit()
    client.logout()

    client.login_editor()

    people = client.get('/people')
    assert 'Keine Personen' in people

    new_person = people.click('Person')
    new_person.form['academic_title'] = 'Dr.'
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form['profession'] = 'Hero'
    new_person.form['organisations_multiple'].select_multiple(
        texts=['Organisation 1', 'Organisation 2', '- Sub-Organisation 2.1',
               '- Sub-Organisation 2.2'])
    person = new_person.form.submit().follow()

    assert 'Gordon Flash' in person
    assert 'Dr.' in person
    assert 'Hero' in person
    assert 'Organisation 1' in person
    assert 'Organisation 2 - Sub-Organisation 2.1, Sub' in person

    vcard = person.click('Elektronische Visitenkarte').text
    assert 'FN;CHARSET=utf-8:Dr. Flash Gordon' in vcard
    assert 'N;CHARSET=utf-8:Gordon;Flash;;Dr.;' in vcard

    client.logout()
    people = client.get('/people')
    assert 'Gordon Flash' in people

    person = people.click('Gordon Flash')
    assert 'Gordon Flash' in person
    assert 'Dr.' not in person
    assert 'Hero' not in person

    vcard = person.click('Elektronische Visitenkarte').text
    assert 'FN;CHARSET=utf-8:Flash Gordon' in vcard
    assert 'N;CHARSET=utf-8:Gordon;Flash;;;' in vcard

    client.login_editor()

    person = client.get('/people').click('Gordon Flash')
    edit_person = person.click('Bearbeiten')
    edit_person.form['first_name'] = 'Merciless'
    edit_person.form['last_name'] = 'Ming'
    person = edit_person.form.submit().follow()

    assert 'Ming Merciless' in person

    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    people = client.get('/people')
    assert 'Keine Personen' in people


def test_with_people(client):
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Merciless'
    new_person.form['last_name'] = 'Ming'
    new_person.form.submit()

    new_page = client.get('/topics/organisation').click('Thema')

    assert 'Gordon Flash' in new_page
    assert 'Ming Merciless' in new_page

    gordon = client.app.session().query(Person) \
        .filter(Person.last_name == 'Gordon') \
        .one()

    new_page.form['title'] = 'About Flash'
    new_page.form['people-0-person'] = gordon.id.hex
    new_page.form['people-0-context_specific_function'] = 'Astronaut'
    new_page.form['people-0-display_function_in_person_directory'] = True
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    assert edit_page.form['people-0-person'].value == gordon.id.hex
    assert edit_page.form['people-0-context_specific_function'].value == (
           'Astronaut')

    assert edit_page.form['people-1-person'].value == ''
    assert edit_page.form['people-1-context_specific_function'].value == ''


def test_people_view_organisation_filter(client):
    org_1 = 'The Nexus'
    sub_org_11 = 'Nexus Innovators'
    sub_org_12 = 'Nexus Guardians'
    sub_org_13 = 'Nexus Diplomats'
    org_2 = 'The Vanguard'
    sub_org_21 = 'Vanguard Tech'
    sub_org_22 = 'Vanguard Capital'

    client.login_admin()
    settings = client.get('/people-settings')
    settings.form['organisation_hierarchy'] = f"""
    - {org_1}:
      - {sub_org_11}
      - {sub_org_12}
      - {sub_org_13}
    - {org_2}:
      - {sub_org_21}
      - {sub_org_22}
    """
    settings.form.submit()
    client.logout()


    client.login_editor()

    def add_person(first_name, last_name, function, org, sub_org):
        people = client.get('/people')
        new_person = people.click('Person')
        new_person.form['first_name'] = first_name
        new_person.form['last_name'] = last_name
        new_person.form['function'] = function
        new_person.form['organisations_multiple'].select_multiple(
        texts=[org, f'- {sub_org}'] if sub_org else [org])
        new_person.form.submit()

    add_person('Aria', 'Chen',
               'brilliant robotics engineer and team leader',
               org_1, sub_org_11)
    add_person('Max', 'Holloway',
               'young prodigy in artificial intelligence',
               org_1, sub_org_11)
    add_person('Olivia', 'Greenwood',
               'leading climate scientists', org_1, sub_org_12)
    add_person('Sofia', 'Mendoza',
               'charismatic public speaker', org_1, sub_org_12)
    add_person('James', 'Thornton',
               'seasoned diplomat', org_1, sub_org_13)
    add_person('Zack', 'Torres',
               'tech-savvy intern, eager to learn from all divisions',
               org_1, '')
    add_person('John', 'Doe', 'CEO and tech mogul',
               org_2, sub_org_21)
    add_person('Victoria', 'Smith',
               'Shrewd investment banker and division head',
               org_2, sub_org_22)

    # no filter
    people = client.get('/people')
    assert 'Chen Aria' in people
    assert 'Holloway Max' in people
    assert 'Greenwood Olivia' in people
    assert 'Mendoza Sofia' in people
    assert 'Thornton James' in people
    assert 'Torres Zack' in people
    assert 'Doe John' in people
    assert 'Smith Victoria' in people

    # filter for organization 'Nexus'
    people = client.get('/people?organisation=The+Nexus')
    assert 'Chen Aria' in people
    assert 'Holloway Max' in people
    assert 'Greenwood Olivia' in people
    assert 'Mendoza Sofia' in people
    assert 'Thornton James' in people
    assert 'Torres Zack' in people
    assert 'Doe John' not in people
    assert 'Smith Victoria' not in people

    # filter for sub organization 'Innovators'
    people = client.get('/people?organisation=The+Nexus&sub_organisation'
                        '=Nexus+Innovators')
    assert 'Chen Aria' in people
    assert 'Holloway Max' in people
    assert 'Greenwood Olivia' not in people
    assert 'Mendoza Sofia' not in people
    assert 'Thornton James' not in people
    assert 'Torres Zack' not in people
    assert 'Doe John' not in people
    assert 'Smith Victoria' not in people

    # filter for sub organization 'Guardians'
    people = client.get('/people?organisation=The+Nexus&sub_organisation'
                        '=Nexus+Guardians')
    assert 'Chen Aria' not in people
    assert 'Holloway Max' not in people
    assert 'Greenwood Olivia' in people
    assert 'Mendoza Sofia' in people
    assert 'Thornton James' not in people
    assert 'Torres Zack' not in people
    assert 'Doe John' not in people
    assert 'Smith Victoria' not in people

    # filter for sub organization 'Diplomats'
    people = client.get('/people?organisation=The+Nexus&sub_organisation'
                        '=Nexus+Diplomats')
    assert 'Chen Aria' not in people
    assert 'Holloway Max' not in people
    assert 'Greenwood Olivia' not in people
    assert 'Mendoza Sofia' not in people
    assert 'Thornton James' in people
    assert 'Torres Zack' not in people
    assert 'Doe John' not in people
    assert 'Smith Victoria' not in people

    # filter for organization 'The Vanguard'
    people = client.get('/people?organisation=The+Vanguard')
    assert 'Chen Aria' not in people
    assert 'Holloway Max' not in people
    assert 'Greenwood Olivia' not in people
    assert 'Mendoza Sofia' not in people
    assert 'Thornton James' not in people
    assert 'Torres Zack' not in people
    assert 'Doe John' in people
    assert 'Smith Victoria' in people

    # filter for sub organization 'Vanguard Tech'
    people = client.get('/people?organisation=The+Vanguard&sub_organisation'
                        '=Vanguard+Tech')
    assert 'Chen Aria' not in people
    assert 'Holloway Max' not in people
    assert 'Greenwood Olivia' not in people
    assert 'Mendoza Sofia' not in people
    assert 'Thornton James' not in people
    assert 'Torres Zack' not in people
    assert 'Doe John' in people
    assert 'Smith Victoria' not in people

    # filter for sub organization 'Vanguard Capital'
    people = client.get('/people?organisation=The+Vanguard&sub_organisation'
                        '=Vanguard+Capital')
    assert 'Chen Aria' not in people
    assert 'Holloway Max' not in people
    assert 'Greenwood Olivia' not in people
    assert 'Mendoza Sofia' not in people
    assert 'Thornton James' not in people
    assert 'Torres Zack' not in people
    assert 'Doe John' not in people
    assert 'Smith Victoria' in people

    # mix filters - no results
    people = client.get('/people?organisation=The+Vanguard&sub_organisation'
                        '=The+Innovators')
    assert 'Keine Personen für aktuelle Filterauswahl gefunden' in people

    # test select options
    people = client.get('/people')
    assert 'The Nexus' in people
    assert 'The Vanguard' in people
    assert 'Nexus Innovators' in people
    assert 'Nexus Guardians' in people
    assert 'Nexus Diplomats' in people
    assert 'Vanguard Tech' in people
    assert 'Vanguard Capital' in people

    people = client.get('/people?organisation=The+Nexus')
    assert 'The Nexus' in people
    assert 'The Vanguard' in people
    assert 'Nexus Innovators' in people
    assert 'Nexus Guardians' in people
    assert 'Nexus Diplomats' in people
    assert 'Vanguard Tech' not in people
    assert 'Vanguard Capital' not in people

    people = client.get('/people?organisation=The+Vanguard')
    assert 'The Nexus' in people
    assert 'The Vanguard' in people
    assert 'Nexus Innovators' not in people
    assert 'Nexus Guardians' not in people
    assert 'Nexus Diplomats' not in people
    assert 'Vanguard Tech' in people
    assert 'Vanguard Capital' in people


def test_delete_linked_person_issue_149(client):
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    gordon = client.app.session().query(Person) \
        .filter(Person.last_name == 'Gordon') \
        .one()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'About Flash'
    new_page.form['people-0-person'] = gordon.id.hex
    new_page.form['people-0-context_specific_function'] = 'Astronaut'
    new_page.form['people-0-display_function_in_person_directory'] = True
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    person = client.get('/people').click('Gordon Flash')
    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    # this used to throw an error before issue 149 was fixed
    edit_page.form.submit().follow()


def test_context_specific_function(session, org_app):
    organizations = ["Forum der Ortsparteien und Quartiervereine", "Urnenbüro"]
    context_specific_functions = [
        "Präsidentin Urnenbüro",
        "Mitglied Forum der Ortsparteien und Quartiervereine"
    ]

    person = Person(
        id=UUID("fa471984-7bf3-41ce-a336-0d01a08cd6ba"),
        first_name="Klara",
        last_name="Fall",
    )
    session.add(person)
    person_to_function1 = [[person.id.hex, (context_specific_functions[0],
                                            True)]]
    person_to_function2 = [[person.id.hex, (context_specific_functions[1],
                                            True)]]

    topic1 = Topic(title=organizations[0], name="topic1")
    topic2 = Topic(title=organizations[1], name="topic2")

    # Pretend we have ContentMixin:
    topic1.content = {'people': person_to_function1}
    topic2.content = {'people': person_to_function2}
    session.add(topic1)
    session.add(topic2)
    topics = [topic1, topic2]
    request = CoreRequest(
        environ={
            "wsgi.url_scheme": "https",
            "PATH_INFO": "/",
            "HTTP_HOST": "localhost",
        }, app=org_app,
    )
    link1, link2 = (request.link(t) for t in topics)
    session.flush()

    organization_to_function = list(person_functions_by_organization(
        person, topics, request
    ))

    org_link_1 = f'<a href="{link1}">{organizations[0]}</a>'
    org_link_2 = f'<a href="{link2}">{organizations[1]}</a>'
    first_expected = Markup(f"<span>{org_link_1}: "
                            f"{context_specific_functions[0]}</span>")

    second_expected = Markup(f"<span>{org_link_2}: "
                             f"{context_specific_functions[1]}</span>")
    assert organization_to_function[0] == first_expected
    assert organization_to_function[1] == second_expected

    # Now make it not visible
    person_to_function1 = [[person.id.hex, (context_specific_functions[0],
                                            False)]]
    person_to_function2 = [[person.id.hex, (context_specific_functions[1],
                                            False)]]

    topic1.content = {'people': person_to_function1}
    topic2.content = {'people': person_to_function2}
    session.add(topic1)
    session.add(topic2)
    topics = [topic1, topic2]

    session.flush()

    organization_to_function = list(person_functions_by_organization(
        person, topics, request
    ))
    assert organization_to_function == []
