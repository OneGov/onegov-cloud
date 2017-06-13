import json
import textwrap
import pytest

from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot import Election
from onegov.ballot import Vote
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import DataSource
from onegov.election_day.models import DataSourceItem
from onegov.election_day.models import Notification
from onegov.election_day.models import Principal
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import Subscriber
from onegov.election_day.models import WebhookNotification
from onegov.election_day.models.principal import cantons
from onegov.election_day.tests import DummyRequest
from time import sleep
from unittest.mock import Mock, patch


SUPPORTED_YEARS = list(range(2002, 2017 + 1))

SUPPORTED_YEARS_MAP = list(range(2013, 2017 + 1))
SUPPORTED_YEARS_NO_MAP = list(set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP))

SUPPORTED_YEARS_MAP_SG = list(range(2004, 2017 + 1))
SUPPORTED_YEARS_NO_MAP_SG = list(
    set(SUPPORTED_YEARS) - set(SUPPORTED_YEARS_MAP_SG)
)


def test_principal_load():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        canton: zg
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}
    assert principal.open_data == {}

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        canton: zg
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        use_maps: false
        wabsti_import: true
        fetch:
            steinhausen:
                - municipality
            baar:
                - municipality
        webhooks:
            'http://abc.com/1':
            'http://abc.com/2':
                My-Header: My-Value
        sms_notification: 'https://wab.zg.ch'
        pdf_signing:
            url: 'http://abc.com/3'
            login: user
            password: pass
            reason: election and vote results
        open_data:
            id: kanton-zug
            name: Staatskanzlei Kanton Zug
            mail: info@zg.ch
    """))

    assert principal.name == 'Kanton Zug'
    assert principal.logo is None
    assert principal.canton == 'zg'
    assert principal.municipality is None
    assert principal.color == '#000'
    assert principal.base == 'http://www.zg.ch'
    assert principal.base_domain == 'zg.ch'
    assert principal.analytics == '<script type="text/javascript"></script>'
    assert principal.use_maps is True
    assert principal.domain is 'canton'
    assert list(principal.available_domains.keys()) == ['federation', 'canton']
    assert principal.fetch == {
        'steinhausen': ['municipality'],
        'baar': ['municipality']
    }
    assert principal.webhooks == {
        'http://abc.com/1': None,
        'http://abc.com/2': {
            'My-Header': 'My-Value'
        }
    }
    assert principal.sms_notification == 'https://wab.zg.ch'
    assert principal.wabsti_import == True
    assert principal.pdf_signing == {
        'url': 'http://abc.com/3',
        'login': 'user',
        'password': 'pass',
        'reason': 'election and vote results'
    }
    assert principal.open_data == {
        'id': 'kanton-zug',
        'name': 'Staatskanzlei Kanton Zug',
        'mail': 'info@zg.ch'
    }

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        municipality: '351'
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is False
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        municipality: '351'
        use_maps: true
    """))

    assert principal.name == 'Stadt Bern'
    assert principal.logo is None
    assert principal.canton is None
    assert principal.municipality == '351'
    assert principal.color == '#000'
    assert principal.base is None
    assert principal.base_domain is None
    assert principal.analytics is None
    assert principal.use_maps is True
    assert principal.domain is 'municipality'
    assert list(principal.available_domains.keys()) == [
        'federation', 'canton', 'municipality'
    ]
    assert principal.fetch == {}
    assert principal.webhooks == {}
    assert principal.sms_notification == None
    assert principal.wabsti_import == False
    assert principal.pdf_signing == {}


def test_principal_municipalities():
    # Bern (municipalitites have districts, not municipalitites)
    principal = Principal(name='Bern', municipality='351')
    assert principal.municipalities == {}

    # Canton Zug
    principal = Principal(name='Zug', canton='zg')
    municipalities = {
        1701: {'name': 'Baar'},
        1702: {'name': 'Cham'},
        1703: {'name': 'Hünenberg'},
        1704: {'name': 'Menzingen'},
        1705: {'name': 'Neuheim'},
        1706: {'name': 'Oberägeri'},
        1707: {'name': 'Risch'},
        1708: {'name': 'Steinhausen'},
        1709: {'name': 'Unterägeri'},
        1710: {'name': 'Walchwil'},
        1711: {'name': 'Zug'},
    }
    assert principal.municipalities == {
        year: municipalities for year in SUPPORTED_YEARS
    }

    # All cantons
    for canton in cantons:
        principal = Principal(name=canton, canton=canton)
        for year in SUPPORTED_YEARS:
            assert principal.municipalities[year]


def test_principal_districts():
    # Canton Zug (cantons have municipalities, not districts)
    principal = Principal(name='Zug', canton='zg')
    assert principal.districts == {}

    # Municipality without districts
    principal = Principal(name='Kriens', municipality='1059')
    assert principal.districts == {
        year: {1059: {'name': 'Kriens'}} for year in SUPPORTED_YEARS
    }

    # Municipality with districts
    principal = Principal(name='Bern', municipality='351')
    districts = {
        1: {'name': 'Innere Stadt'},
        2: {'name': 'Länggasse/Felsenau'},
        3: {'name': 'Mattenhof/Weissenbühl'},
        4: {'name': 'Kirchenfeld/Schosshalde'},
        5: {'name': 'Breitenrain/Lorraine'},
        6: {'name': 'Bümpliz/Bethlehem'},
    }
    assert principal.districts == {year: districts for year in SUPPORTED_YEARS}


def test_principal_entities():
    principal = Principal(name='Zug', canton='zg')
    assert principal.entities == principal.municipalities

    principal = Principal(name='Kriens', municipality='1059')
    assert principal.entities == principal.districts

    principal = Principal(name='Bern', municipality='351')
    assert principal.entities == principal.districts


def test_principal_years_available():
    # Municipality without districts/map
    principal = Principal(name='Kriens', municipality='1059')
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2000, map_required=False)
    for year in SUPPORTED_YEARS:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)

    # Municipality with districts/map
    principal = Principal(name='Bern', municipality='351')
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2000, map_required=False)
    for year in SUPPORTED_YEARS_NO_MAP:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)
    for year in SUPPORTED_YEARS_MAP:
        assert principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)

    # Cantons
    for canton in cantons - {'sg'}:
        principal = Principal(name=canton, canton=canton)

        for year in SUPPORTED_YEARS_NO_MAP:
            assert not principal.is_year_available(year)
            assert principal.is_year_available(year, map_required=False)
        for year in SUPPORTED_YEARS_MAP:
            assert principal.is_year_available(year)
            assert principal.is_year_available(year, map_required=False)

    # Canton SG
    principal = Principal(name='sg', canton='sg')
    for year in SUPPORTED_YEARS_NO_MAP_SG:
        assert not principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)
    for year in SUPPORTED_YEARS_MAP_SG:
        assert principal.is_year_available(year)
        assert principal.is_year_available(year, map_required=False)


def test_principal_notifications_enabled():
    assert Principal(
        name='Kriens', municipality='1059'
    ).notifications == False

    assert Principal(
        name='Kriens', municipality='1059',
        webhooks={'a', 'b'}
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059',
        sms_notification='https://wab.kriens.ch'
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059',
        webhooks={'a', 'b'}, sms_notification='https://wab.kriens.ch'
    ).notifications == True


def test_archived_result(session):
    result = ArchivedResult()
    result.date = date(2007, 1, 1)
    result.last_result_change = datetime(2007, 1, 1, 0, 0, tzinfo=timezone.utc)
    result.schema = 'schema'
    result.url = 'url'
    result.title = 'title'
    result.domain = 'canton'
    result.type = 'vote'
    result.name = 'name'

    session.add(result)
    session.flush()

    assert result.id

    assert result.progress == (0, 0)
    result.total_entities = 10
    assert result.progress == (0, 10)
    result.counted_entities = 5
    assert result.progress == (5, 10)

    result.elected_candidates = [('Joe', 'Quimby')]
    assert result.elected_candidates == [('Joe', 'Quimby')]

    result.answer = 'rejected'
    assert result.answer == 'rejected'

    result.nays_percentage = 20.5
    assert result.nays_percentage == 20.5

    result.yeas_percentage = 79.5
    assert result.yeas_percentage == 79.5

    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0

    request = DummyRequest()
    assert result.display_answer(request) == 'rejected'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    result.counted = True
    assert result.counted == True

    assert result.completed == False
    result.completed = True
    assert result.completed == True

    assert result.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
        'completed': True,
        'elected_candidates': [('Joe', 'Quimby')]
    }

    assert result.title == 'title'

    result.title_translations['en'] = 'title'
    assert result.title_translations == {'en': 'title', 'de_CH': 'title'}

    assert result.name == 'name'
    assert result.title_prefix == ''

    result.domain = 'municipality'
    assert result.title_prefix == result.name

    result.shortcode = 'shortcode'

    copied = ArchivedResult()
    copied.copy_from(result)

    assert copied.date == date(2007, 1, 1)
    assert copied.last_result_change == datetime(2007, 1, 1, 0, 0,
                                                 tzinfo=timezone.utc)
    assert copied.schema == 'schema'
    assert copied.url == 'url'
    assert copied.title == 'title'
    assert copied.title_translations == {'en': 'title', 'de_CH': 'title'}
    assert copied.domain == 'municipality'
    assert copied.type == 'vote'
    assert copied.name == 'name'
    assert copied.total_entities == 10
    assert copied.counted_entities == 5
    assert copied.progress == (5, 10)
    assert copied.answer == 'rejected'
    assert copied.nays_percentage == 20.5
    assert copied.yeas_percentage == 79.5
    assert copied.counted == True
    assert copied.completed == True
    assert copied.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
        'completed': True,
        'elected_candidates': [('Joe', 'Quimby')]
    }
    assert copied.shortcode == 'shortcode'


def test_archived_result_local_results(session):
    result = ArchivedResult()

    assert result.answer == ''
    assert result.nays_percentage == 100.0
    assert result.yeas_percentage == 0.0

    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0

    request = DummyRequest()
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    result.answer = 'accepted'
    result.yeas_percentage = 79.5
    result.nays_percentage = 20.5

    assert result.meta == {
        'answer': 'accepted',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
    }

    assert result.answer == 'accepted'
    assert result.nays_percentage == 20.5
    assert result.yeas_percentage == 79.5

    assert result.local_answer == ''
    assert result.local_nays_percentage == 100.0
    assert result.local_yeas_percentage == 0.0

    request = DummyRequest()
    assert result.display_answer(request) == 'accepted'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == ''
    assert result.display_nays_percentage(request) == 100.0
    assert result.display_yeas_percentage(request) == 0.0

    result.local_answer = 'rejected'
    result.local_yeas_percentage = 40.0
    result.local_nays_percentage = 60.0

    assert result.meta == {
        'answer': 'accepted',
        'yeas_percentage': 79.5,
        'nays_percentage': 20.5,
        'local': {
            'answer': 'rejected',
            'yeas_percentage': 40.0,
            'nays_percentage': 60.0,
        }
    }

    assert result.answer == 'accepted'
    assert result.nays_percentage == 20.5
    assert result.yeas_percentage == 79.5

    assert result.local_answer == 'rejected'
    assert result.local_nays_percentage == 60.0
    assert result.local_yeas_percentage == 40.0

    request = DummyRequest()
    assert result.display_answer(request) == 'accepted'
    assert result.display_nays_percentage(request) == 20.5
    assert result.display_yeas_percentage(request) == 79.5

    request.app.principal.domain = 'municipality'
    assert result.display_answer(request) == 'rejected'
    assert result.display_nays_percentage(request) == 60.0
    assert result.display_yeas_percentage(request) == 40.0


def test_notification(session):
    notification = Notification()
    notification.action = 'action'
    notification.last_change = datetime(2007, 1, 1, 0, 0, tzinfo=timezone.utc)

    session.add(notification)
    session.flush()

    notification = session.query(Notification).one()
    assert notification.id
    assert notification.action == 'action'
    assert notification.last_change == datetime(2007, 1, 1, 0, 0,
                                                tzinfo=timezone.utc)
    assert notification.election_id is None
    assert notification.vote_id is None

    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        session.flush()
        election = session.query(Election).one()

        notification = Notification()
        notification.update_from_model(election)
        assert notification.election_id == election.id
        assert notification.vote_id == None
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

    with freeze_time("2009-01-01 00:00"):
        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        session.flush()
        vote = session.query(Vote).one()

        notification = Notification()
        notification.update_from_model(vote)
        assert notification.election_id == None
        assert notification.vote_id == vote.id
        assert notification.last_change == datetime(2009, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

    with pytest.raises(NotImplementedError):
        notification.trigger(DummyRequest(), election)
    with pytest.raises(NotImplementedError):
        notification.trigger(DummyRequest(), vote)


def test_webhook_notification(session):
    with freeze_time("2008-01-01 00:00"):
        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        notification = WebhookNotification()
        notification.trigger(DummyRequest(), election)

        assert notification.action == 'webhooks'
        assert notification.election_id == election.id
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        notification.trigger(DummyRequest(), vote)

        assert notification.action == 'webhooks'
        assert notification.vote_id == vote.id
        assert notification.last_change == datetime(2008, 1, 1, 0, 0,
                                                    tzinfo=timezone.utc)

        with patch('urllib.request.urlopen') as urlopen:
            request = DummyRequest()
            request.app.principal.webhooks = {'http://abc.com/1': None}

            notification.trigger(request, election)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'elected': [],
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Election'},
                'type': 'election',
                'url': 'Election/election'
            }

            notification.trigger(request, vote)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'answer': None,
                'completed': False,
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'nays_percentage': None,
                'progress': {'counted': 0.0, 'total': 0.0},
                'title': {'de_CH': 'Vote'},
                'type': 'vote',
                'url': 'Vote/vote',
                'yeas_percentage': None
            }


def test_sms_notification(request, election_day_app, session):
    with freeze_time("2008-01-01 00:00"):
        election_day_app.send_sms = Mock()
        election_day_app.principal.sms_notification = 'https://wab.ch.ch'

        session.add(
            Election(
                title="Election",
                domain='federation',
                type='majorz',
                date=date(2011, 1, 1)
            )
        )
        election = session.query(Election).one()

        session.add(
            Vote(
                title="Vote",
                domain='federation',
                date=date(2011, 1, 1),
            )
        )
        vote = session.query(Vote).one()

        request = DummyRequest(app=election_day_app, session=session)
        freezed = datetime(2008, 1, 1, 0, 0, tzinfo=timezone.utc)

        notification = SmsNotification()
        notification.trigger(request, election)
        assert notification.action == 'sms'
        assert notification.election_id == election.id
        assert notification.last_change == freezed
        assert election_day_app.send_sms.call_count == 0

        notification = SmsNotification()
        notification.trigger(request, vote)
        assert notification.action == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_change == freezed
        assert election_day_app.send_sms.call_count == 0

        session.add(Subscriber(phone_number='+41791112233', locale='en'))
        session.add(Subscriber(phone_number='+41791112233', locale='de_CH'))

        notification = SmsNotification()
        # request.app.session().query(Subscriber).one()
        notification.trigger(request, election)

        assert notification.action == 'sms'
        assert notification.election_id == election.id
        assert notification.last_change == freezed
        assert election_day_app.send_sms.call_count == 2
        assert election_day_app.send_sms.call_args_list[0][0] == (
            '+41791112233', 'New results are available on https://wab.ch.ch'
        )
        assert election_day_app.send_sms.call_args_list[1][0] == (
            '+41791112233', 'Neue Resultate verfügbar auf https://wab.ch.ch'
        )

        notification = SmsNotification()
        notification.trigger(request, vote)

        assert notification.action == 'sms'
        assert notification.vote_id == vote.id
        assert notification.last_change == freezed
        assert election_day_app.send_sms.call_count == 4


def test_subscriber(session):
    subscriber = Subscriber()
    subscriber.phone_number = '+41791112233'
    subscriber.locale = 'de_CH'

    session.add(subscriber)
    session.flush()

    subscriber = session.query(Subscriber).one()
    assert subscriber.id
    assert subscriber.phone_number == '+41791112233'
    assert subscriber.locale == 'de_CH'


def test_data_source(session):
    session.add(DataSource(name='ds_vote', type='vote'))
    session.add(DataSource(name='ds_majorz', type='majorz'))
    session.add(DataSource(name='ds_proporz', type='proporz'))
    session.flush()

    ds_vote = session.query(DataSource).filter_by(type='vote').one()
    assert ds_vote.name == 'ds_vote'
    assert ds_vote.label == 'Vote'
    assert ds_vote.token

    ds_majorz = session.query(DataSource).filter_by(type='majorz').one()
    assert ds_majorz.name == 'ds_majorz'
    assert ds_majorz.label == 'Election based on the simple majority system'
    assert ds_majorz.token

    ds_proporz = session.query(DataSource).filter_by(type='proporz').one()
    assert ds_proporz.name == 'ds_proporz'
    assert ds_proporz.label == 'Election based on proportional representation'
    assert ds_proporz.token

    dt = date(2015, 6, 14)
    session.add(Vote(title='v', domain='canton', date=dt))
    session.add(Election(title='m', type='majorz', domain='canton', date=dt))
    session.add(Election(title='p', type='proporz', domain='canton', date=dt))
    session.flush()

    vote = session.query(Vote).one()
    majorz = session.query(Election).filter_by(type='majorz').one()
    proporz = session.query(Election).filter_by(type='proporz').one()

    assert ds_vote.query_candidates().one() == vote
    assert ds_majorz.query_candidates().one() == majorz
    assert ds_proporz.query_candidates().one() == proporz

    ds_vote.items.append(
        DataSourceItem(district='1', number='11', vote_id=vote.id)
    )
    ds_majorz.items.append(
        DataSourceItem(district='2', number='22', election_id=majorz.id)
    )
    ds_proporz.items.append(
        DataSourceItem(district='3', number='33', election_id=proporz.id)
    )
    session.flush()

    item = ds_vote.items.one()
    assert item.item == vote
    assert item.name == 'v'
    assert item.district == '1'
    assert item.number == '11'

    item = ds_majorz.items.one()
    assert item.item == majorz
    assert item.name == 'm'
    assert item.district == '2'
    assert item.number == '22'

    item = ds_proporz.items.one()
    assert item.item == proporz
    assert item.name == 'p'
    assert item.district == '3'
    assert item.number == '33'
