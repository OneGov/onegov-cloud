import hashlib
import os


def random_token(nbytes=512):
    """ Generates an unguessable token. Generates a random string with
    the given number of bytes (may not be lower than 512) and hashes
    the result to get a token with a consistent length of 64.

    The number of different tokens is 256^nbytes, so at least 256^512
    tokens by default. That's more tokens than estimated atoms in the universe.

    More information:

    `<http://wyattbaldwin.com/2014/01/09/generating-random-tokens-in-python>`_

    `<http://www.2uo.de/myths-about-urandom/>`_

    `<http://crypto.stackexchange.com/q/1401`>

    """
    assert nbytes >= 512
    return hashlib.sha256(os.urandom(nbytes)).hexdigest()
