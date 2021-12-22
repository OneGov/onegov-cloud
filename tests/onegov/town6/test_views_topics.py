

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
