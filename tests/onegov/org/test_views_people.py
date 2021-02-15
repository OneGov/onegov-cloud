from onegov.people import Person


def test_people_view(client):
    client.login_admin()
    settings = client.get('/module-settings')
    settings.form['hidden_people_fields'] = ['academic_title', 'profession']
    settings.form.submit()
    client.logout()

    client.login_editor()

    people = client.get('/people')
    assert 'noch keine Personen' in people

    new_person = people.click('Person')
    new_person.form['academic_title'] = 'Dr.'
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form['profession'] = 'Hero'
    person = new_person.form.submit().follow()

    assert 'Gordon Flash' in person
    assert 'Dr.' in person
    assert 'Hero' in person

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
    assert 'noch keine Personen' in people


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

    gordon = client.app.session().query(Person)\
        .filter(Person.last_name == 'Gordon')\
        .one()

    ming = client.app.session().query(Person)\
        .filter(Person.last_name == 'Ming')\
        .one()

    new_page.form['title'] = 'About Flash'
    new_page.form['people_' + gordon.id.hex] = True
    new_page.form['people_' + gordon.id.hex + '_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    assert edit_page.form['people_' + gordon.id.hex].value == 'y'
    assert edit_page.form['people_' + gordon.id.hex + '_function'].value \
        == 'Astronaut'

    assert edit_page.form['people_' + ming.id.hex].value is None
    assert edit_page.form['people_' + ming.id.hex + '_function'].value == ''


def test_delete_linked_person_issue_149(client):
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    gordon = client.app.session().query(Person)\
        .filter(Person.last_name == 'Gordon')\
        .one()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = 'About Flash'
    new_page.form['people_' + gordon.id.hex] = True
    new_page.form['people_' + gordon.id.hex + '_function'] = 'Astronaut'
    edit_page = new_page.form.submit().follow().click('Bearbeiten')

    person = client.get('/people').click('Gordon Flash')
    delete_link = person.pyquery('a.delete-link').attr('ic-delete-from')
    client.delete(delete_link)

    # this used to throw an error before issue 149 was fixed
    edit_page.form.submit().follow()
