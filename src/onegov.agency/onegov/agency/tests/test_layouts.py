from onegov.people import AgencyMembership
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.agency.collections import ExtendedPersonCollection
from onegov.agency.models import ExtendedAgency
from onegov.agency.models import ExtendedPerson
from onegov.agency.layouts import AgencyCollectionLayout
from onegov.agency.layouts import AgencyLayout
from onegov.agency.layouts import MembershipLayout
from onegov.agency.layouts import ExtendedPersonCollectionLayout
from onegov.agency.layouts import ExtendedPersonLayout


class DummyApp(object):
    org = 'Org'


class DummyRequest(object):
    locale = 'en'
    is_logged_in = False
    is_manager = False
    session = None

    def __init__(self):
        self.app = DummyApp()

    def translate(self, text):
        return str(text)

    def include(self, *args, **kwargs):
        pass

    def link(self, model, name=''):
        if isinstance(model, str):
            return f'{model}/{name}'
        return f'{model.__class__.__name__}/{name}'

    def exclude_invisible(self, objects):
        return objects

    def new_csrf_token(self):
        return 'x'


def path(links):
    return '/'.join([link.attrs['href'].strip('/') for link in links])


def hrefs(items):
    for item in items:
        if hasattr(item, 'links'):
            for ln in item.links:
                yield ln.attrs.get('href') or ln.attrs.get('ic-delete-from')
        else:
            yield item.attrs.get('href') or item.attrs.get('ic-delete-from')


def test_agency_collection_layout():
    request = DummyRequest()
    model = ExtendedAgencyCollection(None)

    layout = AgencyCollectionLayout(model, request)
    assert layout.editbar_links is None
    assert path(layout.breadcrumbs) == 'Org/ExtendedAgencyCollection'

    # Log in as manager
    request.is_manager = True
    layout = AgencyCollectionLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'ExtendedAgencyCollection/new'
    ]


def test_agency_layout():
    request = DummyRequest()
    model = ExtendedAgency('Agency')

    layout = AgencyLayout(model, request)
    assert isinstance(layout.collection, ExtendedAgencyCollection)
    assert layout.editbar_links is None
    assert path(layout.breadcrumbs) == \
        'Org/ExtendedAgencyCollection/ExtendedAgency'

    # Log in as manager
    request.is_manager = True
    layout = AgencyLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'AgencyProxy/edit',
        'AgencyProxy/create-pdf',
        'ExtendedAgency/?csrf-token=x',
        'AgencyProxy/new',
        'AgencyProxy/new-membership'
    ]


def test_membership_layout():
    request = DummyRequest()
    model = AgencyMembership(agency=ExtendedAgency(title='Agency'))

    layout = MembershipLayout(model, request)
    assert layout.editbar_links is None
    assert path(layout.breadcrumbs) == \
        'Org/ExtendedAgencyCollection/ExtendedAgency/AgencyMembership'

    # Log in as manager
    request.is_manager = True
    layout = MembershipLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'AgencyMembership/edit',
        'AgencyMembership/?csrf-token=x'
    ]


def test_extended_person_collection_layout():
    request = DummyRequest()
    model = ExtendedPersonCollection(None)

    layout = ExtendedPersonCollectionLayout(model, request)
    assert layout.editbar_links is None
    assert path(layout.breadcrumbs) == 'Org/#'

    # Log in as manager
    request.is_manager = True
    layout = ExtendedPersonCollectionLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'ExtendedPersonCollection/new'
    ]

    # AgencyPathMixin
    root = ExtendedAgency('Root')
    child = ExtendedAgency('Child', parent=root)
    assert layout.agency_path(root) == 'Root'
    assert layout.agency_path(child) == 'Root > Child'

    # VisibilityMixin
    person = ExtendedPerson(
        first_name="Hans",
        last_name="Maulwurf",
        email="hans.maulwurf@springfield.com"
    )
    assert layout.field_visible('first_name', person) is True
    assert layout.field_visible('year', person) is False
    assert layout.field_visible('email', person) is False

    request.is_logged_in = True
    layout = ExtendedPersonCollectionLayout(model, request)
    assert layout.field_visible('email', person) is True


def test_extended_person_layout():
    request = DummyRequest()
    model = ExtendedPerson(
        first_name="Hans",
        last_name="Maulwurf",
        email="hans.maulwurf@springfield.com"
    )

    layout = ExtendedPersonLayout(model, request)
    assert layout.editbar_links is None
    assert path(layout.breadcrumbs) == \
        'Org/ExtendedPersonCollection/ExtendedPerson'

    # Log in as manager
    request.is_manager = True
    layout = ExtendedPersonLayout(model, request)
    assert list(hrefs(layout.editbar_links)) == [
        'ExtendedPerson/edit',
        'ExtendedPerson/?csrf-token=x'
    ]

    # AgencyPathMixin
    root = ExtendedAgency('Root')
    child = ExtendedAgency('Child', parent=root)
    assert layout.agency_path(root) == 'Root'
    assert layout.agency_path(child) == 'Root > Child'

    # VisibilityMixin
    assert layout.field_visible('first_name') is True
    assert layout.field_visible('year') is False
    assert layout.field_visible('email') is False

    request.is_logged_in = True
    layout = ExtendedPersonCollectionLayout(model, request)
    assert layout.field_visible('email') is True
