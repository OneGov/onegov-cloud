from datetime import date
from decimal import Decimal
from io import BytesIO
from onegov.core.utils import module_path
from onegov.swissvotes.external_resources import BsPosters
from onegov.swissvotes.external_resources.posters import MfgPosters
from onegov.swissvotes.external_resources.posters import SaPosters
from onegov.swissvotes.models import ColumnMapperDataset
from onegov.swissvotes.models import SwissVote
from pytest import mark
from tests.shared import Client
from transaction import commit
from unittest.mock import patch
from webtest.forms import Upload
from xlsxwriter.workbook import Workbook


def test_view_votes_pagination(swissvotes_app):
    for day, number in ((1, '100'), (2, '101.1'), (2, '101.2'), (3, '102')):
        swissvotes_app.session().add(
            SwissVote(
                bfs_number=Decimal(number),
                date=date(1990, 6, day),
                title_de="Vote DE",
                title_fr="Vote FR",
                short_title_de="V D",
                short_title_fr="V F",
                keyword="Keyword",
                _legal_form=3,
                initiator_de="Initiator",
            )
        )
    commit()

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    # 102
    page = client.get('/').maybe_follow().click("Abstimmungen")
    page = page.click("Details", index=0)
    assert "<td>102</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" not in page

    # 101.2
    page = page.click("Vorherige Abstimmung")
    assert "<td>101.2</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" in page

    # 101.1
    page = page.click("Vorherige Abstimmung")
    assert "<td>101.1</td>" in page
    assert "Vorherige Abstimmung" in page
    assert "Nächste Abstimmung" in page

    # 100
    page = page.click("Vorherige Abstimmung")
    assert "<td>100</td>" in page
    assert "Vorherige Abstimmung" not in page
    assert "Nächste Abstimmung" in page

    # 101.1
    page = page.click("Nächste Abstimmung")
    assert "<td>101.1</td>" in page

    # 101.2
    page = page.click("Nächste Abstimmung")
    assert "<td>101.2</td>" in page

    # 102
    page = page.click("Nächste Abstimmung")
    assert "<td>102</td>" in page


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
    manage = manage.click("Abstimmungsdatensatz aktualisieren")
    manage.form['dataset'] = Upload(
        'votes.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()

    assert "Datensatz aktualisiert (689 hinzugefügt, 0 geändert)" in manage

    session = swissvotes_app.session()
    vote = session.query(SwissVote).filter_by(bfs_number=82.2).one()
    assert str(vote.bfs_number) == '82.20'
    assert vote.date.isoformat() == '1920-03-21'
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
    manage = manage.click("Abstimmungsdatensatz aktualisieren")
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
    manage = manage.click("Abstimmungsdatensatz aktualisieren")

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
    worksheet.write_row(0, 0, ColumnMapperDataset().columns.values())
    worksheet.write_row(1, 0, [
        '100.1',  # anr
        '1.2.2008',  # datum
        'kurztitel de',  # titel_kurz_d
        'kurztitel fr',  # titel_kurz_f
        'kurztitel en',  # titel_kurz_e
        'titel de',  # titel_off_d
        'titel fr',  # titel_off_f
        'stichwort',  # stichwort
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
        '',  # br-pos
    ])
    workbook.close()
    file.seek(0)

    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Abstimmungsdatensatz aktualisieren")
    manage.form['dataset'] = Upload(
        'votes.xlsx',
        file.read(),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()
    assert "Datensatz aktualisiert (1 hinzugefügt, 0 geändert)" in manage
    assert "unbekannte Deskriptoren: 12.55, 12.6, 13" in manage


@mark.parametrize('file', [
    module_path('tests.onegov.swissvotes', 'fixtures/metadata.xlsx'),
])
def test_view_update_metadata(swissvotes_app, file, sample_vote):
    session = swissvotes_app.session()
    sample_vote.bfs_number = Decimal('236')
    session.add(sample_vote)
    commit()

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
    manage = manage.click("Daten Kampagnenmaterial aktualisieren")
    manage.form['metadata'] = Upload(
        'metadata.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()

    assert "Metadaten aktualisiert (30 hinzugefügt, 0 geändert)" in manage

    session = swissvotes_app.session()
    vote = session.query(SwissVote).filter_by(bfs_number=236).one()
    assert len(vote.campaign_material_metadata) == 33

    # Upload (unchanged)
    manage = client.get('/').maybe_follow().click("Abstimmungen")
    manage = manage.click("Daten Kampagnenmaterial aktualisieren")
    manage.form['metadata'] = Upload(
        'metadata.xlsx',
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    manage = manage.form.submit().follow()
    assert "Metadaten aktualisiert (0 hinzugefügt, 0 geändert)" in manage


@patch.object(MfgPosters, 'fetch',
              return_value=(1, 2, 3, {(Decimal('4'), 'id-4')}))
@patch.object(SaPosters, 'fetch',
              return_value=(5, 6, 7, {(Decimal('8'), 'id-8')}))
@patch.object(BsPosters, 'fetch',
              return_value=(9, 9, 9, {(Decimal('9'), 'id-9')}))
def test_view_update_external_resources(mfg, sa, bs, swissvotes_app):
    swissvotes_app.mfg_api_token = 'xxx'
    swissvotes_app.bs_api_token = 'yyy'

    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()

    manage = client.get('/').maybe_follow().click('Abstimmungen')
    manage = manage.click('Bildquellen aktualisieren')
    manage.form['resources'] = ['mfg', 'sa', 'bs']
    manage = manage.form.submit().follow()

    assert '15 hinzugefügt, 17 geändert, 19 gelöscht' in manage
    assert 'Quellen konnten nicht aktualisiert werden: 4, 8, 9' in manage


def test_view_votes_empty_policy_area(swissvotes_app):
    """ Ensure that the votes view does not crash when the policy area is empty
    """
    client = Client(swissvotes_app)
    client.get('/locale/de_CH').follow()

    page = client.get('/votes')
    assert page.status_code == 200

    page = client.get('/votes?term=&policy_area=9&policy_area=')
    assert page.status_code == 200
