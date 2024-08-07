from typing import Optional


ROMAN_ARABIC_MAP = {
    "I": 1,
    "V": 5,
    "X": 10,
    "L": 50,
    "C": 100,
    "D": 500,
    "M": 1000,
}


def roman_to_num(s: str, up_to: Optional[str] = None) -> int:
    """
    Convert a Roman numeral string, s, to an int.

    Returns 0 if the input is not in `ROMAN_ARABIC_MAP`.

    Handles standard and other additive and substractive forms.
    See https://en.wikipedia.org/wiki/Roman_numerals#Other_additive_forms and
    https://en.wikipedia.org/wiki/Roman_numerals#Other_subtractive_forms.

    Courtesy of Arkiver. :)
    """
    s = s.upper()

    value = 0
    for i, (c1, c2) in enumerate(zip([s[0], *s], s)):
        if c1 not in ROMAN_ARABIC_MAP or c2 not in ROMAN_ARABIC_MAP:
            return 0
        if up_to is not None and ROMAN_ARABIC_MAP[c2] >= ROMAN_ARABIC_MAP[up_to]:
            return value
        if c1 is None or ROMAN_ARABIC_MAP[c1] >= ROMAN_ARABIC_MAP[c2]:
            value += ROMAN_ARABIC_MAP[c2]
        else:
            value += ROMAN_ARABIC_MAP[c2] - roman_to_num(s[:i][::-1], up_to=c2) * 2
    return value
