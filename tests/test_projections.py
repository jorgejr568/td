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
