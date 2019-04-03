from onegov.election_day.collections import UploadTokenCollection


def test_upload_token_collection(session):

    collection = UploadTokenCollection(session)
    assert collection.query().all() == []

    token = collection.create()
    assert collection.query().all() == [token]

    assert collection.by_id(token.id) == token

    another_token = collection.create()
    assert set(collection.query().all()) == set([token, another_token])

    collection.delete(token)
    assert collection.query().all() == [another_token]
