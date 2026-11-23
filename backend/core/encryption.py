# Load libraries
import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_SALT = b"BibliothecaFabulae-v1"


# Derives a 256-bit key from raw hex or a passphrase via PBKDF2
def _derive_key(key_material: str) -> bytes:
    if len(key_material) == 64:
        try:
            raw = bytes.fromhex(key_material)

            if len(raw) == 32:
                return raw

        except ValueError:
            pass

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=480_000,
    )

    return kdf.derive(key_material.encode())


# Encrypts plaintext and returns a base64-encoded nonce + ciphertext string
def encrypt(plaintext: str, key_material: str) -> str:
    key = _derive_key(key_material)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)

    return base64.b64encode(nonce + ciphertext).decode()


# Decrypts a base64-encoded ciphertext string back to plaintext
def decrypt(
    ciphertext_b64: str,
    key_material: str,
    fallback_key: str | None = None,
) -> str:
    try:
        return _decrypt_with_key(ciphertext_b64, key_material)
    except Exception:
        if fallback_key:
            return _decrypt_with_key(ciphertext_b64, fallback_key)
        raise


def _decrypt_with_key(ciphertext_b64: str, key_material: str) -> str:
    key = _derive_key(key_material)
    raw = base64.b64decode(ciphertext_b64)
    nonce = raw[:12]
    ciphertext = raw[12:]
    aesgcm = AESGCM(key)

    return aesgcm.decrypt(nonce, ciphertext, None).decode()


# Re-encrypts a value under the current key if it was encrypted with a different key
def rotate_value(
    ciphertext_b64: str,
    current_key: str,
    previous_key: str,
) -> tuple[str, bool]:
    try:
        _decrypt_with_key(ciphertext_b64, current_key)
        return ciphertext_b64, False
    except Exception:
        pass

    plaintext = _decrypt_with_key(ciphertext_b64, previous_key)
    return encrypt(plaintext, current_key), True
