import base64
import pytest

from tempfile import NamedTemporaryFile


@pytest.fixture(scope='session')
def keytab():
    """ BASE 64 encoded keytab file for Kerberos integration tests

    Principal: HTTP/ogc.example.org@EXAMPLE.ORG
    Password: test

    To create, start ktutil (the latest release, macOS's one is too old):

        ktutil
        addent -password -p HTTP/ogc.example.org@EXAMPLE.ORG -k 1 -e aes256-cts
        wkt service.keytab
        exit
        cat service.keytab | base64

    """
    KEYTAB = (
        "BQIAAABXAAIAC0VYQU1QTEUuT1JHAARIVFRQAA9vZ2MuZXhhbXBsZS5vcmcAAAABXSxM"
        "KQEAEgAgKddJPBCQCDAtxV1NNksmnHT9xkbQLuO5rqFo+a6NEJMAAAAB"
    )

    with NamedTemporaryFile() as f:
        f.write(base64.b64decode(KEYTAB))
        f.flush()

        yield f.name
