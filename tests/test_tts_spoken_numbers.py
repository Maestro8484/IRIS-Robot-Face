from __future__ import annotations

import pytest

from services.tts import spoken_numbers


@pytest.mark.parametrize(
    ("number", "word"),
    [
        (0, "zero"),
        (1, "one"),
        (2, "two"),
        (3, "three"),
        (4, "four"),
        (5, "five"),
        (6, "six"),
        (7, "seven"),
        (8, "eight"),
        (9, "nine"),
    ],
)
def test_units(number, word):
    assert spoken_numbers(str(number)) == word


@pytest.mark.parametrize(
    ("number", "word"),
    [
        (10, "ten"),
        (11, "eleven"),
        (12, "twelve"),
        (13, "thirteen"),
        (14, "fourteen"),
        (15, "fifteen"),
        (16, "sixteen"),
        (17, "seventeen"),
        (18, "eighteen"),
        (19, "nineteen"),
    ],
)
def test_teens(number, word):
    assert spoken_numbers(str(number)) == word


@pytest.mark.parametrize(
    ("number", "word"),
    [
        (20, "twenty"),
        (21, "twenty one"),
        (42, "forty two"),
        (99, "ninety nine"),
    ],
)
def test_tens(number, word):
    assert spoken_numbers(str(number)) == word


@pytest.mark.parametrize(
    ("number", "word"),
    [
        (100, "one hundred"),
        (101, "one hundred one"),
        (215, "two hundred fifteen"),
        (999, "nine hundred ninety nine"),
    ],
)
def test_hundreds(number, word):
    assert spoken_numbers(str(number)) == word


def test_thousands():
    assert spoken_numbers("4210") == "four thousand two hundred ten"


def test_millions():
    assert spoken_numbers("1200003") == "one million two hundred thousand three"


def test_negative():
    assert spoken_numbers("-42") == "negative forty two"


def test_zero():
    assert spoken_numbers("0") == "zero"
