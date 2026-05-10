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
