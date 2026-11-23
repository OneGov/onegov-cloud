import transaction


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_homepage(client: Client) -> None:
    client.app.org.meta['homepage_cover'] = "<b>0xdeadbeef</b>"
    client.app.org.meta['homepage_structure'] = """
    <row-wide>
        <column span="12">
            <slider />
        </column>
    </row-wide>
    <row>
        <column span="8">
            <focus image-src="img_src" image-url="img_url" />
        </column>
        <column span="4">
            <panel>
                <services>
                    <link url="https://admin.digital">admin.digital</link>
                </services>
            </panel>
        </column>
    </row>
    <row-wide bgcolor="gray">
        <column span="12">
            <row>
                <column span="12">
                    <news />
                </column>
            </row>
        </column>
    </row-wide>
    <row-wide bgcolor="primary">
        <column span="12">
            <row>
                <column span="12">
                    <events />
                </column>
            </row>
        </column>
    </row-wide>
    <row>
        <column span="12">
            <homepage-tiles/>
        </column>
    </row>
    <row>
        <column span="12">
            <directories />
        </column>
    </row>
    <row-wide bgcolor="gray">
        <column span="12">
            <row>
                <column span="12">
                    <partners />
                </column>
            </row>
        </column>
    </row-wide>
    """

    transaction.commit()

    homepage = client.get('/')

    assert '<b>0xdeadbeef</b>' not in homepage
    assert 'Alle Veranstaltungen' in homepage
    assert 'admin.digital' in homepage
    assert 'Alle Beiträge' in homepage


def test_add_new_root_topic(client: Client) -> None:
    # ensure a root page can be added once admin is logged-in
    client.login_admin().follow()

    page = client.get('/')
    assert 'Hinzufügen' in page
    assert 'Thema' in page

    page = page.click('Thema')
    page.form['title'] = 'Super Thema'
    page = page.form.submit().follow()
    assert page.status_code == 200
    assert 'Das neue Thema wurde hinzugefügt' in page
    assert page.pyquery('.callout')
    assert page.pyquery('.success')

    page = client.get('/topics/super-thema')
    assert page.status_code == 200
    assert 'Super Thema' in page


def test_chatbot(client: Client) -> None:
    anon = client.spawn()
    admin = client.spawn()
    admin.login_admin().follow()

    page = anon.get('/')
    assert 'floaty-chat' not in page

    settings = admin.get('/chat-settings')
    settings.form['enable_chat'] = 'chatbot'
    settings.form['chat_link'] = 'https://chatbot.example.org'
    settings.form.submit()

    page = anon.get('/')
    assert 'floaty-chat' in page
    assert 'https://chatbot.example.org' in page

    settings = admin.get('/chat-settings')
    settings.form['enable_chat'] = 'disabled'
    settings.form.submit()

    page = anon.get('/')
    assert 'floaty-chat' not in page
