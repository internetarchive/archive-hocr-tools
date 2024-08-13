import pytest

from hocr.daisy.book import DaisyBook
from hocr.daisy.util import roman_to_num


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("1", "1"),
        ("1", 1),
        ("9999", 9999),
        ("6", "vi"),
        ("28", "XXIIX"),
    ],
)
def test_add_pagetarget_handles_int_numstrs_and_roman_numerals(name, value) -> None:
    """
    For testing purposes, `name` is merely a string representation of the
    page number, and it corresponds to the new `max_page_number`, for each
    test.

    Note: this test is mainly meant to verify that `DaisyBook.add_pagetarget`
    can handle Roman numerals, that it can accept an int `value`, and
    that it will properly convert number strings (e.g. "6") to their `int`
    representation.
    """
    book = DaisyBook(out_name="Test", metadata=[{"tag": "blob"}])
    book.add_pagetarget(name=name, value=value)
    assert book.max_page_number == int(name)


def test_add_pagetarget_raises_ValueError_with_unexpected_value() -> None:
    with pytest.raises(ValueError):
        book = DaisyBook(out_name="Test", metadata=[{"tag": "blob"}])
        book.add_pagetarget(name="1", value="one")


@pytest.mark.parametrize(
    ("input", "expected"),
    [
        # Standard form
        ("viii", 8),
        ("VIII", 8),
        ("DCCLXXXIX", 789),
        ("MMCDXXI", 2421),
        ("MdCcLxXvI", 1776),
        # Other additive (see Wikipedia)
        ("LXXIIII", 74),
        ("CCCCLXXXX", 490),
        # Other subtractive (see Wikipedia)
        ("LDVLIV", 499),
        ("XDIX", 499),
        ("IIIXX", 17),
        ("XXIIX", 28),
        # Not a Roman numeral
        ("three", 0),
        ("1", 0),
        ("MI5", 0),
    ],
)
def test_roman_to_num(input: str, expected: int) -> None:
    got = roman_to_num(input)
    assert got == expected
