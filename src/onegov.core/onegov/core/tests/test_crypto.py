import pytest

from onegov.core.crypto import (
    hash_password,
    random_token,
    verify_password,
    random_password
)


def test_hash_password():
    # because we use random salts we won't get the same result twice
    assert hash_password('hunter2') != hash_password('hunter2')

    # but that doesn't matter
    assert verify_password('hunter2', hash_password('hunter2'))
    assert verify_password('hunter2', hash_password('hunter2'))

    assert verify_password('hunter2', (
        '$bcrypt-sha256$2a,12$noO5p60IvoXlJN19'
        'lNwCQ.$sSGl3O6lQIdS8wFX/.i3NVc2HwNn5/.'
    ))


def test_random_token():
    assert random_token() != random_token()
    assert len(random_token()) == 64
    assert len(random_token(nbytes=1024)) == 64

    with pytest.raises(AssertionError):
        random_token(nbytes=511)


def test_no_null_bytes():
    with pytest.raises(AssertionError):
        assert hash_password("\0")

    with pytest.raises(AssertionError):
        assert verify_password("\0", "hash")


def test_random_password():
    assert len(random_password(16)) == 16
    assert len(random_password(32)) == 32
