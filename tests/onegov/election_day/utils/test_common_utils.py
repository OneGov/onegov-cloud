from datetime import date
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import Vote
from onegov.core.utils import Bunch
from onegov.election_day.models import Notification
from onegov.election_day.models import WebsocketNotification
from onegov.election_day.utils import get_last_notified
from onegov.election_day.utils import get_parameter
from pytest import raises


def test_get_last_notified(session):
    vote = Vote(
        title="Vote",
        domain='federation',
        date=date(2011, 1, 1),
    )
    election = Election(
        title="election",
        domain='region',
        date=date(2011, 1, 1),
    )
    compound = ElectionCompound(
        title="Elections",
        domain='canton',
        date=date(2011, 1, 1),
    )

    for model in (vote, election, compound):
        session.add(model)
        session.flush()

        assert get_last_notified(model) is None

        notification = WebsocketNotification()
        notification.update_from_model(model)
        session.add(notification)
        session.flush()

        last_notified = get_last_notified(model)
        assert last_notified is not None

        notification = Notification()
        notification.update_from_model(model)
        session.add(notification)
        session.flush()

        assert get_last_notified(model) == last_notified

        notification = WebsocketNotification()
        notification.update_from_model(model)
        session.add(notification)
        session.flush()

        assert get_last_notified(model) > last_notified


def test_get_param():

    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', float, None)
    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', tuple, None)
    with raises(NotImplementedError):
        get_parameter(Bunch(params={}), 'name', dict, None)

    assert get_parameter(Bunch(params={}), 'name', int, None) is None
    assert get_parameter(Bunch(params={}), 'name', int, 10) == 10
    assert get_parameter(Bunch(params={'name': ''}), 'name', int, 10) == 10
    assert get_parameter(Bunch(params={'name': 5}), 'name', int, 10) == 5
    assert get_parameter(Bunch(params={'name': '5'}), 'name', int, 10) == 5
    assert get_parameter(Bunch(params={'name': '  5 '}), 'name', int, 10) == 5

    assert get_parameter(Bunch(params={}), 'name', list, None) is None
    assert get_parameter(Bunch(params={}), 'name', list, [1, 2]) == [1, 2]
    assert get_parameter(Bunch(params={'name': ''}), 'name', list, [1, 2]) \
        == [1, 2]
    assert get_parameter(Bunch(params={'name': 'a,b'}), 'name', list, None) \
        == ['a', 'b']
    assert get_parameter(Bunch(params={'name': '  a,  b '}), 'name', list, 1) \
        == ['a', 'b']

    assert get_parameter(Bunch(params={}), 'name', bool, None) is None
    assert get_parameter(Bunch(params={}), 'name', bool, False) is False
    assert get_parameter(Bunch(params={'name': ''}), 'name', bool, None) \
        is None
    assert get_parameter(Bunch(params={'name': '1'}), 'name', bool, None) \
        is True
    assert get_parameter(Bunch(params={'name': 'True'}), 'name', bool, None) \
        is True
    assert get_parameter(Bunch(params={'name': 'trUe'}), 'name', bool, None) \
        is True
    assert get_parameter(Bunch(params={'name': '  1 '}), 'name', bool, None) \
        is True
