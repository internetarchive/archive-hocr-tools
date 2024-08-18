import pytest
from PIL import Image

from hocr.util import (needs_grayscale_conversion, needs_rgb_conversion,
                       normalize_language)


def create_image(mode: str, size: tuple = (10, 10)) -> Image.Image:
    """
    Helper function to create a Pillow Image of type `mode`.
    See https://pillow.readthedocs.io/en/stable/handbook/concepts.html#modes.
    """
    return Image.new(mode, size)


@pytest.mark.parametrize(
    ('mode', 'expected'),
    [
        # Grayscale with alpha channel
        ('LA', True),
        # 1 bit pixels, black and white
        ('1', True),
        # Grayscale without alpha channel
        ('L', False),
        # 16-bit unsigned integer pixel
        ('I;16', False),
        # RGB image
        ('RGB', False),
    ],
)
def test_needs_grayscale_conversion(mode: str, expected: bool) -> None:
    """This does not test for functionally grayscale RGB images."""
    image = create_image(mode)
    assert needs_grayscale_conversion(image) is expected


@pytest.mark.parametrize(
    ('mode', 'expected'),
    [
        # RGBA image
        ('RGBA', True),
        # CMYK image
        ('CMYK', True),
        # 16-bit unsigned integer pixel
        ('I;16', True),
        # Grayscale with alpha channel
        ('LA', False),
        # 1 bit pixels, black and white
        ('1', False),
        # Grayscale without alpha channel
        ('L', False),
        # RGB image
        ('RGB', False),
    ],
)
def test_needs_rgb_conversion(mode: str, expected: bool) -> None:
    image = create_image(mode)
    assert needs_rgb_conversion(image) is expected


@pytest.mark.parametrize(
    ("language", "expected"),
    [
        ("fra", "fr"),
        # See, e.g. https://archive.org/metadata/101610331.nlm.nih.gov/metadata/language
        ("fre", "fr"),
        # See, e.g. https://archive.org/metadata/2e013a64-935f-4be4-9c51-3eac22929627/metadata/language
        ("FRE", "fr"),
        # See, e.g. https://archive.org/metadata/4E2218INV1398RES_P11BIS/metadata/language
        ("French", "fr"),
        ("eNg", "en"),
        ("brewer", "brewer"),
        (None, None),
        ("", None),
    ],
)
def test_normalize_language(language: str, expected: str) -> None:
    got = normalize_language(language=language)
    assert got == expected
