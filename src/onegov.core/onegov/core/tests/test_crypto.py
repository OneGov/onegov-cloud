from onegov.core.crypto import hash_password, verify_password


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
