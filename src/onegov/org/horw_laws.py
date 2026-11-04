"""Snapshot and import Horw's law collection into its existing directory.

Fetch: venv/bin/python -m onegov.org.horw_laws /tmp/horw-laws
Import: venv/bin/onegov-org import-horw-laws /tmp/horw-laws.zip
"""

import argparse
import click
import hashlib
import json
import niquests
import re

from concurrent.futures import ThreadPoolExecutor
from datetime import date
from io import BytesIO
from lxml import html
from onegov.core.crypto import random_token
from onegov.directory import Directory
from onegov.directory.models.directory import DirectoryFile
from onegov.file.utils import as_fileintent
from pathlib import Path, PurePosixPath
from operator import itemgetter
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlparse

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from zipfile import ZipFile


SOURCE: str = 'https://www.horw.ch'
DIRECTORY: str = 'systematische-rechtssammlung'
MONTHS: tuple[str, ...] = (
    'Januar',
    'Februar',
    'März',
    'April',
    'Mai',
    'Juni',
    'Juli',
    'August',
    'September',
    'Oktober',
    'November',
    'Dezember',
)
CATEGORIES: tuple[str, ...] = (
    '01 Gemeindeordnung',
    '02 Behörden',
    '03 Gemeindeverwaltung',
    '04 Personalwesen',
    '05 Bildung - Kultur - Sport',
    '06 Ortsplanung - Bauwesen - Strassenwesen - Zivilschutz',
    '07 Ver- und Entsorgung',
    '08 Gesundheits- und Sozialwesen - Alters- und Pflegeheim',
    '09 Volkswirtschaft - Finanzen',
    '10 Rechtskräftige Raumpläne',
)


def source_url(path: str) -> str:
    url = urljoin(SOURCE, path)
    if urlparse(url).netloc != 'www.horw.ch':
        raise ValueError(f'Unexpected source URL: {url}')
    return url


def parse_date(value: str) -> str:
    day, month, year = value.split()
    return date(int(year), MONTHS.index(month) + 1, int(day[:-1])).isoformat()


def category(number: str) -> str:
    if re.fullmatch(r'[1-9]\d{2}[A-Z]?', number):
        return CATEGORIES[int(number[0]) - 1]
    if re.fullmatch(r'(?:B|G|GWR|R)\d{3}', number):
        return CATEGORIES[-1]
    raise ValueError(f'Unknown law number: {number}')


def fetch(url: str, path: Path) -> bytes:
    if path.exists():
        content = path.read_bytes()
        if path.suffix != '.pdf' or content.startswith(b'%PDF-'):
            return content
    with niquests.Session() as client:
        response = client.get(source_url(url), timeout=60)
        response.raise_for_status()
        assert response.content is not None
        if path.suffix == '.pdf':
            if not response.content.startswith(b'%PDF-'):
                warning = html.fromstring(response.content)
                identifier = url.rsplit('/', 1)[-1]
                links = warning.xpath(
                    '//a[@href="/_rtr/dokument_' + identifier + '"]'
                )
                if links:
                    response = client.get(
                        source_url(links[0].get('href')), timeout=60
                    )
                    response.raise_for_status()
                    assert response.content is not None
            assert response.content is not None
            if not response.content.startswith(b'%PDF-'):
                raise ValueError(f'Not a PDF: {url}')
        assert response.content is not None
        content = response.content
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def parse_detail(content: bytes) -> dict[str, Any]:
    root = html.fromstring(content.decode('utf-8'))
    fields = {
        dt.text_content().strip(): dt.getnext() for dt in root.xpath('//dl/dt')
    }
    values = {
        name: ' '.join(element.text_content().split())
        for name, element in fields.items()
    }
    documents: dict[str, str] = {}
    for link in root.xpath('//table//a[starts-with(@href, "/_doc/")]'):
        documents.setdefault(link.get('href'), link.text_content().strip())
    predecessors = (
        [
            source_url(link.get('href'))
            for link in fields['Vorgängerversion'].iter('a')
        ]
        if 'Vorgängerversion' in fields
        else []
    )
    return {
        'number': values['Nummer'],
        'name': values['Name'],
        'enacted': parse_date(values['Erlassdatum']),
        'effective': parse_date(values['Inkrafttreten']),
        'fields': values,
        'predecessors': predecessors,
        'documents': [
            {'url': source_url(url), 'name': name}
            for url, name in documents.items()
        ],
    }


def snapshot_record(row: dict[str, str], path: Path) -> dict[str, Any]:
    link = html.fromstring(row['title'])
    href = link.get('href')
    assert href is not None
    url = source_url(href)
    versions: list[dict[str, Any]] = []
    pending = [url]
    visited: set[str] = set()
    while pending:
        current = pending.pop(0)
        key = re.search(r'(\d+)$', current)
        if key is None:
            raise ValueError(f'Invalid detail URL: {current}')
        identifier = key[1]
        if identifier in visited:
            raise ValueError(f'Duplicate or cyclic predecessor: {current}')
        visited.add(identifier)
        detail = parse_detail(
            fetch(current, path / 'pages' / f'{identifier}.html')
        )
        if detail['number'] != row['_nummer']:
            raise ValueError(f'Predecessor number mismatch: {current}')
        detail['url'] = current
        for document in detail['documents']:
            document_id = document['url'].rsplit('/', 1)[-1]
            relative = f'documents/{document_id}.pdf'
            content = fetch(document['url'], path / relative)
            document['path'] = relative
            document['sha256'] = hashlib.sha256(content).hexdigest()
            if not document['name'].lower().endswith('.pdf'):
                document['name'] += '.pdf'
        versions.append(detail)
        pending.extend(detail['predecessors'])
    listed_documents = {
        source_url(link.attrib['href'])
        for link in html.fromstring(row['_dokumentList']).iter('a')
    }
    detail_documents = {
        document['url'] for document in versions[0]['documents']
    }
    if listed_documents != detail_documents:
        raise ValueError(f'Document list mismatch: {url}')
    if not versions[0]['documents']:
        raise ValueError(f'No current documents: {url}')
    if versions[0]['effective'] != row['_rechtsgueltigkeit-sort']:
        raise ValueError(f'Effective date mismatch: {url}')
    return {'number': row['_nummer'], 'versions': versions}


def snapshot(path: Path) -> None:
    root = html.fromstring(
        fetch(f'{SOURCE}/gesetzessammlung', path / 'index.html')
    )
    table = root.get_element_by_id('icmsTable-gesetzessammlungList')
    entities = table.get('data-entities')
    assert entities is not None
    rows = json.loads(entities)['data']
    numbers = [row['_nummer'] for row in rows]
    if not rows or len(numbers) != len(set(numbers)):
        raise ValueError('Empty source or duplicate current law numbers')
    for number in numbers:
        category(number)
    with ThreadPoolExecutor(max_workers=4) as executor:
        records = list(
            executor.map(lambda row: snapshot_record(row, path), rows)
        )
    records.sort(key=itemgetter('number'))
    (path / 'records.json').write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + '\n'
    )
    click.echo(f'Saved {len(records)} records to {path}')


def read_manifest(
    archive: ZipFile,
) -> tuple[list[dict[str, Any]], PurePosixPath]:
    names = archive.namelist()
    if len(names) != len(set(names)):
        raise ValueError('ZIP contains duplicate filenames')
    manifests = [
        name for name in names if PurePosixPath(name).name == 'records.json'
    ]
    if len(manifests) != 1:
        raise ValueError('ZIP must contain exactly one records.json')
    records = json.loads(archive.read(manifests[0]))
    if not isinstance(records, list) or not records:
        raise ValueError('Snapshot must contain a non-empty list of records')
    numbers = [record['number'] for record in records]
    if len(numbers) != len(set(numbers)):
        raise ValueError('Duplicate law numbers in snapshot')
    return records, PurePosixPath(manifests[0]).parent


def read_document(
    archive: ZipFile,
    root: PurePosixPath,
    document: dict[str, Any],
) -> bytes:
    path = PurePosixPath(document['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Invalid document path: {path}')
    try:
        content = archive.read(str(root / path))
    except KeyError as error:
        raise ValueError(f'Missing document: {root / path}') from error
    if hashlib.sha256(content).hexdigest() != document['sha256']:
        raise ValueError(f'Checksum mismatch: {path}')
    if not content.startswith(b'%PDF-'):
        raise ValueError(f'Not a PDF: {path}')
    return content


def import_records(session: Session, archive: ZipFile) -> dict[str, int]:
    records, root = read_manifest(archive)
    for record in records:
        for version in record['versions']:
            for document in version['documents']:
                read_document(archive, root, document)
    directory = session.query(Directory).filter_by(name=DIRECTORY).one()
    existing = {entry.values['nummer']: entry for entry in directory.entries}
    if len(existing) != len(directory.entries):
        raise ValueError('Duplicate law numbers in target directory')
    report = {'created': 0, 'updated': 0, 'unchanged': 0, 'documents': 0}
    for record in records:
        versions = record['versions']
        current = versions[0]
        fingerprint = hashlib.sha256(
            json.dumps(record, sort_keys=True).encode()
        ).hexdigest()
        entry = existing.get(record['number'])
        if entry and entry.meta.get('horw_laws_sha256') == fingerprint:
            report['unchanged'] += 1
            continue
        values: dict[str, Any] = {
            'nummer': record['number'],
            'name': current['name'],
            'erlassdatum': date.fromisoformat(current['enacted']),
            'inkrafttreten': date.fromisoformat(current['effective']),
            'sachgebiet': [category(record['number'])],
            'informationen': current['fields'].get('Informationen', ''),
            'link': current['url'],
            'text': '',
            'dokument': [],
            'historische_fassungen': [],
        }
        files: list[DirectoryFile] = []
        for field, selected in (
            ('dokument', versions[:1]),
            ('historische_fassungen', versions[1:]),
        ):
            seen: set[str] = set()
            for version in selected:
                for document in version['documents']:
                    if document['url'] in seen:
                        continue
                    seen.add(document['url'])
                    content = read_document(archive, root, document)
                    file = DirectoryFile(
                        id=random_token(),
                        name=document['name'],
                        note=f'{field}:{len(values[field])}',
                        reference=as_fileintent(
                            BytesIO(content), document['name']
                        ),
                    )
                    session.add(file)
                    files.append(file)
                    values[field].append(
                        {
                            'data': f'@{file.id}',
                            'filename': document['name'],
                            'mimetype': 'application/pdf',
                            'size': len(content),
                        }
                    )
        if entry is None:
            entry = directory.add(values)
            report['created'] += 1
        else:
            for old_file in list(entry.files):
                entry.files.remove(old_file)
                session.delete(old_file)
            directory.update(entry, values)
            report['updated'] += 1
        entry.files.extend(files)
        entry.meta = {
            **entry.meta,
            'horw_laws_sha256': fingerprint,
            'horw_laws_source': current['url'],
            'horw_laws_versions': versions,
        }
        entry.update_content_hash()
        report['documents'] += len(files)
    session.flush()
    return report


if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=__doc__
    )
    parser.add_argument('path', type=Path)
    snapshot(parser.parse_args().path)
