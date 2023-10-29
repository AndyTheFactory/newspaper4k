from newspaper.utils import StringReplacement, StringSplitter

MOTLEY_REPLACEMENT = StringReplacement("&#65533;", "")
ESCAPED_FRAGMENT_REPLACEMENT = StringReplacement("#!", "?_escaped_fragment_=")
TITLE_REPLACEMENTS = StringReplacement("&raquo;", "»")
PIPE_SPLITTER = StringSplitter("\\|")
DASH_SPLITTER = StringSplitter(" - ")
UNDERSCORE_SPLITTER = StringSplitter("_")
SLASH_SPLITTER = StringSplitter("/")
ARROWS_SPLITTER = StringSplitter(" » ")
COLON_SPLITTER = StringSplitter(":")
SPACE_SPLITTER = StringSplitter(" ")
NO_STRINGS = set()
A_REL_TAG_SELECTOR = "a[rel=tag]"
A_HREF_TAG_SELECTOR = (
    "a[href*='/tag/'], a[href*='/tags/'], " "a[href*='/topic/'], a[href*='?keyword=']"
)
RE_LANG = r"^[A-Za-z]{2}$"

PUBLISH_DATE_TAGS = [
    {
        "attribute": "property",
        "value": "rnews:datePublished",
        "content": "content",
    },
    {
        "attribute": "property",
        "value": "article:published_time",
        "content": "content",
    },
    {
        "attribute": "name",
        "value": "OriginalPublicationDate",
        "content": "content",
    },
    {"attribute": "itemprop", "value": "datePublished", "content": "datetime"},
    {
        "attribute": "property",
        "value": "og:published_time",
        "content": "content",
    },
    {
        "attribute": "name",
        "value": "article_date_original",
        "content": "content",
    },
    {"attribute": "name", "value": "publication_date", "content": "content"},
    {"attribute": "name", "value": "sailthru.date", "content": "content"},
    {"attribute": "name", "value": "PublishDate", "content": "content"},
    {"attribute": "pubdate", "value": "pubdate", "content": "datetime"},
    {"attribute": "name", "value": "pubdate", "content": "content"},
    {"attribute": "name", "value": "publish_date", "content": "content"},
    {"attribute": "name", "value": "dc.date", "content": "content"},
    {"attribute": "class", "value": "entry-date", "content": "datetime"},
]

url_stopwords = [
    "about",
    "help",
    "privacy",
    "legal",
    "feedback",
    "sitemap",
    "profile",
    "account",
    "mobile",
    "sitemap",
    "facebook",
    "myspace",
    "twitter",
    "linkedin",
    "bebo",
    "friendster",
    "stumbleupon",
    "youtube",
    "vimeo",
    "store",
    "mail",
    "preferences",
    "maps",
    "password",
    "imgur",
    "flickr",
    "search",
    "subscription",
    "itunes",
    "siteindex",
    "events",
    "stop",
    "jobs",
    "careers",
    "newsletter",
    "subscribe",
    "academy",
    "shopping",
    "purchase",
    "site-map",
    "shop",
    "donate",
    "newsletter",
    "product",
    "advert",
    "info",
    "tickets",
    "coupons",
    "forum",
    "board",
    "archive",
    "browse",
    "howto",
    "how to",
    "faq",
    "terms",
    "charts",
    "services",
    "contact",
    "plus",
    "admin",
    "login",
    "signup",
    "register",
    "developer",
    "proxy",
]
