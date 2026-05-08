from __future__ import annotations

import base64
import pytest
from tempfile import NamedTemporaryFile

from onegov.core.utils import module_path


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(scope='session')
def keytab() -> Iterator[str]:
    """ BASE 64 encoded keytab file for Kerberos integration tests

    Principal: HTTP/ogc.example.org@EXAMPLE.ORG
    Password: test

    To create, start ktutil (the latest release, macOS's one is too old)*.

        ktutil
        addent -password -p HTTP/ogc.example.org@EXAMPLE.ORG -k 1 -e aes256-cts
        wkt service.keytab
        exit
        cat service.keytab | base64

    * Use 'brew install krb5', then run '/usr/local/opt/krb5/bin/ktutil'

    """
    KEYTAB = (
        "BQIAAABXAAIAC0VYQU1QTEUuT1JHAARIVFRQAA9vZ2MuZXhhbXBsZS5vcmcAAAABXSxM"
        "KQEAEgAgKddJPBCQCDAtxV1NNksmnHT9xkbQLuO5rqFo+a6NEJMAAAAB"
    )

    with NamedTemporaryFile() as f:
        f.write(base64.b64decode(KEYTAB))
        f.flush()

        yield f.name


@pytest.fixture(scope='session')
def idp_metadata() -> str:
    return module_path('tests.onegov.user', '/fixtures/idp.xml')
