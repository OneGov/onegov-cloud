import pytest
import transaction

from datetime import timedelta
from depot.manager import DepotManager
from io import BytesIO
from onegov.file import FileCollection, FileSetCollection
from onegov_testing.utils import create_image
from sedate import utcnow


@pytest.fixture(scope='function')
def files(session):
    return FileCollection(session)


@pytest.fixture(scope='function')
def filesets(session):
    return FileSetCollection(session)


def test_file_content_assertions(files):
    with pytest.raises(AssertionError):
        files.add('readme.txt', content=None)

    with pytest.raises(AssertionError):
        files.add('readme.txt', content='non-binary')


def test_file_object_assertions(files, temporary_path):
    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('foobar')

    with pytest.raises(AssertionError):
        with (temporary_path / 'readme.txt').open('r') as f:
            files.add('readme.txt', content=f)


def test_file_content_empty(files):
    assert files.add('readme.txt', content=b'')
    assert files.query().count() == 1
    assert files.by_filename('readme.txt').first().reference.file.read() == b''


def test_file_object_empty(files, temporary_path):
    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('')

    with (temporary_path / 'readme.txt').open('rb') as f:
        assert files.add('readme.txt', content=f)

    assert files.query().count() == 1
    assert files.by_filename('readme.txt').first().reference.file.read() == b''


def test_fileset_integration(files, filesets):
    fileset = filesets.add('Documents')
    fileset.files.append(files.add('readme.txt', b'README'))
    fileset.files.append(files.add('manual.txt', b'MANUAL'))
    transaction.commit()

    fileset = filesets.query().first()

    assert fileset is filesets.by_id(fileset.id)
    assert len(fileset.files) == 2
    assert files.query().count() == 2
    assert filesets.query().count() == 1

    filesets.delete(fileset)
    transaction.commit()

    assert files.query().count() == 2
    assert filesets.query().count() == 0
    assert files.query().first() is files.by_id(files.query().first().id)

    files.delete(files.query().first())
    files.delete(files.query().first())
    transaction.commit()

    assert files.query().count() == 0


def test_replace_file(files):
    files.add('readme.txt', content=b'RTFM')
    transaction.commit()

    readme = files.by_filename('readme.txt').first()
    old_id = readme.reference.file.file_id
    assert readme.reference.file.read() == b'RTFM'

    assert len(DepotManager.get().list()) == 1

    files.replace(readme, b'README')
    transaction.commit()

    assert len(DepotManager.get().list()) == 1

    readme = files.by_filename('readme.txt').first()
    assert readme.reference.file.file_id != old_id
    assert readme.reference.file.read() == b'README'


def test_replace_image(files):
    files.add('avatar.png', content=create_image())
    transaction.commit()

    avatar = files.by_filename('avatar.png').first()
    assert 'thumbnail_small' in avatar.reference

    thumbnail_info = avatar.reference['thumbnail_small']
    transaction.commit()

    assert len(DepotManager.get().list()) == 2

    avatar = files.by_filename('avatar.png').first()
    files.replace(avatar, content=create_image())
    transaction.commit()

    avatar = files.by_filename('avatar.png').first()
    assert 'thumbnail_small' in avatar.reference
    assert avatar.reference['thumbnail_small'] != thumbnail_info

    assert len(DepotManager.get().list()) == 2


def test_store_file_from_path(files, temporary_path):

    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('README\n======')

    with (temporary_path / 'readme.txt').open('rb') as f:
        files.add('readme.txt', content=f)

    transaction.commit()

    readme = files.query().first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


def test_store_file_from_bytes_io(files):

    files.add('readme.txt', content=BytesIO(b'README\n======'))
    transaction.commit()

    readme = files.query().first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


def test_handle_duplicates(files):

    files.add('readme.txt', content=b'README')
    files.add('liesmich.txt', content=b'LIESMICH')
    transaction.commit()

    assert files.by_content(b'README')
    assert files.by_checksum(b'c47c7c7383225ab55ff591cb59c41e6b')

    files.allow_duplicates = False

    with pytest.raises(FileExistsError):
        files.add('readme.txt', content=b'README')

    with pytest.raises(FileExistsError):
        files.replace('liesmich.txt', content=b'README')

    files.allow_duplicates = True

    files.add('readme.txt', content=b'README')


def test_file_publication(files):
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
