from datetime import date
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.utils import SogcImporter
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
