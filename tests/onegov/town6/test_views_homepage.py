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
                <services />
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
            <homepage-tiles show-title="True"/>
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
    assert 'Veranstaltungen' in homepage
    assert 'Fokus' in homepage
    assert 'Dienstleistungen' in homepage
    assert 'Aktuelles' in homepage
    assert 'Alle Beiträge' in homepage
    assert 'Ausgewählte Themen' in homepage
    assert 'Partners' in homepage

    # Test chatbot on homepage
    assert not homepage.pyquery('.chatbot')

    client.app.org.chatbot_customer_id = 'HEY'
    client.app.org.chatbot_type = 'scoutss'
    transaction.commit()
    assert client.get('/').pyquery('.chatbot')

    editor = client.spawn()
    editor.login_editor()
    assert editor.get('/').pyquery('.chatbot')

    client.app.org.hide_chatbot_for_roles = ['admin', 'editor']
    transaction.commit()
    assert not editor.get('/').pyquery('.chatbot')

    client.app.org.disable_chatbot = True
    transaction.commit()
    assert not client.get('/').pyquery('.chatbot')
