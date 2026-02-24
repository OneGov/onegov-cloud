from __future__ import annotations

import hashlib
import os
import secrets


# for external reference, update if the hashing function ever changes
RANDOM_TOKEN_LENGTH = 64


def random_token(nbytes: int = 512) -> str:
    """ Generates an unguessable token. Generates a random string with
    the given number of bytes (may not be lower than 512) and hashes
    the result to get a token with a consistent length of 64.

    Why hashing?

    We could of course just create a random token with a length of 64, but that
    would leak the random numbers we actually create. This can be a bit of
    a problem if the random generator you use turns out to have some
    vulnerability. By hashing a larger number we hide the result of our random
    generator.

    Doesn't generating a hash from a larger number limit the number of tokens?

    Yes it does. The number of different tokens is 2^256 after hashing,
    which is a number larger than all the atoms on earth (approx. 2^166).
    So there is a chance of a collision occuring, but it is *very* unlikely
    to *ever* happen.

    More information:

    `<https://wyattbaldwin.com/2014/01/09/generating-random-tokens-in-python>`_

    `<https://www.2uo.de/myths-about-urandom/>`_

    `<https://crypto.stackexchange.com/q/1401>`_

    """
    assert nbytes >= 512
    return hashlib.sha256(secrets.token_bytes(nbytes)).hexdigest()


def stored_random_token(namespace: str, name: str) -> str:
    """ A random token that is only created once per boot of the host
    (assuming the host deletes all files in the /tmp folder).

    This method should only be used for development and is not meant for
    general use!

    """
    # NOTE: Since this is only used for development:
    #       The hardcoded path is a feature, not a bug
    namespace_dir = os.path.join('/tmp/onegov-secrets', namespace)  # nosec:B108
    os.makedirs(namespace_dir, mode=0o700, exist_ok=True)

    path = os.path.join(namespace_dir, name)
    if os.path.isfile(path):
        with open(path) as f:
            return f.read()

    token = random_token()

    with open(path, mode='w') as f:
        f.write(token)

    os.chmod(path, 0o400)
    return token
