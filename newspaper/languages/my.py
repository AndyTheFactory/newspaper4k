## Burmese language tokenizer
import re


def tokenizer(text):
    # regexp from https://github.com/swanhtet1992/ReSegment
    regexp = re.compile(r"(?:(?<!္)([က-ဪဿ၊-၏]|[၀-၉]+|[^က-၏]+)(?![ှျ]?[့္်]))")
    words = regexp.sub(r"𝕊\1", text).strip("𝕊").split("𝕊")
    return words
