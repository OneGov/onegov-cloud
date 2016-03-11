from io import StringIO, BytesIO
from onegov.election_day.utils.csv import FileImportError, load_csv


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
