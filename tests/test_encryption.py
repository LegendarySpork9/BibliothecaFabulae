# Load libraries
import pytest

from backend.core.encryption import decrypt, encrypt, rotate_value


# Test that encrypting then decrypting returns the original plaintext
def test_encrypt_decrypt_roundtrip():
    key = "my-secret-key-for-testing"
    plaintext = "sensitive data here"

    ciphertext = encrypt(plaintext, key)
    result = decrypt(ciphertext, key)
    assert result == plaintext


# Test that different inputs produce different ciphertexts
def test_different_plaintexts_produce_different_ciphertexts():
    key = "my-secret-key-for-testing"

    ct1 = encrypt("hello", key)
    ct2 = encrypt("world", key)
    assert ct1 != ct2


# Test that the same input produces unique ciphertexts each time
def test_same_plaintext_produces_different_ciphertexts():
    key = "my-secret-key-for-testing"
    plaintext = "same data"

    ct1 = encrypt(plaintext, key)
    ct2 = encrypt(plaintext, key)
    assert ct1 != ct2


# Test that decryption with an incorrect key raises an exception
def test_wrong_key_fails():
    ciphertext = encrypt("secret", "correct-key")

    with pytest.raises(Exception):
        decrypt(ciphertext, "wrong-key")


# Test that a 64-character hex string is accepted as a key
def test_hex_key_used_directly():
    hex_key = "a" * 64
    plaintext = "test with hex key"

    ciphertext = encrypt(plaintext, hex_key)
    result = decrypt(ciphertext, hex_key)
    assert result == plaintext


# Test that fallback key decrypts when primary key fails
def test_decrypt_fallback_key():
    old_key = "old-key"
    new_key = "new-key"
    plaintext = "secret data"

    ciphertext = encrypt(plaintext, old_key)

    with pytest.raises(Exception):
        decrypt(ciphertext, new_key)

    result = decrypt(ciphertext, new_key, fallback_key=old_key)
    assert result == plaintext


# Test that primary key is tried first even when fallback is provided
def test_decrypt_prefers_primary_key():
    key = "primary-key"
    plaintext = "data"

    ciphertext = encrypt(plaintext, key)
    result = decrypt(ciphertext, key, fallback_key="other-key")
    assert result == plaintext


# Test that rotate_value re-encrypts data encrypted with the old key
def test_rotate_value_re_encrypts():
    old_key = "old-key"
    new_key = "new-key"
    plaintext = "rotate me"

    old_ciphertext = encrypt(plaintext, old_key)
    new_ciphertext, changed = rotate_value(old_ciphertext, new_key, old_key)

    assert changed is True
    assert new_ciphertext != old_ciphertext
    assert decrypt(new_ciphertext, new_key) == plaintext


# Test that rotate_value skips data already encrypted with the current key
def test_rotate_value_skips_current():
    key = "current-key"
    plaintext = "already current"

    ciphertext = encrypt(plaintext, key)
    result, changed = rotate_value(ciphertext, key, "old-key")

    assert changed is False
    assert result == ciphertext
