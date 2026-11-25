# Load libraries
import pytest

from backend.services.import_service import identify_source_site


def test_identify_ao3():
    result = identify_source_site("https://archiveofourown.org/works/12345")
    assert result == ("ao3", "12345")


def test_identify_ao3_with_chapter():
    result = identify_source_site("https://archiveofourown.org/works/12345/chapters/67890")
    assert result == ("ao3", "12345")


def test_identify_ffnet():
    result = identify_source_site("https://www.fanfiction.net/s/12345678/1/Story-Title")
    assert result == ("ffnet", "12345678")


def test_identify_wattpad():
    result = identify_source_site("https://www.wattpad.com/story/12345-story-title")
    assert result == ("wattpad", "12345")


def test_identify_royalroad():
    result = identify_source_site("https://www.royalroad.com/fiction/12345/story-title")
    assert result == ("royalroad", "12345")


def test_identify_spacebattles():
    result = identify_source_site("https://forums.spacebattles.com/threads/story-title.12345/")
    assert result == ("spacebattles", "12345")


def test_identify_sufficientvelocity():
    result = identify_source_site("https://forums.sufficientvelocity.com/threads/story.12345/")
    assert result == ("sufficientvelocity", "12345")


def test_identify_scribblehub():
    result = identify_source_site("https://www.scribblehub.com/series/12345/story-title/")
    assert result == ("scribblehub", "12345")


def test_identify_fimfiction():
    result = identify_source_site("https://www.fimfiction.net/story/12345/story-title")
    assert result == ("fimfiction", "12345")


def test_identify_unknown():
    result = identify_source_site("https://example.com/unknown")
    assert result is None


def test_identify_empty():
    result = identify_source_site("")
    assert result is None
