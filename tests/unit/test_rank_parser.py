import pytest

from pairing.domain.player import RankParseError, parse_rank


@pytest.mark.parametrize(
    ("raw", "expected_label", "expected_sort"),
    [
        ("7d", "7d", 7),
        ("1 dan", "1d", 1),
        ("1d", "1d", 1),
        ("1k", "1k", -1),
        ("5 kyu", "5k", -5),
        ("30k", "30k", -30),
        ("unranked", "unranked", -999),
        ("", "unranked", -999),
        (None, "unranked", -999),
    ],
)
def test_parse_rank(raw, expected_label, expected_sort):
    rank = parse_rank(raw)
    assert rank.label == expected_label
    assert rank.sort_value == expected_sort


@pytest.mark.parametrize("raw", ["0d", "10d", "0k", "31k", "abc", "3x"])
def test_parse_rank_rejects_invalid_values(raw):
    with pytest.raises(RankParseError):
        parse_rank(raw)
