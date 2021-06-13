from onegov.core.utils import Bunch
from onegov.election_day.utils import get_parameter
from pytest import raises


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
