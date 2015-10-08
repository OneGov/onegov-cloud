import pytest

from onegov.core.csv import (
    match_headers,
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
