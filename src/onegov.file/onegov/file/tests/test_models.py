import transaction
import pytest

from depot.manager import DepotManager
from io import BytesIO
from onegov.core.orm import Base
from onegov.core.utils import module_path
from onegov.file import File, FileSet, AssociatedFiles
from onegov.file.models.fileset import file_to_set_associations
from onegov_testing.utils import create_image
from PIL import Image
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text


class PolymorphicFile(File):
    __mapper_args__ = {'polymorphic_identity': 'polymorphic'}


class Blogpost(Base, AssociatedFiles):
    __tablename__ = 'blogposts'

    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)


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


def test_pdf_preview_creation(session):
    path = module_path('onegov.file', 'tests/fixtures/example.pdf')

    with open(path, 'rb') as f:
        session.add(File(name='example.pdf', reference=f))

    transaction.commit()

    pdf = session.query(File).one()
    pdf.reference['thumbnail_medium']

    # our example file contains a blue backgorund so we can verify that
    # the thumbnail for the pdf is generated correctly

    thumb = DepotManager.get().get(pdf.reference['thumbnail_medium']['id'])
    image = Image.open(thumb)

    assert (0, 91, 161, 255) in set(image.getdata())
    assert image.size == (395, 512)


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


def test_associated_files(session):
    post = Blogpost(
        text="My interview at <company>",
        files=[File(name='frowney.png', reference=create_image(1024, 1024))]
    )

    session.add(post)
    session.flush()

    assert len(post.files) == 1
    assert post.files[0].name == 'frowney.png'
    assert post.files[0].reference.size == ('1024px', '1024px')

    assert session.query(File).one().linked_blogposts == [post]
    assert session.query(File).one().links.all() == (post, )

    session.delete(post)
    session.flush()

    assert session.query(File).count() == 0


def test_update_metadata(session):
    # note that the name is only stored on the database, not the metadata
    session.add(File(name='readme.txt', reference=b'README'))
    transaction.commit()

    def get_file():
        return session.query(File).one()

    assert get_file().reference.file.filename == 'unnamed'

    get_file()._update_metadata(filename='foobar.txt')
    transaction.abort()

    assert get_file().reference.file.filename == 'unnamed'

    get_file()._update_metadata(filename='foobar.txt')
    transaction.commit()

    assert get_file().reference.file.filename == 'foobar.txt'

    get_file()._update_metadata(filename='foo.txt')
    get_file()._update_metadata(filename='bar.txt')
    transaction.commit()

    assert get_file().reference.file.filename == 'bar.txt'
