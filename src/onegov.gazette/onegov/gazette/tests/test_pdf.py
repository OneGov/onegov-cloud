from freezegun import freeze_time
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.gazette.collections import GazetteNoticeCollection
from onegov.gazette.layout import Layout
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import GazetteNoticeFile
from onegov.gazette.models import Issue
from onegov.gazette.pdf import IndexPdf
from onegov.gazette.pdf import IssuePdf
from onegov.gazette.pdf import IssuePrintOnlyPdf
from onegov.gazette.pdf import NoticesPdf
from onegov.gazette.pdf import Pdf
from onegov.gazette.tests.conftest import LOGO
from PyPDF2 import PdfFileReader
from sedate import utcnow
from unittest.mock import patch


class DummyApp(object):
    def __init__(self, session, principal):
        self._session = session
        self.principal = principal
        self.logo_for_pdf = LOGO

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


def extract_pdf_story(pdf):
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
    return story


def pdf_attachment(content):
    pdf = BytesIO()
    inline = Pdf(pdf)
    inline.init_report()
    inline.p(content)
    inline.generate()
    pdf.seek(0)

    attachment = GazetteNoticeFile(id=random_token())
    attachment.name = 'file.pdf'
    attachment.reference = as_fileintent(pdf, 'file.pdf')
    return attachment


def test_notices_pdf_from_notice(gazette_app):
    session = gazette_app.session()

    with freeze_time("2017-01-01 12:00"):
        notice = GazetteNotice(
            title='title',
            text='text',
            author_place='place',
            author_date=utcnow(),
            author_name='author',
            state='drafted'
        )
        notice.files.append(pdf_attachment('attachment'))
        session.add(notice)
        session.flush()

    with freeze_time("2018-01-01 12:00"):
        request = DummyRequest(session, gazette_app.principal)
        file = NoticesPdf.from_notice(notice, request)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            '© 2018 Govikon\n1\n'
            'xxx\ntitle\ntext\nplace, 1. Januar 2017\nauthor\n',
            '© 2018 Govikon\n2\n'
        ]


def test_notices_pdf_from_notices(gazette_app):
    session = gazette_app.session()

    with freeze_time("2017-01-01 12:00"):
        notice = GazetteNotice(
            title='first title',
            text='first text',
            author_place='first place',
            author_date=utcnow(),
            author_name='first author',
            state='submitted'
        )
        notice.files.append(pdf_attachment('first attachment'))
        session.add(notice)
        session.flush()

    with freeze_time("2017-01-02 12:00"):
        notice = GazetteNotice(
            title='second title',
            text='second text',
            author_place='second place',
            author_date=utcnow(),
            author_name='second author',
            state='submitted'
        )
        session.add(notice)
        session.flush()

    with freeze_time("2018-01-01 12:00"):
        request = DummyRequest(session, gazette_app.principal)
        notices = GazetteNoticeCollection(session)
        file = NoticesPdf.from_notices(notices, request)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            (
                '© 2018 Govikon\n1\n'
                'xxx\nfirst title\nfirst text\n'
                'first place, 1. Januar 2017\nfirst author\n'
            ),
            '© 2018 Govikon\n2\n',
            (
                '© 2018 Govikon\n3\n'
                'xxx\nsecond title\nsecond text\n'
                'second place, 2. Januar 2017\nsecond author\n'
            )
        ]

        file = NoticesPdf.from_notices(
            notices.for_order('title', 'desc'), request
        )
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            (
                '© 2018 Govikon\n1\n'
                'xxx\nsecond title\nsecond text\n'
                'second place, 2. Januar 2017\nsecond author\n'
                'xxx\nfirst title\nfirst text\n'
                'first place, 1. Januar 2017\nfirst author\n'
            ),
            '© 2018 Govikon\n2\n'
        ]


def test_index_pdf_from_notices(gazette_app):
    session = gazette_app.session()

    with freeze_time("2017-01-01 12:00"):
        notice = GazetteNotice(
            title='first title',
            text='first text',
            organization_id='100',
            category_id='10',
            _issues={
                '2017-40': '1',
                '2017-41': '3',
            },
            state='accepted'
        )
        session.add(notice)
        session.flush()

    with freeze_time("2017-01-02 12:00"):
        notice = GazetteNotice(
            title='second title',
            text='second text',
            organization_id='200',
            category_id='11',
            _issues={
                '2017-40': '2',
                '2017-42': '4',
            },
            state='published'
        )
        session.add(notice)
        session.flush()

    with freeze_time("2018-01-01 12:00"):
        request = DummyRequest(session, gazette_app.principal)
        notices = GazetteNoticeCollection(session)
        file = IndexPdf.from_notices(notices, request)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            (
                '© 2018 Govikon\n1\nGazette\nIndex\n'
                'Organizations\n'
                'C\n'
                'Civic Community  2017-40-2, 2017-42-4\n'
                'S\n'
                'State Chancellery  2017-40-1, 2017-41-3\n'
            ),
            (
                'Gazette\n© 2018 Govikon\n2\n'
                'Categories\n'
                'C\n'
                'Complaints  2017-40-1, 2017-41-3\n'
                'E\n'
                'Education  2017-40-2, 2017-42-4\n'
            )
        ]


def test_issues_pdf_h():
    pdf = IssuePdf(BytesIO())
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


def test_issues_pdf_notice(gazette_app):
    session = gazette_app.session()

    with freeze_time("2017-01-01 12:00"):
        notice = GazetteNotice(
            title='title',
            text='text',
            author_place='place',
            author_date=utcnow(),
            author_name='author',
            state='drafted'
        )
        notice.files.append(pdf_attachment('attachment'))
        session.add(notice)
        session.flush()

    layout = Layout(notice, DummyRequest(session, gazette_app.principal))

    pdf = IssuePdf(BytesIO())
    pdf.init_a4_portrait()

    pdf.notice(notice, layout, '1')
    assert extract_pdf_story(pdf) == [
        '1', 'title', 'text', 'place, 1. Januar 2017<br/>author'
    ]

    notice.print_only = True
    pdf.notice(notice, layout, '2')
    assert extract_pdf_story(pdf) == [
        '1', 'title', 'text', 'place, 1. Januar 2017<br/>author',
        '2',
        '<i>This official notice is only available in the print version.</i>'
    ]


def test_issues_pdf_excluded_notices_note(gazette_app):
    request = DummyRequest(gazette_app.session(), gazette_app.principal)

    pdf = IssuePdf(BytesIO())
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(0, request)
    assert extract_pdf_story(pdf) == [
        'The electronic official gazette is available at www.amtsblattzug.ch.'
    ]

    pdf = IssuePdf(BytesIO())
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(1, request)
    assert extract_pdf_story(pdf) == [
        'The electronic official gazette is available at www.amtsblattzug.ch.',
        '1 publication(s) with particularly sensitive data are not available '
        'online. They are available in paper form from the State Chancellery, '
        'Seestrasse 2, 6300 Zug, or can be subscribed to at amtsblatt@zg.ch.'
    ]

    pdf = IssuePdf(BytesIO())
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(9, request)
    assert extract_pdf_story(pdf) == [
        'The electronic official gazette is available at www.amtsblattzug.ch.',
        '9 publication(s) with particularly sensitive data are not available '
        'online. They are available in paper form from the State Chancellery, '
        'Seestrasse 2, 6300 Zug, or can be subscribed to at amtsblatt@zg.ch.'
    ]

    pdf = IssuePrintOnlyPdf((BytesIO))
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(0, request)
    assert extract_pdf_story(pdf) == [
        'The electronic official gazette is available at www.amtsblattzug.ch.'
    ]

    pdf = IssuePrintOnlyPdf((BytesIO))
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(1, request)
    assert extract_pdf_story(pdf) == [
        '1 publication(s) with particularly sensitive data according to '
        'BGS 152.3 §7 Abs. 2.',
        'The electronic official gazette is available at www.amtsblattzug.ch.'
    ]

    pdf = IssuePrintOnlyPdf((BytesIO))
    pdf.init_a4_portrait()
    pdf.excluded_notices_note(9, request)
    assert extract_pdf_story(pdf) == [
        '9 publication(s) with particularly sensitive data according to '
        'BGS 152.3 §7 Abs. 2.',
        'The electronic official gazette is available at www.amtsblattzug.ch.'
    ]


def test_issues_pdf_unfold_data(session):
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
    pdf = IssuePdf(file)
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

    assert extract_pdf_story(pdf) == expected

    pdf.generate()
    file.seek(0)
    reader = PdfFileReader(file)
    text = ''.join([page.extractText() for page in reader.pages])
    assert text.strip() == '\n'.join(expected)


def test_issues_pdf_query_notices(session, issues, organizations, categories):
    for _issues in (
        {'2017-40': '1', '2017-41': '4'},
        {'2017-40': '2', '2017-41': '3'},
        {'2017-40': '3', '2017-41': '2'},
        {'2017-40': '4', '2017-41': '1'},
        {'2017-41': '5', '2017-42': '1'},
    ):
        session.add(
            GazetteNotice(
                title='title',
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id='100',
                category_id='10',
                state='published'
            )
        )
    session.flush()

    query = session.query(GazetteNotice)
    assert IssuePdf.query_notices(session, '2017-40', '100', '10') == [
        query.filter_by(text='2017-40-1, 2017-41-4').one().id,
        query.filter_by(text='2017-40-2, 2017-41-3').one().id,
        query.filter_by(text='2017-40-3, 2017-41-2').one().id,
        query.filter_by(text='2017-40-4, 2017-41-1').one().id
    ]
    assert IssuePdf.query_notices(session, '2017-41', '100', '10') == [
        query.filter_by(text='2017-40-4, 2017-41-1').one().id,
        query.filter_by(text='2017-40-3, 2017-41-2').one().id,
        query.filter_by(text='2017-40-2, 2017-41-3').one().id,
        query.filter_by(text='2017-40-1, 2017-41-4').one().id,
        query.filter_by(text='2017-41-5, 2017-42-1').one().id
    ]
    assert IssuePdf.query_notices(session, '2017-42', '100', '10') == [
        query.filter_by(text='2017-41-5, 2017-42-1').one().id
    ]


def test_issues_pdf_query_used(session, issues, organizations, categories):
    issues = {issue.name: issue for issue in issues}
    for _issues, organization_id, category_id in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '14'),
        ({'2017-40': '2', '2017-41': '3'}, '200', '13'),
        ({'2017-40': '3', '2017-41': '2'}, '300', '12'),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11'),
        ({'2017-41': '5', '2017-42': '1'}, '420', '10'),
    ):
        session.add(
            GazetteNotice(
                title='title',
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

    assert IssuePdf.query_used_categories(session, issues['2017-40']) == {
        '11', '12', '13', '14'
    }
    assert IssuePdf.query_used_categories(session, issues['2017-41']) == {
        '10', '11', '12', '13', '14'
    }
    assert IssuePdf.query_used_categories(session, issues['2017-42']) == {'10'}
    assert IssuePdf.query_used_categories(session, issues['2017-43']) == set()

    assert IssuePdf.query_used_organizations(session, issues['2017-40']) == {
        '100', '200', '300', '410'
    }
    assert IssuePdf.query_used_organizations(session, issues['2017-41']) == {
        '100', '200', '300', '410', '420'
    }
    assert IssuePdf.query_used_organizations(session, issues['2017-42']) == {
        '420'
    }
    assert IssuePdf.query_used_organizations(session, issues['2017-43']) == \
        set()


def test_issues_pdf_query_excluded_notices_count(session, issues):
    issues = {issue.name: issue for issue in issues}
    for _issues, meta in (
        ({'2017-40': '1', '2017-41': '4'}, None),
        ({'2017-40': '2', '2017-41': '3'}, {}),
        ({'2017-40': '3', '2017-41': '2'}, {'print_only': None}),
        ({'2017-40': '4', '2017-41': '1'}, {'print_only': True}),
        ({'2017-41': '5', '2017-42': '1'}, {'print_only': False}),
    ):
        session.add(
            GazetteNotice(
                title='title',
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id='100',
                category_id='10',
                state='published',
                meta=meta
            )
        )
    session.flush()

    assert IssuePdf.query_excluded_notices_count(
        session, issues['2017-40']
    ) == 1
    assert IssuePdf.query_excluded_notices_count(
        session, issues['2017-41']
    ) == 1
    assert IssuePdf.query_excluded_notices_count(
        session, issues['2017-42']
    ) == 0
    assert IssuePdf.query_excluded_notices_count(
        session, issues['2017-43']
    ) == 0


def test_issues_pdf_from_issue(gazette_app):
    session = gazette_app.session()
    principal = gazette_app.principal

    for _issues, organization_id, category_id, attachments, meta in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '10', [], None),
        ({'2017-40': '2', '2017-41': '3'}, '200', '10', ['-a-'], {}),
        ({'2017-40': '3', '2017-41': '2'}, '100', '10', [],
         {'print_only': True}),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11', ['-c-', '-d-'],
         {'print_only': False}),
        ({'2017-41': '5', '2017-42': '1'}, '420', '11', [],
         {'print_only': None}),
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
            state='published',
            meta=meta
        )
        for content in attachments:
            notice.files.append(pdf_attachment(content))

        session.add(notice)
    session.flush()

    with freeze_time("2017-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=40).one()
        file = IssuePdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            'onegov.ch\n© 2017 Govikon\n1\nGazette No. 40, 06.10.2017\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
            '1 publication(s) with particularly sensitive data are not '
            'available online. They are available in\npaper form from the '
            'State Chancellery, Seestrasse 2, 6300 Zug, or can be subscribed '
            'to at\namtsblatt@zg.ch.\n'
            'State Chancellery\n'
            'Complaints\n'
            '5\n100-10\n2017-40-1, 2017-41-4\n'
            '6\nThis official notice is only available in the print version.\n'
            'Civic Community\n'
            'Complaints\n'
            '7\n200-10\n2017-40-2, 2017-41-3\n',
            # page 2 (-a-)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n2\n',
            # page 3
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '8\n410-11\n2017-40-4, 2017-41-1\n',
            # page 4 (-c-)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n4\n',
            # page 5 (-d-)
            'Gazette No. 40, 06.10.2017\n© 2017 Govikon\n5\n'
        ]

        issue = session.query(Issue).filter_by(number=41).one()
        file = IssuePdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        test_issues_pdf_from_issue
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            'onegov.ch\n© 2017 Govikon\n1\nGazette No. 41, 13.10.2017\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
            '1 publication(s) with particularly sensitive data are not '
            'available online. They are available in\npaper form from the '
            'State Chancellery, Seestrasse 2, 6300 Zug, or can be subscribed '
            'to at\namtsblatt@zg.ch.\n'
            'State Chancellery\n'
            'Complaints\n'
            '5\nThis official notice is only available in the print version.\n'
            '6\n100-10\n2017-40-1, 2017-41-4\n'
            'Civic Community\n'
            'Complaints\n'
            '7\n200-10\n2017-40-2, 2017-41-3\n',
            # page 2 (-a-)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n2\n',
            # page 3
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n3\n'
            'Churches\n'
            'Evangelical Reformed Parish\n'
            'Education\n'
            '8\n410-11\n2017-40-4, 2017-41-1\n',
            # page 4 (-c-)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n4\n',
            # page 5 (-d-)
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n5\n',
            # page 6
            'Gazette No. 41, 13.10.2017\n© 2017 Govikon\n6\n'
            'Sikh Community\n'
            'Education\n'
            '9\n420-11\n2017-41-5, 2017-42-1\n'
        ]

    with freeze_time("2018-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=42).one()
        file = IssuePdf.from_issue(issue, DummyRequest(session, principal), 5)
        reader = PdfFileReader(file)
        test_issues_pdf_from_issue
        assert [page.extractText() for page in reader.pages] == [
            'onegov.ch\n© 2018 Govikon\n1\nGazette No. 42, 20.10.2017\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
            'Churches\n'
            'Sikh Community\n'
            'Education\n'
            '5\n420-11\n2017-41-5, 2017-42-1\n'
        ]


def test_issues_po_pdf_query_notices(session, issues, organizations,
                                     categories):
    for _issues, meta in (
        ({'2017-40': '1', '2017-41': '4'}, None),
        ({'2017-40': '2', '2017-41': '3'}, {}),
        ({'2017-40': '3', '2017-41': '2'}, {'print_only': None}),
        ({'2017-40': '4', '2017-41': '1'}, {'print_only': True}),
        ({'2017-41': '5', '2017-42': '1'}, {'print_only': False}),
    ):
        session.add(
            GazetteNotice(
                title='title',
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id='100',
                category_id='10',
                state='published',
                meta=meta
            )
        )
    session.flush()

    query = session.query(GazetteNotice)
    assert IssuePrintOnlyPdf.query_notices(
        session, '2017-40', '100', '10'
    ) == [query.filter_by(text='2017-40-4, 2017-41-1').one().id]

    assert IssuePrintOnlyPdf.query_notices(
        session, '2017-41', '100', '10'
    ) == [query.filter_by(text='2017-40-4, 2017-41-1').one().id]

    assert IssuePrintOnlyPdf.query_notices(
        session, '2017-42', '100', '10'
    ) == []


def test_issues_po_pdf_query_used(session, issues, organizations, categories):
    issues = {issue.name: issue for issue in issues}
    for _issues, organization_id, category_id, meta in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '14', None),
        ({'2017-40': '2', '2017-41': '3'}, '200', '13', {}),
        ({'2017-40': '3', '2017-41': '2'}, '300', '12', {'print_only': None}),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11', {'print_only': True}),
        ({'2017-41': '5', '2017-42': '1'}, '420', '10', {'print_only': False}),
    ):
        session.add(
            GazetteNotice(
                title='title',
                text=', '.join([
                    '{}-{}'.format(issue, _issues[issue])
                    for issue in sorted(_issues)
                ]),
                _issues=_issues,
                organization_id=organization_id,
                category_id=category_id,
                state='published',
                meta=meta
            )
        )
    session.flush()

    assert IssuePrintOnlyPdf.query_used_categories(
        session, issues['2017-40']
    ) == {'11'}
    assert IssuePrintOnlyPdf.query_used_categories(
        session, issues['2017-41']
    ) == {'11'}
    assert IssuePrintOnlyPdf.query_used_categories(
        session, issues['2017-42']
    ) == set()
    assert IssuePrintOnlyPdf.query_used_categories(
        session, issues['2017-43']
    ) == set()

    assert IssuePrintOnlyPdf.query_used_organizations(
        session, issues['2017-40']
    ) == {'410'}
    assert IssuePrintOnlyPdf.query_used_organizations(
        session, issues['2017-41']
    ) == {'410'}
    assert IssuePrintOnlyPdf.query_used_organizations(
        session, issues['2017-42']
    ) == set()
    assert IssuePrintOnlyPdf.query_used_organizations(
        session, issues['2017-43']
    ) == set()


def test_issues_po_pdf_from_issue(gazette_app):
    session = gazette_app.session()
    principal = gazette_app.principal

    for _issues, organization_id, category_id, attachments, meta in (
        ({'2017-40': '1', '2017-41': '4'}, '100', '10', [], None),
        ({'2017-40': '2', '2017-41': '3'}, '200', '10', ['-a-'], {}),
        ({'2017-40': '3', '2017-41': '2'}, '100', '10', [],
         {'print_only': True}),
        ({'2017-40': '4', '2017-41': '1'}, '410', '11', ['-c-', '-d-'],
         {'print_only': False}),
        ({'2017-41': '5', '2017-42': '1'}, '420', '11', [],
         {'print_only': None}),
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
            state='published',
            meta=meta
        )
        for content in attachments:
            notice.files.append(pdf_attachment(content))

        session.add(notice)
    session.flush()

    with freeze_time("2017-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=40).one()
        file = IssuePrintOnlyPdf.from_issue(
            issue, DummyRequest(session, principal)
        )
        reader = PdfFileReader(file)
        file.seek(0)
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            'onegov.ch\n© 2017 Govikon\n1\nGazette No. 40, 06.10.2017\n'
            '1 publication(s) with particularly sensitive data according '
            'to BGS 152.3 §7 Abs. 2.\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
            'State Chancellery\n'
            'Complaints\n'
            '3\n100-10\n2017-40-3, 2017-41-2\n'
        ]

        issue = session.query(Issue).filter_by(number=41).one()
        file = IssuePrintOnlyPdf.from_issue(
            issue, DummyRequest(session, principal)
        )
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            # page 1
            'onegov.ch\n© 2017 Govikon\n1\nGazette No. 41, 13.10.2017\n'
            '1 publication(s) with particularly sensitive data according '
            'to BGS 152.3 §7 Abs. 2.\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
            'State Chancellery\n'
            'Complaints\n'
            '2\n100-10\n2017-40-3, 2017-41-2\n'
        ]

    with freeze_time("2018-01-01 12:00"):
        issue = session.query(Issue).filter_by(number=42).one()
        file = IssuePrintOnlyPdf.from_issue(
            issue, DummyRequest(session, principal)
        )
        reader = PdfFileReader(file)
        assert [page.extractText() for page in reader.pages] == [
            'onegov.ch\n© 2018 Govikon\n1\nGazette No. 42, 20.10.2017\n'
            'The electronic official gazette is available at '
            'www.amtsblattzug.ch.\n'
        ]
