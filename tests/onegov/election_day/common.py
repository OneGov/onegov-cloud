import os
import tarfile

from io import BytesIO
from onegov.core.utils import append_query_param
from onegov.core.utils import module_path
from onegov.election_day.formats import import_election_wabstic_proporz
from onegov.election_day.models import Canton
from onegov.election_day.models import Municipality
from pyquery import PyQuery as pq
from unittest.mock import Mock
from webtest.forms import Upload


def get_fixture_path(domain=None, principal=None):
    """Fixtures are organized like
    fixtures/domain/principal/internal_proporz.tar.gz
    """
    fixture_path = module_path('tests.onegov.election_day', 'fixtures')
    if not domain:
        return fixture_path
    if not principal:
        return os.path.join(fixture_path, domain)
    return os.path.join(fixture_path, domain, principal)


def get_tar_archive_name(api_format, model, type_=None):
    if model == 'vote':
        return f'{api_format}_vote.tar.gz'
    elif model == 'election':
        assert type_
        return f'{api_format}_{type_}.tar.gz'
    return f'{api_format}.tar.gz'


def get_tar_file_path(
    domain=None,
    principal=None,
    api_format=None,
    model=None,
    type_=None
):
    if model == 'vote' and api_format == 'wabstic' or api_format == 'wabstim':
        # This format can have all domains, the will be a separate archive
        return os.path.join(
            get_fixture_path(),
            f'{api_format}_vote.tar.gz'
        )
    return os.path.join(
        get_fixture_path(domain, principal),
        get_tar_archive_name(api_format, model, type_)
    )


def create_principal(principal=None, municipality=None):
    if principal in Canton.CANTONS:
        return Canton(canton=principal)

    return Municipality(
        municipality=municipality, canton='be', canton_name='Kanton Bern'
    )


PROPORZ_HEADER = (
    'election_status,'
    'entity_id,'
    'entity_counted,'
    'entity_eligible_voters,'
    'entity_received_ballots,'
    'entity_invalid_ballots,'
    'entity_blank_ballots,'
    'entity_blank_votes,'
    'entity_invalid_votes,'
    'list_id,'
    'list_name,'
    'list_connection_parent,'
    'list_connection,'
    'list_number_of_mandates,'
    'list_votes,'
    'candidate_id,'
    'candidate_elected,'
    'candidate_family_name,'
    'candidate_first_name,'
    'candidate_gender,'
    'candidate_year_of_birth,'
    'candidate_votes,'
    'candidate_party,'
    'list_panachage_votes_from_list_1,'
    'list_panachage_votes_from_list_2'
    '\n'
)


MAJORZ_HEADER = (
    'election_status,'
    'election_absolute_majority,'
    'entity_id,'
    'entity_counted,'
    'entity_eligible_voters,'
    'entity_received_ballots,'
    'entity_invalid_ballots,'
    'entity_blank_ballots,'
    'entity_blank_votes,'
    'entity_invalid_votes,'
    'candidate_id,'
    'candidate_elected,'
    'candidate_family_name,'
    'candidate_first_name,'
    'candidate_votes,'
    'candidate_party,'
    '\n'
)


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyPrincipal:

    all_years = range(2000, 2030)

    entities = {year: {
        1: {'name': 'Entity', 'district': 'District'},
        2: {'name': 'Entity2', 'district': 'District'}
    } for year in all_years}

    def __init__(self):
        self.name = 'name'
        self.webhooks = []
        self.sms_notification = None
        self.email_notification = None
        self.domain = 'canton'
        self.wabsti_import = False
        self.has_districts = False
        self.has_regions = False
        self.has_superregions = False
        self._is_year_available = True
        self.reply_to = None
        self.superregions = []
        self.official_host = None
        self.segmented_notifications = False

    @property
    def notifications(self):
        if (
            (len(self.webhooks) > 0)
            or self.sms_notification
            or self.email_notification
        ):
            return True
        return False

    def is_year_available(self, year):
        return self._is_year_available

    def label(self, type):
        return '__{}'.format(type)

    def get_superregion(self, region, year):
        return ''

    def get_superregions(self, year):
        return self.superregions


class DummyApp:
    version = '1.0'
    sentry_dsn = None

    def __init__(self, session=None, application_id='application_id'):
        self._session = session
        self.application_id = application_id
        self.principal = DummyPrincipal()
        self.schema = 'onegov_election_day-{}'.format(self.principal.name)
        self.websocket_data = []

    def session(self):
        return self._session

    def send_marketing_email_batch(self, prepared_emails):
        # we'll allow sending empty batches for DummyApp
        assert not list(prepared_emails)

    def send_websocket(self, data):
        self.websocket_data.append(data)
        return True


class DummyRequest:

    def __init__(self, session=None, app=None, locale='de',
                 is_logged_in=False, is_secret=False, url='',
                 avoid_quotes_in_url=False):
        self.includes = []
        self.session = session
        self.app = app or DummyApp(session=self.session)
        self.locale = locale
        self.is_logged_in = is_logged_in
        if app and session:
            self.app.session = Mock(return_value=session)
        self.params = {}
        self.default_locale = 'de_CH'
        self.is_secret = lambda x: is_secret
        self.url = url
        self.avoid_quotes_in_url = avoid_quotes_in_url

    def class_link(self, model, variables=None, name=''):
        return f'{model.__name__}/{name}/{variables or {}}'

    def link(self, obj, name='', query_params=None):
        query_params = query_params or {}
        class_name = obj.__class__.__name__
        if class_name == 'Canton' or class_name == 'Municipality':
            class_name = 'Principal'
        result = '{}/{}'.format(
            class_name, name or getattr(obj, 'id', 'archive')
        )
        for key, value in query_params.items():
            result = append_query_param(result, key, value)
        return result

    def translate(self, text):
        try:
            return text.interpolate(
                self.app.translations.get(self.locale).gettext(text)
            )
        except Exception:
            try:
                return text.interpolate()
            except Exception:
                return text

    def include(self, resource):
        self.includes.append(resource)
        self.includes = list(set(self.includes))

    def new_url_safe_token(self, data):
        formatted = str({key: data[key] for key in sorted(data)})
        if self.avoid_quotes_in_url:
            # remove quotes
            return formatted.replace("'", '')
        return formatted

    def get_translate(self, for_chameleon=False):
        if not self.app.locales:
            return None
        if for_chameleon:
            return self.app.chameleon_translations.get(self.locale)
        return self.app.translations.get(self.locale)

    def return_to(self, url, redirect):
        return f'{url}{redirect}'


def login(client, to=''):
    login = client.get(f'/auth/login?to={to}')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    return login.form.submit()


def logout(client, to=''):
    client.get(f'/auth/logout?to={to}')


def upload_vote(client, create=True, canton='zg'):
    if create:
        new = client.get('/manage/votes/new-vote')
        new.form['title_de'] = 'Vote'
        new.form['date'] = '2022-01-01'
        new.form['domain'] = 'federation'
        new.form['type'] = 'simple'
        new.form.submit()

    csv = (
        'entity_id,yeas,nays,eligible_voters,empty,invalid,status,type,'
        'counted\n'
    )

    if canton == 'zg':
        csv += (
            '1701,3049,5111,13828,54,3,final,proposal,true\n'
            '1702,2190,3347,9687,60,,final,proposal,true\n'
            '1703,1497,2089,5842,15,1,final,proposal,true\n'
            '1704,599,1171,2917,17,,final,proposal,true\n'
            '1705,307,522,1289,10,1,final,proposal,true\n'
            '1706,811,1298,3560,18,,final,proposal,true\n'
            '1707,1302,1779,6068,17,,final,proposal,true\n'
            '1708,1211,2350,5989,17,,final,proposal,true\n'
            '1709,1096,2083,5245,18,1,final,proposal,true\n'
            '1710,651,743,2016,8,,final,proposal,true\n'
            '1711,3821,7405,16516,80,1,final,proposal,true\n'
        )
    if canton == 'gr':
        csv += (
            '3506,3049,5111,13828,54,3,final,proposal,true\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_complex_vote(client, create=True, canton='zg'):
    if create:
        new = client.get('/manage/votes/new-vote')
        new.form['title_de'] = 'Complex Vote'
        new.form['date'] = '2022-01-01'
        new.form['domain'] = 'federation'
        new.form['type'] = 'complex'
        new.form.submit()

    csv = (
        'entity_id,yeas,nays,eligible_voters,empty,invalid,status,type,'
        'counted\n'
    )
    for type_ in ('proposal', 'counter-proposal', 'tie-breaker'):
        if canton == 'zg':
            csv += (
                f'1701,3049,5111,13828,54,3,final,{type_},true\n'
                f'1702,2190,3347,9687,60,,final,{type_},true\n'
                f'1703,1497,2089,5842,15,1,final,{type_},true\n'
                f'1704,599,1171,2917,17,,final,{type_},true\n'
                f'1705,307,522,1289,10,1,final,{type_},true\n'
                f'1706,811,1298,3560,18,,final,{type_},true\n'
                f'1707,1302,1779,6068,17,,final,{type_},true\n'
                f'1708,1211,2350,5989,17,,final,{type_},true\n'
                f'1709,1096,2083,5245,18,1,final,{type_},true\n'
                f'1710,651,743,2016,8,,final,{type_},true\n'
                f'1711,3821,7405,16516,80,1,final,{type_},true\n'
            )
        if canton == 'gr':
            csv += (
                f'3506,3049,5111,13828,54,3,final,{type_},true\n'
            )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/complex-vote/upload')
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_majorz_election(client, create=True, canton='gr', status='unknown'):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['title_de'] = 'Majorz Election'
        new.form['date'] = '2022-01-01'
        new.form['mandates'] = 2
        new.form['type'] = 'majorz'
        new.form['domain'] = 'federation'
        new.form.submit()

    csv = (
        'election_status,'
        'election_absolute_majority,'
        'entity_id,'
        'entity_counted,'
        'entity_eligible_voters,'
        'entity_received_ballots,'
        'entity_invalid_ballots,'
        'entity_blank_ballots,'
        'entity_blank_votes,'
        'entity_invalid_votes,'
        'candidate_id,'
        'candidate_elected,'
        'candidate_family_name,'
        'candidate_first_name,'
        'candidate_votes,'
        'candidate_party,'
        '\n'
    )
    if canton == 'gr':
        csv += (
            f'{status},,3506,True,56,25,0,4,1,0,1,True,Engler,Stefan,20,\n'
            f'{status},,3506,True,56,25,0,4,1,0,2,True,Schmid,Martin,18,\n'
        )
    if canton == 'zg':
        csv += (
            f'{status},,1711,True,56,25,0,4,1,0,1,True,Engler,Stefan,20,\n'
            f'{status},,1710,True,56,25,0,4,1,0,2,True,Schmid,Martin,18,\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/election/majorz-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_proporz_election(client, create=True, canton='gr',
                            status='unknown'):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['title_de'] = 'Proporz Election'
        new.form['date'] = '2022-01-01'
        new.form['mandates'] = 5
        new.form['type'] = 'proporz'
        new.form['domain'] = 'federation'
        new.form['show_party_strengths'] = True
        new.form['show_party_panachage'] = True
        new.form.submit()

    csv = PROPORZ_HEADER
    if canton == 'gr':
        csv += (
            f'{status},3506,True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
            '101,False,Casanova,Angela,female,1970,0,,0,1\n'
        )
        csv += (
            f'{status},3506,True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
            '201,False,Caluori,Corina,female,1960,2,,2,0\n'
        )
    elif canton == 'zg':
        csv += (
            f'{status},1711,True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
            '101,False,Casanova,Angela,female,1970,0,,0,1\n'
        )
        csv += (
            f'{status},1711,True,56,32,1,0,1,2,2,CVP,1,2,0,5,'
            '201,False,Caluori,Corina,female,1960,2,,2,0\n'
        )

    csv = csv.encode('utf-8')

    upload = client.get('/election/proporz-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_party_results(
    client, slug='election/proporz-election', domain='', domain_segment=''
):
    csv_parties = (
        "domain,domain_segment,year,total_votes,id,name,color,mandates,"
        "votes,voters_count,voters_count_percentage,"
        "panachage_votes_from_1,panachage_votes_from_2,"
        "panachage_votes_from_3,panachage_votes_from_999\n"
        f"{domain},{domain_segment},2022,11270,1,BDP,"
        "#efb52c,1,60387,603.01,41.73,,11,12,100\n"
        f"{domain},{domain_segment},2022,11270,2,"
        "CVP,#ff6300,1,49117,491.02,33.98,21,,22,200\n"
        f"{domain},{domain_segment},2022,11270,3,"
        "FDP,,0,35134,351.04,24.29,31,32,,300\n"
    ).encode('utf-8')

    upload = client.get(f'/{slug}/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def create_election_compound(client, canton='gr', pukelsheim=False,
                             completes_manually=False, voters_counts=True,
                             exact_voters_counts=True):
    domain = {
        'bl': 'region',
        'gr': 'region',
        'sg': 'district',
        'sz': 'municipality',
        'zg': 'municipality',
    }
    elections_field = {
        'bl': 'region_elections',
        'gr': 'region_elections',
        'sg': 'district_elections',
        'sz': 'municipality_elections',
        'zg': 'municipality_elections',
    }
    segment = {
        'bl': ['Reinach', 'Allschwil'],
        'gr': ['Alvaschein', 'Belfort'],
        'sg': ['Muolen', 'St. Gallen'],
        'sz': ['Einsiedeln', 'Gersau'],
        'zg': ['Baar', 'Cham'],
    }

    # Add two elections
    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Regional Election A'
    new.form['date'] = '2022-01-01'
    new.form['type'] = 'proporz'
    new.form['domain'] = domain[canton]
    new.form[domain[canton]] = segment[canton][0]
    new.form['mandates'] = 10
    new.form.submit()

    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['title_de'] = 'Regional Election B'
    new.form['date'] = '2022-01-01'
    new.form['type'] = 'proporz'
    new.form['domain'] = domain[canton]
    new.form[domain[canton]] = segment[canton][1]
    new.form['mandates'] = 5
    new.form.submit()

    # Add a compound
    new = client.get('/manage/election-compounds').click('Neue Verbindung')
    new.form['title_de'] = 'Elections'
    new.form['date'] = '2022-01-01'
    new.form['domain'] = 'canton'
    new.form['domain_elections'] = domain[canton]
    new.form[elections_field[canton]] = [
        'regional-election-a', 'regional-election-b'
    ]
    new.form['pukelsheim'] = pukelsheim
    new.form['completes_manually'] = completes_manually
    new.form['voters_counts'] = voters_counts
    new.form['exact_voters_counts'] = exact_voters_counts
    new.form['show_seat_allocation'] = True
    new.form['show_list_groups'] = True
    new.form['show_party_strengths'] = True
    new.form['show_party_panachage'] = True
    new.form.submit()


def upload_election_compound(client, create=True, canton='gr',
                             status='unknown', pukelsheim=False,
                             completes_manually=False, voters_counts=True,
                             exact_voters_counts=True):
    entities = {
        'bl': [2761, 2762],
        'gr': [3506, 3513],
        'sg': [3202, 3203],
        'sz': [1301, 1311],
        'zg': [1701, 1702],
    }
    if create:
        create_election_compound(
            client,
            canton=canton,
            pukelsheim=pukelsheim,
            completes_manually=completes_manually,
            voters_counts=voters_counts,
            exact_voters_counts=exact_voters_counts,
        )

    csv = PROPORZ_HEADER
    csv += (
        f'{status},{entities[canton][0]},True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
        f'101,False,Looser,Anna,female,1950,0,,0,1\n'
        f'{status},{entities[canton][0]},True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
        f'201,True,Winner,Carol,female,1990,2,,2,0\n'
    )
    csv += (
        f'{status},{entities[canton][1]},True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
        f'101,True,Sieger,Hans,male,1980,0,,0,1\n'
        f'{status},{entities[canton][1]},True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
        f'201,False,Verlierer,Peter,male,1920,2,,2,0\n'
    )
    csv = csv.encode('utf-8')

    upload = client.get('/elections/elections/upload')
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def import_wabstic_data(election, tar_file, principal, has_expats=False):
    # The tar file contains a test dataset

    with tarfile.open(tar_file, 'r:gz') as f:
        regional_wp_gemeinden = f.extractfile('WP_Gemeinden.csv').read()
        regional_wp_kandidaten = f.extractfile(
            'WP_Kandidaten.csv').read()
        regional_wp_kandidatengde = f.extractfile(
            'WP_KandidatenGde.csv').read()
        regional_wp_listen = f.extractfile('WP_Listen.csv').read()
        regional_wp_listengde = f.extractfile('WP_ListenGde.csv').read()
        regional_wpstatic_gemeinden = f.extractfile(
            'WPStatic_Gemeinden.csv').read()
        regional_wpstatic_kandidaten = f.extractfile(
            'WPStatic_Kandidaten.csv').read()
        regional_wp_wahl = f.extractfile('WP_Wahl.csv').read()

    # Test cantonal elections
    election.has_expats = has_expats

    errors = import_election_wabstic_proporz(
        election, principal, '1', None,
        BytesIO(regional_wp_wahl), 'text/plain',
        BytesIO(regional_wpstatic_gemeinden), 'text/plain',
        BytesIO(regional_wp_gemeinden), 'text/plain',
        BytesIO(regional_wp_listen), 'text/plain',
        BytesIO(regional_wp_listengde), 'text/plain',
        BytesIO(regional_wpstatic_kandidaten), 'text/plain',
        BytesIO(regional_wp_kandidaten), 'text/plain',
        BytesIO(regional_wp_kandidatengde), 'text/plain',
    )
    assert not errors


def get_email_link(message, contains):
    elements = pq(message['HtmlBody'])('*')
    links = [e.attrib['href'] for e in elements if 'href' in e.attrib]
    links = [l for l in links if contains in l]
    return links[0]
