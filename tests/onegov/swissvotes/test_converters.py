from onegov.swissvotes.converters import policy_area_converter


def test_policy_area_converter():
    converter = policy_area_converter

    # assert converter.decode(['']) == [None]
    # assert converter.decode([None]) == [None]

    assert converter.decode(['']) == []
    assert converter.decode([None]) == []
    assert converter.decode([]) == []
    assert converter.decode(['1']) == ['1']
    assert converter.decode(['1', '4']) == ['1', '4']
    assert converter.decode(['1', '4', '8', '10']) == ['1', '4', '8', '10']
    assert converter.decode(['1', '', '8', '22']) == ['1', '8', '22']
    assert converter.decode(['1', '', '', '22']) == ['1', '22']

    assert converter.encode(None) == []
    assert converter.encode('') == []
    assert converter.encode([]) == []
    assert converter.encode(['1']) == ['1']
    assert converter.encode(['21']) == ['21']
    assert converter.encode(['1', '4']) == ['1', '4']
    assert converter.encode(['1', '4', '8', '10']) == ['1', '4', '8', '10']

    assert converter.decode(['1.12']) == ['1.12']
    assert converter.decode(['1.12.121']) == ['1.12.121']
    assert converter.decode(['4.42.421']) == ['4.42.421']
    assert converter.decode(['10.102']) == ['10.102']
    assert converter.decode(['10.103.1035']) == ['10.103.1035']
    assert converter.decode(['12.125.1251']) == ['12.125.1251']
    assert converter.decode(['1.12.123.1231']) == ['1.12.123.1231']

    # invalid policy area(s)
    assert converter.decode(['z']) == []
    assert converter.decode(['1,12,121']) == []
    assert converter.decode(['1.32.121']) == []
    assert converter.decode(['4.92.421']) == []
    assert converter.decode(['a.a2.a21']) == []
