from io import BytesIO
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection


def test_app_root_pages(agency_app):
    root_pages = agency_app.root_pages
    assert len(root_pages) == 2

    assert isinstance(root_pages[0], ExtendedPersonCollection)
    assert root_pages[0].is_visible is True
    assert str(root_pages[0].title) == "People"

    assert isinstance(root_pages[1], ExtendedAgencyCollection)
    assert root_pages[1].is_visible is True
    assert str(root_pages[1].title) == "Agencies"


def test_app_root_pdf(agency_app):
    assert agency_app.root_pdf is None
    assert agency_app.root_pdf_exists is False

    agency_app.root_pdf = BytesIO(b'PDF')
    assert agency_app.root_pdf == b'PDF'
    assert agency_app.root_pdf_exists is True
