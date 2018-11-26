from datetime import date
from datetime import datetime
from lxml import etree
from onegov.core.utils import module_path
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.utils import bool_is
from onegov.gazette.utils import SogcImporter
from onegov.gazette.utils.sogc_converter import KK01
from onegov.gazette.utils.sogc_converter import KK02
from onegov.gazette.utils.sogc_converter import KK03
from onegov.gazette.utils.sogc_converter import KK04
from onegov.gazette.utils.sogc_converter import KK05
from onegov.gazette.utils.sogc_converter import KK06
from onegov.gazette.utils.sogc_converter import KK07
from onegov.gazette.utils.sogc_converter import KK08
from onegov.gazette.utils.sogc_converter import KK09
from onegov.gazette.utils.sogc_converter import KK10
from pytest import mark
from unittest.mock import call
from unittest.mock import patch


BULK_EMPTY = """<bulk:bulk-export xmlns:bulk="https://shab.ch/bulk-export">
</bulk:bulk-export>"""

BULK_NOT_EMPTY = """<bulk:bulk-export xmlns:bulk="https://shab.ch/bulk-export">
  <publication>
    <meta>
      <id>XXX1</id>
      <publicationNumber>YYY1</publicationNumber>
    </meta>
  </publication>
  <publication>
    <meta>
      <id>XXX2</id>
      <publicationNumber>YYY2</publicationNumber>
    </meta>
  </publication>
  <publication>
    <meta>
      <id>XXX3</id>
      <publicationNumber>YYY3</publicationNumber>
    </meta>
  </publication>
</bulk:bulk-export>"""


SINGLE_KK01 = """<?xml version='1.0' encoding='UTF-8'?>
<KK01:publication
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:KK01="https://shab.ch/shab/KK01-export"
    xsi:schemaLocation="https://shab.ch/shab/KK01-export
     https://int.eshab.shab.ch/api/v1/schemas/shab/1.1/KK01-export.xsd">
<meta>
  <id>XXX1</id>
  <rubric>KK</rubric>
  <subRubric>KK01</subRubric>
  <language>fr</language>
  <publicationNumber>YYY1</publicationNumber>
  <publicationState>PUBLISHED</publicationState>
  <publicationDate>2018-06-25</publicationDate>
  <expirationDate>2023-06-25</expirationDate>
  <legalRemedy>legal</legalRemedy>
  <title><de>title</de></title>
</meta>
<content>
  <debtor>
    <selectType>person</selectType>
    <person>
      <prename>prename</prename>
      <name>name</name>
      <countryOfOrigin>
        <name><de>Spanien</de></name>
        <isoCode>ES</isoCode>
      </countryOfOrigin>
      <dateOfBirth>1959-12-23</dateOfBirth>
      <dateOfDeath>2017-12-22</dateOfDeath>
      <residence><selectType>switzerland</selectType></residence>
      <addressSwitzerland>
        <street>street</street>
        <houseNumber>houseNumber</houseNumber>
        <swissZipCode>swissZipCode</swissZipCode>
        <town>town</town>
      </addressSwitzerland>
      <personInformation>personInformation</personInformation>
    </person>
  </debtor>
  <addition>refusedLegacy</addition>
  <resolutionDate>2018-05-31</resolutionDate>
  <additionalLegalRemedy>add</additionalLegalRemedy>
  <remarks>remarks</remarks>
</content>
</KK01:publication>"""


def create_importer(session):
    return SogcImporter(
        session,
        {
            'endpoint': 'https://localhost',
            'canton': 'GV',
            'category': '190',
            'organization': '200',
        }
    )


class DummyResponse():

    def __init__(self, texts):
        self.texts = texts
        self.count = 0

    @property
    def text(self):
        result = self.texts[self.count]
        self.count += 1
        return result

    def raise_for_status(self):
        pass


def test_sogc_importer_create(session):
    importer = create_importer(session)
    assert importer.endpoint == 'https://localhost'
    assert importer.canton == 'GV'
    assert importer.category == '190'
    assert importer.organization == '200'
    assert sorted(importer.converters.keys()) == [
        'KK01', 'KK02', 'KK03', 'KK04', 'KK05', 'KK06', 'KK07', 'KK08', 'KK09',
        'KK10'
    ]
    assert sorted(importer.subrubrics) == [
        'KK01', 'KK02', 'KK03', 'KK04', 'KK05', 'KK06', 'KK07', 'KK08', 'KK09',
        'KK10'
    ]


def test_sogc_importer_get_publication_ids(session):

    importer = create_importer(session)
    with patch('onegov.gazette.utils.sogc_importer.get') as get:
        get.return_value = DummyResponse([BULK_EMPTY])

        result = importer.get_publication_ids()

        assert result == []
        assert get.called
        assert get.call_args == call(
            'https://localhost/publications/xml',
            params={
                'publicationStates': 'PUBLISHED',
                'cantons': 'GV',
                'subRubrics': [
                    'KK01', 'KK02', 'KK03', 'KK04', 'KK05', 'KK06', 'KK07',
                    'KK08', 'KK09', 'KK10'
                ],
                'pageRequest.page': 0,
                'pageRequest.size': 2000
            }
        )

    session.add(
        GazetteNotice(
            title='title',
            text='text',
            source='YYY2'
        )
    )

    with patch('onegov.gazette.utils.sogc_importer.get') as get:
        get.return_value = DummyResponse([
            BULK_NOT_EMPTY,
            BULK_NOT_EMPTY,
            BULK_EMPTY
        ])

        result = importer.get_publication_ids()

        assert result == ['XXX1', 'XXX3']
        assert get.called


def test_sogc_importer_get_publication(session):

    session.add(Issue(name='2018-6', number=1, date=date(2018, 6, 1)))
    session.add(Issue(name='2018-7', number=1, date=date(2018, 7, 1)))

    importer = create_importer(session)
    with patch('onegov.gazette.utils.sogc_importer.get') as get:
        get.return_value = DummyResponse([SINGLE_KK01])

        importer.get_publication('XXX1')

        assert get.called
        assert get.call_args == call(
            'https://localhost/publications/XXX1/xml',
        )

        notice = session.query(GazetteNotice).one()

        assert notice.state == 'imported'
        assert notice.author_date.date() == date(2018, 6, 25)
        assert notice.expiry_date.date() == date(2023, 6, 25)
        assert notice.title == 'title'
        assert notice.text == (
            '<p><strong>Schuldner</strong><br>prename name</p>'
            '<p>Staatsbürger: Spanien</p>'
            '<p>Geburtsdatum: 23.12.1959</p>'
            '<p>Todesdatum: 22.12.2017</p>'
            '<p>Wohnsitz:<br>street houseNumber<br>swissZipCode town</p>'
            '<p>Weitere Informationen zur Person:<br>personInformation</p>'
            '<p><strong>Datum der Konkurseröffnung</strong><br>31.05.2018</p>'
            '<p><strong>Zusatz</strong><br>ausgeschlagene Erbschaft</p>'
            '<p><strong>Rechtliche Hinweise und Fristen</strong><br>legal</p>'
            '<p><strong>Ergänzende rechtliche Hinweise</strong><br>add</p>'
            '<p><strong>Bemerkungen</strong><br>remarks</p>')
        assert notice.category_id == '190'
        assert notice.organization_id == '200'
        assert notice.source == 'YYY1'
        assert list(notice.issues.keys()) == ['2018-7']
        assert notice.first_issue.date() == date(2018, 7, 1)


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK01.xml')
])
def test_sogc_converter_KK01(gazette_app, xml):
    converter = KK01(etree.parse(xml))
    assert converter.source == 'KK01-0000000008'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Vorläufige Konkursanzeige Museum Company mit UID'
    )
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Museum Company mit UID</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Grossmatt 144<br>5618 Bettwil</p>'
        '<p><strong>Datum der Konkurseröffnung</strong><br>03.05.2018</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach Art. 222 SchKG. Die Publikation betreffend Art, '
        'Verfahren, Eingabefrist usw. erfolgt später.</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK02.xml')
])
def test_sogc_converter_KK02(gazette_app, xml):
    converter = KK02(etree.parse(xml))
    assert converter.source == 'KK02-0000000038'
    assert converter.publication_date == datetime(2018, 7, 3, 0, 0)
    assert converter.expiration_date == datetime(2023, 7, 3, 0, 0)
    assert converter.title == (
        'Konkurspublikation/Schuldenruf CK - HAIR SARL, en liquidation'
    )
    assert converter.text == (
        "<p><strong>Schuldner</strong><br>CK - HAIR SARL, en liquidation</p>"
        "<p>UID: CHE-260.477.536</p>"
        "<p>chemin des Beaux-Champs 7<br>1234 Vessy</p>"
        "<p><strong>Art des Konkursverfahrens</strong><br>summarisch</p>"
        "<p><strong>Datum der Konkurseröffnung</strong><br>01.01.2018</p>"
        "<p><strong>Frist</strong><br>30 Tage</p>"
        "<p><strong>Ablauf der Frist</strong><br>02.08.2018</p>"
        "<p><strong>Kommentar zur Frist</strong><br>test_commentaire_delai</p>"
        "<p><strong>Anmeldestelle</strong><br>"
        "Office des poursuites et faillites de l'Etat Genève - Faillites<br>"
        "Rue du Stand 46<br>1204 Genève</p>"
        "<p><strong>Rechtliche Hinweise und Fristen</strong><br>"
        "Notification selon LP 231, 232; ORFI, du 23 avril 1920, "
        "art. 29 et 123</p>"
        "<p><strong>Ergänzende rechtliche Hinweise</strong><br>"
        "test_remarques_juridiques_complémentaires</p>"
        "<p><strong>Bemerkungen</strong><br>"
        "test_remaques_autres_indications_publication</p>"
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK03.xml')
])
def test_sogc_converter_KK03(gazette_app, xml):
    converter = KK03(etree.parse(xml))
    assert converter.source == 'KK03-0000000004'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Einstellung des Konkursverfahrens Burger Chef'
    )
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Burger Chef</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Bahnhofstrasse 25<br>6525 Gnosca</p>'
        '<p><strong>Datum der Konkurseröffnung</strong><br>03.08.2018</p>'
        '<p><strong>Datum der Einstellung</strong><br>03.05.2018</p>'
        '<p><strong>Betrag des Kostenvorschusses</strong><br>125.50 CHF</p>'
        '<p><strong>Frist</strong><br>30 Tage</p>'
        '<p><strong>Ablauf der Frist</strong><br>03.05.2018</p>'
        '<p><strong>Kommentar zur Frist</strong><br>'
        'Hier kann ein Kommentar stehen</p>'
        '<p><strong>Anmeldestelle</strong><br>Konkursamt Bern<br>'
        'Patricia Test<br>8193  Test</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 230, 230a. Das Konkursverfahren wird als '
        'geschlossen erklärt, falls nicht ein Gläubiger innert der '
        'obgenannten Frist die Durchführung verlangt und für die Deckung der '
        'Kosten den erwähnten Vorschuss leistet. Die Nachforderung weiterer '
        'Kostenvorschüsse bleibt vorbehalten.</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK04.xml')
])
def test_sogc_converter_KK04(gazette_app, xml):
    converter = KK04(etree.parse(xml))
    assert converter.source == 'KK04-0000000014'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Kollokationsplan und Inventar American Appliance'
    )
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>American Appliance</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Hauptstrasse 35<br>1870 Monthey</p>'
        '<p><strong>Auflagefrist Kollokationsplan nach Publikation</strong>'
        '<br>20 Tage</p>'
        '<p><strong>Ablauf der Auflagefrist Kollokationsplan</strong><br>'
        '03.05.2018</p>'
        '<p><strong>Kommentar zur Auflagefrist Kollokationsplan</strong><br>'
        'Kommentar zu Frist 1</p>'
        '<p><strong>Auflagefrist Inventar nach Publikation</strong>'
        '<br>10 Tage</p>'
        '<p><strong>Ablauf der Auflagefrist Inventar</strong><br>'
        '03.05.2018</p>'
        '<p><strong>Kommentar zur Auflagefrist Inventar</strong><br>'
        'Kommentar zu Frist 2</p>'
        '<p><strong>Anmeldestelle</strong><br>Konkursamt Bern<br>'
        'Patricia Test<br>8193  Test</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 221, 249-250</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK05.xml')
])
def test_sogc_converter_KK05(gazette_app, xml):
    converter = KK05(etree.parse(xml))
    assert converter.source == 'KK05-0000000021'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Verteilungsliste und Schlussrechnung Franklin Simon'
    )
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Franklin Simon</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Bahnhofstrasse 114<br>6656 Golino</p>'
        '<p><strong>Angaben zur Auflage</strong><br>'
        'Hier stehen die Angaben zur Auflage</p>'
        '<p><strong>Frist</strong><br>10 Tage</p>'
        '<p><strong>Ablauf der Frist</strong><br>03.05.2018</p>'
        '<p><strong>Kommentar zur Frist</strong><br>'
        'Das ist der Kommentar zur Frist</p>'
        '<p><strong>Anmeldestelle</strong><br>Konkursamt Bern<br>'
        'Patricia Test<br>8193  Test</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 263</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK06.xml')
])
def test_sogc_converter_KK06(gazette_app, xml):
    converter = KK06(etree.parse(xml))
    assert converter.source == 'KK06-0000000025'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == 'Schluss des Konkursverfahrens Gamma Gas'
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Gamma Gas</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Obere Bahnhofstrasse 146<br>6375 Beckenried</p>'
        '<p><strong>Datum des Schlusses</strong><br>03.05.2018</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 268 Abs. 4</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK07.xml')
])
def test_sogc_converter_KK07(gazette_app, xml):
    converter = KK07(etree.parse(xml))
    assert converter.source == 'KK07-0000000026'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == 'Widerruf des Konkurses Beatties'
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Beatties</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Valéestrasse 31<br>1937 Orsières</p>'
        '<p><strong>Datum des Widerrufs</strong><br>03.05.2018</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 195, 196, 332</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK08.xml')
])
def test_sogc_converter_KK08(gazette_app, xml):
    converter = KK08(etree.parse(xml))
    assert converter.source == 'KK08-0000000009'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Konkursamtliche Grundstücksteigerung Castle Realty'
    )
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Castle Realty</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Üerklisweg 136<br>3855 Brienz</p>'
        '<p><strong>Steigerung</strong><br>03.05.2018 um 14:50<br>Bern</p>'
        '<p><strong>Steigerungsobjekte</strong><br>'
        'Das sind die betroffenen Objekte</p>'
        '<p><strong>Angaben zur Auflage</strong><br>'
        'Hier können Angaben zur Auflage publiziert werden</p>'
        '<p><strong>Beginn der Frist</strong><br>03.05.2018</p>'
        '<p><strong>Ablauf der Frist</strong><br>03.05.2018</p>'
        '<p><strong>Kommentar zur Frist</strong><br>Kommentar zur Frist</p>'
        '<p><strong>Anmeldestelle</strong><br>Konkursamt Test<br>Patricia</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG 257 - 259</p>'
        '<p><strong>Ergänzende rechtliche Hinweise</strong><br>'
        'Hier können ergänzende rechtliche Hinweise stehen</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK09.xml')
])
def test_sogc_converter_KK09(gazette_app, xml):
    converter = KK09(etree.parse(xml))
    assert converter.source == 'KK09-0000000006'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == 'Lastenverzeichnisse Body Toning'
    assert converter.text == (
        '<p><strong>Schuldner</strong><br>Body Toning</p>'
        '<p>UID: CHE-123.456.789</p>'
        '<p>Bösch 128<br>1263 Crassier</p>'
        '<p><strong>Betroffenes Grundstück</strong><br>'
        'Grundstück Nr. 13543, Blaustrasse 23, 300 Bern</p>'
        '<p><strong>Weitere Angaben</strong><br>'
        'Weitere Angaben zum betroffenen Grundstück stehen in diesem Feld</p>'
        '<p><strong>Angaben zur Auflage</strong><br>'
        'Hier können die Angaben zu der Auflage stehen</p>'
        '<p><strong>Frist</strong><br>20 Tage</p>'
        '<p><strong>Ablauf der Frist</strong><br>03.05.2018</p>'
        '<p><strong>Klage- und Beschwerdefrist</strong><br>30 Tage</p>'
        '<p><strong>Ablauf der Klage- und Beschwerdefrist</strong><br>'
        '03.05.2018</p>'
        '<p><strong>Kommentar zur Klage- und Beschwerdefrist</strong><br>'
        'Hier kann ein Kommentar zur Frist gemacht werden</p>'
        '<p><strong>Anmeldestelle für Klagen</strong><br>'
        'Das ist die Anmeldestelle für Klagen</p>'
        '<p><strong>Anmeldestelle für Beschwerden</strong><br>'
        'Das ist die Anmeldestelle für Beschwerden</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong><br>'
        'Meldung nach SchKG</p>'
        '<p><strong>Bemerkungen</strong><br>110618_VIew</p>'
    )


@mark.parametrize("xml", [
    module_path('onegov.gazette', 'tests/fixtures/KK10.xml')
])
def test_sogc_converter_KK10(gazette_app, xml):
    converter = KK10(etree.parse(xml))
    assert converter.source == 'KK10-0000000022'
    assert converter.publication_date == datetime(2018, 7, 2, 0, 0)
    assert converter.expiration_date == datetime(2020, 12, 12, 0, 0)
    assert converter.title == (
        'Das ist ein KK verschiedenes, dieser Titel wird durch die Meldung '
        'gesteuert'
    )
    assert converter.text == (
        '<p>INhalt der Meldung</p>'
        '<p><strong>Rechtliche Hinweise und Fristen</strong>'
        '<br>Meldung nach SchKG</p>'
    )


def test_bool_is(session):
    session.add(GazetteNotice(title='F.1'))
    session.add(GazetteNotice(title='F.2', meta={'y': 1}))
    session.add(GazetteNotice(title='F.3', meta={'x': None}))
    session.add(GazetteNotice(title='F.4', meta={'x': None, 'y': 1}))
    session.add(GazetteNotice(title='F.5', meta={'x': False}))
    session.add(GazetteNotice(title='F.6', meta={'x': False, 'y': 1}))
    session.add(GazetteNotice(title='T.1', meta={'x': True}))
    session.add(GazetteNotice(title='T.2', meta={'x': True, 'y': 1}))
    session.flush()

    query = session.query(GazetteNotice)
    assert sorted([
        r.title for r in query.filter(bool_is(GazetteNotice.meta['x'], True))
    ]) == ['T.1', 'T.2']
    assert sorted([
        r.title for r in query.filter(bool_is(GazetteNotice.meta['x'], False))
    ]) == ['F.1', 'F.2', 'F.3', 'F.4', 'F.5', 'F.6']
