# Load libraries
import os
import tempfile
import zipfile

import pytest

from backend.downloader.metadata_extractor import extract_chapters, extract_metadata

CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

CONTENT_OPF = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test Fic Title</dc:title>
    <dc:creator>Author One</dc:creator>
    <dc:creator>Author Two</dc:creator>
    <dc:description>A test summary of the fic.</dc:description>
    <dc:language>en</dc:language>
    <dc:subject>Fantasy</dc:subject>
    <dc:subject>Adventure</dc:subject>
    <meta name="fanficfare:numChapters" content="2"/>
    <meta name="fanficfare:numWords" content="5000"/>
    <meta name="fanficfare:status" content="Complete"/>
    <meta name="fanficfare:rating" content="Teen And Up"/>
    <meta name="fanficfare:siteabbrev" content="ao3"/>
    <meta name="fanficfare:storyId" content="12345"/>
    <meta name="fanficfare:storyUrl" content="https://archiveofourown.org/works/12345"/>
  </metadata>
  <manifest>
    <item id="ch1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="ch2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
    <item id="css" href="style.css" media-type="text/css"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
    <itemref idref="ch2"/>
  </spine>
</package>"""

CHAPTER1_HTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 1</title></head>
<body>
<h2>The Beginning</h2>
<p>It was a dark and stormy night. The wind howled through the trees.</p>
<p>She walked forward into the unknown, her resolve unwavering.</p>
</body>
</html>"""

CHAPTER2_HTML = """<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Chapter 2</title></head>
<body>
<h2>The Journey</h2>
<p>The road stretched endlessly before her. Miles of untouched wilderness.</p>
</body>
</html>"""


def _create_test_epub(directory: str) -> str:
    epub_path = os.path.join(directory, "test.epub")

    with zipfile.ZipFile(epub_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("content.opf", CONTENT_OPF)
        zf.writestr("chapter1.xhtml", CHAPTER1_HTML)
        zf.writestr("chapter2.xhtml", CHAPTER2_HTML)

    return epub_path


def test_extract_metadata():
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_path = _create_test_epub(tmpdir)
        metadata = extract_metadata(epub_path)

        assert metadata["title"] == "Test Fic Title"
        assert "Author One" in metadata["creators"]
        assert "Author Two" in metadata["creators"]
        assert metadata["description"] == "A test summary of the fic."
        assert metadata["language"] == "en"
        assert "Fantasy" in metadata["subjects"]
        assert "Adventure" in metadata["subjects"]
        assert metadata.get("numChapters") == "2"
        assert metadata.get("numWords") == "5000"
        assert metadata.get("status") == "Complete"
        assert metadata.get("rating") == "Teen And Up"
        assert metadata.get("siteabbrev") == "ao3"
        assert metadata.get("storyId") == "12345"


def test_extract_chapters():
    with tempfile.TemporaryDirectory() as tmpdir:
        epub_path = _create_test_epub(tmpdir)
        chapters = extract_chapters(epub_path)

        assert len(chapters) == 2
        assert chapters[0]["chapter_number"] == 1
        assert chapters[0]["title"] == "The Beginning"
        assert chapters[0]["word_count"] > 0
        assert "dark and stormy" in chapters[0]["html_content"]
        assert chapters[1]["chapter_number"] == 2
        assert chapters[1]["title"] == "The Journey"


def test_extract_metadata_invalid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = os.path.join(tmpdir, "bad.epub")

        with open(bad_path, "w") as f:
            f.write("not an epub")

        metadata = extract_metadata(bad_path)
        assert metadata == {}


def test_extract_chapters_invalid_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        bad_path = os.path.join(tmpdir, "bad.epub")

        with open(bad_path, "w") as f:
            f.write("not an epub")

        chapters = extract_chapters(bad_path)
        assert chapters == []
