from freezegun import freeze_time
from io import BytesIO
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Issue
from onegov.gazette.pdf import Pdf
from PyPDF2 import PdfFileReader
from unittest.mock import patch


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session, principal):
        self.app = DummyApp(session, principal)
        self.locale = 'de_CH'

    def translate(self, text):
        return text.interpolate()

    def include(self, resource):
        pass


def test_pdf_h():
    pdf = Pdf(BytesIO())
    pdf.init_a4_portrait()

    with patch.object(pdf, 'h1') as h1:
        pdf.h('h1', 1)
        assert h1.called

    with patch.object(pdf, 'h2') as h2:
        pdf.h('h2', 2)
        assert h2.called

    with patch.object(pdf, 'h3') as h3:
        pdf.h('h3', 3)
        assert h3.called

    with patch.object(pdf, 'h3') as h3:
        pdf.h('h3', 4)
        assert h3.called


def test_pdf_unfold_data():
    data = [
        {
            'title': 'title-1',
            'children': [
                {
                    'title': 'title-1-1',
                    'children': [{'title': 'title-1-1-1'}],
                    'notices': [['title-1-1-a', 'text-1-1-a']]
                },
                {
                    'title': 'title-1-2',
                    'notices': [
                        ['title-1-2-a', 'text-1-2-a'],
                        ['title-1-2-b', 'text-1-2-b'],
                        ['title-1-2-c', 'text-1-2-c'],
                    ],
                    'children': [{
                        'notices': [
                            ['title-1-2-1-a', 'text-1-2-1-a'],
                            ['title-1-2-1-b', 'text-1-2-1-b']
                        ]
                    }]
                }
            ]
        },
        {
            'title': 'title-2',
            'notices': [['title-2-a', 'text-2-a']],
            'children': [
                {'notices': [['title-2-1-a', 'text-2-1-a']]},
                {'notices': [['title-2-2-a', 'text-2-2-a']]},
                {'notices': [['title-2-3-a', 'text-2-3-a']]}
            ]
        },
        {
            'notices': [
                ['title-3-a', 'text-3-a'],
                ['title-3-b', 'text-3-b'],
                ['title-3-c', 'text-3-c'],
                ['title-3-d', 'text-3-d'],
            ]
        }
    ]

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    pdf.unfold_data(data)

    story = [x.text for x in pdf.story if hasattr(x, 'text')]
    expected = [
        'title-1',
        'title-1-1',
        'title-1-1-a', 'text-1-1-a',
        'title-1-1-1',
        'title-1-2',
        'title-1-2-a', 'text-1-2-a',
        'title-1-2-b', 'text-1-2-b',
        'title-1-2-c', 'text-1-2-c',
        'title-1-2-1-a', 'text-1-2-1-a',
        'title-1-2-1-b', 'text-1-2-1-b',
        'title-2',
        'title-2-a', 'text-2-a',
        'title-2-1-a', 'text-2-1-a',
        'title-2-2-a', 'text-2-2-a',
        'title-2-3-a', 'text-2-3-a',
        'title-3-a', 'text-3-a',
        'title-3-b', 'text-3-b',
        'title-3-c', 'text-3-c',
        'title-3-d', 'text-3-d'
    ]
    assert story == expected

    pdf.generate()
    file.seek(0)
    reader = PdfFileReader(file)
    text = ''.join([page.extractText() for page in reader.pages])
    assert text.strip() == '\n'.join(expected)


def test_pdf_query_notices(session, issues, organizations, categories):
    for _issues, organization_id, category_id in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '10'),
        ({'2017-40': '2', '2017-41': '3'}, '100', '10'),
        ({'2017-40': '3', '2017-41': '2'}, '100', '10'),
        ({'2017-40': '4', '2017-41': '1'}, '100', '10'),
        ({'2017-41': '5', '2017-42': '1'}, '100', '10'),
    ):
        session.add(
            GazetteNotice(
                title='{}-{}'.format(organization_id, category_id),
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id=organization_id,
                category_id=category_id,
                state='published'
            )
        )
    session.flush()

    assert Pdf.query_notices(session, '2017-40', '100', '10') == [
        ('100-10', '2017-40-1, 2017-41-4'),
        ('100-10', '2017-40-2, 2017-41-3'),
        ('100-10', '2017-40-3, 2017-41-2'),
        ('100-10', '2017-40-4, 2017-41-1')
    ]
    assert Pdf.query_notices(session, '2017-41', '100', '10') == [
        ('100-10', '2017-40-4, 2017-41-1'),
        ('100-10', '2017-40-3, 2017-41-2'),
        ('100-10', '2017-40-2, 2017-41-3'),
        ('100-10', '2017-40-1, 2017-41-4'),
        ('100-10', '2017-41-5, 2017-42-1')
    ]
    assert Pdf.query_notices(session, '2017-42', '100', '10') == [
        ('100-10', '2017-41-5, 2017-42-1')
    ]


def test_pdf_from_issue(gazette_app):
    session = gazette_app.session()
    principal = gazette_app.principal

    for _issues, organization_id, category_id in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '10'),
        ({'2017-40': '2', '2017-41': '3'}, '200', '10'),
        ({'2017-40': '3', '2017-41': '2'}, '100', '10'),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11'),
        ({'2017-41': '5', '2017-42': '1'}, '420', '11'),
    ):
        session.add(
            GazetteNotice(
                title='{}-{}'.format(organization_id, category_id),
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id=organization_id,
                category_id=category_id,
                state='published'
            )
        )
    session.flush()

    with freeze_time("2017-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=40).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal))
        reader = PdfFileReader(file)
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n1\n'
            'Gazette No. 40, Freitag 06.10.2017\n'
            'State Chancellery\n'
            'Complaints\n'
            '100-10\n'
            '2017-40-1, 2017-41-4\n'
            '100-10\n'
            '2017-40-3, 2017-41-2\n'
            'Civic Community\n'
            'Complaints\n'
            '200-10\n'
            '2017-40-2, 2017-41-3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '410-11\n'
            '2017-40-4, 2017-41-1\n'
        )

        issue = session.query(Issue).filter_by(number=41).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal))
        reader = PdfFileReader(file)
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2017 Govikon\n1\n'
            'Gazette No. 41, Freitag 13.10.2017\n'
            'State Chancellery\n'
            'Complaints\n'
            '100-10\n'
            '2017-40-3, 2017-41-2\n'
            '100-10\n'
            '2017-40-1, 2017-41-4\n'
            'Civic Community\n'
            'Complaints\n'
            '200-10\n'
            '2017-40-2, 2017-41-3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '410-11\n'
            '2017-40-4, 2017-41-1\n'
            'Sikh Community\n'
            'Education\n'
            '420-11\n'
            '2017-41-5, 2017-42-1\n'
        )

    with freeze_time("2018-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=42).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal))
        reader = PdfFileReader(file)
        text = ''.join([page.extractText() for page in reader.pages])
        assert text == (
            '© 2018 Govikon\n1\n'
            'Gazette No. 42, Freitag 20.10.2017\n'
            'Churches\n'
            'Sikh Community\n'
            'Education\n'
            '420-11\n'
            '2017-41-5, 2017-42-1\n'
        )
