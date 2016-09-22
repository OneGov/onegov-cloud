import onegov.feriennet

from onegov.testing import utils
from onegov.org.testing import Client, get_message


def get_publication_url(page, kind):
    return page.pyquery('a.{}'.format(kind)).attr('ic-post-to')


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.feriennet, onegov.feriennet.FeriennetApp)


def test_activity_permissions(es_feriennet_app):
    anonymous = Client(es_feriennet_app)

    admin = Client(es_feriennet_app)
    admin.login_admin()

    editor = Client(es_feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    url = '/angebot/learn-how-to-program'

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anonymous.get('/angebote')
    assert "Learn How to Program" not in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anonymous.get(url, expect_errors=True).status_code == 403
    assert admin.get(url, expect_errors=True).status_code == 403

    editor.post(get_publication_url(editor.get(url), 'request-publication'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anonymous.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anonymous.get(url, expect_errors=True).status_code == 403
    assert admin.get(url).status_code == 200

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_publication_url(ticket, 'accept-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" in anonymous.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anonymous.get(url).status_code == 200
    assert admin.get(url).status_code == 200

    ticket = admin.get(ticket.request.url)
    admin.post(get_publication_url(ticket, 'archive-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anonymous.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anonymous.get(url, expect_errors=True).status_code == 403
    assert admin.get(url).status_code == 200


def test_activity_communication(feriennet_app):
    admin = Client(feriennet_app)
    admin.login_admin()

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn PHP"
    new.form['lead'] = "Using a Raspberry Pi we will learn PHP"
    new.form.submit()

    editor.post(get_publication_url(
        editor.get('/angebot/learn-php'), 'request-publication'))

    assert len(feriennet_app.smtp.outbox) == 1
    assert "Ein neues Ticket" in get_message(feriennet_app, 0)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen", index=0).follow()
    assert "Learn PHP" in ticket

    admin.post(get_publication_url(ticket, 'reject-activity'))
    assert len(feriennet_app.smtp.outbox) == 2
    message = get_message(feriennet_app, 1)
    assert "leider abgelehnt" in message
    assert "Learn PHP" in message
    assert "Using a Raspberry Pi we will learn PHP" in message

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn Python"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    editor.post(get_publication_url(
        editor.get('/angebot/learn-python'), 'request-publication'))

    assert len(feriennet_app.smtp.outbox) == 3
    assert "Ein neues Ticket" in get_message(feriennet_app, 2)

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    assert "Learn Python" in ticket

    admin.post(get_publication_url(ticket, 'accept-activity'))
    assert len(feriennet_app.smtp.outbox) == 4
    message = get_message(feriennet_app, 3)
    assert "wurde angenommen" in message
    assert "Learn Python" in message
    assert "Using a Raspberry Pi we will learn Python" in message


def test_activity_search(es_feriennet_app):
    anonymous = Client(es_feriennet_app)

    admin = Client(es_feriennet_app)
    admin.login_admin()

    editor = Client(es_feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    url = '/angebot/learn-how-to-program'

    # in preview, activites can't be found
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' not in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anonymous.get('/suche?q=Learn')

    editor.post(get_publication_url(editor.get(url), 'request-publication'))

    # once proposed, activites can be found by the admin only
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anonymous.get('/suche?q=Learn')

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_publication_url(ticket, 'accept-activity'))

    # once accepted, activites can be found by anyone
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' in anonymous.get('/suche?q=Learn')

    ticket = admin.get(ticket.request.url)
    admin.post(get_publication_url(ticket, 'archive-activity'))

    # archived the search will fail again, except for admins
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anonymous.get('/suche?q=Learn')
