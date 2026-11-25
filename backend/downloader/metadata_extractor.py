# Load libraries
import json
import logging
import os
import xml.etree.ElementTree as ET
import zipfile

logger = logging.getLogger(__name__)

_DC = "http://purl.org/dc/elements/1.1/"
_OPF = "http://www.idpf.org/2007/opf"


# Splits a comma-separated string into a list, unescaping HTML entities
def _split_csv(value: str) -> list[str]:
    import html as html_mod

    if not value:
        return []

    return [html_mod.unescape(v.strip()) for v in value.split(",") if v.strip()]


# Loads the .json metadata file that FanFicFare writes alongside the EPUB
def load_fff_json_metadata(epub_path: str) -> dict | None:
    json_path = epub_path + ".json"

    if not os.path.exists(json_path):
        return None

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        import html as html_mod

        return {
            "title": html_mod.unescape(raw.get("title", "")),
            "creators": _split_csv(raw.get("author", "")),
            "description": _strip_html_tags(raw.get("description", "")),
            "language": raw.get("langcode", raw.get("language", "")),
            "rating": html_mod.unescape(raw.get("rating", "") or ""),
            "warnings": html_mod.unescape(raw.get("warnings", "") or ""),
            "ao3categories": _split_csv(raw.get("ao3categories", "")),
            "fandoms": _split_csv(raw.get("fandoms", raw.get("category", ""))),
            "ships": _split_csv(raw.get("ships", "")),
            "characters": _split_csv(raw.get("characters", "")),
            "freeformtags": _split_csv(raw.get("freeformtags", "")),
            "numChapters": raw.get("numChapters"),
            "numWords": raw.get("numWords", "").replace(",", ""),
            "status": raw.get("status", ""),
            "datePublished": raw.get("datePublished"),
            "dateUpdated": raw.get("dateUpdated"),
            "siteabbrev": raw.get("siteabbrev"),
            "storyId": raw.get("storyId"),
            "storyUrl": raw.get("storyUrl"),
            "authorUrl": raw.get("authorUrl"),
            "authorId": raw.get("authorId"),
            "subjects": _split_csv(raw.get("genre", "")),
        }

    except Exception:
        logger.exception("Failed to load FanFicFare JSON metadata from %s", json_path)

        return None


# Strips HTML tags from a string, returning plain text
def _strip_html_tags(html: str) -> str:
    if not html:
        return ""

    import re

    text = re.sub(r"<[^>]+>", " ", html)

    return " ".join(text.split()).strip()


# Extracts metadata from an EPUB's OPF content file
def extract_metadata(epub_path: str) -> dict:
    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            opf_path = _find_opf(zf)

            if not opf_path:
                return {}

            opf_content = zf.read(opf_path).decode("utf-8")
            root = ET.fromstring(opf_content)
            md = root.find(f"{{{_OPF}}}metadata")

            if md is None:
                md = root.find("metadata")

            if md is None:
                return {}

            return _parse_opf_metadata(md)

    except Exception:
        logger.exception("Failed to extract metadata from %s", epub_path)

        return {}


# Extracts chapter information and HTML content from an EPUB
def extract_chapters(epub_path: str) -> list[dict]:
    try:
        with zipfile.ZipFile(epub_path, "r") as zf:
            opf_path = _find_opf(zf)

            if not opf_path:
                return []

            opf_dir = os.path.dirname(opf_path)
            opf_content = zf.read(opf_path).decode("utf-8")
            root = ET.fromstring(opf_content)

            spine = root.find(f"{{{_OPF}}}spine")
            manifest = root.find(f"{{{_OPF}}}manifest")

            if spine is None:
                spine = root.find("spine")

            if manifest is None:
                manifest = root.find("manifest")

            if spine is None or manifest is None:
                return []

            item_map = {}

            for item in manifest.findall(f"{{{_OPF}}}item"):
                item_id = item.get("id", "")
                href = item.get("href", "")
                media_type = item.get("media-type", "")
                item_map[item_id] = {"href": href, "media_type": media_type}

            for item in manifest.findall("item"):
                item_id = item.get("id", "")
                href = item.get("href", "")
                media_type = item.get("media-type", "")
                item_map[item_id] = {"href": href, "media_type": media_type}

            chapters = []
            chapter_num = 0

            spine_items = spine.findall(f"{{{_OPF}}}itemref") or spine.findall("itemref")

            for itemref in spine_items:
                idref = itemref.get("idref", "")
                item = item_map.get(idref)

                if not item:
                    continue

                if "html" not in item["media_type"] and "xhtml" not in item["media_type"]:
                    continue

                href_lower = item["href"].lower()
                idref_lower = idref.lower()

                if "title_page" in href_lower or "title_page" in idref_lower:
                    continue

                if "titlepage" in href_lower or "titlepage" in idref_lower:
                    continue

                file_path = os.path.join(opf_dir, item["href"]).replace("\\", "/")

                try:
                    html_content = zf.read(file_path).decode("utf-8")

                except KeyError:
                    try:
                        html_content = zf.read(item["href"]).decode("utf-8")

                    except KeyError:
                        continue

                chapter_num += 1
                title = _extract_chapter_title(html_content, chapter_num)
                word_count = _count_words(html_content)

                chapters.append({
                    "chapter_number": chapter_num,
                    "title": title,
                    "html_content": html_content,
                    "word_count": word_count,
                })

            return chapters

    except Exception:
        logger.exception("Failed to extract chapters from %s", epub_path)

        return []


# Finds the .opf content file within the EPUB archive
def _find_opf(zf: zipfile.ZipFile) -> str | None:
    try:
        container = zf.read("META-INF/container.xml").decode("utf-8")
        root = ET.fromstring(container)

        for rootfile in root.iter():
            if rootfile.tag.endswith("rootfile"):
                return rootfile.get("full-path")

    except (KeyError, ET.ParseError):
        pass

    for name in zf.namelist():
        if name.endswith(".opf"):
            return name

    return None


# Parses OPF metadata element into a dictionary
def _parse_opf_metadata(md: ET.Element) -> dict:
    metadata: dict = {}

    # Returns the text content of the first matching element, or None
    def _text(tag: str, ns: str = _DC) -> str | None:
        el = md.find(f"{{{ns}}}{tag}")

        if el is None:
            el = md.find(tag)

        return el.text.strip() if el is not None and el.text else None

    # Returns text content of all matching elements as a deduplicated list
    def _all_text(tag: str, ns: str = _DC) -> list[str]:
        results = []

        for el in md.findall(f"{{{ns}}}{tag}"):
            if el.text and el.text.strip():
                results.append(el.text.strip())

        for el in md.findall(tag):
            if el.text and el.text.strip():
                val = el.text.strip()

                if val not in results:
                    results.append(val)

        return results

    metadata["title"] = _text("title")
    metadata["creators"] = _all_text("creator")
    metadata["description"] = _text("description")
    metadata["language"] = _text("language")
    metadata["publisher"] = _text("publisher")
    metadata["date"] = _text("date")
    metadata["subjects"] = _all_text("subject")

    for meta in md.findall(f"{{{_OPF}}}meta"):
        name = meta.get("name", "")
        content = meta.get("content", "")

        if name and content:
            key = name.replace("fanficfare:", "").replace("calibre:", "")
            metadata[key] = content

    for meta in md.findall("meta"):
        name = meta.get("name", "")
        content = meta.get("content", "")

        if name and content:
            key = name.replace("fanficfare:", "").replace("calibre:", "")
            metadata[key] = content

    return metadata


# Extracts a chapter title from its HTML content
def _extract_chapter_title(html: str, default_num: int) -> str:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "xml")

        for tag in ["h1", "h2", "h3"]:
            heading = soup.find(tag)

            if heading and heading.get_text(strip=True):
                return heading.get_text(strip=True)

        title = soup.find("title")

        if title and title.get_text(strip=True):
            return title.get_text(strip=True)

    except Exception:
        pass

    return f"Chapter {default_num}"


# Counts words in an HTML string by stripping tags
def _count_words(html: str) -> int:
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "xml")
        text = soup.get_text(separator=" ", strip=True)

        return len(text.split())

    except Exception:
        pass

    import re

    text = re.sub(r"<[^>]+>", " ", html)

    return len(text.split())
