import base64
import hashlib
from cryptography.fernet import Fernet
from onegov.gever.encrypt import encrypt_symmetric


def test_encryption_decryption_cycle():

    # Fernet key must be 32 url-safe base64-encoded bytes
    too_long_key = \
        b"QLetYMnULqtDlFmAzvpBf0NMGJWQESoafwUs6OsDWt8AKNxmmasMCsibcnG6"

    hash_object = hashlib.sha256()
    hash_object.update(too_long_key)
    short_key = hash_object.digest()

    assert len(short_key) == 32

    key_base64 = base64.b64encode(short_key)
    text_to_encrypt = "the_secret"
    encrypted_text = encrypt_symmetric(text_to_encrypt, key_base64)
    f = Fernet(key_base64)

    decrypted = f.decrypt(encrypted_text).decode('utf-8')
    assert decrypted == "the_secret"
