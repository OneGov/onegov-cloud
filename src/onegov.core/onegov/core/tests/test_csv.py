import pytest
import tempfile

from io import BytesIO
from onegov.core import utils
from onegov.core.csv import (
    CSVFile,
    convert_list_of_dicts_to_csv,
    convert_list_of_dicts_to_xlsx,
    convert_xls_to_csv,
    detect_encoding,
    match_headers,
    normalize_header,
    parse_header,
)
from onegov.core.errors import (
    AmbiguousColumnsError,
    DuplicateColumnNamesError,
    EmptyLineInFileError,
    MissingColumnsError,
)
from openpyxl import load_workbook


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
    assert detect_encoding(BytesIO('jöö'.encode('ISO-8859-2'))) == 'cp1252'
    assert detect_encoding(BytesIO('jöö'.encode('utf-8'))) == 'utf-8'

    assert detect_encoding(
        BytesIO('abcdefabcdefabcdefabcdefö'.encode('utf-8'))
    ) == 'utf-8'


def test_simple_csv_file():
    data = (
        b'Datum, Reale Temperatur, Gef\xfchlte Temperatur\n'
        b'01.01.2015, 5, k\xfchl\n'
        b'02.01.2015, 0, kalt'
    )

    csv = CSVFile(
        BytesIO(data), ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    )

    assert list(csv.headers.keys()) == [
        'datum', 'reale_temperatur', 'gefuhlte_temperatur'
    ]
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


@pytest.mark.parametrize("excel_file", [
    utils.module_path('onegov.core', 'tests/fixtures/excel.xls'),
    utils.module_path('onegov.core', 'tests/fixtures/excel.xlsx'),
])
def test_convert_to_csv(excel_file):
    with open(excel_file, 'rb') as f:
        convert_xls_to_csv(f, None)
        convert_xls_to_csv(f, '')
        with pytest.raises(IOError):
            convert_xls_to_csv(f, 'Sheet 3')

        csv = CSVFile(convert_xls_to_csv(f), ['ID', 'Namä', 'Date'])

        assert list(csv.headers.keys()) == ['ID', 'Namä', 'Date']
        assert list(csv.lines) == [
            csv.rowtype(
                rownumber=2,
                id='1',
                nama='Döner',
                date='31.12.2015'
            ),
            csv.rowtype(
                rownumber=3,
                id='2',
                nama='“Cola”',
                date='31.12.2014 12:00'
            )
        ]

        csv = CSVFile(convert_xls_to_csv(f, 'Sheet 2'), ['ID', 'Namä', 'Date'])

        assert list(csv.headers.keys()) == ['ID', 'Namä', 'Date']
        assert list(csv.lines) == [
            csv.rowtype(
                rownumber=2,
                id='1',
                nama='Döner',
                date='31.12.2015'
            ),
            csv.rowtype(
                rownumber=3,
                id='3',
                nama='“Cola”',
                date='31.12.2014 12:00'
            )
        ]


def test_empty_line_csv_file():
    data = (
        b'Datum, Reale Temperatur, Gef\xfchlte Temperatur\n'
        b'\n'
        b'02.01.2015, 0, kalt'
    )

    csv = CSVFile(
        BytesIO(data), ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    )

    csv.headers == ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    with pytest.raises(EmptyLineInFileError):
        list(csv.lines)

    # accept empty lines at the end
    data = (
        b'Datum, Reale Temperatur, Gef\xfchlte Temperatur\n'
        b'02.01.2015, 0, kalt'
        b'\n'
        b'\n'
    )

    csv = CSVFile(
        BytesIO(data), ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    )

    csv.headers == ['datum', 'reale_temperatur', 'gefuhlte_temperatur']
    assert list(csv.lines)


def test_match_headers_duplicate():
    with pytest.raises(DuplicateColumnNamesError):
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


def test_convert_list_of_dicts_to_csv():
    data = [
        {
            'first_name': 'Dick',
            'last_name': 'Cheney'
        },
        {
            'first_name': 'Donald',
            'last_name': 'Rumsfeld'
        }
    ]

    # without providing a list of fields, the order of fields is random
    csv = convert_list_of_dicts_to_csv(data)
    header, dick, donald = csv.splitlines()

    assert 'first_name' in header
    assert 'last_name' in header

    assert 'Dick' in dick
    assert 'Cheney' in dick

    assert 'Donald' in donald
    assert 'Rumsfeld' in donald

    # we can change this by being explicit
    csv = convert_list_of_dicts_to_csv(data, ('first_name', 'last_name'))
    header, dick, donald = csv.splitlines()

    assert header == 'first_name,last_name'
    assert dick == 'Dick,Cheney'
    assert donald == 'Donald,Rumsfeld'

    csv = convert_list_of_dicts_to_csv(data, ('last_name', 'first_name'))
    header, dick, donald = csv.splitlines()

    assert header == 'last_name,first_name'
    assert dick == 'Cheney,Dick'
    assert donald == 'Rumsfeld,Donald'

    # or by providing a key
    csv = convert_list_of_dicts_to_csv(data, key=lambda f: f, reverse=True)
    header, dick, donald = csv.splitlines()

    assert header == 'last_name,first_name'
    assert dick == 'Cheney,Dick'
    assert donald == 'Rumsfeld,Donald'

    csv = convert_list_of_dicts_to_csv(data, key=lambda f: f, reverse=False)
    header, dick, donald = csv.splitlines()

    assert header == 'first_name,last_name'
    assert dick == 'Dick,Cheney'
    assert donald == 'Donald,Rumsfeld'


def test_convert_list_of_dicts_to_csv_escaping():
    data = [
        {
            'value': ',;"'
        }
    ]

    # without providing a list of fields, the order of fields is random
    csv = convert_list_of_dicts_to_csv(data)
    header, row = csv.splitlines()

    assert header == 'value'
    assert row == '",;"""'


def test_convert_list_of_dicts_to_xlsx():
    data = [
        {
            'first_name': 'Dick',
            'last_name': 'Cheney'
        },
        {
            'first_name': 'Donald',
            'last_name': 'Rumsfeld'
        }
    ]

    xlsx = convert_list_of_dicts_to_xlsx(data, ('first_name', 'last_name'))

    with tempfile.NamedTemporaryFile() as f:
        f.write(xlsx)

        rows = tuple(load_workbook(f).active.rows)

        assert rows[0][0].value == 'first_name'
        assert rows[0][1].value == 'last_name'
        assert rows[1][0].value == 'Dick'
        assert rows[1][1].value == 'Cheney'
        assert rows[2][0].value == 'Donald'
        assert rows[2][1].value == 'Rumsfeld'


def test_convert_irregular_list_of_dicts_to_csv():
    data = [
        {
            'name': 'Batman',
            'role': 'Superhero',
            'identity': 'Bruce Wayne'
        },
        {
            'name': 'Joker',
            'role': 'Supervillain',
            'gang': 'Injustice League'
        }
    ]

    # fields in random order
    csv = convert_list_of_dicts_to_csv(data)
    header, batman, joker = csv.splitlines()

    for column in ('name', 'role', 'identity', 'gang'):
        assert column in header

    for value in ('Batman', 'Superhero', 'Bruce Wayne'):
        assert value in batman

    for value in ('Joker', 'Supervillain', 'Injustice League'):
        assert value in joker

    # fields in defined order
    csv = convert_list_of_dicts_to_csv(
        data, ('name', 'role', 'identity', 'gang'))

    header, batman, joker = csv.splitlines()
    assert header == 'name,role,identity,gang'
    assert batman == 'Batman,Superhero,Bruce Wayne,'
    assert joker == 'Joker,Supervillain,,Injustice League'
