import textwrap

import pytest
import transaction
from webtest import Upload

from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.form import FormCollection


@pytest.mark.flaky(reruns=3)
def test_basic_search(client_with_es):
    client = client_with_es
    client.login_admin()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Now supporting fulltext search"
    add_news.form['lead'] = "It is pretty awesome"
    add_news.form['text'] = "Much <em>wow</em>"
    news = add_news.form.submit().follow()

    client.app.es_client.indices.refresh(index='_all')

    root_page = client.get('/')
    root_page.form['q'] = "fulltext"

    search_page = root_page.form.submit()
    assert "fulltext" in search_page
    assert "Now supporting fulltext search" in search_page
    assert "It is pretty awesome" in search_page

    search_page.form['q'] = "wow"
    search_page = search_page.form.submit()
    assert "fulltext" in search_page
    assert "Now supporting fulltext search" in search_page
    assert "It is pretty awesome" in search_page

    # make sure anonymous doesn't see hidden things in the search results
    assert "fulltext" in client.spawn().get('/search?q=fulltext')
    edit_news = news.click("Bearbeiten")
    edit_news.form['access'] = 'private'
    edit_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    assert "Now supporting" not in client.spawn().get('/search?q=fulltext')
    assert "Now supporting" in client.get('/search?q=fulltext')


@pytest.mark.flaky(reruns=3)
def test_view_search_is_limiting(client_with_es):
    # ensures that the search doesn't just return all results
    # a regression that occured for anonymous uses only

    client = client_with_es
    client.login_admin()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Foobar"
    add_news.form['lead'] = "Foobar"
    add_news.form.submit()

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Deadbeef"
    add_news.form['lead'] = "Deadbeef"
    add_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page

    client.logout()

    root_page = client.get('/')
    root_page.form['q'] = "Foobar"
    search_page = root_page.form.submit()

    assert "1 Resultat" in search_page


@pytest.mark.flaky(reruns=3)
def test_basic_autocomplete(client_with_es):
    client = client_with_es
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    client.app.es_client.indices.refresh(index='_all')
    assert client.get('/search/suggest?q=Go').json == ["Gordon Flash"]
    assert client.get('/search/suggest?q=Fl').json == ["Flash Gordon"]


def test_search_signed_files(client_with_es):
    client = client_with_es
    client.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with open(path, 'rb') as f:
        page = client.get('/files')
        page.form['file'] = Upload('Sample.pdf', f.read(), 'application/pdf')
        page.form.submit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' not in client.spawn().get('/search?q=Adobe')

    transaction.begin()
    pdf = FileCollection(client.app.session()).query().one()
    pdf.signed = True
    transaction.commit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' in client.spawn().get('/search?q=Adobe')


def test_search_hashtags(client_with_es):

    client = client_with_es
    client.login_admin()

    page = client.get('/news').click("Nachricht")
    page.form['title'] = "We have a new homepage"
    page.form['lead'] = "It is very good"
    page.form['text'] = "It is lots of fun #newhomepage"

    page = page.form.submit().follow()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    assert 'We have a new homepage' in client.get('/search?q=%23newhomepage')
    assert 'We have a new homepage' not in client.get('/search?q=%23newhomepa')


def test_ticket_chat_search(client_with_es):
    client = client_with_es

    collection = FormCollection(client.app.session())
    collection.definitions.add('Profile', definition=textwrap.dedent("""
        First name * = ___
        Last name * = ___
        E-Mail * = @@@
    """), type='custom')

    transaction.commit()

    # submit a form
    client.login_admin()

    page = client.get('/forms').click('Profile')
    page.form['first_name'] = 'Foo'
    page.form['last_name'] = 'Bar'
    page.form['e_mail'] = 'foo@bar.baz'
    page = page.form.submit().follow().form.submit().follow()

    # send a message that should be findable through the search
    page.form['text'] = "I spelt my name wrong: it's deadbeef"
    page = page.form.submit().follow()

    # at this point logged in users should find the ticket by 'deadbeef'
    client.app.es_client.indices.refresh(index='_all')

    page = client.get('/search?q=deadbeef')
    assert 'Foo' in page

    # but anonymous users should not
    page = client.spawn().get('/search?q=deadbeef')
    assert 'Foo' not in page
