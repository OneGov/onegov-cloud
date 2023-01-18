import base64

from cryptography.fernet import Fernet


def test_encrypt_decrypt():
    text_to_encrypt = "the-secret".encode('utf-8')
    rnd = "QGqJPLetYMnULqtDlFmAzvpBf0NMGJWQESoafwUs6OsDWt8AKNxmmasMCsibcnG6"
    key = rnd[32:]
    key_as_bytes = key.encode("utf-8")  # create bytes
    key_as_bytes_base_64 = base64.b64encode(key_as_bytes)

    f = Fernet(key_as_bytes_base_64)
    encrypted_text = f.encrypt(text_to_encrypt)
    decrypted = f.decrypt(encrypted_text)

    assert decrypted == text_to_encrypt
