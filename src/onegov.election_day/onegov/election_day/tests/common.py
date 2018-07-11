from datetime import date
from unittest.mock import Mock
from webtest.forms import Upload


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
    'candidate_votes,'
    'candidate_party,'
    'panachage_votes_from_list_1,'
    'panachage_votes_from_list_2'
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


class DummyPrincipal(object):

    def __init__(self):
        self.name = 'name'
        self.webhooks = []
        self.sms_notification = None
        self.email_notification = None
        self.domain = 'canton'
        self.wabsti_import = False
        self.has_districts = False
        self._is_year_available = True

    def is_year_available(self, year):
        return self._is_year_available

    def label(self, type):
        return '__{}'.format(type)


class DummyApp(object):
    def __init__(self, session=None, application_id='application_id'):
        self._session = session
        self.application_id = application_id
        self.principal = DummyPrincipal()
        self.schema = 'onegov_election_day-{}'.format(self.principal.name)

    def session(self):
        return self._session


class DummyRequest(object):

    def __init__(self, session=None, app=None, locale='de',
                 is_logged_in=False):
        self.includes = []
        self.session = session
        self.app = app or DummyApp(session=self.session)
        self.locale = locale
        self.is_logged_in = is_logged_in
        if app and session:
            self.app.session = Mock(return_value=session)
        self.params = {}
        self.default_locale = 'de_CH'

    def link(self, model, name=''):
        class_name = model.__class__.__name__
        if class_name == 'Canton' or class_name == 'Municipality':
            class_name = 'Principal'
        return '{}/{}'.format(
            class_name, name or getattr(model, 'id', 'archive')
        )

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
        return str(data)

    def get_translate(self, for_chameleon=False):
        if not self.app.locales:
            return None
        if for_chameleon:
            return self.app.chameleon_translations.get(self.locale)
        return self.app.translations.get(self.locale)


def login(client):
    login = client.get('/auth/login')
    login.form['username'] = 'admin@example.org'
    login.form['password'] = 'hunter2'
    login.form.submit()


def upload_vote(client, create=True, canton='zg'):
    if create:
        new = client.get('/manage/votes/new-vote')
        new.form['vote_de'] = 'Vote'
        new.form['date'] = date(2015, 1, 1)
        new.form['domain'] = 'federation'
        new.form['vote_type'] = 'simple'
        new.form.submit()

    csv = (
        'ID,Ja Stimmen,Nein Stimmen,'
        'Stimmberechtigte,Leere Stimmzettel,Ungültige Stimmzettel\n'
    )
    if canton == 'zg':
        csv += (
            '1701,3049,5111,13828,54,3\n'
            '1702,2190,3347,9687,60,\n'
            '1703,1497,2089,5842,15,1\n'
            '1704,599,1171,2917,17,\n'
            '1705,307,522,1289,10,1\n'
            '1706,811,1298,3560,18,\n'
            '1707,1302,1779,6068,17,\n'
            '1708,1211,2350,5989,17,\n'
            '1709,1096,2083,5245,18,1\n'
            '1710,651,743,2016,8,\n'
            '1711,3821,7405,16516,80,1\n'
        )
    if canton == 'gr':
        csv += (
            '3503,3049,5111,13828,54,3\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form['type'] = 'simple'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_complex_vote(client, create=True, canton='zg'):
    if create:
        new = client.get('/manage/votes/new-vote')
        new.form['vote_de'] = 'Complex Vote'
        new.form['date'] = date(2015, 1, 1)
        new.form['domain'] = 'federation'
        new.form['vote_type'] = 'complex'
        new.form.submit()

    csv = (
        'ID,Ja Stimmen,Nein Stimmen,'
        'Stimmberechtigte,Leere Stimmzettel,Ungültige Stimmzettel\n'
    )
    if canton == 'zg':
        csv += (
            '1701,3049,5111,13828,54,3\n'
            '1702,2190,3347,9687,60,\n'
            '1703,1497,2089,5842,15,1\n'
            '1704,599,1171,2917,17,\n'
            '1705,307,522,1289,10,1\n'
            '1706,811,1298,3560,18,\n'
            '1707,1302,1779,6068,17,\n'
            '1708,1211,2350,5989,17,\n'
            '1709,1096,2083,5245,18,1\n'
            '1710,651,743,2016,8,\n'
            '1711,3821,7405,16516,80,1\n'
        )
    if canton == 'gr':
        csv += (
            '3503,3049,5111,13828,54,3\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/complex-vote/upload')
    upload.form['type'] = 'complex'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload.form['counter_proposal'] = Upload('data.csv', csv, 'text/plain')
    upload.form['tie_breaker'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_majorz_election(client, create=True, canton='gr'):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = 'Majorz Election'
        new.form['date'] = date(2015, 1, 1)
        new.form['mandates'] = 2
        new.form['election_type'] = 'majorz'
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
            'unknown,,3503,True,56,25,0,4,1,0,1,True,Engler,Stefan,20,\n'
            'unknown,,3503,True,56,25,0,4,1,0,2,True,Schmid,Martin,18,\n'
        )
    if canton == 'zg':
        csv += (
            'unknown,,1711,True,56,25,0,4,1,0,1,True,Engler,Stefan,20,\n'
            'unknown,,1710,True,56,25,0,4,1,0,2,True,Schmid,Martin,18,\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/election/majorz-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_proporz_election(client, create=True, canton='gr'):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = 'Proporz Election'
        new.form['date'] = date(2015, 1, 1)
        new.form['mandates'] = 5
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'federation'
        new.form.submit()

    csv = PROPORZ_HEADER
    if canton == 'gr':
        csv += (
            'unknown,3503,True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
            '101,False,Casanova,Angela,0,,0,1\n'
        )
        csv += (
            'unknown,3503,True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
            '201,False,Caluori,Corina,2,,2,0\n'
        )
    elif canton == 'zg':
        csv += (
            'unknown,1711,True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
            '101,False,Casanova,Angela,0,,0,1\n'
        )
        csv += (
            'unknown,1711,True,56,32,1,0,1,2,2,CVP,1,2,0,5,'
            '201,False,Caluori,Corina,2,,2,0\n'
        )
    csv = csv.encode('utf-8')

    upload = client.get('/election/proporz-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_party_results(client, create=True,
                         slug='election/proporz-election'):
    csv_parties = (
        "year,total_votes,id,name,color,mandates,votes,"
        "panachage_votes_from_1,panachage_votes_from_2,"
        "panachage_votes_from_3,panachage_votes_from_999\n"
        "2015,11270,1,BDP,#efb52c,1,60387,,11,12,100\n"
        "2015,11270,2,CVP,#ff6300,1,49117,21,,22,200\n"
        "2015,11270,3,FDP,,0,35134,31,32,,300\n"
    ).encode('utf-8')

    upload = client.get(f'/{slug}/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()


def create_election_compound(client):
    # Add two elections
    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['election_de'] = 'Regional Election A'
    new.form['date'] = date(2015, 1, 1)
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['distinct'] = True
    new.form['mandates'] = 10
    new.form.submit()

    new = client.get('/manage/elections').click('Neue Wahl')
    new.form['election_de'] = 'Regional Election B'
    new.form['date'] = date(2015, 1, 1)
    new.form['election_type'] = 'proporz'
    new.form['domain'] = 'region'
    new.form['distinct'] = True
    new.form['mandates'] = 5
    new.form.submit()

    # Add a compound
    new = client.get('/manage/election-compounds').click('Neue Verbindung')
    new.form['election_de'] = 'Elections'
    new.form['date'] = date(2015, 1, 1)
    new.form['domain'] = 'canton'
    new.form['elections'] = ['regional-election-a', 'regional-election-b']
    new.form.submit()


def upload_election_compound(client, create=True, canton='gr'):
    if create:
        # Add two elections
        new = client.get('/manage/elections').click('Neue Wahl')
        new.form['election_de'] = 'Regional Election A'
        new.form['date'] = date(2015, 1, 1)
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'region'
        new.form['distinct'] = True
        new.form['mandates'] = 10
        new.form.submit()

        new = client.get('/manage/elections').click('Neue Wahl')
        new.form['election_de'] = 'Regional Election B'
        new.form['date'] = date(2015, 1, 1)
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'region'
        new.form['distinct'] = True
        new.form['mandates'] = 5
        new.form.submit()

        # Add a compound
        new = client.get('/manage/election-compounds').click('Neue Verbindung')
        new.form['election_de'] = 'Elections'
        new.form['date'] = date(2015, 1, 1)
        new.form['domain'] = 'canton'
        new.form['elections'] = ['regional-election-a', 'regional-election-b']
        new.form.submit()

    for index, slug in enumerate((
        'regional-election-a', 'regional-election-b'
    )):
        csv = PROPORZ_HEADER

        if index:
            entity = 3503 if canton == 'gr' else 1711
            csv += (
                f'unknown,{entity},True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
                f'101,True,Hans,Sieger,0,,0,1\n'
                f'unknown,{entity},True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
                f'201,False,Peter,Verlierer,2,,2,0\n'
            )
        else:
            entity = 3633 if canton == 'gr' else 1711
            csv += (
                f'unknown,{entity},True,56,32,1,0,1,1,1,FDP,1,1,0,8,'
                f'101,False,Anna,Looser,0,,0,1\n'
                f'unknown,{entity},True,56,32,1,0,1,2,2,CVP,1,2,0,6,'
                f'201,True,Carol,Winner,2,,2,0\n'
            )
        csv = csv.encode('utf-8')

        upload = client.get(f'/election/{slug}/upload').follow()
        upload.form['file_format'] = 'internal'
        upload.form['results'] = Upload('data.csv', csv, 'text/plain')
        upload = upload.form.submit()

        assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
