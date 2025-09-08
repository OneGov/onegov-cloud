from freezegun import freeze_time


def test_meetings(client):
    client.login_admin().follow()

    # ris views not enabled
    assert client.get('/meetings', status=404)
    assert client.get('/meetings/new', status=404)

    # enable ris
    settings = client.get('/ris-enable')
    settings.form['ris_enabled'] = True
    settings.form.submit()

    with freeze_time("2025-09-08 8:00"):
        page = client.get('/meetings')
        assert 'Sitzungen' in page
        assert 'Noch keine Sitzungen definiert' in page
        assert 'Nächste Sitzung' not in page

        # filters
        assert 'Vergangene Sitzungen' in page
        assert 'Künftige Sitzungen' in page

        # add meeting
        new = page.click('Sitzung', index=0)
        new.form['title'] = 'Test Meeting'
        new.form['address'] = 'Town Hall'
        meeting = new.form.submit().follow()
        assert 'Test Meeting' in meeting
        assert 'Es wurden noch keine Traktanden erfasst' in meeting
        assert 'Town Hall' in meeting

        page = client.get('/meetings')
        # FIXME: the meeting is kind of lost as there is no date set
        # assert 'Test Meeting' in page

        # edit meeting
        edit = meeting.click('Bearbeiten')
        edit.form['start_datetime'] = '2025-10-01 13:00'
        meeting = edit.form.submit().follow()

        assert 'Test Meeting' in meeting
        assert 'Es wurden noch keine Traktanden erfasst' in meeting
        assert 'Town Hall' in meeting
        assert '01.10.2025 13:00' in meeting

        page = client.get('/meetings')
        assert 'Test Meeting' in page
        assert '01.10.2025 13:00' in page
        assert 'Nächste Sitzung' in page

        # delete meeting
        meeting.click('Löschen')
        assert 'Noch keine Sitzungen definiert' in client.get('/meetings')
