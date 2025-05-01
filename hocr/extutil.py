from typing import Optional

def needs_grayscale_conversion(image) -> bool:
    """
    Return True if image should be converted to grayscale, and False otherwise.
    Grayscale images with alpha layers need conversion because the JPEG target
    doesn't support transparency.

    Note: this will return False for RGB images that are functionally grayscale,
    as the cost of identifying them is not worth the effort. For a good, yet
    still too slow strategy, see https://stackoverflow.com/a/34175631.
    """
    return image.mode in ('LA', '1')


def needs_rgb_conversion(image) -> bool:
    """
    Return True if image should be converted to RGB, and False otherwise.

    Anything that isn't a grayscale image that also isn't already RGB needs conversion.
    """
    return image.mode not in ('RGB', 'L', 'LA', '1')


def normalize_language(language) -> Optional[str]:
    """
    Attempt to convert a language tag to a valid country code
    """
    import iso639
    from internetarchiveocr.language import language_to_alpha3lang

    if not language:
        return None

    def get_alpha2_code(language: str, part: str) -> Optional[str]:
        """
        Try to get a two-character language code from a three character code.

        `part` is an ISO 639 part (e.g. part3, part2b).
        """
        try:
            return iso639.languages.get(**{part: language_to_alpha3lang(language)}).alpha2
        except KeyError:
            return None

    alpha2_code = get_alpha2_code(language=language, part="part3")
    if alpha2_code is None:
        alpha2_code = get_alpha2_code(language=language, part="part2b")

    return alpha2_code or language
