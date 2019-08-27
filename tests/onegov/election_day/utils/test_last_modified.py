from datetime import datetime
from mock import Mock
from onegov.election_day.utils import add_last_modified_header


def test_add_last_modified_header():
    response = Mock()

    add_last_modified_header(response, datetime(2011, 12, 31, 12, 1))
    assert str(response.method_calls[0]) \
        == "call.headers.add('Last-Modified', 'Sat, 31 Dec 2011 12:01:00 GMT')"
