import onegov.feriennet
import transaction

from onegov.testing import utils
from onegov.org.testing import Client, get_message, select_checkbox
from onegov.activity import ActivityCollection


def get_publication_url(page, kind):
    return page.pyquery('a.{}'.format(kind)).attr('ic-post-to')


def test_view_permissions():
    utils.assert_explicit_permissions(
        onegov.feriennet, onegov.feriennet.FeriennetApp)


def test_activity_permissions(es_feriennet_app):
    anon = Client(es_feriennet_app)

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
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" not in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anon.get(url, expect_errors=True).status_code == 404
    assert admin.get(url, expect_errors=True).status_code == 404

    editor.post(get_publication_url(editor.get(url), 'request-publication'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anon.get(url, expect_errors=True).status_code == 404
    assert admin.get(url).status_code == 200

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_publication_url(ticket, 'accept-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anon.get(url).status_code == 200
    assert admin.get(url).status_code == 200

    ticket = admin.get(ticket.request.url)
    admin.post(get_publication_url(ticket, 'archive-activity'))

    assert "Learn How to Program" in editor.get('/angebote')
    assert "Learn How to Program" not in anon.get('/angebote')
    assert "Learn How to Program" in admin.get('/angebote')
    assert editor.get(url).status_code == 200
    assert anon.get(url, expect_errors=True).status_code == 404
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
    anon = Client(es_feriennet_app)

    admin = Client(es_feriennet_app)
    admin.login_admin()

    editor = Client(es_feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"
    new.form.submit()

    url = '/angebot/learn-how-to-program'

    # in preview, activities can't be found
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' not in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')

    editor.post(get_publication_url(editor.get(url), 'request-publication'))

    # once proposed, activities can be found by the admin only
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')

    ticket = admin.get('/tickets/ALL/open').click("Annehmen").follow()
    admin.post(get_publication_url(ticket, 'accept-activity'))

    # once accepted, activities can be found by anyone
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' in anon.get('/suche?q=Learn')

    ticket = admin.get(ticket.request.url)
    admin.post(get_publication_url(ticket, 'archive-activity'))

    # archived the search will fail again, except for admins
    es_feriennet_app.es_client.indices.refresh(index='_all')
    assert 'search-result-vacation' in admin.get('/suche?q=Learn')
    assert 'search-result-vacation' not in editor.get('/suche?q=Learn')
    assert 'search-result-vacation' not in anon.get('/suche?q=Learn')


def test_activity_filter(feriennet_app):

    anon = Client(feriennet_app)

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Program"
    new.form['lead'] = "Using a Raspberry Pi we will learn Python"

    select_checkbox(new, "tags", "Computer")
    select_checkbox(new, "tags", "Wissenschaft")

    new.form.submit()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Cook"
    new.form['lead'] = "Using a Stove we will cook a Python"

    select_checkbox(new, "tags", "Kochen")
    select_checkbox(new, "tags", "Wissenschaft")

    new.form.submit()

    for activity in ActivityCollection(feriennet_app.session()).query().all():
        activity.propose().accept()

    transaction.commit()

    activities = anon.get('/angebote')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" not in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Kochen')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" not in activities

    activities = activities.click('Computer')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    activities = activities.click('Computer')
    activities = activities.click('Kochen')
    activities = activities.click('Wissenschaft')
    assert "Learn How to Cook" in activities
    assert "Learn How to Program" in activities

    # the state filter works for editors
    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Learn How to Dance"
    new.form['lead'] = "We will dance with a Python"
    new.form.submit()

    # editors see the state as a filter
    assert "Vorschau" in editor.get('/angebote')

    # anonymous does not
    assert "Vorschau" not in anon.get('/angebote')

    activities = editor.get('/angebote').click('Vorschau')
    assert "Learn How to Cook" not in activities
    assert "Learn How to Program" not in activities
    assert "Learn How to Dance" in activities


def test_organiser_info(feriennet_app):

    admin = Client(feriennet_app)
    admin.login_admin()

    editor = Client(feriennet_app)
    editor.login_editor()

    new = editor.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Legos"
    new.form['lead'] = "Like Minecraft, but in the real world"
    new.form.submit()

    new = admin.get('/angebote').click("Angebot erfassen")
    new.form['title'] = "Play with Playmobil"
    new.form['lead'] = "Like Second Life, but in the real world"
    new.form.submit()

    for activity in ActivityCollection(feriennet_app.session()).query().all():
        activity.propose().accept()

    transaction.commit()

    # by default the email address of the owner is shown
    assert 'editor@example.org' in admin.get('/angebot/play-with-legos')
    assert 'admin@example.org' in editor.get('/angebot/play-with-playmobil')

    # only the owner gets the change contact link
    assert "Kontakt ändern" in editor.get('/angebot/play-with-legos')
    assert "Kontakt ändern" not in editor.get('/angebot/play-with-playmobil')

    # only the owner gets the change contact link
    assert "Kontakt ändern" not in admin.get('/angebot/play-with-legos')
    assert "Kontakt ändern" in admin.get('/angebot/play-with-playmobil')

    # changes are reflected on the activity
    contact = editor.get('/angebot/play-with-legos').click('Kontakt ändern')
    contact.form['name'] = 'Editors Association'
    contact.form['address'] = 'Washington'
    contact.form['email'] = 'editors-association@example.org'
    contact.form['phone'] = '+41 23 456 789'
    contact.form['website'] = 'https://www.example.org'
    contact.form.submit()

    activity = editor.get('/angebot/play-with-legos')

    assert "Editors Association" in activity
    assert "Washington" in activity
    assert "editors-association@example.org" in activity
    assert "editor@example.org" not in activity
    assert "+41 23 456 789" in activity
    assert "https://www.example.org" in activity
