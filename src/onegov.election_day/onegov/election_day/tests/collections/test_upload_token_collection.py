from onegov.election_day.collections import UploadTokenCollection
from uuid import uuid4


def test_upload_token_collection(session):

    collection = UploadTokenCollection(session)
    assert collection.list() == []

    token = collection.create()
    assert collection.list() == [token]

    token = collection.create(token=token)
    assert collection.list() == [token]

    another_token = collection.create(token=uuid4())
    assert set(collection.list()) == set([token, another_token])

    collection.delete(token)
    assert collection.list() == [another_token]

    collection.create()
    collection.create()
    collection.create()
    assert len(collection.list()) == 4

    collection.clear()
    assert collection.list() == []
