from io import BytesIO
from onegov.agency.custom import get_global_tools
from onegov.agency.custom import get_top_navigation
from onegov.agency.pdf import AgencyPdfAr
from onegov.agency.pdf import AgencyPdfDefault
from onegov.agency.pdf import AgencyPdfZg
from onegov.core.elements import Link
from onegov.core.elements import LinkGroup
from onegov.core.utils import Bunch


class DummyRequest():
    is_logged_in = False
    is_manager = False
    is_admin = False
    is_supporter = False
    root_pages = ()
    current_user = Bunch(id=Bunch(hex='abcd'))
    authenticated_email = None
    path = ''
    path_qs = ''
    url = ''

    def class_link(self, cls, name='', variables: dict = None):
        return f'{cls.__name__}/{name}'

    def link(self, target, name=None):
        return f"{target.__class__.__name__}/{name}"

    def transform(self, url):
        return url

    def include(self, asset):
        pass

    def exclude_invisible(self, items):
        return


def test_app_custom(agency_app):
    def as_text(items):
        result = []
        for item in items:
            if isinstance(item, Link):
                result.append(item.text)
            if isinstance(item, LinkGroup):
                result.append({item.title: as_text(item.links)})
        return result

    request = DummyRequest()
    request.app = agency_app

    assert as_text(get_top_navigation(request)) == ['People', 'Agencies']
    assert as_text(get_global_tools(request)) == ['Login']

    request.is_logged_in = True
    request.current_username = 'Peter'
    assert as_text(get_top_navigation(request)) == ['People', 'Agencies']
    assert as_text(get_global_tools(request)) == [
        {'Account': ['User Profile', 'Logout']}
    ]

    request.is_manager = True
    assert as_text(get_top_navigation(request)) == ['People', 'Agencies']
    assert as_text(get_global_tools(request)) == [
        {'Account': ['User Profile', 'Logout']},
        {'Management': ['Dashboard', 'Timeline', 'Files', 'Images', 'Payments',
                        'Invoices', 'Text modules', 'Archived Tickets',
                        'Forms', 'Surveys', 'Hidden contents']},
        {'Tickets': ['My Tickets', 'Open Tickets', 'Pending Tickets',
                     'Closed Tickets']}
    ]

    request.is_admin = True
    assert as_text(get_top_navigation(request)) == ['People', 'Agencies']
    assert as_text(get_global_tools(request)) == [
        {'Account': ['User Profile', 'Logout']},
        {'Management': ['Dashboard', 'Timeline', 'Files', 'Images', 'Payments',
                        'Invoices', 'Text modules', 'Settings', 'Users',
                        'User groups', 'Link Check', 'Archived Tickets',
                        'Forms', 'Surveys', 'Hidden contents']},
        {'Tickets': ['My Tickets', 'Open Tickets', 'Pending Tickets',
                     'Closed Tickets']}
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
