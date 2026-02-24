from __future__ import annotations

import pytest
import transaction

from datetime import date
from decimal import Decimal
from onegov.core.security import Secret
from onegov.org.app import OrgApp
from onegov.org.forms import ExportForm
from onegov.org.models import Export
from onegov.pay import PaymentCollection
from tests.onegov.org.conftest import create_org_app, Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pay.types import PaymentState
    from sqlalchemy.orm import Session


def test_export(request: pytest.FixtureRequest) -> None:

    class App(OrgApp):
        pass

    @App.export(
        id='my-export',
        form_class=ExportForm,
        permission=Secret,
        title="My Export",
        explanation="Foo bar.")
    class MyExport(Export):
        def run(
            self,
            form: object,
            session: Session
        ) -> list[list[tuple[str, str]]]:
            return [[
                ('id', 'foo'),
                ('content', 'bar')
            ]]

    app = create_org_app(request, enable_search=False, cls=App)

    # the export should work for admins
    admin = Client(app)
    admin.login_admin()

    page = admin.get('/exports')
    assert "My Export" in page
    assert "Foo bar." in page

    page = page.click("My Export")
    page.form['file_format'] = 'json'
    result = page.form.submit().json

    assert result == [
        {
            'id': 'foo',
            'content': 'bar'
        }
    ]

    # but because of our permission editors don't have a chance
    editor = Client(app)
    editor.login_editor()

    page = editor.get('/exports')
    assert "My Export" not in page
    assert "Foo bar." not in page

    page = editor.get('/export/my-export', status=403)
    assert "Ihnen fehlt die nötige Berechtigung" in page


def test_exports_view(client: Client) -> None:
    client.get('/exports', status=403)

    client.login_editor()
    exports = client.get('/exports')
    assert 'Zahlungen' in exports


@pytest.mark.skip_night_hours
def test_payments_export(client: Client) -> None:
    client.login_editor()
    session = client.app.session()
    assert client.app.payment_providers_enabled
    exports = client.get('/payments').click('Export')
    exports.form['start'] = '2021-01-01'
    end = date.today().strftime('%Y-%m-%d')
    exports.form['end'] = end
    exports.form['file_format'] = 'json'

    resp = exports.form.submit()
    assert resp.json == []

    payments = PaymentCollection(session)

    # exceed the batch size of the query, ordered by desc created
    states: tuple[PaymentState, ...] = ('open', 'paid', 'failed', 'cancelled')
    sources = ('manual',)
    for ix, state in enumerate(states, start=1):
        for source in sources:
            payments.add(source=source, amount=Decimal(ix), state=state)

    transaction.commit()
    resp = exports.form.submit().json
    assert len(resp) == len(states) * len(sources)

    # oldest entry is the first
    entry = resp[-1]
    assert entry.pop('Datum erstellt')
    assert entry == {
        'Referenz Ticket': None,
        'Email Antragsteller': None,
        'Kategorie Ticket': None,
        'Status Ticket': None,
        'Ticket entschieden': None,
        'ID beim Zahlungsanbieter': None,
        'Referenzen beim Zahlungsanbieter': [],
        'Status': 'Offen',
        'Währung': 'CHF',
        'Betrag': 1.0,
        'Netto Betrag': 1.0,
        'Gebühr': 0,
        'Zahlungsanbieter': 'Manuell',
        'Datum Bezahlt': None,
        'Referenzen': [],
    }
