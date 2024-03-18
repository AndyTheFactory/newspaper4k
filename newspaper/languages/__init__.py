from pathlib import Path
from typing import Optional

from newspaper import settings


languages_tuples = [
    ("aa", "Afar"),
    ("ab", "Abkhazian"),
    ("ae", "Avestan"),
    ("af", "Afrikaans"),
    ("ak", "Akan"),
    ("am", "Amharic"),
    ("an", "Aragonese"),
    ("ar", "Arabic"),
    ("as", "Assamese"),
    ("av", "Avaric"),
    ("ay", "Aymara"),
    ("az", "Azerbaijani"),
    ("ba", "Bashkir"),
    ("be", "Belarusian"),
    ("bg", "Bulgarian"),
    ("bh", "Bihari languages"),
    ("bi", "Bislama"),
    ("bm", "Bambara"),
    ("bn", "Bengali"),
    ("bo", "Tibetan"),
    ("br", "Breton"),
    ("bs", "Bosnian"),
    ("ca", "Catalan; Valencian"),
    ("ce", "Chechen"),
    ("ch", "Chamorro"),
    ("co", "Corsican"),
    ("cr", "Cree"),
    ("cs", "Czech"),
    ("cv", "Chuvash"),
    ("cy", "Welsh"),
    ("da", "Danish"),
    ("de", "German"),
    ("dv", "Divehi; Dhivehi; Maldivian"),
    ("dz", "Dzongkha"),
    ("ee", "Ewe"),
    ("el", "Greek, Modern (1453-)"),
    ("en", "English"),
    ("eo", "Esperanto"),
    ("es", "Spanish; Castilian"),
    ("et", "Estonian"),
    ("eu", "Basque"),
    ("fa", "Persian"),
    ("ff", "Fulah"),
    ("fi", "Finnish"),
    ("fj", "Fijian"),
    ("fo", "Faroese"),
    ("fr", "French"),
    ("fy", "Western Frisian"),
    ("ga", "Irish"),
    ("gd", "Gaelic; Scottish Gaelic"),
    ("gl", "Galician"),
    ("gn", "Guarani"),
    ("gu", "Gujarati"),
    ("gv", "Manx"),
    ("ha", "Hausa"),
    ("he", "Hebrew"),
    ("hi", "Hindi"),
    ("ho", "Hiri Motu"),
    ("hr", "Croatian"),
    ("ht", "Haitian; Haitian Creole"),
    ("hu", "Hungarian"),
    ("hy", "Armenian"),
    ("hz", "Herero"),
    ("id", "Indonesian"),
    ("ig", "Igbo"),
    ("ii", "Sichuan Yi; Nuosu"),
    ("ik", "Inupiaq"),
    ("io", "Ido"),
    ("is", "Icelandic"),
    ("it", "Italian"),
    ("iu", "Inuktitut"),
    ("ja", "Japanese"),
    ("jv", "Javanese"),
    ("ka", "Georgian"),
    ("kg", "Kongo"),
    ("ki", "Kikuyu; Gikuyu"),
    ("kj", "Kuanyama; Kwanyama"),
    ("kk", "Kazakh"),
    ("kl", "Kalaallisut; Greenlandic"),
    ("km", "Central Khmer"),
    ("kn", "Kannada"),
    ("ko", "Korean"),
    ("kr", "Kanuri"),
    ("ks", "Kashmiri"),
    ("ku", "Kurdish"),
    ("kv", "Komi"),
    ("kw", "Cornish"),
    ("ky", "Kirghiz; Kyrgyz"),
    ("la", "Latin"),
    ("lb", "Luxembourgish; Letzeburgesch"),
    ("lg", "Ganda"),
    ("li", "Limburgan; Limburger; Limburgish"),
    ("ln", "Lingala"),
    ("lo", "Lao"),
    ("lt", "Lithuanian"),
    ("lu", "Luba-Katanga"),
    ("lv", "Latvian"),
    ("mg", "Malagasy"),
    ("mh", "Marshallese"),
    ("mi", "Maori"),
    ("mk", "Macedonian"),
    ("ml", "Malayalam"),
    ("mn", "Mongolian"),
    ("mr", "Marathi"),
    ("ms", "Malay"),
    ("mt", "Maltese"),
    ("my", "Burmese"),
    ("na", "Nauru"),
    ("nb", "Bokmål, Norwegian; Norwegian Bokmål"),
    ("nd", "Ndebele, North; North Ndebele"),
    ("ne", "Nepali"),
    ("ng", "Ndonga"),
    ("nl", "Dutch; Flemish"),
    ("nn", "Norwegian Nynorsk; Nynorsk, Norwegian"),
    ("no", "Norwegian"),
    ("nr", "Ndebele, South; South Ndebele"),
    ("nv", "Navajo; Navaho"),
    ("oc", "Occitan (post 1500)"),
    ("oj", "Ojibwa"),
    ("om", "Oromo"),
    ("or", "Oriya"),
    ("os", "Ossetian; Ossetic"),
    ("pa", "Panjabi; Punjabi"),
    ("pi", "Pali"),
    ("pl", "Polish"),
    ("ps", "Pushto; Pashto"),
    ("pt", "Portuguese"),
    ("qu", "Quechua"),
    ("rm", "Romansh"),
    ("rn", "Rundi"),
    ("ro", "Romanian; Moldavian; Moldovan"),
    ("ru", "Russian"),
    ("rw", "Kinyarwanda"),
    ("sa", "Sanskrit"),
    ("sc", "Sardinian"),
    ("sd", "Sindhi"),
    ("se", "Northern Sami"),
    ("sg", "Sango"),
    ("si", "Sinhala; Sinhalese"),
    ("sk", "Slovak"),
    ("sl", "Slovenian"),
    ("sm", "Samoan"),
    ("sn", "Shona"),
    ("so", "Somali"),
    ("sq", "Albanian"),
    ("sr", "Serbian"),
    ("ss", "Swati"),
    ("st", "Sotho, Southern"),
    ("su", "Sundanese"),
    ("sv", "Swedish"),
    ("sw", "Swahili"),
    ("ta", "Tamil"),
    ("te", "Telugu"),
    ("tg", "Tajik"),
    ("th", "Thai"),
    ("ti", "Tigrinya"),
    ("tk", "Turkmen"),
    ("tl", "Tagalog"),
    ("tn", "Tswana"),
    ("to", "Tonga (Tonga Islands)"),
    ("tr", "Turkish"),
    ("ts", "Tsonga"),
    ("tt", "Tatar"),
    ("tw", "Twi"),
    ("ty", "Tahitian"),
    ("ug", "Uighur; Uyghur"),
    ("uk", "Ukrainian"),
    ("ur", "Urdu"),
    ("uz", "Uzbek"),
    ("ve", "Venda"),
    ("vi", "Vietnamese"),
    ("vo", "Volapük"),
    ("wa", "Walloon"),
    ("wo", "Wolof"),
    ("xh", "Xhosa"),
    ("yi", "Yiddish"),
    ("yo", "Yoruba"),
    ("za", "Zhuang; Chuang"),
    ("zh", "Chinese"),
    ("zu", "Zulu"),
]

languages_dict = {code: language for code, language in languages_tuples}

# See https://www.omniglot.com/writing/ for details
languages_unicode_regex = {
    "aa": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ab": r"\u0400-\u04ff",
    "ae": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "am": r"\u1200-\u137f",
    "ar": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "as": r"\u0980-\u09ff",
    "av": r"\u0400-\u04ff\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "az": r"\u0600-\u06ff",
    "ba": r"\u0400-\u04ff",
    "be": r"\u0400-\u04ff",
    "bg": r"\u0400-\u04ff",
    "bh": r"\u0900-\u097f",
    "bn": r"\u0980-\u09ff",
    "bo": r"\u0f00-\u0fff",
    "bs": r"\u0400-\u04ff",
    "ce": r"\u0400-\u04ff",
    "cr": r"\u1400-\u167f",
    "cv": r"\u0400-\u04ff",
    "cy": r"\u1680-\u169f",
    "dv": r"\u0f00-\u0fff",
    "dz": r"\u0780-\u07bf\u0f00-\u0fff",
    "el": r"\u0370-\u03ff\u1f00-\u1fff",
    "fa": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ff": r"\u0600-\u06ff",
    "ga": r"\u1680-\u169f",
    "gu": r"\u0a80-\u0aff",
    "ha": r"\u0600-\u06ff",
    "he": r"\u0590-\u05ff",
    "hi": r"\u0900-\u097f",
    "hy": r"\u0530-\u058f",
    "ii": (
        r"\u3100-\u312f\u31a0-\u31bf\u3200-\u32ff\u3300-\u33ff"
        r"\u3400-\u4db5\u4e00-\u9fff\ua000-\ua48f\ua490-\ua4cf"
        r"\uf900-\ufaff\ufe30-\ufe4f\U00020000-\U0002a6d6\U0002f800-\U0002fa1f"
    ),
    "ja": (
        r"\u3040-\u309f\u30a0-\u30ff\u3190-\u319f\u3200-\u32ff"
        r"\u3300-\u33ff\u3400-\u4db5\u4e00-\u9fff\uf900-\ufaff"
        r"\ufe30-\ufe4f\U00020000-\U0002a6d6\U0002f800-\U0002fa1f"
    ),
    "jv": r"\u0600-\u06ff",
    "ka": r"\u10a0-\u10ff",
    "kk": r"\u0400-\u04ff",
    "km": r"\u1780-\u17ff",
    "kn": r"\u0c80-\u0cff",
    "ko": (
        r"\u1100-\u11ff\u3130-\u318f\u3200-\u32ff\u3300-\u33ff"
        r"\u3400-\u4db5\u4e00-\u9fff\uac00-\ud7a3\uf900-\ufaff"
        r"\ufe30-\ufe4f\U00020000-\U0002a6d6\U0002f800-\U0002fa1f"
    ),
    "kr": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ks": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ku": r"\u0600-\u06ff",
    "kv": r"\u0400-\u04ff",
    "ky": r"\u0400-\u04ff\u0600-\u06ff",
    "lg": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "lo": r"\u0e80-\u0eff",
    "mk": r"\u0400-\u04ff",
    "ml": r"\u0d00-\u0d7f",
    "mn": r"\u1800-\u18af\u0400-\u04ff",
    "mr": r"\u0900-\u097f",
    "my": r"\u1000-\u109f",
    "ne": r"\u0900-\u097f",
    "oj": r"\u1400-\u167f",
    "or": r"\u0b00-\u0b7f",
    "os": r"\u0400-\u04ff",
    "pa": r"\u0a00-\u0a7f",
    "pi": r"\u1000-\u109f\u1780-\u17ff",
    "ps": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ru": r"\u0400-\u04ff",
    "sa": (
        r"\u0900-\u097f\u0980-\u09ff\u0c80-\u0cff\u0d00-\u0d7f\u0f00-\u0fff"
        r"\u1000-\u109f"
    ),
    "sd": r"\ufb50-\ufdff\ufe70-\ufefe",
    "si": r"\u0d80-\u0dff",
    "sr": r"\u0400-\u04ff",
    "sw": r"\u0600-\u06ff",
    "ta": r"\u0b80-\u0bff",
    "te": r"\u0c00-\u0c7f",
    "tg": r"\u0400-\u04ff",
    "th": r"\u0e00-\u0e7f",
    "ti": r"\u1200-\u137f",
    "tk": r"\u0400-\u04ff\u0600-\u06ff",
    "tt": r"\u0400-\u04ff\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "ug": r"\u0400-\u04ff\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "uk": r"\u0400-\u04ff",
    "ur": r"\u0600-\u06ff\ufb50-\ufdff\ufe70-\ufefe",
    "uz": r"\u0400-\u04ff\u0600-\u06ff",
    "wo": r"\u0600-\u06ff",
    "yi": r"\u0590-\u05ff",
    "za": r"\u0400-\u04ff",
    "zh": (
        r"\u3100-\u312f\u31a0-\u31bf\u3200-\u32ff\u3300-\u33ff"
        r"\u3400-\u4db5\u4e00-\u9fff\ua000-\ua48f\ua490-\ua4cf"
        r"\uf900-\ufaff\ufe30-\ufe4f\U00020000-\U0002a6d6\U0002f800-\U0002fa1f"
    ),
}


def get_language_from_iso639_1(iso639_1: str) -> Optional[str]:
    """Returns the long language name from the iso639_1 code

    Args:
        iso639_1 (str): the two character iso639_1 code

    Returns:
        str: Language name (in english)
    """
    return languages_dict.get(iso639_1)


def get_available_languages():
    """Returns a list of available languages and their 2 char input codes"""
    stopword_files = Path(settings.STOPWORDS_DIR).glob("stopwords-??.txt")
    for file in stopword_files:
        yield file.stem.split("-")[1]


def valid_languages():
    """Returns the List of available Languages as tuples (iso-code, language)"""
    languages = []
    for code, language in languages_tuples:
        stopwords_file = Path(settings.STOPWORDS_DIR) / f"stopwords-{code}.txt"
        if stopwords_file.exists():
            languages.append((code, language))

    return languages


def language_regex(language: str) -> str:
    """Returns the regex for alphabet used by the given language
    Args:
         language (str): the two character iso639_1 code

    Returns:
         str: regex for the language
    """
    latin_regex = r"\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u00ff\u0100-\u024fa-zA-Z0-9\ "
    if language in languages_unicode_regex:
        return f"{languages_unicode_regex[language]}{latin_regex}"
    return latin_regex
