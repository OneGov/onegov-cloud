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
    assert "Hinzufügen" in page

    page = page.click('Hinzufügen')
    page.form['title'] = 'Super Org Thema'
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert 'Das neue Thema wurde hinzugefügt' in page
    assert page.pyquery('.callout')
    assert page.pyquery('.success')

    page = client.get('/topics/super-org-thema')
    assert page.status_code == 200
    assert 'Super Org Thema' in page
