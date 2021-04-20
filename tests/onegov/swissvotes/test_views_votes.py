from decimal import Decimal
from io import BytesIO

from onegov.core.utils import module_path
from onegov.swissvotes.external_resources.posters import MfgPosters
from onegov.swissvotes.external_resources.posters import SaPosters
from onegov.swissvotes.models import ColumnMapper
from onegov.swissvotes.models import SwissVote
from pytest import mark
from unittest.mock import patch
from webtest import TestApp as Client
from webtest.forms import Upload
from xlsxwriter.workbook import Workbook


@mark.parametrize('file', [
    module_path('tests.onegov.swissvotes', 'fixtures/dataset.xlsx'),
])
def test_view_update_votes(swissvotes_app, file):
    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    with open(file, 'rb') as f:
        content = f.read()

    # Upload
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Datensatz aktualisieren")
    manage.form['dataset'] = Upload(
        'votes.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()

    assert "Datensatz aktualisiert (659 hinzugefügt, 0 geändert)" in manage

    session = swissvotes_app.session()
    vote = session.query(SwissVote).filter_by(bfs_number=82.2).one()
    assert str(vote.bfs_number) == '82.20'
    assert vote.date.isoformat() == '1920-03-21'
    assert vote.legislation_number == 25
    assert vote.title == (
        "Gegenentwurf zur Volksinitiative "
        "«für ein Verbot der Errichtung von Spielbanken»"
    )
    assert vote.short_title_de == "Gegenentwurf zur Initiative " \
                                  "für ein Verbot der Spielbanken"
    assert [str(pa) for pa in vote.policy_areas] == ['4.41.413', '4.44.443']
    assert str(vote.result_turnout) == '60.2323410000'
    assert vote.recommendations_parties['Nay'][0].name == 'sps'

    # Upload (unchanged)
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Datensatz aktualisieren")
    manage.form['dataset'] = Upload(
        'votes.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()
    assert "Datensatz aktualisiert (0 hinzugefügt, 0 geändert)" in manage

    # Download
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    csv = manage.click("Datensatz herunterladen", index=0).body
    # xlsx = manage.click("Datensatz herunterladen", index=1).body

    # Upload (roundtrip)
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Datensatz aktualisieren")

    # Changed from xlsx to content to upload since
    # generated file lacks the CITATION sheet

    manage.form['dataset'] = Upload(
        'votes.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()
    assert "Datensatz aktualisiert (0 hinzugefügt, 0 geändert)" in manage

    assert csv == client.get('/votes/csv').body

    # Delete all votes
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Alle Abstimmungen löschen")
    manage = manage.form.submit().follow()

    assert swissvotes_app.session().query(SwissVote).count() == 0


def test_view_update_votes_unknown_descriptors(swissvotes_app):
    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    file = BytesIO()
    workbook = Workbook(file)
    worksheet = workbook.add_worksheet('DATA')
    workbook.add_worksheet('CITATION')
    worksheet.write_row(0, 0, ColumnMapper().columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr
        '1.2.2008',  # datum
        'kurztitel de',  # titel_kurz_d
        'kurztitel fr',  # titel_kurz_f
        'titel de',  # titel_off_d
        'titel fr',  # titel_off_f
        'stichwort',  # stichwort
        'link',  # swissvoteslink
        '2',  # anzahl
        '3',  # rechtsform
        '',  # anneepolitique
        '',  # bkchrono-de
        '',  # bkchrono-fr
        '13',  # d1e1
        '',  # d1e2
        '',  # d1e3
        '12',  # d2e1
        '12.6',  # d2e2
        '',  # d2e3
        '12',  # d3e1
        '12.5',  # d3e2
        '12.55',  # d3e3
        '',  # dep
        '',  # br-pos
        '1',  # legislatur
        '2004-2008',  # legisjahr
    ])
    workbook.close()
    file.seek(0)

    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Datensatz aktualisieren")
    manage.form['dataset'] = Upload(
        'votes.xlsx',
        file.read(),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()
    assert "Datensatz aktualisiert (1 hinzugefügt, 0 geändert)" in manage
    assert "unbekannte Deskriptoren: 12.55, 12.6, 13" in manage


@patch.object(MfgPosters, 'fetch', return_value=(1, 2, 3, {Decimal('4')}))
@patch.object(SaPosters, 'fetch', return_value=(5, 6, 7, {Decimal('8')}))
def test_view_update_external_resources(mfg, sa, swissvotes_app):
    swissvotes_app.mfg_api_token = 'xxx'

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/').maybe_follow().click('Abstimmungen')
    manage = manage.click('Externe Quellen aktualisieren')
    manage.form['resources'] = ['mfg', 'sa']
    manage = manage.form.submit().follow()

    assert '6 hinzugefügt, 8 geändert, 10 gelöscht' in manage
    assert 'Quellen konnten nicht aktualisiert werden: 4, 8' in manage
