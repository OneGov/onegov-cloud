from __future__ import annotations

from xml.etree.ElementTree import tostring

import transaction
from markupsafe import Markup

from onegov.api.models import ApiKey
from onegov.core.utils import Bunch
from onegov.org.models import News
from onegov.org.models import Organisation
from onegov.org.models import Topic
from onegov.org.models.page import TopicCollection, NewsCollection

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .conftest import Client


def test_gever_settings_only_https_allowed(client: Client) -> None:
    client.login_admin()
    settings = client.get('/gever-credentials')
    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'http://example.org/'

    settings = settings.form.submit().maybe_follow()

    assert "Link muss mit 'https' beginnen" in settings

    settings.form['gever_username'] = 'foo'
    settings.form['gever_password'] = 'bar'
    settings.form['gever_endpoint'] = 'https://example.org/'

    res = client.get('/gever-credentials')
    assert res.status_code == 200


def test_api_keys_create_and_delete(client: Client) -> None:
    client.login_admin()

    settings = client.get('/api-keys')
    settings.form['name'] = "My API key"
    page = settings.form.submit()
    assert 'My API key' in page

    key = client.app.session().query(ApiKey).first()
    assert key is not None
    assert key.name == "My API key"
    assert key.read_only == True

    # manually extract the link
    delete_link = tostring(page.pyquery('a.confirm')[0]).decode('utf-8')
    url = client.extract_href(delete_link)
    remove_chars = len("http://localhost")
    link = url[remove_chars:]

    client.delete(link)
    # should be gone
    assert client.app.session().query(ApiKey).first() is None


def test_all_settings_are_reachable(client: Client) -> None:
    # The purpose is to identify any broken or unreachable settings links that
    # might happen if a view is missing

    client.login_admin()
    page = client.get('/settings')
    links = [
        e.attrib.get('href')
        for e in page.pyquery('[data-settings-item] > a[href]')
    ]

    assert all(client.get(link).status_code == 200 for link in links)


def test_settings_search_markup(client: Client) -> None:
    client.login_admin()
    page = client.get('/settings')

    assert page.pyquery('[data-settings-search]').attr('type') == 'search'
    assert page.pyquery('[data-settings-search-results]').attr('hidden')
    assert page.pyquery('.settings-category')
    assert page.pyquery('[data-settings-item]')

    primary_color = page.pyquery(
        '[data-settings-result-kind="field"]' '[href$="#primary_color"]'
    )
    assert primary_color.find('strong').text() == 'Primärfarbe'
    assert primary_color.attr('href').endswith(
        '/appearance-settings#primary_color'
    )
    assert 'Primärfarbe' in primary_color.attr('data-settings-search-text')
    assert 'Primary Color' in primary_color.attr('data-settings-search-text')

    reply_to = page.pyquery(
        '[data-settings-result-kind="field"][href$="#reply_to"]'
    )
    assert 'Antworten an automatisch generierte E-Mails' in reply_to.text()
    assert 'Replies to automated e-mails' in reply_to.attr(
        'data-settings-search-text'
    )


def test_setting_view_registry(client: Client) -> None:
    registry = client.app.config.setting_view_registry
    appearance = registry[(Organisation, 'appearance-settings')]

    assert appearance.setting == 'Appearance'
    assert appearance.icon == 'fa-eye'
    assert appearance.order == 30
    assert (Organisation, 'migrate-links') not in registry


def test_settings_search_french_locale(client: Client) -> None:
    client.login_admin()
    organisation = client.get('/organisation-settings')
    organisation.form['locales'] = 'fr_CH'
    organisation.form.submit()
    client.set_cookie('locale', 'fr_CH')
    header_settings = client.get('/header-settings')
    page = client.get('/settings')

    primary_color = page.pyquery(
        '[data-settings-result-kind="field"]' '[href$="#primary_color"]'
    )
    assert primary_color.find('strong').text() == 'Couleur primaire'
    assert 'Couleur primaire' in primary_color.attr(
        'data-settings-search-text'
    )
    assert 'Primary Color' in primary_color.attr('data-settings-search-text')

    reply_to = page.pyquery(
        '[data-settings-result-kind="field"][href$="#reply_to"]'
    )
    assert 'Les réponses aux e-mails automatisés' in reply_to.text()
    assert 'Replies to automated e-mails' in reply_to.attr(
        'data-settings-search-text'
    )

    announcement = page.pyquery(
        '[data-settings-result-kind="fieldset"]'
        '[href$="#fieldset-announcement"]'
    )
    assert announcement.find('strong').text() == 'Annonce'
    assert 'Announcement' in announcement.attr('data-settings-search-text')
    assert header_settings.pyquery('#fieldset-announcement')


def test_general_settings(client: Client) -> None:
    client.login_admin()

    page = client.get('/topics/themen')
    assert 'class="header-image"' not in page

    # Appearance settings
    settings = client.get('/appearance-settings')
    settings.form['standard_image'] = 'standard_image.png'
    settings.form['page_image_position'] = 'header'
    settings.form['custom_css'] = 'h2 { text-decoration: underline; }'
    page = settings.form.submit().follow()

    # Organisation settings
    settings = client.get('/organisation-settings')
    settings.form['reply_to'] = 'info@govikon.ch'
    page = settings.form.submit().follow()

    assert '<style>h2 { text-decoration: underline; }</style>' in page

    assert 'class="header-image"' in page


def test_analytics_settings(client: Client) -> None:
    # plausible
    client.login_admin()

    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'plausible'
    settings.form['plausible_domain'] = 'govikon.ch'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'src="https://dummy-plausible.test/script.js"' in settings
    assert 'href="https://dummy-plausible.test/govikon.ch"' in settings

    # matomo
    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'matomo'
    settings.form['matomo_site_id'] = '28'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'var u="https://dummy-matomo.test/";' in settings
    assert 'href="https://dummy-matomo.test/"' in settings

    # siteimprove
    settings = client.get('/analytics-settings')
    settings.form['analytics_provider_name'] = 'siteimprove'
    settings.form['siteimprove_site_id'] = '5775'
    settings.form.submit()

    settings = client.get('/analytics-settings')
    assert 'href="https://www.siteimprove.com/"' in settings
    assert (
        'src="https://siteimproveanalytics.com/js/siteanalyze_5775.js"'
    ) in settings


def test_firebase_settings(client: Client) -> None:
    client.login_admin()

    # Pretend this is real data (it's completely random)
    code = """
    {
  "type": "service_account",
  "project_id": "test-project-54321",
  "private_key_id": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",
  "private_key": "private key",
  "client_email": "firebase-admin@test-project-54321.iam.gserviceaccount.com",
  "client_id": "123456789012345678901",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "foobar.com",
  "universe_domain": "googleapis.com"
    }
    """

    settings = client.get('/firebase')
    assert 'Übersicht Push-Benachrichtigungen' in settings

    settings.form['firebase_adminsdk_credential'] = code

    settings = settings.form.submit().maybe_follow()
    assert 'Ihre Änderungen wurden gespeichert' in settings


def test_resource_settings(client: Client) -> None:
    client.login_admin()

    settings = client.get('/resource-settings')
    settings.form['resource_header_html'] = '<h1>foo</h1>'
    settings.form['resource_footer_html'] = '<p>bar</p>'
    assert ('Ihre Änderungen wurden gespeichert' in
            settings.form.submit().maybe_follow())

    page = client.get('/resources')
    assert 'Allgemeine Informationen zu Reservationen' in page
    assert '<h1>foo</h1>' in page
    assert '<p>bar</p>' in page


def test_migrate_links(client: Client) -> None:
    session = client.app.session()
    request: Any = Bunch(**{
        'session': session,
        'identity.role': 'admin'
    })
    old_domain = 'foo.ch'

    # create topic
    topic = Topic(title='Foo Topic', name='foo-topic')
    topic.text = Markup('<p>Wow, <a href="https://foo.ch/abc">foo</a> is a '
                        'great page!</p>')
    session.add(topic)
    topic_text = topic.text

    # add news article (must be under the seeded /news/ root)
    from onegov.page import PageCollection
    news_root = PageCollection(session).by_path('/news/', ensure_type='news')
    assert isinstance(news_root, News)
    news = News(title='Big News', name='big-news', parent=news_root)
    news.text = Markup(
        '<p>Big news https://foo.ch/big-news and '
        '<a href="https://foo.ch/bigger-news">bigger news</a> can be found '
        'here</p>'
    )
    session.add(news)
    news_text = news.text

    transaction.commit()

    def verify_tags_in_text(text: Markup) -> None:
        # verify p tag not escaped
        assert '<p>' in text
        assert '&lt;p&gt;' not in text

        # verify a tag not escaped
        assert '<a href="' in text
        assert '</a>' in text
        assert '&lt;a&gt;' not in text

    def get_topic_text() -> Markup:
        t = TopicCollection(request).by_name('foo-topic')
        assert t is not None and t.text is not None
        verify_tags_in_text(t.text)
        return t.text

    def get_news_text() -> Markup:
        n = NewsCollection(request).by_title('Big News')
        assert n is not None and n.text is not None
        verify_tags_in_text(n.text)
        return n.text

    assert old_domain in get_topic_text()
    assert old_domain in get_news_text()

    # execute migrate links as test
    client.login_admin()
    migrate_page = client.get('/migrate-links')
    migrate_page.form['old_domain'] = old_domain
    migrate_page.form['test'] = True
    result = migrate_page.form.submit()
    assert 'Total 3 Links gefunden' in result

    assert old_domain in get_topic_text()
    assert old_domain in get_news_text()

    # execute migrate links
    migrate_page = client.get('/migrate-links')
    migrate_page.form['old_domain'] = old_domain
    migrate_page.form['test'] = False
    result = migrate_page.form.submit().follow()
    assert '3 Links migriert' in result

    topic_text_new = get_topic_text()
    news_text_new = get_news_text()
    assert old_domain not in topic_text_new
    assert old_domain not in news_text_new

    assert topic_text.replace('foo.ch', 'localhost') == topic_text_new
    assert news_text.replace('foo.ch', 'localhost') == news_text_new
