import pytest


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession):
    pass  # override the password hashing set by onegov.testing for the core
