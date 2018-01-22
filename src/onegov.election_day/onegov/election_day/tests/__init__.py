from datetime import date
from unittest.mock import Mock
from webtest.forms import Upload


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
            return text.interpolate()

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


def upload_vote(client, create=True):
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
        '1711,3821,7405,16516,80,1\n'
        '1706,811,1298,3560,18,\n'
        '1709,1096,2083,5245,18,1\n'
        '1704,599,1171,2917,17,\n'
        '1701,3049,5111,13828,54,3\n'
        '1702,2190,3347,9687,60,\n'
        '1703,1497,2089,5842,15,1\n'
        '1708,1211,2350,5989,17,\n'
        '1707,1302,1779,6068,17,\n'
        '1710,651,743,2016,8,\n'
        '1705,307,522,1289,10,1\n'
    )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form['type'] = 'simple'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
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
        'entity_id,'
        'entity_elegible_voters,'
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
        'election_counted_entities,'
        'election_total_entities,'
        'election_absolute_majority,'
        'list_name,'
        'list_id,'
        'list_number_of_mandates,'
        'list_votes,'
        'list_connection,'
        'list_connection_parent,'
        'candidate_party,'
        '\n'
    )
    if canton == 'gr':
        csv += (
            "unknown,3503,56,25,0,4,1,0,1,True,"
            "Engler,Stefan,20,1,125,,,,,,,,\n"
        )
        csv += (
            "unknown,3503,56,25,0,4,1,0,2,True,"
            "Schmid,Martin,18,1,125,,,,,,,,\n"
        )
    if canton == 'zg':
        csv += (
            "unknown,1711,56,25,0,4,1,0,1,True,"
            "Engler,Stefan,20,1,125,,,,,,,,\n"
        )
        csv += (
            "unknown,1710,56,25,0,4,1,0,2,True,"
            "Schmid,Martin,18,1,125,,,,,,,,\n"
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

    csv = (
        'election_status,'
        'entity_id,'
        'entity_elegible_voters,'
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
        'election_counted_entities,'
        'election_total_entities,'
        'election_absolute_majority,'
        'candidate_party,'
        'panachage_votes_from_list_1,'
        'panachage_votes_from_list_2'
        '\n'
    )
    if canton == 'gr':
        csv += (
            "unknown,3503,56,32,1,0,1,1,1,FDP,1,1,0,8,"
            "101,False,Casanova,Angela,0,1,125,,,0,1\n"
        )
        csv += (
            "unknown,3503,56,32,1,0,1,2,2,CVP,1,2,0,6,"
            "201,False,Caluori,Corina,2,1,125,,,2,0\n"
        )
    elif canton == 'zg':
        csv += (
            "unknown,1711,56,32,1,0,1,1,1,FDP,1,1,0,8,"
            "101,False,Casanova,Angela,0,1,125,,,0,1\n"
        )
        csv += (
            "unknown,1711,56,32,1,0,1,2,2,CVP,1,2,0,5,"
            "201,False,Caluori,Corina,2,1,125,,,2,0\n"
        )
    csv = csv.encode('utf-8')

    upload = client.get('/election/proporz-election/upload').follow()
    upload.form['file_format'] = 'internal'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_party_results(client, create=True, canton='gr'):
    csv_parties = (
        "year,total_votes,name,color,mandates,votes\n"
        "2015,11270,BDP,,1,60387\n"
        "2015,11270,CVP,,1,49117\n"
        "2015,11270,FDP,,0,35134\n"
    ).encode('utf-8')

    upload = client.get('/election/proporz-election/upload-party-results')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()
