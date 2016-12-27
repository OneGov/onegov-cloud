import json
import textwrap
import pytest

from datetime import date, datetime, timezone
from freezegun import freeze_time
from onegov.ballot import Election, Vote
from onegov.election_day.models import ArchivedResult
from onegov.election_day.models import Notification
from onegov.election_day.models import Principal
from onegov.election_day.models import SmsNotification
from onegov.election_day.models import Subscriber
from onegov.election_day.models import WebhookNotification
from onegov.election_day.models.principal import cantons
from onegov.election_day.tests import DummyRequest
from time import sleep
from unittest.mock import Mock, patch


def test_principal_load():
    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        logo:
        canton: zg
        color: '#000'
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

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Kanton Zug
        logo:
        canton: zg
        color: '#000'
        base: 'http://www.zg.ch'
        analytics: "<script type=\\"text/javascript\\"></script>"
        use_maps: false
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

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        logo:
        municipality: '351'
        color: '#000'
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

    principal = Principal.from_yaml(textwrap.dedent("""
        name: Stadt Bern
        logo:
        municipality: '351'
        color: '#000'
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


def test_principal_municipalities():
    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert principal.municipalities == {}

    principal = Principal(name='Zug', canton='zg', logo=None, color=None)

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
        2009: municipalities,
        2010: municipalities,
        2011: municipalities,
        2012: municipalities,
        2013: municipalities,
        2014: municipalities,
        2015: municipalities,
        2016: municipalities,
        2017: municipalities,
    }

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        for year in range(2009, 2018):
            assert principal.municipalities[year]


def test_principal_districts():
    principal = Principal(name='Zug', canton='zg', logo=None, color=None)
    assert principal.districts == {}

    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )

    assert principal.districts == {
        2009: {1059: {'name': 'Kriens'}},
        2010: {1059: {'name': 'Kriens'}},
        2011: {1059: {'name': 'Kriens'}},
        2012: {1059: {'name': 'Kriens'}},
        2013: {1059: {'name': 'Kriens'}},
        2014: {1059: {'name': 'Kriens'}},
        2015: {1059: {'name': 'Kriens'}},
        2016: {1059: {'name': 'Kriens'}},
        2017: {1059: {'name': 'Kriens'}},
    }

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    districts = {
        1: {'name': 'Innere Stadt'},
        2: {'name': 'Länggasse/Felsenau'},
        3: {'name': 'Mattenhof/Weissenbühl'},
        4: {'name': 'Kirchenfeld/Schosshalde'},
        5: {'name': 'Breitenrain/Lorraine'},
        6: {'name': 'Bümpliz/Bethlehem'},
    }
    assert principal.districts == {
        2012: districts,
        2013: districts,
        2014: districts,
        2015: districts,
        2016: districts,
        2017: districts
    }


def test_principal_entities():
    principal = Principal(name='Zug', canton='zg', logo=None, color=None)
    assert principal.entities == principal.municipalities

    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )
    assert principal.entities == principal.districts

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert principal.entities == principal.districts


def test_principal_years_available():
    principal = Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    )
    assert not principal.is_year_available(2000)
    assert not principal.is_year_available(2016)
    assert not principal.is_year_available(2000, map_required=False)
    assert principal.is_year_available(2016, map_required=False)

    principal = Principal(
        name='Bern', municipality='351', logo=None, color=None
    )
    assert not principal.is_year_available(2000)
    assert principal.is_year_available(2016)
    assert not principal.is_year_available(2000, map_required=False)
    assert principal.is_year_available(2016, map_required=False)

    for canton in cantons:
        principal = Principal(
            name=canton, canton=canton, logo=None, color=None
        )

        for year in range(2009, 2013):
            assert not principal.is_year_available(year)
        for year in range(2013, 2017):
            assert principal.is_year_available(year)
        for year in range(2009, 2017):
            assert principal.is_year_available(year, map_required=False)

        if canton in ['gr', 'sg', 'sz', 'zg']:
            assert principal.is_year_available(2017)
            assert principal.is_year_available(2017, map_required=False)
        else:
            assert not principal.is_year_available(2017)
            assert principal.is_year_available(2017, map_required=False)


def test_principal_notifications_enabled():
    assert Principal(
        name='Kriens', municipality='1059', logo=None, color=None
    ).notifications == False

    assert Principal(
        name='Kriens', municipality='1059', logo=None, color=None,
        webhooks={'a', 'b'}
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059', logo=None, color=None,
        sms_notification='https://wab.kriens.ch'
    ).notifications == True

    assert Principal(
        name='Kriens', municipality='1059', logo=None, color=None,
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

    result.answer = 'rejected'
    assert result.answer == 'rejected'

    result.nays_percentage = 20.5
    assert result.nays_percentage == 20.5

    result.yeas_percentage = 79.5
    assert result.yeas_percentage == 79.5

    result.counted = True
    assert result.counted == True

    assert result.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
    }

    assert result.title == 'title'

    result.title_translations['en'] = 'title'
    assert result.title_translations == {'en': 'title', 'de_CH': 'title'}

    assert result.name == 'name'
    assert result.title_prefix(session=session) == ''

    result.domain = 'municipality'
    assert result.title_prefix(session=session) == result.name

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
    assert copied.meta == {
        'answer': 'rejected',
        'nays_percentage': 20.5,
        'yeas_percentage': 79.5,
        'counted': True,
    }
    assert copied.shortcode == 'shortcode'


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

            notification.trigger(DummyRequest(), election)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'progress': {'counted': 0, 'total': 0},
                'title': {'de_CH': 'Election'},
                'type': 'election',
                'url': 'Election/election'
            }

            notification.trigger(DummyRequest(), vote)
            sleep(5)
            assert urlopen.called

            headers = urlopen.call_args[0][0].headers
            data = urlopen.call_args[0][1]
            assert headers['Content-type'] == 'application/json; charset=utf-8'
            assert headers['Content-length'] == len(data)

            assert json.loads(data.decode('utf-8')) == {
                'answer': '',
                'date': '2011-01-01',
                'domain': 'federation',
                'last_modified': '2008-01-01T00:00:00+00:00',
                'nays_percentage': 100.0,
                'progress': {'counted': 0.0, 'total': 0.0},
                'title': {'de_CH': 'Vote'},
                'type': 'vote',
                'url': 'Vote/vote',
                'yeas_percentage': 0.0
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
