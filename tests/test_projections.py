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


from main import (
    average_spread,
    project_real_value_at_conversion,
    future_aporte_future_value,
)


class TestAverageSpread:
    def test_invested_weighted_average(self, sample_purchases):
        # 50@6% + 100@6% + 200@7% -> (50*0.06 + 100*0.06 + 200*0.07) / 350
        avg = average_spread(sample_purchases)
        assert avg == pytest.approx((50*0.06 + 100*0.06 + 200*0.07) / 350.0, abs=1e-6)

    def test_empty_returns_zero(self):
        assert average_spread([]) == 0.0


class TestFutureAporteFutureValue:
    def test_zero_months_returns_zero(self):
        assert future_aporte_future_value(monthly=1000.0, yearly_rate=0.06,
                                          n_months=0) == 0.0

    def test_zero_monthly_returns_zero(self):
        assert future_aporte_future_value(monthly=0.0, yearly_rate=0.06,
                                          n_months=120) == 0.0

    def test_annuity_future_value_formula(self):
        # Standard ordinary annuity FV: M * ((1+i)^n - 1) / i, with i = monthly rate.
        monthly = 1000.0
        yearly = 0.06
        n = 120
        i = (1 + yearly) ** (1 / 12) - 1
        expected = monthly * ((1 + i) ** n - 1) / i
        assert future_aporte_future_value(monthly, yearly, n) == pytest.approx(expected)

    def test_zero_rate_falls_back_to_simple_sum(self):
        assert future_aporte_future_value(monthly=500.0, yearly_rate=0.0,
                                          n_months=24) == pytest.approx(12000.0)


class TestProjectRealValueAtConversion:
    def test_existing_only_no_future(self, sample_purchases):
        # Conversion 5 years after the latest purchase (2024-03-10 -> 2029-03-10).
        # Each grows at its spread for years_to_conv from purchase.
        conversion = date(2029, 3, 10)
        result = project_real_value_at_conversion(
            purchases=sample_purchases,
            conversion_date=conversion,
            today=date(2026, 5, 9),
            future_monthly_aporte=0.0,
            avg_future_spread=0.065,
        )
        # Manual: P1 grows 5+~2/12 yr at 6%, P2 same, P3 grows 5yr at 7%.
        from datetime import timedelta
        expected = 0.0
        for p in sample_purchases:
            yrs = (conversion - p["date"]).days / 365.25
            expected += p["invested"] * (1 + p["spread"]) ** yrs
        assert result == pytest.approx(expected, rel=1e-3)

    def test_with_future_aportes(self, sample_purchases):
        conversion = date(2029, 3, 10)
        today = date(2026, 5, 9)
        result_no = project_real_value_at_conversion(
            sample_purchases, conversion, today,
            future_monthly_aporte=0.0, avg_future_spread=0.065,
        )
        result_with = project_real_value_at_conversion(
            sample_purchases, conversion, today,
            future_monthly_aporte=500.0, avg_future_spread=0.065,
        )
        assert result_with > result_no
        # Difference equals annuity FV of 500/mo at 6.5% over n_months from today to conversion.
        n_months = (conversion.year - today.year) * 12 + (conversion.month - today.month)
        i = (1.065) ** (1 / 12) - 1
        expected_diff = 500.0 * ((1 + i) ** n_months - 1) / i
        assert (result_with - result_no) == pytest.approx(expected_diff, rel=1e-3)


from main import inflate_to_nominal, renda_mais_payout


class TestInflateToNominal:
    def test_inflates_real_value_by_yearly_ipca(self):
        # 1000 real, 5% IPCA, 10 calendar years (with leap days).
        start = date(2025, 1, 1)
        end = date(2035, 1, 1)
        years = (end - start).days / 365.25
        expected = 1000.0 * (1.05 ** years)
        nominal = inflate_to_nominal(real_value=1000.0, yearly_ipca=0.05,
                                     start=start, end=end)
        assert nominal == pytest.approx(expected, abs=1e-6)

    def test_zero_years_is_identity(self):
        d = date(2030, 6, 15)
        assert inflate_to_nominal(1000.0, 0.05, d, d) == pytest.approx(1000.0)


class TestRendaMaisPayout:
    def test_240_months_split(self):
        # 240,000 real at spread 7% -> PMT formula, not /240.
        result = renda_mais_payout(
            real_value_at_conversion=240_000.0,
            total_invested=120_000.0,
            conversion_date=date(2035, 1, 15),
            maturity_date=date(2054, 12, 15),
            yearly_ipca_for_inflation=0.05,
            today=date(2025, 1, 15),
            payout_spread=0.07,
        )
        assert result["n_months"] == 240
        # Annuity PMT at 7% real over 240 months: V_c × pmt_factor
        i = (1.07) ** (1 / 12) - 1
        pmt_factor = i / (1 - (1 + i) ** -240)
        expected_gross = 240_000.0 * pmt_factor
        assert result["real_monthly_gross"] == pytest.approx(expected_gross, rel=1e-6)
        # IR on gain portion of total real cashflow
        total_cashflow = expected_gross * 240
        gain_frac = (total_cashflow - 120_000.0) / total_cashflow
        expected_ir = expected_gross * gain_frac * 0.15
        expected_net = expected_gross - expected_ir
        assert result["real_monthly_net"] == pytest.approx(expected_net, rel=1e-6)
        # Nominal first parcel: real_monthly_net inflated to conversion
        years_to_conv = (date(2035, 1, 15) - date(2025, 1, 15)).days / 365.25
        expected_first_net = expected_net * (1.05 ** years_to_conv)
        assert result["nominal_first_net"] == pytest.approx(expected_first_net, rel=1e-6)
        # Nominal last parcel: inflated to maturity
        years_to_mat = (date(2054, 12, 15) - date(2025, 1, 15)).days / 365.25
        expected_last_net = expected_net * (1.05 ** years_to_mat)
        assert result["nominal_last_net"] == pytest.approx(expected_last_net, rel=1e-6)

    def test_no_gain_means_no_ir(self):
        result = renda_mais_payout(
            real_value_at_conversion=120_000.0,
            total_invested=999_999.0,  # >> total real cashflow, so no gain
            conversion_date=date(2035, 1, 15),
            maturity_date=date(2054, 12, 15),
            yearly_ipca_for_inflation=0.04,
            today=date(2025, 1, 15),
            payout_spread=0.06,
        )
        assert result["real_monthly_net"] == pytest.approx(result["real_monthly_gross"])
        assert result["real_monthly_ir"] == pytest.approx(0.0)


from main import build_bond_projection


class TestBuildBondProjection:
    def test_returns_six_scenarios_for_renda_mais(self, sample_purchases):
        bond = {
            "name": "Tesouro Renda+ Aposentadoria Extra 2035",
            "maturity": date(2054, 12, 15),
            "purchases": sample_purchases,
            "total_invested": 350.0,
        }
        result = build_bond_projection(
            bond=bond,
            today=date(2025, 1, 15),
            ipca_avg=0.05,
            ipca_median=0.04,
        )
        assert result["is_renda_mais"] is True
        assert result["conversion_date"] == date(2035, 1, 15)
        assert set(result["scenarios"].keys()) == {
            "no_aporte_avg_ipca",
            "no_aporte_median_ipca",
            "avg_aporte_avg_ipca",
            "avg_aporte_median_ipca",
            "median_aporte_avg_ipca",
            "median_aporte_median_ipca",
        }
        # aporte_stats now derived from this bond's own purchases:
        # Jan 2024 -> R$50+R$100 = R$150; Mar 2024 -> R$200; avg=median=175.
        assert "aporte_stats" in result
        assert result["aporte_stats"]["avg"] == pytest.approx(175.0)
        assert result["aporte_stats"]["median"] == pytest.approx(175.0)
        assert result["aporte_stats"]["months"] == 2
        scen = result["scenarios"]["avg_aporte_avg_ipca"]
        # higher aporte and higher IPCA -> larger nominal first payment
        assert scen["real_value_at_conversion"] > 0
        assert scen["nominal_value_at_conversion"] >= scen["real_value_at_conversion"]
        assert scen["payout"]["n_months"] == 240
        # no_aporte baseline must be smaller than avg_aporte (assuming positive aporte)
        no_avg = result["scenarios"]["no_aporte_avg_ipca"]["real_value_at_conversion"]
        yes_avg = result["scenarios"]["avg_aporte_avg_ipca"]["real_value_at_conversion"]
        assert no_avg < yes_avg
        # total_invested for no_aporte equals bond's existing total (no future aportes added)
        assert (
            result["scenarios"]["no_aporte_avg_ipca"]["total_invested_through_conversion"]
            == pytest.approx(bond["total_invested"])
        )

    def test_returns_none_for_non_renda_mais(self, sample_purchases):
        bond = {
            "name": "Tesouro IPCA+ 2035",
            "maturity": date(2035, 5, 15),
            "purchases": sample_purchases,
            "total_invested": 350.0,
        }
        result = build_bond_projection(
            bond=bond, today=date(2025, 1, 15),
            ipca_avg=0.05, ipca_median=0.04,
        )
        assert result["is_renda_mais"] is False
        assert result["scenarios"] == {}


from main import compute_life_phases, monthly_income_by_phase


class TestComputeLifePhases:
    def _proj(self, conversion, maturity):
        return {
            "is_renda_mais": True,
            "conversion_date": conversion,
            "maturity_date": maturity,
            "scenarios": {},
        }

    def test_single_bond_one_phase(self):
        projections = {"A": self._proj(date(2035, 1, 15), date(2054, 12, 15))}
        phases = compute_life_phases(projections)
        assert len(phases) == 1
        assert phases[0]["active"] == ("A",)
        assert phases[0]["n_months"] == 240
        assert phases[0]["start"] == date(2035, 1, 15)
        assert phases[0]["end"] == date(2054, 12, 15)

    def test_two_bonds_three_phases(self):
        # A: 2035–2054, B: 2040–2059
        projections = {
            "A": self._proj(date(2035, 1, 15), date(2054, 12, 15)),
            "B": self._proj(date(2040, 1, 15), date(2059, 12, 15)),
        }
        phases = compute_life_phases(projections)
        assert len(phases) == 3
        assert phases[0]["active"] == ("A",)
        assert phases[0]["n_months"] == 60  # 2035–2039
        assert phases[1]["active"] == ("A", "B")
        assert phases[1]["n_months"] == 180  # 2040–2054
        assert phases[2]["active"] == ("B",)
        assert phases[2]["n_months"] == 60  # 2055–2059

    def test_four_bond_user_timeline(self):
        # Mirror the user's actual bonds.
        projections = {
            "2035": self._proj(date(2035, 1, 15), date(2054, 12, 15)),
            "2040": self._proj(date(2040, 1, 15), date(2059, 12, 15)),
            "2050": self._proj(date(2050, 1, 15), date(2069, 12, 15)),
            "2060": self._proj(date(2060, 1, 15), date(2079, 12, 15)),
        }
        phases = compute_life_phases(projections)
        assert len(phases) == 6
        expected_actives = [
            ("2035",),
            ("2035", "2040"),
            ("2035", "2040", "2050"),
            ("2040", "2050"),
            ("2050", "2060"),
            ("2060",),
        ]
        expected_months = [60, 120, 60, 60, 120, 120]
        for ph, expected_active, expected_n in zip(phases, expected_actives, expected_months):
            assert ph["active"] == expected_active
            assert ph["n_months"] == expected_n
        # totals
        assert sum(ph["n_months"] for ph in phases) == 540

    def test_no_renda_mais_returns_empty(self):
        projections = {"X": {"is_renda_mais": False, "scenarios": {}}}
        phases = compute_life_phases(projections)
        assert phases == []


class TestMonthlyIncomeByPhase:
    def test_sums_real_monthly_across_active_bonds(self):
        projections = {
            "A": {
                "is_renda_mais": True,
                "conversion_date": date(2035, 1, 15),
                "maturity_date": date(2054, 12, 15),
                "scenarios": {
                    "avg_aporte_avg_ipca": {
                        "payout": {"real_monthly_net": 100.0, "real_monthly_gross": 120.0},
                        "ipca_yearly": 0.05,
                    },
                },
            },
            "B": {
                "is_renda_mais": True,
                "conversion_date": date(2040, 1, 15),
                "maturity_date": date(2059, 12, 15),
                "scenarios": {
                    "avg_aporte_avg_ipca": {
                        "payout": {"real_monthly_net": 50.0, "real_monthly_gross": 60.0},
                        "ipca_yearly": 0.05,
                    },
                },
            },
        }
        phases = compute_life_phases(projections)
        income = monthly_income_by_phase(phases, projections, "avg_aporte_avg_ipca")
        # phase 1 (A only): 100, phase 2 (A+B): 150, phase 3 (B only): 50
        assert income[0]["real_monthly_net"] == pytest.approx(100.0)
        assert income[1]["real_monthly_net"] == pytest.approx(150.0)
        assert income[2]["real_monthly_net"] == pytest.approx(50.0)


from main import short_phase_label, short_renda_mais_label


class TestShortLabels:
    def test_short_renda_mais_label_extracts_year(self):
        assert short_renda_mais_label("Tesouro Renda+ Aposentadoria Extra 2035") == "2035"
        assert short_renda_mais_label("Tesouro Renda+ Aposentadoria Extra 2060") == "2060"

    def test_short_renda_mais_label_fallback(self):
        assert short_renda_mais_label("Tesouro IPCA+ 2035") == "Tesouro IPCA+ 2035"

    def test_short_phase_label_joins_with_plus(self):
        names = (
            "Tesouro Renda+ Aposentadoria Extra 2035",
            "Tesouro Renda+ Aposentadoria Extra 2040",
        )
        assert short_phase_label(names) == "2035 + 2040"
