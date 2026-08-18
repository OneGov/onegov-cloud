from __future__ import annotations

import transaction


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_homepage(client: Client) -> None:
    client.app.org.meta['homepage_cover'] = "<b>0xdeadbeef</b>"
    client.app.org.meta['homepage_structure'] = """
        <row>
            <column span="8">
                <homepage-cover />
            </column>
            <column span="4">
                <panel>
                    <news />
                </panel>
                <panel>
                    <events />
                </panel>
            </column>
        </row>
    """

    transaction.commit()

    homepage = client.get('/')

    assert '<b>0xdeadbeef</b>' in homepage
    assert '<h2>Veranstaltungen</h2>' in homepage


def test_add_new_root_topic(client: Client) -> None:
    # ensure a root page can be added once admin is logged-in
    client.login_admin().follow()

    page = client.get('/')
    assert 'Hinzufügen' in page
    assert 'Thema' in page

    page = page.click('Thema')
    page.form['title'] = 'Super Org Thema'
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert 'Das neue Thema wurde hinzugefügt' in page
    assert page.pyquery('.callout')
    assert page.pyquery('.success')

    page = client.get('/topics/super-org-thema')
    assert page.status_code == 200
    assert 'Super Org Thema' in page


def test_homepage_settings_return_to(client: Client) -> None:
    client.login_admin()

    # opening the settings from the homepage remembers the origin, so both
    # the cancel link and a successful save return to the homepage
    homepage = client.get('/')
    home_url = homepage.request.url
    edit_href = homepage.pyquery('.edit-bar a.edit-link').attr('href')
    settings = client.get(edit_href)

    cancel_href = settings.pyquery('a.cancel-link').attr('href')
    assert cancel_href == home_url
    assert settings.form.submit().location == home_url

    # opening it directly (no origin) falls back to the settings index
    settings = client.get('/homepage-settings')
    cancel_href = settings.pyquery('a.cancel-link').attr('href')
    assert cancel_href is not None and cancel_href.endswith('/settings')
    location = settings.form.submit().location
    assert location is not None and location.endswith('/settings')
