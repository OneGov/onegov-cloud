from __future__ import annotations

from onegov.election_day.collections import UploadTokenCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_upload_token_collection(session: Session) -> None:

    collection = UploadTokenCollection(session)
    assert collection.query().all() == []

    token = collection.create()
    assert collection.query().all() == [token]

    assert collection.by_id(token.id) == token

    another_token = collection.create()
    assert set(collection.query()) == {token, another_token}

    collection.delete(token)
    assert collection.query().all() == [another_token]
