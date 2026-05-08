from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from onegov.election_day.models import UploadToken
from pytest import raises
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_upload_token(session: Session) -> None:
    session.add(UploadToken())
    session.flush()
    assert session.query(UploadToken).one().token

    token = uuid4()
    session.add(UploadToken(token=token))
    session.flush()
    assert session.query(UploadToken).count() == 2
    assert token in [t.token for t in session.query(UploadToken)]


def test_upload_token_duplicates(session: Session) -> None:
    token = uuid4()
    session.add(UploadToken(token=token))
    session.flush()
    assert session.query(UploadToken).one().token == token

    session.add(UploadToken(token=token))
    with raises(IntegrityError):
        session.flush()
