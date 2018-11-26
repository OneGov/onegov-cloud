from io import BytesIO
from onegov.agency.app import get_top_navigation


class DummyRequest():
    is_manager = False

    def class_link(self, cls, name=''):
        return f'{cls.__name__}/{name}'


def test_app_get_top_navigation():
    request = DummyRequest()
    assert [a.text for a in get_top_navigation(request)] == [
        'People', 'Agencies'
    ]

    request.is_manager = True
    assert [a.text for a in get_top_navigation(request)] == [
        'People', 'Agencies', 'Hidden elements'
    ]


def test_app_root_pdf(agency_app):
    assert agency_app.root_pdf is None
    assert agency_app.root_pdf_exists is False

    agency_app.root_pdf = BytesIO(b'PDF')
    assert agency_app.root_pdf == b'PDF'
    assert agency_app.root_pdf_exists is True
