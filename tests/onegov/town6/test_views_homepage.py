import transaction


def test_homepage(client):
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

    # Test chatbot on homepage
    assert not homepage.pyquery('.chatbot')

    client.app.org.chat_customer_id = 'HEY'
    client.app.org.chat_type = 'scoutss'
    transaction.commit()
    assert client.get('/').pyquery('.chat')

    editor = client.spawn()
    editor.login_editor()
    assert editor.get('/').pyquery('.chat')

    client.app.org.hide_chat_for_roles = ['admin', 'editor']
    transaction.commit()
    assert not editor.get('/').pyquery('.chat')

    client.app.org.disable_chat = True
    transaction.commit()
    assert not client.get('/').pyquery('.chat')
