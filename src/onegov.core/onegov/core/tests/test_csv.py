import pytest

from io import BytesIO
from onegov.core.csv import (
    CSVFile,
    detect_encoding,
    match_headers,
    normalize_header,
    parse_header
)

from onegov.core.errors import (
    AmbiguousColumnsError,
    DuplicateColumnNames,
    MissingColumnsError
)


def test_parse_header():
    assert parse_header("   Firtst name;  LastNAME; Designation")\
        == ['firtst name', 'lastname', 'designation']
    assert parse_header("a") == ['a']
    assert parse_header("") == []
    assert parse_header("a,b,c;d") == ['a', 'b', 'c;d']


def test_normalize_header():
    assert normalize_header("") == ""
    assert normalize_header("Wääh") == "waah"
    assert normalize_header(" a   b\tc ") == "a b c"


def test_detect_encoding():
    assert detect_encoding(BytesIO(b''))['encoding'] is None

    assert detect_encoding(BytesIO('jöö'.encode('ISO-8859-2')))['encoding'] \
        == 'ISO-8859-2'

    assert detect_encoding(BytesIO('jöö'.encode('utf-8')))['encoding'] \
        == 'utf-8'


def test_simple_csv_file():
    data = (
        b'Datum, Reale Temperatur, Gef\xfchlte Temperatur\n'
        b'01.01.2015, 5, k\xfchl\n'
        b'02.01.2015, 0, kalt'
    )

    csv = CSVFile(
        BytesIO(data), ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    )

    csv.headers == ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    list(csv.lines) == [
        csv.rowtype(
            rownumber=1,
            datum='01.01.2015',
            reale_temperatur='5',
            gefuhlte_temperatur='kühl'
        ),
        csv.rowtype(
            rownumber=2,
            datum='01.01.2015',
            reale_temperatur='5',
            gefuhlte_temperatur='kalt'
        ),
    ]


def test_match_headers_duplicate():
    with pytest.raises(DuplicateColumnNames):
        match_headers(['first_name', 'first_name'], expected=None)


def test_match_headers_order():
    matches = match_headers(
        headers=['firtst name', 'lastname'],
        expected=('first_name', 'last_name')
    )
    assert matches == ['first_name', 'last_name']

    matches = match_headers(
        headers=['firtst name', 'lastname'],
        expected=('last_name', 'first_name')
    )
    assert matches == ['first_name', 'last_name']


def test_match_headers_case():
    assert match_headers(['a', 'b'], expected=('A', 'B')) == ['A', 'B']
    assert match_headers(['a', 'b'], expected=('b', 'a')) == ['a', 'b']


def test_match_headers_missing():
    with pytest.raises(MissingColumnsError) as e:
        match_headers(['a', 'b'], expected=('a', 'c'))
    assert e.value.columns == ['c']

    with pytest.raises(MissingColumnsError) as e:
        match_headers(['ab', 'ba'], expected=('a', 'b'))
    assert e.value.columns == ['a', 'b']

    with pytest.raises(MissingColumnsError) as e:
        match_headers(['first', 'second'], expected=('first', 'third'))
    assert e.value.columns == ['third']

    assert match_headers(['a1', 'b2'], expected=('a1', 'c2')) == ['a1', 'c2']

    assert match_headers(['first', 'second'], expected=('first', 'sekond')) \
        == ['first', 'sekond']

    assert match_headers(['a', 'b', 'c'], expected=('a', 'c')) \
        == ['a', 'b', 'c']


def test_match_headers_ambiguous():
    with pytest.raises(AmbiguousColumnsError) as e:
        match_headers(['abcd', 'bcde'], expected=('bcd', ))

    assert list(e.value.columns.keys()) == ['bcd']
    assert set(e.value.columns['bcd']) == {'abcd', 'bcde'}
