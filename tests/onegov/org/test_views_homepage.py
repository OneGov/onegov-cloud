import transaction


def test_homepage(client):
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
