# Maps site-specific rating codes to friendly display names

RATING_MAP: dict[str, str] = {
    # FanFiction.Net
    "K": "Kids (5+)",
    "K+": "Kids Plus (9+)",
    "T": "Teen (13+)",
    "M": "Mature (16+)",

    # AO3
    "General Audiences": "General Audiences",
    "Teen And Up Audiences": "Teen And Up",
    "Teen And Up": "Teen And Up",
    "Mature": "Mature",
    "Explicit": "Explicit",
    "Not Rated": "Not Rated",

    # Wattpad
    "everyone": "Everyone",
    "Everyone": "Everyone",
    "mature": "Mature (17+)",

    # Fimfiction
    "Everyone": "Everyone",
    "Teen": "Teen",
    "Mature": "Mature",
    "Sex": "Explicit (Sex)",
    "Gore": "Explicit (Gore)",

    # SpaceBattles / Sufficient Velocity / XenForo
    "Threadmarked": "Threadmarked",

    # Royal Road uses content warnings, not ratings
    # Scribble Hub
    "All Ages": "All Ages",
    "Teen (13+)": "Teen (13+)",
    "Mature (17+)": "Mature (17+)",
    "R-18": "Adult (18+)",
}


# Normalizes a raw rating string to its friendly display name
def normalize_rating(raw_rating: str | None) -> str | None:
    if not raw_rating:
        return None

    stripped = raw_rating.strip()

    if stripped in RATING_MAP:
        return RATING_MAP[stripped]

    return stripped
