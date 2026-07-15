import pytest

from oddsmatcher.odds import (
    american_to_decimal,
    decimal_to_implied,
    normalize_odds,
)


class TestImpliedProbability:
    def test_decimal_to_implied(self):
        assert decimal_to_implied(2.0) == pytest.approx(0.5)
        assert decimal_to_implied(4.0) == pytest.approx(0.25)

    @pytest.mark.parametrize("odds", [1.0, 0.9, 0.0, -2.0])
    def test_rejects_odds_at_or_below_one(self, odds):
        with pytest.raises(ValueError):
            decimal_to_implied(odds)


class TestAmerican:
    @pytest.mark.parametrize(
        ("american", "expected"),
        [(150, 2.5), (100, 2.0), (-100, 2.0), (-120, 1.0 + 100 / 120), (250, 3.5)],
    )
    def test_to_decimal(self, american, expected):
        assert american_to_decimal(american) == pytest.approx(expected)

    def test_zero_rejected(self):
        with pytest.raises(ValueError):
            american_to_decimal(0)


class TestNormalizeOdds:
    def test_decimal_passthrough(self):
        assert normalize_odds(2.5, "decimal") == pytest.approx(2.5)

    def test_decimal_accepts_strings(self):
        assert normalize_odds("1.91", "decimal") == pytest.approx(1.91)

    def test_american(self):
        assert normalize_odds(-110, "american") == pytest.approx(1.0 + 100 / 110)

    def test_returns_plain_float(self):
        result = normalize_odds(2.5, "decimal")
        assert isinstance(result, float)

    def test_unknown_format_raises(self):
        with pytest.raises(ValueError):
            normalize_odds(2.0, "hongkong")

    def test_fractional_no_longer_supported(self):
        with pytest.raises(ValueError):
            normalize_odds("7/2", "fractional")

    def test_junk_decimal_raises(self):
        with pytest.raises(ValueError):
            normalize_odds("n/a", "decimal")

    @pytest.mark.parametrize("bad", [1.0, 0.9, 0.0])
    def test_invalid_decimal_raises(self, bad):
        with pytest.raises(ValueError):
            normalize_odds(bad, "decimal")

    def test_american_zero_raises(self):
        with pytest.raises(ValueError):
            normalize_odds(0, "american")

    @pytest.mark.parametrize("bad", [50, -50, 99, -99, 0])
    def test_sub_100_american_rejected(self, bad):
        # Real American odds are always >= 100 in magnitude; -50 must not
        # quietly become decimal 3.0.
        with pytest.raises(ValueError):
            normalize_odds(bad, "american")

    @pytest.mark.parametrize("ok", [100, -100, 150, -110])
    def test_valid_american_accepted(self, ok):
        assert normalize_odds(ok, "american") > 1.0
