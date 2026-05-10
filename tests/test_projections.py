"""Tests for Renda+ projection logic in main.py."""
from datetime import date

import pytest

from main import extract_renda_mais_year, renda_mais_conversion_date


class TestExtractRendaMaisYear:
    def test_extracts_year_from_aposentadoria_extra(self):
        assert extract_renda_mais_year("Tesouro Renda+ Aposentadoria Extra 2035") == 2035

    def test_extracts_year_from_lowercase_renda(self):
        assert extract_renda_mais_year("Tesouro renda+ Aposentadoria Extra 2040") == 2040

    def test_returns_none_for_non_renda_mais(self):
        assert extract_renda_mais_year("Tesouro IPCA+ 2035") is None
        assert extract_renda_mais_year("Tesouro Selic 2029") is None

    def test_returns_none_when_no_year(self):
        assert extract_renda_mais_year("Tesouro Renda+ Aposentadoria Extra") is None


class TestRendaMaisConversionDate:
    def test_january_15_of_named_year(self):
        assert renda_mais_conversion_date(2035) == date(2035, 1, 15)
        assert renda_mais_conversion_date(2060) == date(2060, 1, 15)


from main import monthly_aporte_stats


class TestMonthlyAporteStats:
    def test_groups_by_calendar_month_and_computes_avg_median(self, sample_purchases):
        # Jan: 50 + 100 = 150; Mar: 200. Two months -> avg 175, median 175.
        s = monthly_aporte_stats(sample_purchases)
        assert s["months"] == 2
        assert s["avg"] == pytest.approx(175.0)
        assert s["median"] == pytest.approx(175.0)
        assert s["total"] == pytest.approx(350.0)
        assert s["first_month"] == (2024, 1)
        assert s["last_month"] == (2024, 3)

    def test_handles_single_purchase(self):
        purchases = [{"date": date(2024, 5, 10), "invested": 500.0}]
        s = monthly_aporte_stats(purchases)
        assert s["months"] == 1
        assert s["avg"] == pytest.approx(500.0)
        assert s["median"] == pytest.approx(500.0)

    def test_empty_purchases_returns_zeros(self):
        s = monthly_aporte_stats([])
        assert s == {"months": 0, "avg": 0.0, "median": 0.0, "total": 0.0,
                     "first_month": None, "last_month": None}

    def test_median_with_three_months(self):
        purchases = [
            {"date": date(2024, 1, 5), "invested": 100.0},
            {"date": date(2024, 2, 5), "invested": 300.0},
            {"date": date(2024, 3, 5), "invested": 500.0},
        ]
        s = monthly_aporte_stats(purchases)
        assert s["avg"] == pytest.approx(300.0)
        assert s["median"] == pytest.approx(300.0)


from main import compound_monthly_to_yearly, yearly_ipca_stats


class TestCompoundMonthlyToYearly:
    def test_compounds_twelve_months(self):
        # 12 months of 0.5% each -> (1.005)^12 - 1 ≈ 0.0617
        monthly = [0.5] * 12
        yearly = compound_monthly_to_yearly(monthly)
        assert yearly == pytest.approx(0.0616778, abs=1e-5)

    def test_does_not_simply_sum(self):
        monthly = [1.0, 1.0]  # NOT 0.02; should be (1.01)^2 - 1 = 0.0201
        yearly = compound_monthly_to_yearly(monthly)
        assert yearly == pytest.approx(0.0201, abs=1e-5)


class TestYearlyIpcaStats:
    def test_avg_and_median_across_years(self):
        # 3 calendar years of 12 months each; year totals 6%, 4%, 5%.
        series = []
        for year, monthly_pct in [(2022, 0.4868), (2023, 0.3274), (2024, 0.4074)]:
            for m in range(1, 13):
                series.append((date(year, m, 15), monthly_pct))
        stats = yearly_ipca_stats(series)
        # (1.004868)^12 - 1 ≈ 0.06; same logic for 4% and 5%.
        assert stats["avg"] == pytest.approx(0.05, abs=2e-3)
        assert stats["median"] == pytest.approx(0.05, abs=2e-3)
        assert stats["years"] == [(2022, pytest.approx(0.06, abs=2e-3)),
                                  (2023, pytest.approx(0.04, abs=2e-3)),
                                  (2024, pytest.approx(0.05, abs=2e-3))]

    def test_skips_incomplete_years(self):
        # only 6 months of 2024 -> excluded entirely
        series = [(date(2024, m, 15), 0.5) for m in range(1, 7)]
        stats = yearly_ipca_stats(series)
        assert stats == {"avg": 0.0, "median": 0.0, "years": []}
