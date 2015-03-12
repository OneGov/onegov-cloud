import hashlib
import binascii
import os


def random_token(nbytes=512):
    """ Generates an unguessable token. Generates a random string with
    the given number of bytes (may not be lower than 512) and hashes
    the result to get a token with a consistent length of 64.

    More information:

    `<http://wyattbaldwin.com/2014/01/09/generating-random-tokens-in-python>`_

    `<http://www.2uo.de/myths-about-urandom/>`_

    """
    assert nbytes >= 512

    random_string = binascii.hexlify(os.urandom(nbytes))
    return hashlib.sha256(random_string).hexdigest()
