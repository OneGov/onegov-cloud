from freezegun import freeze_time
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import GazetteNoticeFile
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
        self.session = session

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

    with patch.object(pdf, 'h4') as h4:
        pdf.h('h4', 4)
        assert h4.called

    with patch.object(pdf, 'h4') as h4:
        pdf.h('h5', 5)
        assert h4.called


def test_pdf_unfold_data(session):
    def notice(title, text, number=None):
        notice = GazetteNotice(
            title=title,
            text=text,
            _issues={'2017-40': '1'},
            organization_id='100',
            category_id='10',
            state='published'
        )
        session.add(notice)
        session.flush()
        return notice

    data = [
        {
            'title': 'title-1',
            'children': [
                {
                    'title': 'title-1-1',
                    'children': [{'title': 'title-1-1-1'}],
                    'notices': [notice('title-1-1-a', 'text-1-1-a').id]
                },
                {
                    'title': 'title-1-2',
                    'notices': [
                        notice('title-1-2-a', 'text-1-2-a').id,
                        notice('title-1-2-b', 'text-1-2-b').id,
                        notice('title-1-2-c', 'text-1-2-c').id,
                    ],
                    'children': [{
                        'notices': [
                            notice('title-1-2-1-a', 'text-1-2-1-a').id,
                            notice('title-1-2-1-b', 'text-1-2-1-b').id,
                        ]
                    }]
                }
            ]
        },
        {
            'title': 'title-2',

            'notices': [notice('title-2-a', 'text-2-a').id],
            'children': [
                {'notices': [notice('title-2-1-a', 'text-2-1-a').id]},
                {'notices': [notice('title-2-2-a', 'text-2-2-a').id]},
                {'notices': [notice('title-2-3-a', 'text-2-3-a').id]}
            ]
        },
        {
            'notices': [
                notice('title-3-a', 'text-3-a').id,
                notice('title-3-b', 'text-3-b').id,
                notice('title-3-c', 'text-3-c').id,
                notice('title-3-d', 'text-3-d').id,
            ]
        }
    ]

    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_a4_portrait()
    assert pdf.unfold_data(session, None, '2017-40', data, 1) == 15

    expected = [
        'title-1',
        'title-1-1',
        '1', 'title-1-1-a', 'text-1-1-a',
        'title-1-1-1',
        'title-1-2',
        '2', 'title-1-2-a', 'text-1-2-a',
        '3', 'title-1-2-b', 'text-1-2-b',
        '4', 'title-1-2-c', 'text-1-2-c',
        '5', 'title-1-2-1-a', 'text-1-2-1-a',
        '6', 'title-1-2-1-b', 'text-1-2-1-b',
        'title-2',
        '7', 'title-2-a', 'text-2-a',
        '8', 'title-2-1-a', 'text-2-1-a',
        '9', 'title-2-2-a', 'text-2-2-a',
        '10', 'title-2-3-a', 'text-2-3-a',
        '11', 'title-3-a', 'text-3-a',
        '12', 'title-3-b', 'text-3-b',
        '13', 'title-3-c', 'text-3-c',
        '14', 'title-3-d', 'text-3-d',
    ]

    story = []
    for element in pdf.story:
        if hasattr(element, 'text'):
            story.append(
                element.text.replace('<b>', '')
                       .replace('</b>', '')
                       .replace('<i><font size="9.84375">', '')
                       .replace('</font></i>', '')
            )
        elif hasattr(element, '_cellvalues'):
            story.extend([x.text for x in element._cellvalues[0]])
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

    query = session.query(GazetteNotice)
    assert Pdf.query_notices(session, '2017-40', '100', '10') == [
        query.filter_by(text='2017-40-1, 2017-41-4').one().id,
        query.filter_by(text='2017-40-2, 2017-41-3').one().id,
        query.filter_by(text='2017-40-3, 2017-41-2').one().id,
        query.filter_by(text='2017-40-4, 2017-41-1').one().id
    ]
    assert Pdf.query_notices(session, '2017-41', '100', '10') == [
        query.filter_by(text='2017-40-4, 2017-41-1').one().id,
        query.filter_by(text='2017-40-3, 2017-41-2').one().id,
        query.filter_by(text='2017-40-2, 2017-41-3').one().id,
        query.filter_by(text='2017-40-1, 2017-41-4').one().id,
        query.filter_by(text='2017-41-5, 2017-42-1').one().id
    ]
    assert Pdf.query_notices(session, '2017-42', '100', '10') == [
        query.filter_by(text='2017-41-5, 2017-42-1').one().id
    ]


def test_pdf_from_issue(gazette_app):
    session = gazette_app.session()
    principal = gazette_app.principal

    def pdf(content):
        pdf = BytesIO()
        inline = Pdf(pdf)
        inline.init_report()
        inline.p(content)
        inline.generate()
        pdf.seek(0)
        return pdf

    for _issues, organization_id, category_id, attachments in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '10', []),
        ({'2017-40': '2', '2017-41': '3'}, '200', '10', ['--a--']),
        ({'2017-40': '3', '2017-41': '2'}, '100', '10', []),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11', ['--c--', '--d--']),
        ({'2017-41': '5', '2017-42': '1'}, '420', '11', []),
    ):
        notice = GazetteNotice(
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
        for content in attachments:
            attachment = GazetteNoticeFile(id=random_token())
            attachment.name = 'file.pdf'
            attachment.reference = as_fileintent(pdf(content), 'file.pdf')
            notice.files.append(attachment)

        session.add(notice)
    session.flush()

    with freeze_time("2017-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=40).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            '© 2017 Govikon\n1\nGazette No. 40, 06.10.2017\n'
            'State Chancellery\n'
            'Complaints\n'
            '5\n100-10\n2017-40-1, 2017-41-4\n'
            '6\n100-10\n2017-40-3, 2017-41-2\n'
            'Civic Community\n'
            'Complaints\n'
            '7\n200-10\n2017-40-2, 2017-41-3\n',
            # page 2 (--a--)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n2\n',
            # page 3
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '8\n410-11\n2017-40-4, 2017-41-1\n',
            # page 4 (--c--)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n4\n',
            # page 5 (--d--)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n5\n'
        ]

        issue = session.query(Issue).filter_by(number=41).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            '© 2017 Govikon\n1\nGazette No. 41, 13.10.2017\n'
            'State Chancellery\n'
            'Complaints\n'
            '5\n100-10\n2017-40-3, 2017-41-2\n'
            '6\n100-10\n2017-40-1, 2017-41-4\n'
            'Civic Community\n'
            'Complaints\n'
            '7\n200-10\n2017-40-2, 2017-41-3\n',
            # page 2 (--a--)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n2\n',
            # page 3
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '8\n410-11\n2017-40-4, 2017-41-1\n',
            # page 4 (--c--)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n4\n',
            # page 5 (--d--)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n5\n',
            # page 6
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n6\n'
            'Sikh Community\n'
            'Education\n'
            '9\n420-11\n2017-41-5, 2017-42-1\n'
        ]

    with freeze_time("2018-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=42).one()
        file = Pdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            '© 2018 Govikon\n1\nGazette No. 42, 20.10.2017\n'
            'Churches\n'
            'Sikh Community\n'
            'Education\n'
            '5\n420-11\n2017-41-5, 2017-42-1\n'
        ]
