# Load libraries
from backend.downloader.rating_map import normalize_rating


# Test that a known FFN rating maps to its friendly name
def test_normalize_known_rating_k():
    assert normalize_rating("K") == "Kids (5+)"


# Test that a known AO3 rating maps to its friendly name
def test_normalize_known_rating_explicit():
    assert normalize_rating("Explicit") == "Explicit"


# Test that an unknown rating string is returned as-is
def test_normalize_unknown_rating():
    assert normalize_rating("SomeUnknownRating") == "SomeUnknownRating"


# Test that None input returns None
def test_normalize_none():
    assert normalize_rating(None) is None


# Test that an empty string returns None
def test_normalize_empty():
    assert normalize_rating("") is None


# Test that surrounding whitespace is stripped before lookup
def test_normalize_whitespace():
    assert normalize_rating("  T  ") == "Teen (13+)"
