import pytest
import transaction

from onegov.file import FileCollection, FileSetCollection


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
