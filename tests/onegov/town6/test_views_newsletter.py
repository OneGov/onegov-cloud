

def test_news(client):
    client.login_admin().follow()

    page = client.get('/news')
    page = page.click('Nachricht')
    page.form['title'] = "We have a new homepage"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun"
    page = page.form.submit().follow()

    page = client.get('/news')
    assert "Newsletter" in page.text
    page = client.get('/')
    assert "Newsletter" in page.text

    page = client.get('/newsletter-settings')
    page.form['show_newsletter'] = False
    page = page.form.submit().follow()

    page = client.get('/')
    assert "Newsletter" not in page.text

    page = client.get('/newsletter-settings')
    page.form['show_newsletter'] = True
    page = page.form.submit().follow()

    page = client.get('/')
    assert "Newsletter" in page.text
