import textwrap
import pytest
import transaction

from datetime import date
from datetime import datetime
from datetime import timedelta


from onegov.core.utils import module_path
from onegov.file import FileCollection
from onegov.form import FormCollection
from onegov.org.models.page import Page

from tests.onegov.org.common import get_cronjob_by_name
from tests.onegov.org.common import get_cronjob_url
from time import sleep
from sedate import utcnow
from webtest import Upload


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
    # elasticsearch
    assert "fulltext" in client.spawn().get('/search?q=fulltext')
    # postgres
    assert "fulltext" in client.spawn().get('/search-postgres?q=fulltext')

    edit_news = news.click("Bearbeiten")
    edit_news.form['access'] = 'private'
    edit_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch
    assert ("Now supporting" not in
            client.spawn().get('/search?q=fulltext'))
    assert "Now supporting" in client.get('/search?q=fulltext')

    # postgres
    assert ("Now supporting" not in
            client.spawn().get('/search-postgres?q=fulltext'))
    assert "Now supporting" in client.get('/search-postgres?q=fulltext')


@pytest.mark.flaky(reruns=3)
def test_view_search_is_limiting(client_with_es):
    # ensures that the search doesn't just return all results
    # a regression that occurred for anonymous uses only

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
def test_search_recently_published_object(client_with_es):
    client = client_with_es
    client.login_admin()
    anom = client.spawn()
    session = client.app.session()

    # Create objects, not yet published
    start = datetime.now() + timedelta(days=1)

    add_news = client.get('/news').click('Nachricht')
    add_news.form['title'] = "Now supporting fulltext search"
    add_news.form['lead'] = "It is pretty awesome"
    add_news.form['text'] = "Much <em>wow</em>"
    add_news.form['publication_start'] = start.isoformat()
    add_news.form.submit()

    client.app.es_client.indices.refresh(index='_all')

    page = session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one()
    assert page.access == 'public'
    assert page.published == False
    assert page.es_public == False

    # elasticsearch
    assert 'fulltext' in client.get('/search?q=wow')
    assert 'fulltext' not in anom.get('/search?q=wow')
    assert 'It is pretty awesome' in client.get('/search?q=fulltext')
    assert 'It is pretty awesome' not in anom.get('/search?q=fulltext')

    # postgres
    assert 'fulltext' in client.get('/search-postgres?q=wow')
    assert 'fulltext' not in anom.get('/search-postgres?q=wow')
    assert 'pretty awesome' in client.get('/search-postgres?q=fulltext')
    assert 'pretty awesome' not in anom.get('/search-postgres?q=fulltext')

    # Publish
    then = utcnow() - timedelta(minutes=30)
    transaction.begin()
    session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one().publication_start = then
    transaction.commit()

    # needed for ES
    job = get_cronjob_by_name(client.app, 'hourly_maintenance_tasks')
    job.app = client.app
    url = get_cronjob_url(job)
    client.get(url)
    sleep(5)

    page = session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one()
    assert page.access == 'public'
    assert page.published == True
    assert page.es_public == True

    # elasticsearch
    assert 'fulltext' in client.get('/search?q=wow')
    assert 'fulltext' in anom.get('/search?q=wow')
    assert 'It is pretty awesome' in client.get('/search?q=fulltext')
    assert 'It is pretty awesome' in anom.get('/search?q=fulltext')

    # postgres
    assert 'fulltext' in client.get('/search-postgres?q=wow')
    assert 'fulltext' in anom.get('/search-postgres?q=wow')
    assert 'It is pretty awesome' in client.get('/search-postgres?q=fulltext')
    assert 'It is pretty awesome' in anom.get('/search-postgres?q=fulltext')

    # Unpublish
    transaction.begin()
    session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one().publication_start = None
    session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one().publication_end = then
    transaction.commit()

    client.get(url)
    sleep(5)

    page = session.query(Page).filter(
        Page.title == "Now supporting fulltext search"
    ).one()
    assert page.access == 'public'
    assert page.published == False
    assert page.es_public == False

    # elasticsearch
    assert 'fulltext' in client.get('/search-postgres?q=wow')
    assert 'fulltext' not in anom.get('/search-postgres?q=wow')
    assert 'is pretty awesome' in client.get('/search-postgres?q=fulltext')
    assert 'is pretty awesome' not in anom.get('/search-postgres?q=fulltext')

    # postgres
    assert 'fulltext' in client.get('/search-postgres?q=wow')
    assert 'fulltext' not in anom.get('/search-postgres?q=wow')
    assert 'is pretty awesome' in client.get('/search-postgres?q=fulltext')
    assert 'is pretty awesome' not in anom.get('/search-postgres?q=fulltext')


@pytest.mark.flaky(reruns=3)
def test_search_for_page_with_member_access(client_with_es):
    client = client_with_es
    client.login_admin()
    anom = client.spawn()
    member = client.spawn()
    member.login_member()

    new_page = client.get('/topics/organisation').click('Thema')
    new_page.form['title'] = "Test"
    new_page.form['lead'] = "Memberius testius"
    new_page.form['access'] = 'member'
    new_page.form.submit().follow()

    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch
    assert 'Test' in client.get('/search?q=Memberius')
    assert 'Test' in member.get('/search?q=Memberius')
    assert 'Test' not in anom.get('/search?q=Memberius')

    # postgres
    assert 'Test' in client.get('/search-postgres?q=Memberius')
    assert 'Test' in member.get('/search-postgres?q=Memberius')
    assert 'Test' not in anom.get('/search-postgres?q=Memberius')


@pytest.mark.flaky(reruns=3)
def test_basic_autocomplete(client_with_es):
    client = client_with_es
    client.login_editor()

    people = client.get('/people')

    new_person = people.click('Person')
    new_person.form['first_name'] = 'Flash'
    new_person.form['last_name'] = 'Gordon'
    new_person.form.submit()

    # elasticsearch
    client.app.es_client.indices.refresh(index='_all')
    assert client.get('/search/suggest?q=Go').json == ["Gordon Flash"]
    assert client.get('/search/suggest?q=Fl').json == ["Flash Gordon"]

    # postgres has no auto-complete
    assert (client.get('/search-postgres/suggest?q=Gordon').
            json == ["Gordon Flash"])
    assert (client.get('/search-postgres/suggest?q=Flash').
            json == ["Gordon Flash"])


def test_search_publication_files(client_with_es):
    client = client_with_es
    client.login_admin()

    path = module_path('tests.onegov.org', 'fixtures/sample.pdf')
    with (open(path, 'rb') as f):
        page = client.get('/files')
        page.form['file'] = Upload(
            'Sample.pdf', f.read(), 'application/pdf')
        page.form.submit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch
    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' not in client.spawn().get('/search?q=Adobe')

    # postgres
    assert 'Sample' in client.get('/search-postgres?q=Adobe')
    assert 'Sample' not in client.spawn().get('/search-postgres?q=Adobe')

    transaction.begin()
    pdf = FileCollection(client.app.session()).query().one()
    pdf.publication = True
    transaction.commit()

    client.app.es_indexer.process()
    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch
    assert 'Sample' in client.get('/search?q=Adobe')
    assert 'Sample' in client.spawn().get('/search?q=Adobe')

    # postgres
    assert 'Sample' in client.get('/search-postgres?q=Adobe')
    assert 'Sample' in client.spawn().get('/search-postgres?q=Adobe')


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

    assert 'We have a new homepage' in client.get(
        '/search-postgres?q=%23newhomepage')
    assert 'We have a new homepage' not in client.get(
        '/search-postgres?q=%23newhomepa')


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

    page = client.get('/search-postgres?q=deadbeef')
    assert 'Foo' in page

    # but anonymous users should not
    page = client.spawn().get('/search-postgres?q=deadbeef')
    assert 'Foo' not in page


def test_search_future_events_are_sorted_by_occurrence_date(client_with_es):
    client = client_with_es
    client.login_admin()
    anom = client.spawn()
    member = client.spawn()
    member.login_member()

    event_data = [
        {
            "email": "test@example.org",
            "title": "Not sorted Concert",
            "location": "Location0",
            "organizer": "Organizer0",
            "start_date": date.today() - timedelta(days=10),
        },
        {
            "email": "test2@example.org",
            "title": "Second Concert",
            "location": "Location2",
            "organizer": "Organizer2",
            "start_date": date.today() + timedelta(days=20),
        },
        {
            "email": "test1@example.org",
            "title": "First Concert",
            "location": "Location1",
            "organizer": "Organizer1",
            "start_date": date.today() + timedelta(days=1),
        },
        {
            "email": "test4@example.org",
            "title": "Forth Concert",
            "location": "Location4",
            "organizer": "Organizer4",
            "start_date": date.today() + timedelta(days=111),
        },
        {
            "email": "test3@example.org",
            "title": "Third Concert",
            "location": "Location3",
            "organizer": "Organizer3",
            "start_date": date.today() + timedelta(days=35),
        },

    ]

    # Create a couple of events
    for data in event_data:
        form_page = client.get('/events/enter-event')
        form_page.form['email'] = data['email']
        form_page.form['title'] = data['title']
        form_page.form['location'] = data['location']
        form_page.form['organizer'] = data['organizer']
        form_page.form['start_date'] = data['start_date'].isoformat()
        form_page.form['start_time'] = "18:00"
        form_page.form['end_time'] = "22:00"
        form_page.form['repeat'] = 'without'

        events_redirect = form_page.form.submit().follow().follow()
        assert "erfolgreich erstellt" in events_redirect

    client.app.es_client.indices.refresh(index='_all')

    # elasticsearch even sorts past events by occurrence date
    for current_client in (client, member, anom):
        results = current_client.get('/search?q=Concert')
        # Expect ordered by occurrence date, for all search results of 'Event'
        assert [a.text.rstrip(' \n') for a in
                results.pyquery('li.search-result-events a')] == [
            'Not sorted Concert', 'First Concert', 'Second Concert',
            'Third Concert', 'Forth Concert'
        ]

    # postgres
    for current_client in (client, member, anom):
        results = current_client.get('/search-postgres?q=Concert')
        # Expect future events ordered by occurrence date, fare future first.
        # Past events are not sorted by occurrence date.
        assert [a.text.rstrip(' \n') for a in
                results.pyquery('li.search-result-events a')] == [
            'Forth Concert', 'Third Concert', 'Second Concert',
            'First Concert', 'Not sorted Concert'
        ]
