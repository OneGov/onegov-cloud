import re

from yubico_client import Yubico
from yubico_client.yubico_exceptions import (
    StatusCodeError,
    SignatureVerificationError
)


def is_valid_yubikey(client_id, secret_key, expected_yubikey_id, yubikey):
    """ Asks the yubico validation servers if the given yubikey OTP is valid.

    :client_id:
        The yubico API client id.

    :secret_key:
        The yubico API secret key.

    :expected_yubikey_id:
        The expected yubikey id. The yubikey id is defined as the first twelve
        characters of any yubikey value. Each user should have a yubikey
        associated with it's account. If the yubikey value comes from a
        different key, the key is invalid.

    :yubikey:
        The actual yubikey value that should be verified.

    :return: True if yubico confirmed the validity of the key.

    """
    assert client_id and secret_key and expected_yubikey_id and yubikey
    assert len(expected_yubikey_id) == 12

    # if the yubikey doesn't start with the expected yubikey id we do not
    # need to make a roundtrip to the validation server
    if not yubikey.startswith(expected_yubikey_id):
        return False

    try:
        return Yubico(client_id, secret_key).verify(yubikey)
    except StatusCodeError as e:
        if e.status_code != 'REPLAYED_OTP':
            raise e

        return False
    except SignatureVerificationError as e:
        return False


ALPHABET = 'cbdefghijklnrtuv'
ALPHABET_RE = re.compile(r'^[cbdefghijklnrtuv]{12,44}$')


def is_valid_yubikey_format(otp):
    """ Returns True if the given OTP has the correct format. Does not actually
    contact Yubico, so this function may return true, for some invalid keys.

    """

    return ALPHABET_RE.match(otp) and True or False


def yubikey_otp_to_serial(otp):
    """ Takes a Yubikey OTP and calculates the serial number of the key.

    The serial key is printed on the yubikey, in decimal and as a QR code.

    Example:

        >>> yubikey_otp_to_serial(
            'ccccccdefghdefghdefghdefghdefghdefghdefghklv')
        2311522

    Adapted from Java:

        https://github.com/Yubico/yubikey-salesforce-client/blob/
        e38e46ee90296a852374a8b744555e99d16b6ca7/src/classes/Modhex.cls

    If the key cannot be calculated, None is returned. This can happen if
    they key is malformed.

    """

    if not is_valid_yubikey_format(otp):
        return None

    token = 'cccc' + otp[:12]

    toggle = False
    keep = 0

    bytesarray = []

    for char in token:
        n = ALPHABET.index(char)

        toggle = not toggle

        if toggle:
            keep = n
        else:
            bytesarray.append((keep << 4) | n)

    value = 0

    # in Java, shifts on integers are masked with 0x1f using AND
    # https://docs.oracle.com/javase/specs/jls/se8/html/jls-15.html#jls-15.19
    mask_value = 0x1f

    for i in range(0, 8):
        shift = (4 - 1 - i) * 8
        value += (bytesarray[i] & 255) << (shift & mask_value)

    return value
