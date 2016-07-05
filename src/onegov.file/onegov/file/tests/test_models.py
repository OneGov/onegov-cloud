import transaction

from onegov.file import File


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
