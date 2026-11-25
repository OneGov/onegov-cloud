from __future__ import annotations

import base64
import threading
import transaction
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from unittest.mock import patch

from onegov.pdf.utils import extract_pdf_info
from onegov.translator_directory.collections.translator import (
    TranslatorCollection,
)
from onegov.user import UserGroupCollection
from tests.onegov.translator_directory.shared import create_languages
from tests.onegov.translator_directory.test_views import (
    collect_emails,
    filter_emails_by_recipient,
)


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
    from unittest.mock import MagicMock
    from .conftest import Client


@patch('onegov.websockets.integration.connect')
@patch('onegov.websockets.integration.authenticate')
@patch('onegov.websockets.integration.broadcast')
def test_time_report_pdf_escapes_translator_data(
    broadcast: MagicMock,
    authenticate: MagicMock,
    connect: MagicMock,
    client: Client,
    tmp_path: Path,
) -> None:
    """HTML in the translator's address must neither fetch local files
    (embedded as PDF attachments) nor reach internal hosts (SSRF)."""

    secret = tmp_path / 'secret.yml'
    secret.write_text('dsn: postgres://u:SECRET_MARKER@db/onegov\n')

    hits: list[str] = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            hits.append(self.path)
            self.send_response(404)
            self.end_headers()

        def log_message(self, *args: object) -> None:
            pass

    server = HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]

    session = client.app.session()
    create_languages(session)
    address = (
        f'Street 1 <a rel="attachment" href="file://{secret}">x</a>'
        f'<img src="http://127.0.0.1:{port}/internal">'
    )
    translator_id = (
        TranslatorCollection(client.app)
        .add(
            first_name='Eve',
            last_name='<b>Attacker</b>',
            admission='certified',
            email='translator@example.org',
            drive_distance=35.0,
            address=address,
            zip_code='8200',
            city='Schaffhausen',
        )
        .id
    )
    group = UserGroupCollection(session).add(
        name='migrationsamt_und_passbuero'
    )
    group.meta = {
        'finanzstelle': 'migrationsamt_und_passbuero',
        'accountant_emails': ['editor@example.org'],
    }
    transaction.commit()

    client.login_translator()
    page = client.get(f'/translator/{translator_id}/add-time-report')
    page.form['assignment_type'] = 'on-site'
    page.form['assignment_location'] = 'obergericht'
    page.form['finanzstelle'] = 'migrationsamt_und_passbuero'
    page.form['start_date'] = '2025-01-13'
    page.form['start_time'] = '09:00'
    page.form['end_date'] = '2025-01-13'
    page.form['end_time'] = '10:00'
    page.form['case_number'] = 'C-1'
    page = page.form.submit().follow()
    ticket_url = page.request.url.replace('/status', '')
    client.logout()

    client.login_editor()
    ticket_page = client.get(ticket_url).click('Ticket annehmen').follow()
    accept_url = ticket_page.pyquery('a.accept-link')[0].attrib['ic-post-to']
    client.post(accept_url).follow()

    mails = [
        mail
        for mail in filter_emails_by_recipient(
            collect_emails(client), 'translator@example.org'
        )
        if 'akzeptiert' in mail['Subject']
    ]
    pdf = base64.b64decode(mails[0]['Attachments'][0]['Content'])

    assert b'/EmbeddedFile' not in pdf
    assert b'SECRET_MARKER' not in pdf
    assert hits == []

    _, text = extract_pdf_info(BytesIO(pdf))
    assert '<b>Attacker</b>' in text
    assert '<a rel="attachment"' in text
