from __future__ import annotations

import pytest
import transaction

from datetime import timedelta
from io import BytesIO
from onegov.file import FileCollection, FileSetCollection
from tests.shared.utils import create_image
from sedate import utcnow


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from depot.io.interfaces import FileStorage
    from onegov.file import File, FileSet
    from pathlib import Path
    from sqlalchemy.orm import Session
    from typing_extensions import TypeAlias

    Files: TypeAlias = FileCollection[File]
    FileSets: TypeAlias = FileSetCollection[FileSet]


@pytest.fixture(scope='function')
def files(session: Session) -> Files:
    return FileCollection(session)


@pytest.fixture(scope='function')
def filesets(session: Session) -> FileSets:
    return FileSetCollection(session)


def test_file_content_assertions(files: Files) -> None:
    with pytest.raises(AssertionError):
        files.add('readme.txt', content=None)  # type: ignore[arg-type]

    with pytest.raises(AssertionError):
        files.add('readme.txt', content='non-binary')  # type: ignore[arg-type]


def test_file_object_assertions(files: Files, temporary_path: Path) -> None:
    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('foobar')

    with pytest.raises(AssertionError):
        with (temporary_path / 'readme.txt').open('r') as f:
            files.add('readme.txt', content=f)  # type: ignore[arg-type]


def test_file_content_empty(files: Files) -> None:
    assert files.add('readme.txt', content=b'')
    assert files.query().count() == 1
    file = files.by_filename('readme.txt').first()
    assert file is not None
    assert file.reference.file.read() == b''


def test_file_object_empty(files: Files, temporary_path: Path) -> None:
    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('')

    with (temporary_path / 'readme.txt').open('rb') as f:
        assert files.add('readme.txt', content=f)

    assert files.query().count() == 1
    file = files.by_filename('readme.txt').first()
    assert file is not None
    assert file.reference.file.read() == b''


def test_fileset_integration(files: Files, filesets: FileSets) -> None:
    fileset = filesets.add('Documents')
    fileset.files.append(files.add('readme.txt', b'README'))
    fileset.files.append(files.add('manual.txt', b'MANUAL'))
    transaction.commit()

    fileset = filesets.query().one()

    assert fileset is filesets.by_id(fileset.id)
    assert len(fileset.files) == 2
    assert files.query().count() == 2
    assert filesets.query().count() == 1

    filesets.delete(fileset)
    transaction.commit()

    assert files.query().count() == 2
    assert filesets.query().count() == 0
    file = files.query().first()
    assert file is not None
    assert files.query().first() is files.by_id(file.id)

    files.delete(files.query().first())  # type: ignore[arg-type]
    files.delete(files.query().first())  # type: ignore[arg-type]
    transaction.commit()

    assert files.query().count() == 0


def test_replace_file(files: Files, depot: FileStorage) -> None:
    files.add('readme.txt', content=b'RTFM')
    transaction.commit()

    readme = files.by_filename('readme.txt').one()
    old_id = readme.reference.file.file_id
    assert readme.reference.file.read() == b'RTFM'

    assert len(depot.list()) == 1

    files.replace(readme, b'README')
    transaction.commit()

    assert len(depot.list()) == 1

    readme = files.by_filename('readme.txt').one()
    assert readme.reference.file.file_id != old_id
    assert readme.reference.file.read() == b'README'


def test_replace_image(files: Files, depot: FileStorage) -> None:
    files.add('avatar.png', content=create_image())
    transaction.commit()

    avatar = files.by_filename('avatar.png').one()
    assert 'thumbnail_small' in avatar.reference

    thumbnail_info = avatar.reference['thumbnail_small']
    transaction.commit()

    assert len(depot.list()) == 2

    avatar = files.by_filename('avatar.png').one()
    files.replace(avatar, content=create_image())
    transaction.commit()

    avatar = files.by_filename('avatar.png').one()
    assert 'thumbnail_small' in avatar.reference
    assert avatar.reference['thumbnail_small'] != thumbnail_info

    assert len(depot.list()) == 2


def test_store_file_from_path(files: Files, temporary_path: Path) -> None:

    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('README\n======')

    with (temporary_path / 'readme.txt').open('rb') as f:
        files.add('readme.txt', content=f)

    transaction.commit()

    readme = files.query().one()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


def test_store_file_from_bytes_io(files: Files) -> None:

    files.add('readme.txt', content=BytesIO(b'README\n======'))
    transaction.commit()

    readme = files.query().one()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


def test_handle_duplicates(files: Files) -> None:

    files.add('readme.txt', content=b'README')
    files.add('liesmich.txt', content=b'LIESMICH')
    transaction.commit()

    assert files.by_content(b'README')
    assert files.by_checksum('c47c7c7383225ab55ff591cb59c41e6b')

    files.allow_duplicates = False

    with pytest.raises(FileExistsError):
        files.add('readme.txt', content=b'README')

    liesmich = files.by_filename('liesmich.txt').one()
    with pytest.raises(FileExistsError):
        files.replace(liesmich, content=b'README')

    files.allow_duplicates = True

    files.add('readme.txt', content=b'README')
    files.replace(liesmich, content=b'README')


def test_file_publication(files: Files) -> None:
    horizon = utcnow()

    files.add(
        filename='foo',
        content=b'',
        published=False,
        publish_date=None
    )
    files.add(
        filename='bar',
        content=b'',
        published=False,
        publish_date=horizon - timedelta(hours=1)
    )
    files.add(
        filename='baz',
        content=b'',
        published=False,
        publish_date=horizon + timedelta(hours=1)
    )

    assert files.query().filter_by(published=True).count() == 0

    files.publish_files(horizon=horizon - timedelta(hours=1, seconds=1))
    assert files.query().filter_by(published=True).count() == 0

    files.publish_files(horizon=horizon)
    assert files.query().filter_by(published=True).count() == 1

    files.publish_files(horizon=horizon + timedelta(hours=1))
    assert files.query().filter_by(published=True).count() == 2


def test_file_publication_with_end_date(files: Files) -> None:
    horizon = utcnow()

    files.add(
        filename='published_for_epoch',
        content=b'',
        published=False,
        publish_date=horizon - timedelta(hours=1),
        publish_end_date=horizon + timedelta(hours=1)
    )

    files.publish_files(horizon=horizon)
    assert files.query().filter_by(published=True).count() == 1

    # publishing after the publish_end_date ...
    files.publish_files(horizon=(horizon + timedelta(hours=2)))

    # should no longer be published.
    assert files.query().filter_by(published=True).count() == 0


def test_filter_by_signature_digest(files: Files) -> None:
    file = files.add(
        filename='foo',
        content=b'',
    )

    file.signed = True
    file.signature_metadata = {  # type: ignore[assignment]
        'old_digest': 'foo',
        'new_digest': 'bar'
    }

    files.session.flush()

    assert files.by_signature_digest('foo').count() == 1
    assert files.by_signature_digest('bar').count() == 1
