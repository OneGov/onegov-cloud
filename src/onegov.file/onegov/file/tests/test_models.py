import transaction
import pytest

from io import BytesIO
from onegov.file import File, FileSet
from onegov.file.models.fileset import file_to_set_associations
from onegov.testing.utils import create_image
from PIL import Image


class PolymorphicFile(File):
    __mapper_args__ = {'polymorphic_identity': 'polymorphic'}


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_string(session, cls):
    session.add(cls(name='readme.txt', reference=b'README\n======'))
    transaction.commit()

    readme = session.query(cls).first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'application/octet-stream'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'unnamed'


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_path(session, temporary_path, cls):

    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('README\n======')

    with (temporary_path / 'readme.txt').open('rb') as f:
        session.add(cls(name='readme.txt', reference=f))

    transaction.commit()

    readme = session.query(cls).first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_bytes_io(session, cls):

    f = BytesIO(b'README\n======')
    session.add(cls(name='readme.txt', reference=f))

    transaction.commit()

    readme = session.query(cls).first()

    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'application/octet-stream'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'unnamed'


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


def test_max_image_size(session):
    session.add(File(name='unchanged.png', reference=create_image(1024, 1024)))
    session.add(File(name='limited.png', reference=create_image(1025, 1024)))

    transaction.commit()

    limited, unchanged = session.query(File).order_by(File.name).all()

    assert Image.open(limited.reference.file).size == (1024, 1023)
    assert Image.open(unchanged.reference.file).size == (1024, 1024)

    assert unchanged.reference.size == ['1024px', '1024px']
    assert limited.reference.size == ['1024px', '1023px']

    assert unchanged.reference.thumbnail_small['size'] == ['256px', '256px']
    assert limited.reference.thumbnail_small['size'] == ['256px', '255px']


def test_checksum(session):
    session.add(File(name='readme.txt', reference=b'README'))
    transaction.commit()

    readme = session.query(File).one()
    assert readme.checksum == 'c47c7c7383225ab55ff591cb59c41e6b'

    readme.reference = b'LIESMICH'
    transaction.commit()

    readme = session.query(File).one()
    assert readme.checksum == 'c122d482328c0e832610dd2c8d65db8b'


def test_determine_svg_size(session, temporary_path):
    with (temporary_path / 'logo.svg').open('wb') as f:
        f.write((
            b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            b'<svg width="281px" height="99px" '
            b'version="1.1" xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            b'</svg>'
        ))

    with (temporary_path / 'logo.svg').open('rb') as f:
        session.add(File(name='logo.svg', reference=f))

    transaction.commit()

    logo = session.query(File).order_by(File.name).one()
    assert logo.reference.size == ['281px', '99px']


def test_determine_unknown_svg_size(session, temporary_path):
    with (temporary_path / 'logo.svg').open('wb') as f:
        f.write((
            b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            b'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            b'</svg>'
        ))

    with (temporary_path / 'logo.svg').open('rb') as f:
        session.add(File(name='logo.svg', reference=f))

    transaction.commit()

    # use the default max size as the size if we can't determine one
    logo = session.query(File).order_by(File.name).one()
    assert logo.reference.size == ['1024px', '1024px']
