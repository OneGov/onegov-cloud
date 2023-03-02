def test_sort_topics(client):
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 1"
    page = page.form.submit().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 2"
    page = page.form.submit().follow()

    page = page.click('Sortieren')
    page = page.follow()

    assert "Topic 1" in page
    assert "Topic 2" in page


def get_select_option_id_by_text(select_form, search_text):
    found = []
    for option in select_form.options:
        # each option is a tuple (id, bool, select text)
        if search_text in option[2]:
            found.append(option[0])  # append page id

    if len(found) == 1:
        return found[0]
    else:
        print(f'Found multiple ids with {search_text}: {found}')
        return None


def test_move_topics(client):
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 1"
    page = page.form.submit().follow()
    assert page.status_code == 200

    page = client.get('/topics/themen')
    page = page.click('Thema')
    page.form['title'] = "Topic 2"
    page = page.form.submit().follow()
    assert page.status_code == 200

    page = page.click('Verschieben')  # move topic 2 under topic 1
    parent_id = get_select_option_id_by_text(page.form['parent_id'], 'Topic 1')
    page.form['parent_id'].select(parent_id)
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert client.get('/topics/themen/topic-1/topic-2')

    # move page topic-1 to 'root' including subpage
    page = client.get('/topics/themen/topic-1')
    page = page.click('Verschieben')
    page.form['parent_id'].select('root')
    page = page.form.submit().follow()
    print(page.request.url)
    assert client.get('/topics/topic-1')
    assert client.get('/topics/topic-1/topic-2')

    # test moving topic to itself
    page = client.get('/topics/topic-1/topic-2')
    page = page.click('Verschieben')
    parent_id = get_select_option_id_by_text(page.form['parent_id'], 'Topic 2')
    page.form['parent_id'].select(parent_id)
    page = page.form.submit()
    assert page.pyquery('.alert')
    assert page.pyquery('.error')
    assert 'Invalid destination selected' in page


def test_contact_info_visible(client):
    client.login_admin().follow()

    page = client.get('/topics/themen')
    page = page.click('Bearbeiten')
    page.form['contact'] = "Test contact info"
    page = page.form.submit().follow()

    assert "Test contact info" in page

    page = page.click('Bearbeiten')
    page.form['hide_contact'] = True
    page = page.form.submit().follow()

    assert "Test contact info" not in page

    page = page.click('Bearbeiten')
    page.form['hide_contact'] = False
    page = page.form.submit().follow()

    assert "Test contact info" in page


def test_view_page_as_member(client):
    admin = client
    client.login_admin()

    new_page = admin.get('/topics/organisation').click('Thema')
    new_page.form['title'] = "Test"
    new_page.form['access'] = 'member'
    page = new_page.form.submit().follow()
    page_url = '/topics/organisation/test'

    # Test if admin can see page
    admin.get(page_url)
    page = admin.get('/topics/organisation')
    assert 'Test' in page

    # Test if a member can see the page
    member = client.spawn()
    member.login_member()
    member.get(page_url)
    page = member.get('/topics/organisation')
    assert 'Test' in page

    # Test if a visitor can not see the page
    anon = client.spawn()
    anon.get(page_url, status=403)
    page = anon.get('/topics/organisation')
    assert 'Test' not in page
