from newspaper.utils import StringReplacement

MOTLEY_REPLACEMENT = StringReplacement("&#65533;", "")
ESCAPED_FRAGMENT_REPLACEMENT = StringReplacement("#!", "?_escaped_fragment_=")
TITLE_REPLACEMENTS = StringReplacement("&raquo;", "»")

A_REL_TAG_SELECTOR = "a[rel=tag]"
A_HREF_TAG_SELECTOR = (
    "a[href*='/tag/'], a[href*='/tags/'], a[href*='/topic/'], a[href*='?keyword=']"
)
RE_LANG = r"^[A-Za-z]{2}$"

AUTHOR_ATTRS = ["name", "rel", "itemprop", "class", "id", "property"]
AUTHOR_VALS = [
    "author",
    "byline",
    "dc.creator",
    "byl",
    "article:author",
    "story-byline",
    "article-author",
]
AUTHOR_STOP_WORDS = [
    "By",
    "Reuters",
    "IANS",
    "AP",
    "AFP",
    "PTI",
    "IANS",
    "ANI",
    "DPA",
    "Senior Reporter",
    "Reporter",
    "Writer",
    "Opinion Writer",
]

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
    {"attribute": "itemprop", "value": "datePublished", "content": "content"},
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
    {"attribute": "property", "value": "og:regDate", "content": "content"},
    {"attribute": "name", "value": "publication_date", "content": "content"},
    {"attribute": "name", "value": "sailthru.date", "content": "content"},
    {"attribute": "name", "value": "PublishDate", "content": "content"},
    {"attribute": "pubdate", "value": "pubdate", "content": "datetime"},
    {"attribute": "name", "value": "pubdate", "content": "content"},
    {"attribute": "name", "value": "publish_date", "content": "content"},
    {"attribute": "name", "value": "dc.date", "content": "content"},
    {"attribute": "class", "value": "entry-date", "content": "datetime"},
]
ARTICLE_BODY_TAGS = [
    {"tag": "article", "role": "article"},
    {"itemprop": "articleBody"},
    {"itemtype": "https://schema.org/Article"},
    {"itemtype": "https://schema.org/NewsArticle"},
    {"itemtype": "https://schema.org/BlogPosting"},
    {"itemtype": "https://schema.org/ScholarlyArticle"},
    {"itemtype": "https://schema.org/SocialMediaPosting"},
    {"itemtype": "https://schema.org/TechArticle"},
]
META_IMAGE_TAGS = [
    {"tag": "meta", "field": 'meta[property="og:image"]', "score": 10},
    {"tag": "link", "attr": "rel", "value": "image_src|img_src", "score": 8},
    {"tag": "meta", "field": 'meta[name="og:image"]', "score": 8},
    {"tag": "link", "attr": "rel", "value": "icon", "score": 5},
]
META_LANGUAGE_TAGS = [
    {"tag": "meta", "attr": "property", "value": "og:locale"},
    {"tag": "meta", "attr": "http-equiv", "value": "content-language"},
    {"tag": "meta", "attr": "name", "value": "lang"},
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
