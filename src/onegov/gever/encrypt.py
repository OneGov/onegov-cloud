from cryptography.fernet import Fernet


def encrypt_symmetric(plaintext, key_base64) -> bytes:
    """ Encrypts the given text using Fernet (symmetric encryption).

    plaintext (str): The data to encrypt.
    key (bytes): The encryption key, base-64 encoded bytes.

    Returns: the encrypted data in bytes.
    """
    text_to_encrypt = plaintext.encode("utf-8")
    f = Fernet(key_base64)
    encrypted = f.encrypt(text_to_encrypt)
    return encrypted


def decrypt_symmetric(fernet_token, key_base64) -> str:
    """ Decrypts the encrypted data using the provided key.

    fernet_token (bytes): Data to decrypt.
    key (bytes): The encryption key: 32 url-safe base64-encoded bytes.

    Returns the decrypted text.
    """
    f = Fernet(key_base64)
    decrypted = f.decrypt(fernet_token).decode("utf-8")
    return decrypted
