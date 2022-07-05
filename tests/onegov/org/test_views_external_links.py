def test_external_links_in_forms(client):
    """
    Test adding a fake form that is a dummy to an external url. So this
    is the first collection mixing models together. """
    client.login_admin()
    page = client.get('/forms').click('Externes Formular', index=0)

    assert page.pyquery('.main-title').text().strip() ==\
           'Neues externes Formular'

    url = 'https://bye-bye.future'
    page.form['title'] = 'AAA My external form'
    page.form['lead'] = 'My Description'
    page.form['url'] = url

    page = page.form.submit().follow()

    # Tests the to redirect given in the link on forms page
    assert page.request.url.endswith('/forms')
    assert 'Neues externes Formular hinzugefügt' in page
    assert 'My Description' in page
    entries = page.pyquery('a.list-title')

    urls = [e.attrib['href'] for e in entries]
    assert url in urls

    names = [e.text.strip() for e in entries]
    assert names == sorted(names)

    # edit the link
    edit_link = page.pyquery('.edit-link').attr('href')
    page = client.get(edit_link)
    assert 'Externes Formular editieren' in page.pyquery('.main-title').text()
    assert page.form['title'].value == 'AAA My external form'
    assert page.form['url'].value == url

    page = page.form.submit().follow()
    assert page.request.url.endswith('/forms')
