from passlib.hash import bcrypt_sha256


def hash_password(password):
    """ The default password hashing algorithm used by onegov.

    Over time the underlying algorithm may change, at which point
    :meth:`verify_password` must issue a deprecation warning when using
    the old algorithm.

    Note that no salt is being passed, because the algorithm we use now
    (bcrypt), as well as the algorithm that we might use in the future
    (scrypt), generate their own salt automatically by default.

    The salt is then stored in the resulting hash. That means that we do
    not pass or store a salt ourselves.

    """

    # like bcrypt, but with the ability to support any password length
    return bcrypt_sha256.encrypt(password)


def verify_password(password, hash):
    """ Compares a password to a hash and returns true if they match according
    to the hashing algorithm used.

    """
    return bcrypt_sha256.verify(password, hash)
