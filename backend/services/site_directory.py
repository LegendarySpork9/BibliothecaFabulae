# Load libraries
import logging
import re

logger = logging.getLogger(__name__)

SYNC_CAPABLE_SITES = {
    "archiveofourown.org": {
        "sync_type": "bookmark_sync",
        "sync_label": "Bookmark Sync",
        "sync_description": "Automatically syncs your AO3 bookmarks",
        "auth_required": True,
        "config_required": False,
        "auth_help": {
            "credentials": {
                "format": '{"username": "your_ao3_username", "password": "your_ao3_password"}',
                "instructions": "Use your AO3 username and password. If AO3 has Cloudflare protection active, use cookies instead.",
            },
            "cookies": {
                "format": "_otwarchive_session=abc123; user_credentials=xyz789",
                "instructions": "Open AO3 in your browser while logged in. Press F12 → Application tab → Cookies → archiveofourown.org. Copy the _otwarchive_session cookie value.",
                "expiry": "2 weeks (3 months with 'Remember Me')",
            },
        },
        "config_help": None,
    },
    "www.fanfiction.net": {
        "sync_type": "favourites_sync",
        "sync_label": "Favourites Sync",
        "sync_description": "Syncs favourites from your FFNet profile page. FFNet has aggressive Cloudflare protection — cookies are recommended.",
        "auth_required": False,
        "config_required": True,
        "auth_help": {
            "cookies": {
                "format": "cf_clearance=abc123",
                "instructions": "FFNet is behind Cloudflare. If sync fails without cookies, log into FFNet in your browser, press F12 → Application tab → Cookies → fanfiction.net. Copy the cf_clearance cookie and any session cookies.",
                "expiry": "Session-based (varies, typically hours to days)",
            },
        },
        "config_help": {
            "profile_url": {
                "format": '{"profile_url": "https://www.fanfiction.net/u/YOUR_ID/YOUR_NAME"}',
                "instructions": "Go to your FFNet profile page and copy the full URL from the address bar.",
            },
        },
    },
    "www.fimfiction.net": {
        "sync_type": "bookshelf_sync",
        "sync_label": "Bookshelf Sync",
        "sync_description": "Syncs stories from a Fimfiction bookshelf",
        "auth_required": False,
        "config_required": True,
        "auth_help": {
            "cookies": {
                "format": "session_token=abc123",
                "instructions": "Only needed for private bookshelves. Log into Fimfiction in your browser, press F12 → Application tab → Cookies → fimfiction.net. Copy the session cookies.",
                "expiry": "Session-based (typically days to weeks)",
            },
        },
        "config_help": {
            "bookshelf_url": {
                "format": '{"bookshelf_url": "https://www.fimfiction.net/bookshelf/YOUR_ID/name"}',
                "instructions": "Go to your Fimfiction profile → Bookshelves. Click the bookshelf you want to sync and copy the URL from the address bar.",
            },
        },
    },
    "forums.spacebattles.com": {
        "sync_type": "watched_threads",
        "sync_label": "Watched Threads Sync",
        "sync_description": "Syncs your watched threads list",
        "auth_required": True,
        "config_required": True,
        "auth_help": {
            "cookies": {
                "format": "xf_session=abc123; xf_user=xyz789",
                "instructions": "Log into SpaceBattles in your browser. Press F12 → Application tab → Cookies → forums.spacebattles.com. Copy the xf_session and xf_user cookie values. The xf_user cookie provides persistent login.",
                "expiry": "xf_session: 1 hour of inactivity. xf_user: 30 days (with 'Stay logged in')",
            },
        },
        "config_help": {
            "watched_url": {
                "format": '{"watched_url": "https://forums.spacebattles.com/watched/threads"}',
                "instructions": "This is the URL of your watched threads page. The default URL works for most users.",
            },
        },
    },
    "forums.sufficientvelocity.com": {
        "sync_type": "watched_threads",
        "sync_label": "Watched Threads Sync",
        "sync_description": "Syncs your watched threads list",
        "auth_required": True,
        "config_required": True,
        "auth_help": {
            "cookies": {
                "format": "xf_session=abc123; xf_user=xyz789",
                "instructions": "Log into Sufficient Velocity in your browser. Press F12 → Application tab → Cookies → forums.sufficientvelocity.com. Copy the xf_session and xf_user cookie values. The xf_user cookie provides persistent login.",
                "expiry": "xf_session: 1 hour of inactivity. xf_user: 30 days (with 'Stay logged in')",
            },
        },
        "config_help": {
            "watched_url": {
                "format": '{"watched_url": "https://forums.sufficientvelocity.com/watched/threads"}',
                "instructions": "This is the URL of your watched threads page. The default URL works for most users.",
            },
        },
    },
    "www.royalroad.com": {
        "sync_type": "reading_list",
        "sync_label": "Reading List Sync",
        "sync_description": "Syncs your Read Later list",
        "auth_required": True,
        "config_required": True,
        "auth_help": {
            "cookies": {
                "format": ".AspNetCore.Identity.Application=abc123",
                "instructions": "Log into Royal Road in your browser. Press F12 → Application tab → Cookies → www.royalroad.com. Copy the .AspNetCore.Identity.Application cookie value.",
                "expiry": "14 days (with sliding expiration — refreshed on activity)",
            },
        },
        "config_help": {
            "readlist_url": {
                "format": '{"readlist_url": "https://www.royalroad.com/my/readlater"}',
                "instructions": "This is the URL of your Read Later list. The default URL works for most users.",
            },
        },
    },
}

FRIENDLY_NAMES = {
    "althistory.com": "Alternate History (AltHistory)",
    "archive.fanfictalk.com": "FanFic Talk Archive",
    "archiveofourown.org": "Archive of Our Own (AO3)",
    "ashwinder.sycophanthex.com": "Ashwinder (Sycophant Hex)",
    "bloodshedverse.com": "Bloodshedverse",
    "chaos.sycophanthex.com": "Chaos (Sycophant Hex)",
    "chireads.com": "Chireads",
    "chosentwofanfic.com": "Chosen Two Fanfic",
    "dark-solace.org": "Dark Solace",
    "efpfanfic.net": "EFP Fanfic",
    "erosnsappho.sycophanthex.com": "Eros & Sappho (Sycophant Hex)",
    "fanfics.me": "Fanfics.me",
    "ficbook.net": "Ficbook",
    "fiction.live": "Fiction.live",
    "fictionhunt.com": "Fiction Hunt",
    "fictionmania.tv": "FictionMania",
    "ficwad.com": "FicWad",
    "forum.questionablequesting.com": "Questionable Questing",
    "forums.spacebattles.com": "SpaceBattles",
    "forums.sufficientvelocity.com": "Sufficient Velocity",
    "gluttonyfiction.com": "Gluttony Fiction",
    "imagine.e-fic.com": "Imagine eFic",
    "inkbunny.net": "Inkbunny",
    "kakuyomu.jp": "Kakuyomu",
    "ksarchive.com": "KS Archive",
    "lcfanfic.com": "LC Fanfic",
    "literotica.com": "Literotica",
    "lumos.sycophanthex.com": "Lumos (Sycophant Hex)",
    "mcstories.com": "MC Stories",
    "mtt.just-once.net": "MTT Just Once",
    "ncisfiction.com": "NCIS Fiction",
    "ninelivesarchive.com": "Nine Lives Archive",
    "novelfull.com": "NovelFull",
    "novelonlinefull.com": "Novel Online Full",
    "occlumency.sycophanthex.com": "Occlumency (Sycophant Hex)",
    "quotev.com": "Quotev",
    "readonlymind.com": "Read Only Mind",
    "samandjack.net": "Sam and Jack",
    "scifistories.com": "Sci-Fi Stories",
    "sheppardweir.com": "Sheppard/Weir",
    "sinful-dreams.com/unicorn/fic": "Sinful Dreams (Unicorn)",
    "sinful-dreams.com/wicked/temptation": "Sinful Dreams (Wicked Temptation)",
    "sofurry.com": "SoFurry",
    "spikeluver.com": "Spike Luver",
    "squidgeworld.org": "Squidgeworld",
    "starslibrary.net": "Stars Library",
    "storiesonline.net": "Stories Online",
    "storyroom.com": "Story Room",
    "superlove.sayitditto.net": "Superlove",
    "syosetu.com": "Syosetu",
    "t.evancurrie.ca": "Evan Currie",
    "tgstorytime.com": "TG Storytime",
    "thehookupzone.net": "The Hook Up Zone",
    "themasque.net": "The Masque",
    "touchfluffytail.org": "Touch Fluffy Tail",
    "trekfanfiction.net": "Trek Fan Fiction",
    "valentchamber.com": "Valent Chamber",
    "voracity2.e-fic.com": "Voracity eFic",
    "www.adastrafanfic.com": "Ad Astra Fanfic",
    "www.adult-fanfiction.org": "Adult-FanFiction.org",
    "www.alternatehistory.com": "Alternate History",
    "www.aneroticstory.com": "An Erotic Story",
    "www.asexstories.com": "Asex Stories",
    "www.asianfanfics.com": "Asian Fanfics",
    "www.bdsmlibrary.com": "BDSM Library",
    "www.cfaarchive.org": "CFA Archive",
    "www.deviantart.com": "DeviantArt",
    "www.dokuga.com": "Dokuga",
    "www.dracoandginny.com": "Draco and Ginny",
    "www.fanficauthors.net": "FanFic Authors",
    "www.fanfiction.net": "FanFiction.Net",
    "www.fanfictions.fr": "FanFictions.fr",
    "www.fanfiktion.de": "FanFiktion.de",
    "www.fictionalley-archive.org": "Fiction Alley Archive",
    "www.fictionpress.com": "FictionPress",
    "www.fimfiction.net": "Fimfiction",
    "www.fireflyfans.net": "Firefly Fans",
    "www.giantessworld.net": "Giantess World",
    "www.hentai-foundry.com": "Hentai Foundry",
    "www.libraryofmoria.com": "Library of Moria",
    "www.masseffect2.in": "Mass Effect 2",
    "www.mediaminer.org": "MediaMiner",
    "www.midnightwhispers.net": "Midnight Whispers",
    "www.mugglenetfanfiction.com": "MuggleNet Fan Fiction",
    "www.naiceanilme.net": "Naice a Nilme",
    "www.narutofic.org": "NarutoFic",
    "www.novelall.com": "Novel All",
    "www.phoenixsong.net": "Phoenix Song",
    "www.pmdfanfiction.com": "PMD Fanfiction",
    "www.potionsandsnitches.org": "Potions and Snitches",
    "www.pretendercentre.com": "Pretender Centre",
    "www.psychfic.com": "Psych Fic",
    "www.royalroad.com": "Royal Road",
    "www.scribblehub.com": "Scribble Hub",
    "www.siye.co.uk": "SIYE",
    "www.spiritfanfiction.com": "Spirit Fanfiction",
    "www.storiesofarda.com": "Stories of Arda",
    "www.sunnydaleafterdark.com": "Sunnydale After Dark",
    "www.the-sietch.com": "The Sietch",
    "www.thedelphicexpanse.com": "The Delphic Expanse",
    "www.tthfanfic.org": "Twisting the Hellmouth",
    "www.twilighted.net": "Twilighted",
    "www.utopiastories.com": "Utopia Stories",
    "www.walkingtheplank.org": "Walking the Plank",
    "www.wattpad.com": "Wattpad",
    "www.whofic.com": "WhoFic",
    "www.wolverineandrogue.com": "Wolverine and Rogue",
}

_TEST_SITES = {"test1.com", "test2.com", "test3.com", "test4.com"}


# Returns the full site directory with capabilities
def get_site_directory() -> list[dict]:
    try:
        from fanficfare.adapters import getSiteExamples

        examples = getSiteExamples()
    except Exception:
        logger.exception("Failed to load FanFicFare site examples")
        examples = []

    sites = []

    for domain, urls in examples:
        if domain in _TEST_SITES:
            continue

        name = FRIENDLY_NAMES.get(domain, _domain_to_name(domain))
        sync_info = SYNC_CAPABLE_SITES.get(domain)

        sites.append({
            "domain": domain,
            "name": name,
            "example_urls": urls[:2],
            "manual_import": True,
            "update_checking": True,
            "list_sync": sync_info is not None,
            "sync_type": sync_info["sync_type"] if sync_info else None,
            "sync_label": sync_info["sync_label"] if sync_info else None,
            "sync_description": sync_info["sync_description"] if sync_info else None,
            "auth_required": sync_info.get("auth_required", False) if sync_info else False,
            "config_required": sync_info.get("config_required", False) if sync_info else False,
            "auth_help": sync_info.get("auth_help") if sync_info else None,
            "config_help": sync_info.get("config_help") if sync_info else None,
        })

    sites.sort(key=lambda s: s["name"].lower())

    return sites


# Converts a domain string to a human-readable site name
def _domain_to_name(domain: str) -> str:
    name = domain.replace("www.", "").replace("forums.", "").replace("forum.", "")
    name = re.sub(r"\.(com|org|net|co\.uk|de|fr|jp|tv)$", "", name)

    return name.replace("-", " ").replace(".", " ").title()
