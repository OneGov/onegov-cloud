from datetime import datetime
from onegov.core.custom_json import dumps, loads


def test_custom_json():

    dt = datetime(2015, 6, 25, 12, 0)

    data = {
        'datetime': dt,
        'date': dt.date(),
        'time': dt.time(),
        'generator': (x for x in range(0, 4))
    }

    text = dumps(data)

    assert '__time__@12:00:00' in text
    assert '__date__@2015-06-25' in text
    assert '__datetime__@2015-06-25T12:00:00' in text
    assert '[0, 1, 2, 3]' in text

    data['generator'] = [x for x in range(0, 4)]
    assert loads(text) == data
