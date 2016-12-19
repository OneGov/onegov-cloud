from datetime import date
from unittest.mock import Mock
from webtest.forms import Upload


class DummyPrincipal(object):
    name = 'name'
    webhooks = []
    sms_notification = None


class DummyApp(object):
    def __init__(self, session=None, application_id='application_id'):
        self._session = session
        self.application_id = application_id

    def session(self):
        return self._session

    principal = DummyPrincipal()


class DummyRequest(object):

    def __init__(self, session=None, app=None, locale='de',
                 is_logged_in=False):
        self.includes = []
        self.session = session
        self._app = app
        self.locale = locale
        self.is_logged_in = is_logged_in
        if app and session:
            app.session = Mock(return_value=session)

    def link(self, model, name=''):
        return '{}/{}'.format(
            model.__class__.__name__, name or getattr(model, 'id', 'archive')
        )

    @property
    def app(self):
        return self._app or DummyApp(session=self.session)

    def translate(self, text):
        return text.interpolate()

    def include(self, resource):
        self.includes.append(resource)
        self.includes = list(set(self.includes))


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
        new.form.submit()

    csv = (
        'Bezirk,ID,Name,Ja Stimmen,Nein Stimmen,'
        'Stimmberechtigte,Leere Stimmzettel,Ungültige Stimmzettel\n'
        ',1711,Zug,3821,7405,16516,80,1\n'
        ',1706,Oberägeri,811,1298,3560,18,\n'
        ',1709,Unterägeri,1096,2083,5245,18,1\n'
        ',1704,Menzingen,599,1171,2917,17,\n'
        ',1701,Baar,3049,5111,13828,54,3\n'
        ',1702,Cham,2190,3347,9687,60,\n'
        ',1703,Hünenberg,1497,2089,5842,15,1\n'
        ',1708,Steinhausen,1211,2350,5989,17,\n'
        ',1707,Risch,1302,1779,6068,17,\n'
        ',1710,Walchwil,651,743,2016,8,\n'
        ',1705,Neuheim,307,522,1289,10,1\n'
    )
    csv = csv.encode('utf-8')

    upload = client.get('/vote/vote/upload')
    upload.form['type'] = 'simple'
    upload.form['proposal'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_majorz_election(client, create=True, zg=False):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = 'Majorz Election'
        new.form['date'] = date(2015, 1, 1)
        new.form['mandates'] = 1
        new.form['election_type'] = 'majorz'
        new.form['domain'] = 'federation'
        new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,"
        "Ungueltige Stimmen,Kandidaten-Nr,Gewaehlt,Name,Vorname,Stimmen,"
        "Anzahl Gemeinden\n"
    )
    if zg:
        csv += "2,1711,56,25,0,4,1,0,1,Gewaehlt,Engler,Stefan,20,1 von 125\n"
        csv += "2,1710,56,25,0,4,1,0,2,Gewaehlt,Schmid,Martin,18,1 von 125\n"
    else:
        csv += "2,3503,56,25,0,4,1,0,1,Gewaehlt,Engler,Stefan,20,1 von 125\n"
        csv += "2,3503,56,25,0,4,1,0,2,Gewaehlt,Schmid,Martin,18,1 von 125\n"
    csv = csv.encode('utf-8')

    upload = client.get('/election/majorz-election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload


def upload_proporz_election(client, create=True):
    if create:
        new = client.get('/manage/elections/new-election')
        new.form['election_de'] = 'Proporz Election'
        new.form['date'] = date(2015, 1, 1)
        new.form['mandates'] = 1
        new.form['election_type'] = 'proporz'
        new.form['domain'] = 'federation'
        new.form.submit()

    csv = (
        "Anzahl Sitze,Wahlkreis-Nr,Stimmberechtigte,Wahlzettel,"
        "Ungültige Wahlzettel,Leere Wahlzettel,Leere Stimmen,Listen-Nr,"
        "Partei-ID,Parteibezeichnung,HLV-Nr,ULV-Nr,Anzahl Sitze Liste,"
        "Unveränderte Wahlzettel Liste,Veränderte Wahlzettel Liste,"
        "Kandidatenstimmen unveränderte Wahlzettel,"
        "Zusatzstimmen unveränderte Wahlzettel,"
        "Kandidatenstimmen veränderte Wahlzettel,"
        "Zusatzstimmen veränderte Wahlzettel,Kandidaten-Nr,Gewählt,Name,"
        "Vorname,Stimmen unveränderte Wahlzettel,"
        "Stimmen veränderte Wahlzettel,Stimmen Total aus Wahlzettel,"
        "01 FDP,02 CVP, Anzahl Gemeinden\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,1,19,FDP,1,1,0,0,0,0,0,8,0,101,"
        "nicht gewählt,Casanova,Angela,0,0,0,0,1,1 von 125\n"
    )
    csv += (
        "5,3503,56,32,1,0,1,2,20,CVP,1,2,0,1,0,5,0,0,0,201,"
        "nicht gewählt,Caluori,Corina,1,0,1,2,0,1 von 125\n"
    )
    csv = csv.encode('utf-8')

    csv_parties = (
        "Partei,Sitze,Stimmen\n"
        "BDP,1,60387\n"
        "CVP,1,49117\n"
        "FDP,0,35134\n"
    ).encode('utf-8')

    upload = client.get('/election/proporz-election/upload')
    upload.form['file_format'] = 'sesam'
    upload.form['results'] = Upload('data.csv', csv, 'text/plain')
    upload.form['parties'] = Upload('parties.csv', csv_parties, 'text/plain')
    upload = upload.form.submit()

    assert "Ihre Resultate wurden erfolgreich hochgeladen" in upload
    return upload
