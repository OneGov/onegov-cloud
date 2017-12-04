import pytest

from io import BytesIO
from onegov.core.utils import module_path
from onegov.election_day.formats.common import load_csv


def test_load_csv():
    result = load_csv(BytesIO(), 'text/plain', [])
    assert result[1].error == 'The csv/xls/xlsx file is empty.'

    result = load_csv(BytesIO(''.encode('utf-8')), 'text/plain', [])
    assert result[1].error == 'The csv/xls/xlsx file is empty.'

    result = load_csv(BytesIO('a,b,d'.encode('utf-8')), 'text/plain', ['c'])
    assert 'Missing columns' in result[1].error

    result = load_csv(BytesIO('a,a,b'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1].error == 'Some column names appear twice.'

    result = load_csv(BytesIO('<html />'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1].error == 'Not a valid csv/xls/xlsx file.'

    result = load_csv(BytesIO('a,b\n1,2'.encode('utf-8')), 'text/plain', ['a'])
    assert result[1] is None


@pytest.mark.parametrize("excel_file", [
    module_path('onegov.election_day', 'tests/fixtures/wb_v1.xls'),
    module_path('onegov.election_day', 'tests/fixtures/wb_v2.xls'),
    module_path('onegov.election_day', 'tests/fixtures/wb_v3.xls'),
    module_path('onegov.election_day', 'tests/fixtures/wb_v1.xlsx'),
    module_path('onegov.election_day', 'tests/fixtures/wb_v2.xlsx'),
    module_path('onegov.election_day', 'tests/fixtures/wb_v3.xlsx'),
])
def test_load_csv_excel(election_day_app, excel_file):
    with open(excel_file, 'rb') as f:
        csv, error = load_csv(f, 'application/excel', ['A'])
    assert not error
    assert [(line.a, line.b) for line in csv.lines] == [('1', '2')]


@pytest.mark.parametrize("excel_file", [
    module_path('onegov.election_day', 'tests/fixtures/wb_error_v1.xls'),
    module_path('onegov.election_day', 'tests/fixtures/wb_error_v1.xlsx'),
    module_path('onegov.election_day', 'tests/fixtures/wb_error_v2.xls'),
    module_path('onegov.election_day', 'tests/fixtures/wb_error_v2.xlsx'),
])
def test_load_csv_excel_invalid(election_day_app, excel_file):
    with open(excel_file, 'rb') as f:
        csv, error = load_csv(f, 'application/excel', ['A'])
    assert error.error == 'The xls/xlsx file contains unsupported cells.'


def test_load_csv_errors(election_day_app):
    csv, error = load_csv(
        BytesIO('A,B\n1,2\n'.encode('utf-8')), 'text/plain', ['A']
    )
    assert not error

    csv, error = load_csv(
        BytesIO('abcd'.encode('utf-8')), 'text/plain', ['A']
    )
    assert error.error == 'Not a valid csv/xls/xlsx file.'

    csv, error = load_csv(
        BytesIO('A,B\n1,2\n'.encode('utf-8')), 'text/plain', ['D']
    )
    assert 'Missing columns' in error.error

    csv, error = load_csv(
        BytesIO('A,A\n1,2\n'.encode('utf-8')), 'text/plain', ['A']
    )
    assert error.error == 'Some column names appear twice.'

    csv, error = load_csv(
        BytesIO('A,B\n\n\n1,2\n'.encode('utf-8')), 'text/plain', ['A']
    )
    assert error.error == 'The file contains an empty line.'

    csv, error = load_csv(
        BytesIO(''.encode('utf-8')), 'text/plain', ['A']
    )
    assert error.error == 'The csv/xls/xlsx file is empty.'

    csv, error = load_csv(
        BytesIO('a_a,aa_\n1,2\n'.encode('utf-8')), 'text/plain', ['aaa']
    )
    assert 'Could not find the expected columns' in error.error

    csv, error = load_csv(
        BytesIO('A,B\n1,2\n'.encode('utf-8')), 'application/excel', ['A']
    )
    assert error.error == 'Not a valid xls/xlsx file.'
