from datetime import date
from datetime import datetime
from tests.shared.utils import create_app
from onegov.core.crypto import hash_password
from onegov.core.orm.observer import ScopedPropertyObserver
from onegov.gazette import GazetteApp
from onegov.gazette.collections import CategoryCollection
from onegov.gazette.collections import IssueCollection
from onegov.gazette.collections import OrganizationCollection
from onegov.gazette.models import Principal
from onegov.user import User
from onegov.user import UserGroup
from pytest import fixture
from sedate import standardize_date
from textwrap import dedent
from transaction import commit
from uuid import uuid4


PRINCIPAL = """
    name: Govikon
    color: '#006FB5'
    logo: 'govikon.svg'
    logo_for_pdf: 'govikon-pdf.svg'
    on_accept:
        mail_to: 'printer@onegov.org'
    publishing: True
"""


LOGO = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   id="svg3765"
   version="1.1"
   viewBox="0 0 30.000002 7.8254137"
   height="0.78254139cm"
   width="3.0000002cm">
  <g transform="translate(-95.867724,-50.018762)">
    <text
       id="text3769"
       y="54.592094"
       x="95.535599"
       style="font-size:6.01939869px;line-height:125%;font-family:sans-serif;"
       xml:space="preserve"><tspan
         style="stroke-width:0.15048496px"
         y="54.592094"
         x="95.535599"
         id="tspan3767">onegov.ch</tspan></text>
  </g>
</svg>
"""


def create_organizations(session):
    organizations = OrganizationCollection(session)
    organizations.add_root(
        name='100', order=1, title='State Chancellery', active=True
    )
    organizations.add_root(
        name='200', order=2, title='Civic Community', active=True
    )
    organizations.add_root(
        name='300', order=3, title='Municipality', active=True
    )
    churches = organizations.add_root(
        name='400', order=4, title='Churches', active=True
    )
    organizations.add(
        parent=churches,
        name='410', order=1, title='Evangelical Reformed Parish', active=True
    )
    organizations.add(
        parent=churches,
        name='420', order=2, title='Sikh Community', active=False,
        external_name='4'
    )
    organizations.add(
        parent=churches,
        name='430', order=3, title='Catholic Parish', active=True
    )
    organizations.add_root(
        name='500', order=5, title='Corporation', active=True
    )
    return organizations.query().all()


def create_categories(session):
    categories = CategoryCollection(session)
    categories.add_root(name='10', title='Complaints', active=False)
    categories.add_root(name='11', title='Education', active=True)
    categories.add_root(name='12', title='Submissions', active=True)
    categories.add_root(name='13', title='Commercial Register', active=True)
    categories.add_root(name='14', title='Elections', active=True)
    return categories.query().all()


def create_issues(session):
    issues = IssueCollection(session)
    issues.add(
        name='2017-40', number=40, date=date(2017, 10, 6),
        deadline=standardize_date(datetime(2017, 10, 4, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-41', number=41, date=date(2017, 10, 13),
        deadline=standardize_date(datetime(2017, 10, 11, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-42', number=42, date=date(2017, 10, 20),
        deadline=standardize_date(datetime(2017, 10, 18, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-43', number=43, date=date(2017, 10, 27),
        deadline=standardize_date(datetime(2017, 10, 25, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-44', number=44, date=date(2017, 11, 3),
        deadline=standardize_date(datetime(2017, 11, 1, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-45', number=45, date=date(2017, 11, 10),
        deadline=standardize_date(datetime(2017, 11, 8, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-46', number=46, date=date(2017, 11, 17),
        deadline=standardize_date(datetime(2017, 11, 15, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-47', number=47, date=date(2017, 11, 24),
        deadline=standardize_date(datetime(2017, 11, 22, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-48', number=48, date=date(2017, 12, 1),
        deadline=standardize_date(datetime(2017, 11, 29, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-49', number=49, date=date(2017, 12, 8),
        deadline=standardize_date(datetime(2017, 12, 6, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-50', number=50, date=date(2017, 12, 15),
        deadline=standardize_date(datetime(2017, 12, 13, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-51', number=51, date=date(2017, 12, 22),
        deadline=standardize_date(datetime(2017, 12, 20, 12, 0), 'UTC')
    )
    issues.add(
        name='2017-52', number=52, date=date(2017, 12, 29),
        deadline=standardize_date(datetime(2017, 12, 27, 12, 0), 'UTC')
    )
    issues.add(
        name='2018-1', number=1, date=date(2018, 1, 5),
        deadline=standardize_date(datetime(2018, 1, 3, 12, 0), 'UTC')
    )
    return issues.query().all()


def create_gazette(request, temporary_path):
    app = create_app(
        GazetteApp,
        request,
        use_maildir=True,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path),
    )
    app.session_manager.set_locale('de_CH', 'de_CH')
    app.filestorage.writetext('principal.yml', dedent(PRINCIPAL))
    app.filestorage.writetext('govikon-pdf.svg', LOGO)

    group = UserGroup(name='TestGroup', id=uuid4())
    session = app.session()
    session.add(group)

    session.add(User(
        username='admin@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='admin',
        phone_number='+41415112250'
    ))
    session.add(User(
        realname='Publisher',
        username='publisher@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='editor',
        phone_number='+41415112260'
    ))
    session.add(User(
        realname='First Editor',
        username='editor1@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member',
        groups=[group],
        phone_number='+41415112271'
    ))
    session.add(User(
        realname='Second Editor',
        username='editor2@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member',
        groups=[group],
        phone_number='+41415112272'
    ))
    session.add(User(
        realname='Third Editor',
        username='editor3@example.org',
        password_hash=request.getfixturevalue('gazette_password'),
        role='member',
        phone_number='+41415112273'
    ))

    create_organizations(session)
    create_categories(session)
    create_issues(session)
    commit()
    return app


@fixture(scope='session')
def gazette_password():
    return hash_password('hunter2')


@fixture(scope="function")
def organizations(session):
    """ Adds some default organizations to the database. """
    yield create_organizations(session)


@fixture(scope="function")
def categories(session):
    """ Adds some default categories to the database. """
    yield create_categories(session)


@fixture(scope="function")
def issues(session):
    """ Adds some default issues to the database. """
    yield create_issues(session)


@fixture(scope="function")
def principal(organizations, categories, issues):
    yield Principal.from_yaml(dedent(PRINCIPAL))


@fixture(scope="function")
def gazette_app(request, temporary_path):
    app = create_gazette(request, temporary_path)
    yield app
    app.session_manager.dispose()


@fixture(scope="session", autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(GazetteApp)
