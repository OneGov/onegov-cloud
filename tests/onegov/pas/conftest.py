from pytest_localserver.http import WSGIServer
from onegov.core.orm.observer import ScopedPropertyObserver
from os import path
from yaml import dump

from onegov.core.utils import Bunch
from onegov.core.utils import module_path
from onegov.pas.app import PasApp
from onegov.pas.content.initial import create_new_organisation
from onegov.user import User
from pytest import fixture
from sqlalchemy.orm.session import close_all_sessions
from tests.shared import Client
from tests.shared.utils import create_app
from transaction import commit


@fixture(scope='function')
def cfg_path(postgres_dsn, session_manager, temporary_directory, redis_url):
    cfg = {
        'applications': [
            {
                'path': '/pas/*',
                'application': 'onegov.pas.app.PasApp',
                'namespace': 'pas',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                    'depot_backend': 'depot.io.memory.MemoryFileStorage',
                    'filestorage': 'fs.osfs.OSFS',
                    'filestorage_options': {
                        'root_path': '{}/file-storage'.format(
                            temporary_directory
                        ),
                        'create': 'True',
                    },
                    'websockets': {
                        'client_url': 'ws://localhost:8766',
                        'manage_url': 'ws://localhost:8766',
                        'manage_token': 'super-super-secret-token',
                    },
                },
            }
        ]
    }

    cfg_path = path.join(temporary_directory, 'onegov.yml')
    with open(cfg_path, 'w') as f:
        f.write(dump(cfg))

    return cfg_path


def create_pas_app(request, use_elasticsearch=False):
    app = create_app(
        PasApp,
        request,
        use_maildir=True,
        use_elasticsearch=use_elasticsearch,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token',
        },
    )
    org = create_new_organisation(app, name='Govikon')
    org.meta['reply_to'] = 'mails@govikon.ch'
    org.meta['locales'] = 'de_CH'

    session = app.session()
    test_password = request.getfixturevalue('test_password')
    session.add(
        User(
            username='admin@example.org',
            password_hash=test_password,
            role='admin',
        )
    )
    session.add(
        User(
            username='editor@example.org',
            password_hash=test_password,
            role='editor',
        )
    )
    session.add(
        User(
            username='member@example.org',
            password_hash=test_password,
            role='member',
        )
    )

    commit()
    close_all_sessions()
    return app


@fixture
def people_json():
    """Fixture providing sample people data as JSON string."""
    return {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {
                'created': '2024-12-23T16:44:12.056040+01:00',
                'firstName': 'Daniel',
                'fullName': 'Abt Daniel',
                'id': 'd9403b52-d178-454c-8ac7-abb75af14aa6',
                'isActive': True,
                'modified': '2024-12-23T16:44:12.056046+01:00',
                'officialName': 'Abt',
                'personTypeTitle': None,
                'primaryEmail': {
                    'id': 'c28dbad1-99fd-4694-8816-9c1bbd3dec72',
                    'label': '1. E-Mail',
                    'email': 'da@example.org',
                    'isDefault': True,
                    'thirdPartyId': None,
                    'modified': '2024-12-23T16:44:12.059162+01:00',
                    'created': '2024-12-23T16:44:12.059150+01:00',
                },
                'salutation': 'Herr',
                'tags': [],
                'thirdPartyId': '37',
                'title': 'Dr',
                'username': None,
            },
            {
                'created': '2024-12-23T16:44:19.413799+01:00',
                'firstName': 'Heinz',
                'fullName': 'Achermann Heinz',
                'id': '56603980-d390-4cf8-bc2b-5335affe22be',
                'isActive': True,
                'modified': '2024-12-23T16:44:19.413805+01:00',
                'officialName': 'Achermann',
                'personTypeTitle': None,
                'primaryEmail': {
                    'id': 'e6d45171-0bf7-483d-9d38-d686982a3f68',
                    'label': '1. E-Mail',
                    'email': 'ha@example.org',
                    'isDefault': True,
                    'thirdPartyId': None,
                    'modified': '2024-12-23T16:44:19.416512+01:00',
                    'created': '2024-12-23T16:44:19.416484+01:00',
                },
                'salutation': 'Herr',
                'tags': [],
                'thirdPartyId': '142',
                'title': '',
                'username': None,
            },
        ],
    }


@fixture
def organization_json():
    """Fixture providing sample organizations data as JSON string.

    """
    return {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {
                'created': '2024-12-23T16:44:24.920938+01:00',
                'description': '',
                'id': 'ef39e789-10e1-4117-8507-63b6cb3ef7cc',
                'isActive': True,
                'memberCount': 17,
                'modified': '2025-01-06T10:19:49.765454+01:00',
                'name': 'ad-hoc-Gastgewerbegesetz, 3699',
                'organizationTypeTitle': 'Kommission',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
            {
                'created': '2024-12-23T16:44:24.928269+01:00',
                'description': '',
                'id': 'f124b1fe-99b8-4bc2-b40d-bc8dec4997bc',
                'isActive': True,
                'memberCount': 16,
                'modified': '2025-01-06T10:19:54.708568+01:00',
                'name': 'ad-hoc-KiBe_SchulG, 3652',
                'organizationTypeTitle': 'Kommission',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
        ],
    }


@fixture
def organization_json_with_fraktion():
    return {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {
                'created': '2024-12-23T16:44:24.920938+01:00',
                'description': '',
                'id': 'ef39e789-10e1-4117-8507-63b6cb3ef7cc',
                'isActive': True,
                'memberCount': 17,
                'modified': '2025-01-06T10:19:49.765454+01:00',
                'name': 'ad-hoc-Gastgewerbegesetz, 3699',
                'organizationTypeTitle': 'Kommission',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
            {
                'created': '2024-12-23T16:44:24.928269+01:00',
                'description': '',
                'id': 'f124b1fe-99b8-4bc2-b40d-bc8dec4997bc',
                'isActive': True,
                'memberCount': 16,
                'modified': '2025-01-06T10:19:54.708568+01:00',
                'name': 'ALG',
                'organizationTypeTitle': 'Fraktion',
                'primaryEmail': None,
                'status': 1,
                'thirdPartyId': None,
            },
        ],
    }




@fixture
def memberships_json():
    """Fixture providing sample memberships data as JSON string."""
    return {
        'count': 2,
        'next': None,
        'previous': None,
        'results': [
            {
                'department': '',
                'description': '',
                'emailReceptionType': 'to',
                'end': False,
                'id': '8151a14a-5f13-444b-9695-be9bb63f0ad5',
                'isDefault': True,
                'organization': {
                    'created': '2024-12-23T16:44:24.955967+01:00',
                    'description': '',
                    'id': 'a962a086-0261-4b9b-b15f-b4064672efe8',
                    'isActive': True,
                    'memberCount': 3,
                    'modified': '2025-01-06T10:20:32.206637+01:00',
                    'name': 'amtliche Missione KRP, Vize-KRP',
                    'organizationTypeTitle': 'Kommission',
                    'primaryEmail': False,
                    'status': 1,
                    'thirdPartyId': False,
                    'organizationType': 3,
                    'primaryAddress': False,
                    'primaryPhoneNumber': False,
                    'primaryUrl': False,
                    'statusDisplay': 'Aktiv',
                    'tags': [],
                    'type': 'organization',
                },
                'person': {
                    'created': '2024-12-23T16:44:13.642607+01:00',
                    'firstName': 'Karl',
                    'fullName': 'Nussbaumer Karl',
                    'id': '149ad0c8-c8e0-4e97-97cd-3add9b49ad9f',
                    'isActive': True,
                    'modified': '2024-12-23T16:44:13.642615+01:00',
                    'officialName': 'Nussbaumer',
                    'personTypeTitle': False,
                    'primaryEmail': {
                        'id': '7e4597de-2dd8-45f7-a615-d11ab43bb69f',
                        'label': '1. E-Mail',
                        'email': 'kn@example.org',
                        'isDefault': True,
                        'thirdPartyId': False,
                        'modified': '2024-12-23T16:44:13.645788+01:00',
                        'created': '2024-12-23T16:44:13.645778+01:00',
                    },
                    'salutation': 'Herr',
                    'tags': [],
                    'thirdPartyId': '59',
                    'title': '',
                    'username': False,
                },
                'primaryAddress': {
                    'formattedAddress': 'Redacted 1, 1111 Foobar',
                    'id': '9f89946c-e7aa-479c-8876-e0227b37a57d',
                    'label': 'Post-Adresse',
                    'isDefault': True,
                    'organisationName': '',
                    'organisationNameAddOn1': '',
                    'organisationNameAddOn2': '',
                    'addressLine1': '',
                    'addressLine2': '',
                    'street': 'Redacted',
                    'houseNumber': '1',
                    'dwellingNumber': '',
                    'postOfficeBox': '',
                    'swissZipCode': '1111',
                    'swissZipCodeAddOn': '',
                    'swissZipCodeId': '',
                    'foreignZipCode': '',
                    'locality': '',
                    'town': 'Foobar',
                    'countryIdISO2': 'CH',
                    'countryName': 'Schweiz',
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:13.645077+01:00',
                    'created': '2024-12-23T16:44:13.645067+01:00',
                },
                'primaryEmail': {
                    'id': '7e4597de-2dd8-45f7-a615-d11ab43bb69f',
                    'label': '1. E-Mail',
                    'email': 'kn@example.org',
                    'isDefault': True,
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:13.645788+01:00',
                    'created': '2024-12-23T16:44:13.645778+01:00',
                },
                'primaryPhoneNumber': {
                    'id': 'b8a6ca48-7484-49d0-b120-2c659d48cf45',
                    'label': 'Telefon Privat',
                    'phoneNumber': '041 111 11 11',
                    'phoneCategory': 1,
                    'otherPhoneCategory': False,
                    'phoneCategoryText': 'Private Telefonnummer',
                    'isDefault': True,
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:13.646427+01:00',
                    'created': '2024-12-23T16:44:13.646418+01:00',
                },
                'primaryUrl': {
                    'id': '64da31dc-23c7-4b9e-b9c0-f175a615f74f',
                    'label': 'Webseite',
                    'isDefault': True,
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:13.647164+01:00',
                    'created': '2024-12-23T16:44:13.647154+01:00',
                },
                'email': False,
                'phoneNumber': False,
                'address': False,
                'urlField': False,
                'role': 'Präsident/-in',
                'start': False,
                'text': 'Nussbaumer Karl - amtliche Missione KRP, Vize-KRP',
                'thirdPartyId': False,
                'type': 'membership',
                'typedId': 'membership:8151a14a-5f13-444b-9695-be9bb63f0ad5',
            },
            {
                'department': '',
                'description': '',
                'emailReceptionType': 'to',
                'end': False,
                'id': '3b55570d-7613-4ece-8dd3-e36ecf6ef1b3',
                'isDefault': True,
                'organization': {
                    'created': '2024-12-23T16:44:24.967106+01:00',
                    'description': '',
                    'id': '92dc0abf-fc1e-444b-845c-0de297d9c0d4',
                    'isActive': True,
                    'memberCount': 8,
                    'modified': '2025-01-06T10:21:25.979702+01:00',
                    'name': 'Justizprüfungskommission (JPK)',
                    'organizationTypeTitle': 'Kommission',
                    'primaryEmail': False,
                    'status': 1,
                    'thirdPartyId': False,
                    'organizationType': 3,
                    'primaryAddress': False,
                    'primaryPhoneNumber': False,
                    'primaryUrl': False,
                    'statusDisplay': 'Aktiv',
                    'tags': [],
                    'type': 'organization',
                },
                'person': {
                    'created': '2024-12-23T16:44:14.895333+01:00',
                    'firstName': 'Thomas',
                    'fullName': 'Werner Thomas',
                    'id': '0204b9ca-04f0-4549-8c69-bd719d9c87e5',
                    'isActive': True,
                    'modified': '2024-12-23T16:44:14.895340+01:00',
                    'officialName': 'Werner',
                    'personTypeTitle': False,
                    'primaryEmail': {
                        'id': '598eff17-b3a1-4332-be42-952335ef82d5',
                        'label': '1. E-Mail',
                        'email': 'wt@example.org',
                        'isDefault': True,
                        'thirdPartyId': False,
                        'modified': '2024-12-23T16:44:14.898115+01:00',
                        'created': '2024-12-23T16:44:14.898105+01:00',
                    },
                    'salutation': 'Herr',
                    'tags': [],
                    'thirdPartyId': '75',
                    'title': '',
                    'username': False,
                },
                'primaryAddress': {
                    'formattedAddress': 'Redacted 2, 1111 Redacted2',
                    'id': '0082ac33-ca82-4275-b696-b37955805889',
                    'label': 'Post-Adresse',
                    'isDefault': True,
                    'organisationName': '',
                    'organisationNameAddOn1': '',
                    'organisationNameAddOn2': '',
                    'addressLine1': '',
                    'addressLine2': '',
                    'street': 'Redacted',
                    'houseNumber': '2',
                    'dwellingNumber': '',
                    'postOfficeBox': '',
                    'swissZipCode': '1111',
                    'swissZipCodeAddOn': '',
                    'swissZipCodeId': '',
                    'foreignZipCode': '',
                    'locality': '',
                    'town': 'Redacted2',
                    'countryIdISO2': 'CH',
                    'countryName': 'Schweiz',
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:14.897448+01:00',
                    'created': '2024-12-23T16:44:14.897438+01:00',
                },
                'primaryEmail': {
                    'id': '598eff17-b3a1-4332-be42-952335ef82d5',
                    'label': '1. E-Mail',
                    'email': 'wt@example.org',
                    'isDefault': True,
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:14.898115+01:00',
                    'created': '2024-12-23T16:44:14.898105+01:00',
                },
                'primaryPhoneNumber': {
                    'id': '367a569a-b89c-41fa-9829-183f512e90f2',
                    'label': 'Telefon Privat',
                    'phoneNumber': '041 111 11 11',
                    'phoneCategory': 1,
                    'otherPhoneCategory': False,
                    'phoneCategoryText': 'Private Telefonnummer',
                    'isDefault': True,
                    'thirdPartyId': False,
                    'modified': '2024-12-23T16:44:14.898840+01:00',
                    'created': '2024-12-23T16:44:14.898831+01:00',
                },
                'primaryUrl': False,
                'email': False,
                'phoneNumber': False,
                'address': False,
                'urlField': False,
                'role': 'Mitglied',
                'start': False,
                'text': 'Werner Thomas - Justizprüfungskommission (JPK) '
                '(Mitglied)',
                'thirdPartyId': False,
                'type': 'membership',
                'typedId': 'membership:3b55570d-7613-4ece-8dd3-e36ecf6ef1b3',
            },
        ],
    }


@fixture(scope='function')
def pas_app(request):
    app = create_pas_app(request, use_elasticsearch=False)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def es_pas_app(request):
    app = create_pas_app(request, use_elasticsearch=True)
    yield app
    app.session_manager.dispose()


@fixture(scope='function')
def client(pas_app):
    client = Client(pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@fixture(scope='function')
def client_with_es(es_pas_app):
    client = Client(es_pas_app)
    client.skip_n_forms = 1
    client.use_intercooler = True
    return client


@fixture(scope='function')
def wsgi_server(request):
    app = create_pas_app(request, False)
    app.print_exceptions = True
    server = WSGIServer(application=app)
    server.start()
    yield server
    server.stop()


@fixture(scope='function')
def browser(request, browser, wsgi_server):
    browser.baseurl = wsgi_server.url
    browser.wsgi_server = wsgi_server
    yield browser


@fixture(scope='session', autouse=True)
def enter_observer_scope():
    """Ensures app specific observers are active"""
    ScopedPropertyObserver.enter_class_scope(PasApp)


@fixture
def commission_test_files():
    csv = module_path('tests.onegov.pas', '/fixtures/commission_test.csv')
    xlsx = module_path('tests.onegov.pas', '/fixtures/commission_test.xlsx')
    return {'csv': csv, 'xlsx': xlsx}


class DummyApp:

    def __init__(self, session, application_id='my-app'):
        self._session = session
        self.application_id = application_id
        self.org = Bunch(
            geo_provider='none',
            open_files_target_blank=True
        )

    def session(self):
        return self._session
