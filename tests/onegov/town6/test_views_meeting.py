from __future__ import annotations

import io
import json
import zipfile

from freezegun import freeze_time
from tests.shared.utils import create_image
from webtest import Upload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_meetings(client: Client) -> None:
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
        edit.form['audio_link'] = 'https://audio.example.com/meeting.mp3'
        edit.form['video_link'] = 'https://video.example.com/meeting.mp4'
        meeting = edit.form.submit().follow()

        assert 'Test Meeting' in meeting
        assert 'Es wurden noch keine Traktanden erfasst' in meeting
        assert 'Town Hall' in meeting
        assert '01.10.2025 13:00' in meeting
        assert 'Links' in meeting
        assert 'https://audio.example.com/meeting.mp3' in meeting
        assert 'https://video.example.com/meeting.mp4' in meeting

        page = client.get('/meetings')
        assert 'Test Meeting' in page
        assert '01.10.2025 13:00' in page
        assert 'Nächste Sitzung' in page

        # add doc to meeting
        edit = meeting.click('Bearbeiten')
        edit.form.set('files', [
            Upload('flyer.jpg', create_image().read())], -1)
        meeting = edit.form.submit().follow()

        assert 'Test Meeting' in meeting
        assert 'Dokumente' in meeting
        assert 'flyer.jpg' in meeting

        # test meeting items
        edit = meeting.click('Bearbeiten')
        edit.form['start_datetime'] = '2025-10-01 14:00'
        edit.form['meeting_items'] = json.dumps({  # many field
            'values': [{
                'number': '0.1',
                'title': 'Intro',
                'agenda_item': ''
            }]
        })
        meeting = edit.form.submit().follow()

        assert 'Test Meeting' in meeting
        assert 'Es wurden noch keine Traktanden erfasst' not in meeting
        assert 'Town Hall' in meeting
        assert '01.10.2025 14:00' in meeting
        assert 'Links' in meeting
        assert 'https://audio.example.com/meeting.mp3' in meeting
        assert 'https://video.example.com/meeting.mp4' in meeting
        assert '0.1'
        assert 'Intro' in meeting

        # test export view
        export = meeting.click('Export')
        assert 'Sitzungsdokumente exportieren' in export
        response = export.form.submit()
        assert response.status_code == 200
        assert response.content_type == 'application/zip'
        assert response.content_disposition == (
            'attachment; filename="Test Meeting 01.10.2025.zip"')
        with zipfile.ZipFile(io.BytesIO(response.body), 'r') as zf:
            file_list = zf.namelist()
            # Verify that meeting and political business documents are stored
            # in their respective folders
            assert 'Test Meeting 01.10.2025/flyer.jpg' in file_list

        # delete meeting
        meeting.click('Löschen')
        assert 'Noch keine Sitzungen definiert' in client.get('/meetings')
