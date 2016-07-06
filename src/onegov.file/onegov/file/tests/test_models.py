import transaction

from onegov.file import File, FileSet
from onegov.file.models.fileset import file_to_set_associations
from onegov.testing.utils import create_image


def test_store_file_from_string(session):
    session.add(File(name='readme.txt', reference=b'README\n======'))
    transaction.commit()

    readme = session.query(File).first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'application/octet-stream'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'unnamed'


def test_store_file_from_path(session, temporary_path):

    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('README\n======')

    with (temporary_path / 'readme.txt').open('rb') as f:
        session.add(File(name='readme.txt', reference=f))

    transaction.commit()

    readme = session.query(File).first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


def test_associate_files_with_sets(session):
    session.add(File(name='readme.txt', reference=b'README'))
    session.add(File(name='manual.txt', reference=b'MANUAL'))
    session.add(FileSet(title='Textfiles'))
    session.add(FileSet(title='Documents'))

    transaction.commit()

    readme, manual = session.query(File).order_by(File.name).all()
    textfiles, documents = session.query(FileSet).order_by(FileSet.title).all()

    assert session.query(file_to_set_associations).count() == 0
    assert not readme.filesets
    assert not manual.filesets
    assert not textfiles.files
    assert not documents.files

    textfiles.files.append(readme)
    textfiles.files.append(manual)
    documents.files.append(readme)

    transaction.commit()

    readme, manual = session.query(File).order_by(File.name).all()
    textfiles, documents = session.query(FileSet).order_by(FileSet.title).all()

    assert session.query(file_to_set_associations).count() == 3
    assert len(readme.filesets) == 2
    assert len(manual.filesets) == 1
    assert len(textfiles.files) == 2
    assert len(documents.files) == 1

    session.delete(manual)
    transaction.commit()

    readme = session.query(File).order_by(File.name).one()
    textfiles, documents = session.query(FileSet).order_by(FileSet.title).all()

    assert session.query(file_to_set_associations).count() == 2
    assert len(readme.filesets) == 2
    assert len(textfiles.files) == 1
    assert len(documents.files) == 1


def test_thumbnail_creation(session):
    session.add(File(name='large.png', reference=create_image(1024, 1024)))
    session.add(File(name='small.png', reference=create_image(32, 32)))

    transaction.commit()

    large, small = session.query(File).order_by(File.name).all()

    assert 'thumbnail_small' in large.reference
    assert 'thumbnail_small' in small.reference
