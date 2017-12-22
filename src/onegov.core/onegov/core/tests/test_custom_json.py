import pytest

from datetime import datetime
from decimal import Decimal
from onegov.core.custom import json


def test_custom_json():

    dt = datetime(2015, 6, 25, 12, 0)

    data = {
        'datetime': dt,
        'date': dt.date(),
        'time': dt.time(),
        'generator': (x for x in range(0, 4)),
        'decimal': Decimal('3.1415926')
    }

    text = json.dumps(data)

    assert '__time__@12:00:00' in text
    assert '__date__@2015-06-25' in text
    assert '__datetime__@2015-06-25T12:00:00' in text
    assert '__decimal__@3.1415926' in text
    assert '[0,1,2,3]' in text

    data['generator'] = [x for x in range(0, 4)]
    assert json.loads(text) == data


def test_not_serializable():
    with pytest.raises(TypeError):
        json.dumps({'x': object()})


def test_sort_keys():
    data = {'c': 1, 'a': 2}
    assert json.dumps(data, sort_keys=True) == '{"a":2,"c":1}'


def test_deprecated_custom_json():
    from onegov.core import custom_json
    assert custom_json.dumps is json.dumps
