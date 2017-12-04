from onegov.election_day.models import UploadToken
from pytest import raises
from uuid import uuid4


def test_upload_token(session):
    session.add(UploadToken())
    session.flush()
    assert session.query(UploadToken).one().token

    token = uuid4()
    session.add(UploadToken(token=token))
    session.flush()
    assert session.query(UploadToken).count() == 2
    assert token in [t.token for t in session.query(UploadToken)]


def test_upload_token_duplicates(session):
    token = uuid4()
    session.add(UploadToken(token=token))
    session.flush()
    assert session.query(UploadToken).one().token == token

    session.add(UploadToken(token=token))
    with raises(Exception):
        session.flush()
