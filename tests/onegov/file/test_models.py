from __future__ import annotations

import pytest
import os
import sedate
import transaction

from depot.manager import DepotManager
from io import BytesIO
from onegov.core.orm import Base
from onegov.core.orm.abstract import associated
from onegov.core.utils import module_path
from onegov.file import File, FileSet, AssociatedFiles, NamedFile
from onegov.file.filters import WithPDFThumbnailFilter
from onegov.file.models.fileset import file_to_set_associations
from tests.shared.utils import create_image
from pathlib import Path
from onegov.file.utils import as_fileintent
from PIL import Image
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import Text
from unittest.mock import Mock


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path
    from sqlalchemy.orm import Session


class PolymorphicFile(File):
    __mapper_args__ = {'polymorphic_identity': 'polymorphic'}


class Blogpost(Base, AssociatedFiles):
    __tablename__ = 'blogposts'

    id: Column[int] = Column(Integer, primary_key=True)
    text: Column[str] = Column(Text, nullable=False)


class MediaItemFile(File):
    __mapper_args__ = {'polymorphic_identity': 'media_item'}


class MediaItem(Base):
    __tablename__ = 'media_items'

    id: Column[int] = Column(Integer, primary_key=True)
    description: Column[str] = Column(Text, nullable=False)
    content = associated(MediaItemFile, 'content', 'one-to-one')


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_string(session: Session, cls: type[File]) -> None:
    session.add(cls(name='readme.txt', reference=b'README\n======'))  # type: ignore[misc]
    transaction.commit()

    readme = session.query(cls).first()
    assert readme is not None
    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'application/octet-stream'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'unnamed'


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_path(
    session: Session,
    temporary_path: Path,
    cls: type[File]
) -> None:

    with (temporary_path / 'readme.txt').open('w') as f:
        f.write('README\n======')

    with (temporary_path / 'readme.txt').open('rb') as f:
        session.add(cls(name='readme.txt', reference=f))  # type: ignore[misc]

    transaction.commit()

    readme = session.query(cls).first()
    assert readme is not None
    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'text/plain'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'readme.txt'


@pytest.mark.parametrize('cls', [File, PolymorphicFile])
def test_store_file_from_bytes_io(session: Session, cls: type[File]) -> None:

    f = BytesIO(b'README\n======')
    session.add(cls(name='readme.txt', reference=f))  # type: ignore[misc]

    transaction.commit()

    readme = session.query(cls).first()
    assert readme is not None
    assert readme.reference.file.content_length == 13
    assert readme.reference.file.content_type == 'application/octet-stream'
    assert readme.reference.file.read() == b'README\n======'
    assert readme.reference.file.name == 'unnamed'


def test_associate_files_with_sets(session: Session) -> None:
    session.add(File(name='readme.txt', reference=b'README'))  # type: ignore[misc]
    session.add(File(name='manual.txt', reference=b'MANUAL'))  # type: ignore[misc]
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


def test_thumbnail_creation(session: Session) -> None:
    session.add(File(name='large.png', reference=create_image(1024, 1024)))  # type: ignore[misc]
    session.add(File(name='small.png', reference=create_image(32, 32)))  # type: ignore[misc]

    transaction.commit()

    large, small = session.query(File).order_by(File.name).all()

    assert 'thumbnail_small' in large.reference
    assert 'thumbnail_small' in small.reference


def test_save_png_zipbomb(session: Session) -> None:
    path = module_path('tests.onegov.file', 'fixtures/bomb.png')

    with open(path, 'rb') as f:
        session.add(File(name='zipbomb.png', reference=f))  # type: ignore[misc]

    transaction.commit()
    file = session.query(File).one()
    assert file.reference.file.read() == b''
    assert file.reference.content_type == 'application/malicious'


def test_save_image_internal_exception(
    session: Session,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    # simulate internal error in Pillow
    mock_open = Mock(side_effect=ValueError)
    monkeypatch.setattr('PIL.Image.open', mock_open)

    session.add(File(name='causes-error.png', reference=create_image(32, 32)))  # type: ignore[misc]

    transaction.commit()
    file = session.query(File).one()
    assert file.reference.file.read() == b''
    assert file.reference.content_type == 'application/unidentified-image'


def test_strip_image_exif(session: Session) -> None:
    path = module_path('tests.onegov.file', 'fixtures/exif.jpg')

    with open(path, 'rb') as f:
        session.add(File(name='exif.jpg', reference=f))  # type: ignore[misc]

    transaction.commit()
    file = session.query(File).one()

    image = Image.open(file.reference.file)
    assert not image.getexif()


def test_pdf_preview_creation(session: Session) -> None:
    path = module_path('tests.onegov.file', 'fixtures/example.pdf')

    with open(path, 'rb') as f:
        session.add(File(name='example.pdf', reference=f))  # type: ignore[misc]

    transaction.commit()

    pdf = session.query(File).one()
    assert pdf.reference.get('thumbnail_medium', None) is not None

    # our example file contains a blue backgorund so we can verify that
    # the thumbnail for the pdf is generated correctly

    thumb = DepotManager.get().get(pdf.reference['thumbnail_medium']['id'])  # type: ignore[union-attr]
    image = Image.open(thumb)

    assert (0, 91, 161, 255) in set(image.get_flattened_data())

    w, h = image.size
    assert h == 512

    # this somewhat varies between local and test, probably due to some
    # version difference - not a big deal though, just keep an eye on it
    # if the values should change some more
    assert w in (362, 396)


def test_pdf_preview_creation_with_erroneous_pdf(
    session: Session,
    monkeypatch: pytest.MonkeyPatch
) -> None:
    # There was a pdf which made ghostscript fail with stderr: "circular
    # reference to indirect object".
    # However, we can't upload the original pdf due to sensitive information.
    # So we have to kind of mock the error here.
    mock = Mock(side_effect=ValueError)
    monkeypatch.setattr(
        WithPDFThumbnailFilter,
        'generate_preview',
       mock
    )

    filname = 'example.pdf'
    path = module_path('tests.onegov.file', f'fixtures/{filname}')

    with open(path, 'rb') as f:
        session.add(File(name=f'{filname}', reference=f))  # type: ignore[misc]
    transaction.commit()
    pdf = session.query(File).one()
    assert pdf.reference.get('thumbnail_medium', None) is not None
    thumb = DepotManager.get().get(pdf.reference['thumbnail_medium']['id'])  # type: ignore[union-attr]

    # expect to be the default one

    thumbnail_medium_pdf_preview_fallback = BytesIO(
        Path(
            module_path('onegov.org', 'static/pdf_preview')
            + os.sep
            + 'thumbnail_medium_pdf_preview_fallback.png'
        ).read_bytes()
    )

    assert thumb.read() == thumbnail_medium_pdf_preview_fallback.read()


def test_max_image_size(session: Session) -> None:
    session.add(File(name='unchanged.png', reference=create_image(2048, 2048)))  # type: ignore[misc]
    session.add(File(name='limited.png', reference=create_image(2049, 2048)))  # type: ignore[misc]

    transaction.commit()

    limited, unchanged = session.query(File).order_by(File.name).all()

    assert Image.open(limited.reference.file).size == (2048, 2047)
    assert Image.open(unchanged.reference.file).size == (2048, 2048)

    assert unchanged.reference.size == ['2048px', '2048px']
    assert limited.reference.size == ['2048px', '2047px']

    assert unchanged.reference.thumbnail_small['size'] == ['512px', '512px']
    assert limited.reference.thumbnail_small['size'][0] in ['512px', '511px']
    assert limited.reference.thumbnail_small['size'][1] in ['512px', '511px']


def test_checksum(session: Session) -> None:
    session.add(File(name='readme.txt', reference=b'README'))  # type: ignore[misc]
    transaction.commit()

    readme = session.query(File).one()
    assert readme.checksum == 'c47c7c7383225ab55ff591cb59c41e6b'

    readme.reference = b'LIESMICH'  # type: ignore[assignment]
    transaction.commit()

    readme = session.query(File).one()
    assert readme.checksum == 'c122d482328c0e832610dd2c8d65db8b'


def test_determine_svg_size(session: Session, temporary_path: Path) -> None:
    with (temporary_path / 'logo.svg').open('wb') as f:
        f.write((
            b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            b'<svg width="281px" height="99px" '
            b'version="1.1" xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            b'</svg>'
        ))

    with (temporary_path / 'logo.svg').open('rb') as f:
        session.add(File(name='logo.svg', reference=f))  # type: ignore[misc]

    transaction.commit()

    logo = session.query(File).order_by(File.name).one()
    assert logo.reference.size == ['281px', '99px']


def test_determine_unknown_svg_size(
    session: Session,
    temporary_path: Path
) -> None:
    with (temporary_path / 'logo.svg').open('wb') as f:
        f.write((
            b'<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
            b'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
            b'xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            b'</svg>'
        ))

    with (temporary_path / 'logo.svg').open('rb') as f:
        session.add(File(name='logo.svg', reference=f))  # type: ignore[misc]

    transaction.commit()

    # use the default max size as the size if we can't determine one
    logo = session.query(File).order_by(File.name).one()
    assert logo.reference.size == ['2048px', '2048px']


def test_associated_files(session: Session) -> None:
    post = Blogpost(
        text="My interview at <company>",
        files=[File(name='frowney.png', reference=create_image(2048, 2048))]  # type: ignore[misc]
    )

    session.add(post)
    session.flush()

    assert len(post.files) == 1
    assert post.files[0].name == 'frowney.png'
    assert post.files[0].reference.size == ('2048px', '2048px')

    folder = Path(post.files[0].reference.file._metadata_path).parent.parent  # type: ignore[attr-defined]

    # 1 image + 1 thumbnail
    assert sum(1 for p in folder.iterdir()) == 2

    assert session.query(File).one().linked_blogposts == [post]  # type: ignore[attr-defined]
    assert session.query(File).one().links.all() == (post, )

    session.delete(post)

    session.flush()
    assert session.query(File).count() == 0
    assert sum(1 for p in folder.iterdir()) == 2  # not commited yet..

    transaction.commit()
    assert session.query(File).count() == 0
    assert sum(1 for p in folder.iterdir()) == 0


def test_update_metadata(session: Session) -> None:
    # note that the name is only stored on the database, not the metadata
    session.add(File(name='readme.txt', reference=b'README'))  # type: ignore[misc]
    transaction.commit()

    def get_file() -> File:
        return session.query(File).one()

    assert get_file().reference.file.filename == 'unnamed'
    assert get_file().reference.file.content_type == 'application/octet-stream'

    get_file()._update_metadata(filename='foobar.txt')
    transaction.abort()

    assert get_file().reference.file.filename == 'unnamed'
    assert get_file().reference.file.content_type == 'application/octet-stream'

    get_file()._update_metadata(
        filename='foobar.txt',
        content_type='text/markdown'
    )
    transaction.commit()

    assert get_file().reference.file.filename == 'foobar.txt'
    assert get_file().reference.file.content_type == 'text/markdown'

    get_file()._update_metadata(filename='foo.txt', content_type='text/plain')
    # this should only override filename not the updated content_type
    get_file()._update_metadata(filename='bar.txt')
    transaction.commit()

    assert get_file().reference.file.filename == 'bar.txt'
    assert get_file().reference.file.content_type == 'text/plain'


def test_pdf_text_extraction(session: Session) -> None:
    path = module_path('tests.onegov.file', 'fixtures/sample.pdf')

    with open(path, 'rb') as f:
        session.add(File(name='sample.pdf', reference=f))  # type: ignore[misc]

    transaction.commit()

    pdf = session.query(File).one()
    assert pdf.extract is not None
    assert 'Adobe® Portable Document Format (PDF)' in pdf.extract
    assert pdf.stats is not None
    assert pdf.stats['pages'] == 1
    assert pdf.stats['words'] > 20


def test_signature_timestamp(session: Session) -> None:
    path = module_path('tests.onegov.file', 'fixtures/sample.pdf')
    time = sedate.utcnow()

    with open(path, 'rb') as f:
        session.add(File(name='sample.pdf', reference=f, signature_metadata={  # type: ignore[misc]
            'timestamp': time.isoformat()
        }))

    transaction.commit()

    # if unsinged, the timestamp is ignored
    assert session.query(File).one().signature_timestamp is None
    assert session.query(File).with_entities(File.signature_timestamp
        ).one().signature_timestamp is None

    # if signed the timestamp is in UTC (not timezone-aware)
    session.query(File).one().signed = True
    transaction.commit()

    assert session.query(File).one().signature_timestamp == time
    assert session.query(File).with_entities(File.signature_timestamp
        ).one().signature_timestamp == time

    # make sure we can filter by time
    assert session.query(File).filter_by(signature_timestamp=time).first()

    # make sure we get utc for both
    assert session.query(File).one().signature_timestamp.tzinfo.zone == 'UTC'
    assert session.query(File).with_entities(File.signature_timestamp
        ).one().signature_timestamp.tzinfo.zone == 'UTC'


def test_file_cleanup(session: Session) -> None:
    session.add(File(name='readme.txt', reference=b'foo'))  # type: ignore[misc]
    transaction.commit()

    readme = session.query(File).first()
    assert readme is not None
    folder = Path(readme.reference.file._metadata_path).parent.parent  # type: ignore[attr-defined]
    assert sum(1 for f in folder.iterdir()) == 1

    readme.reference = as_fileintent(b'bar', 'readme.txt')
    transaction.commit()

    assert sum(1 for f in folder.iterdir()) == 1
    assert session.query(File).first().reference.file.read() == b'bar'  # type: ignore[union-attr]


def test_associated_files_cleanup(session: Session) -> None:
    post = Blogpost(
        text="Foo",
        files=[
            File(name='foo.txt', reference=b'foo'),  # type: ignore[misc]
            File(name='bar.txt', reference=b'bar')  # type: ignore[misc]
        ]
    )

    session.add(post)
    session.flush()

    post = session.query(Blogpost).one()
    folder = Path(post.files[0].reference.file._metadata_path).parent.parent  # type: ignore[attr-defined]
    assert session.query(File).count() == 2
    assert sum(1 for p in folder.iterdir()) == 2

    post = session.query(Blogpost).one()
    post.files = [File(name='bar.txt', reference=b'bar')]  # type: ignore[misc]

    session.flush()
    assert session.query(File).count() == 1
    assert sum(1 for p in folder.iterdir()) == 3

    transaction.commit()
    assert session.query(File).count() == 1
    assert sum(1 for p in folder.iterdir()) == 1

    post.files = []
    session.flush()
    transaction.abort()

    assert session.query(File).count() == 1
    assert sum(1 for p in folder.iterdir()) == 1


def test_1n1_associated_file_cleanup(session: Session) -> None:

    item = MediaItem(description="Foo")
    item.content = MediaItemFile(id='abcd', name='bar')
    item.content.reference = as_fileintent(b'bar', 'bar')

    session.add(item)
    session.flush()

    item = session.query(MediaItem).one()

    folder = Path(item.content.reference.file._metadata_path).parent.parent  # type: ignore[union-attr]
    assert session.query(File).count() == 1
    assert item.content.reference.file.read() == b'bar'  # type: ignore[union-attr]
    assert sum(1 for p in folder.iterdir()) == 1

    item.content = MediaItemFile(id='abcd', name='baz')
    item.content.reference = as_fileintent(b'baz', 'baz')

    session.flush()
    transaction.commit()

    assert session.query(File).count() == 1
    assert item.content.reference.file.read() == b'baz'
    assert sum(1 for p in folder.iterdir()) == 1  # 2


def test_named_file() -> None:

    class MyFile(File):
        __mapper_args__ = {'polymorphic_identity': 'my_file'}

    class CustomBlogPost(Blogpost):
        x = NamedFile(cls=MyFile)
        y = NamedFile()

    post = CustomBlogPost(text="My interview at <company>")
    # avoid narrowing of post.x/post.y
    post2 = post

    assert post2.x is None
    assert post2.y is None

    del post.x
    del post.y

    x = create_image(2048, 2048)
    y = create_image(2048, 2048)
    post.x = (x, 'x.png')
    post.y = (y, 'y.png')
    x.seek(0)
    y.seek(0)
    assert len(post.files) == 2
    assert isinstance(post.x, MyFile)
    assert post.x.name == 'x'
    assert post.x.reference.filename == 'x.png'
    assert post.x.reference.file.read() == x.read()
    assert isinstance(post.y, File)
    assert not isinstance(post.y, MyFile)
    assert post.y.name == 'y'
    assert post.y.reference.filename == 'y.png'
    assert post.y.reference.file.read() == y.read()

    del post.x
    assert len(post.files) == 1
    assert post2.x is None
    assert post.y
