import hashlib
import json
import pytest

from io import BytesIO
from onegov.org.horw_laws import (
    category,
    fetch,
    import_records,
    parse_detail,
    read_document,
    read_manifest,
    source_url,
)
from pathlib import Path
from unittest.mock import MagicMock, patch
from zipfile import ZipFile


def test_parse_horw_law_and_predecessor() -> None:
    record = parse_detail(
        b'''
        <dl>
          <dt>Nummer</dt><dd>100</dd>
          <dt>Name</dt><dd>Gemeindeordnung von Horw</dd>
          <dt>Erlassdatum</dt><dd>18. Juni 2023</dd>
          <dt>Inkrafttreten</dt><dd>1. September 2024</dd>
          <dt>Vorg\xc3\xa4ngerversion</dt>
          <dd><a href="/_rtr/information_537217">Old version</a></dd>
          <dt>Nachfolgeversion</dt>
          <dd><a href="/_rtr/information_999">New version</a></dd>
        </dl>
        <a href="/_doc/42">Unrelated navigation document</a>
        <table><tr><td>
          <a href="/_doc/5519410">Gemeindeordnung</a>
          <a href="/_doc/5519410">Download</a>
        </td></tr></table>
    '''
    )
    assert record['number'] == '100'
    assert record['enacted'] == '2023-06-18'
    assert record['effective'] == '2024-09-01'
    assert record['predecessors'] == [
        'https://www.horw.ch/_rtr/information_537217'
    ]
    assert record['documents'] == [
        {
            'url': 'https://www.horw.ch/_doc/5519410',
            'name': 'Gemeindeordnung',
        }
    ]


def test_horw_categories_and_source_validation() -> None:
    assert category('601A').startswith('06 ')
    assert category('GWR101') == '10 Rechtskräftige Raumpläne'
    with pytest.raises(ValueError, match='Unknown law number'):
        category('unknown')
    with pytest.raises(ValueError, match='Unexpected source URL'):
        source_url('https://example.org/_doc/123')


def test_horw_historical_download(tmp_path: Path) -> None:
    warning = MagicMock()
    warning.content = b'<a href="/_rtr/dokument_123">Weiter</a>'
    pdf = MagicMock()
    pdf.content = b'%PDF-1.7 test'
    path = tmp_path / '123.pdf'
    with patch('onegov.org.horw_laws.niquests.Session') as factory:
        client = factory.return_value.__enter__.return_value
        client.get.side_effect = [warning, pdf]
        assert fetch('/_doc/123', path) == pdf.content
        assert client.get.call_count == 2
        assert client.get.call_args.args[0] == (
            'https://www.horw.ch/_rtr/dokument_123'
        )
        assert fetch('/_doc/123', path) == pdf.content
        assert client.get.call_count == 2
    assert path.read_bytes() == pdf.content


def test_horw_rejects_html_download(tmp_path: Path) -> None:
    response = MagicMock()
    response.content = b'<html>Not a document</html>'
    path = tmp_path / '123.pdf'
    with patch('onegov.org.horw_laws.niquests.Session') as factory:
        client = factory.return_value.__enter__.return_value
        client.get.return_value = response
        with pytest.raises(ValueError, match='Not a PDF'):
            fetch('/_doc/123', path)
    assert not path.exists()


@pytest.mark.parametrize('prefix', ['', 'source/', 'migration/source/'])
def test_horw_zip_layouts(prefix: str) -> None:
    content = b'%PDF-1.7 test'
    document = {
        'path': 'documents/123.pdf',
        'sha256': hashlib.sha256(content).hexdigest(),
    }
    records = [{'number': '100', 'versions': [{'documents': [document]}]}]
    with ZipFile(BytesIO(), 'w') as archive:
        archive.writestr(prefix + 'records.json', json.dumps(records))
        archive.writestr(prefix + document['path'], content)
        loaded, root = read_manifest(archive)
        assert loaded == records
        assert read_document(archive, root, document) == content


@pytest.mark.parametrize(
    'files', [[], ['records.json', 'source/records.json']]
)
def test_horw_zip_requires_one_manifest(files: list[str]) -> None:
    with ZipFile(BytesIO(), 'w') as archive:
        for name in files:
            archive.writestr(name, '[]')
        with pytest.raises(ValueError, match='exactly one records.json'):
            read_manifest(archive)


@pytest.mark.parametrize('content', [None, b'%PDF-1.7 corrupt'])
def test_horw_zip_invalid_document_before_database_changes(
    content: bytes | None,
) -> None:
    document = {
        'path': 'documents/123.pdf',
        'sha256': hashlib.sha256(b'%PDF-1.7 original').hexdigest(),
    }
    records = [{'number': '100', 'versions': [{'documents': [document]}]}]
    session = MagicMock()
    with ZipFile(BytesIO(), 'w') as archive:
        archive.writestr('records.json', json.dumps(records))
        if content is not None:
            archive.writestr(document['path'], content)
        with pytest.raises(ValueError, match='Missing document|Checksum'):
            import_records(session, archive)
    session.query.assert_not_called()
