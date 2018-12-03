from io import BytesIO
from onegov.agency.app import get_top_navigation
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg


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
        'People', 'Agencies', 'Hidden contents'
    ]


def test_app_root_pdf(agency_app):
    assert agency_app.root_pdf is None
    assert agency_app.root_pdf_exists is False

    agency_app.root_pdf = BytesIO(b'PDF')
    assert agency_app.root_pdf == b'PDF'
    assert agency_app.root_pdf_exists is True


def test_app_pdf_class(agency_app):
    assert agency_app.pdf_class == AgencyPdfDefault

    agency_app.org.meta['pdf_layout'] = 'default'
    assert agency_app.pdf_class == AgencyPdfDefault

    agency_app.org.meta['pdf_layout'] = 'ar'
    assert agency_app.pdf_class == AgencyPdfAr

    agency_app.org.meta['pdf_layout'] = 'zg'
    assert agency_app.pdf_class == AgencyPdfZg

    agency_app.org.meta['pdf_layout'] = ''
    assert agency_app.pdf_class == AgencyPdfDefault

    agency_app.org.meta['pdf_layout'] = 'invalid'
    assert agency_app.pdf_class == AgencyPdfDefault


def test_app_enable_yubikey(agency_app):
    assert 'enable_yubikey' not in agency_app.org.meta
    assert agency_app.enable_yubikey is False

    agency_app.org.meta['enable_yubikey'] = True
    assert agency_app.enable_yubikey is True

    agency_app._enable_yubikey = True
    agency_app.org.meta['enable_yubikey'] = False
    assert agency_app.enable_yubikey is False
