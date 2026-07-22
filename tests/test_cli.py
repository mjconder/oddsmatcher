import pytest

from oddsmatcher import cli


class TestScan:
    @pytest.fixture
    def output(self, fixtures_root, capsys):
        rc = cli.main(["scan", "--fixtures", str(fixtures_root)])
        assert rc == 0
        return capsys.readouterr().out

    def test_prints_best_prices(self, output):
        assert "Los Angeles Dodgers @ Chicago Cubs [moneyline]" in output
        assert "Bournemouth @ Manchester City [match_winner]" in output

    def test_prints_best_price_per_outcome(self, output):
        assert "away     1.52  (openline)" in output
        assert "home     2.70  (stateline)" in output

    def test_partial_coverage_event_shown(self, output):
        assert "St. Louis Cardinals @ New York Yankees [moneyline]" in output
        assert "home     1.30  (northwood)" in output

    def test_missing_fixtures_fail_gracefully(self, tmp_path, capsys):
        rc = cli.main(["scan", "--fixtures", str(tmp_path / "nope")])
        assert rc == 1
        captured = capsys.readouterr()
        assert captured.err.strip() != ""
        assert "not found" in captured.err
        # A graceful error prints one stderr line, not a traceback.
        assert "Traceback" not in captured.err
