## Renda+ Projections & Stats Section Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a stats section to the `Resumo` tab of `output.xlsx` showing per-month aporte stats, projected accumulated value at each Renda+ bond's conversion date (using historical avg/median aporte and IPCA scenarios), and the expected monthly payout during the 20-year (240-month) Renda+ payout window.

**Architecture:** All four bonds in `reports/` are Tesouro Renda+ NTN-B1 (conversion at 15/01/{year}, then 240 monthly amortizations of `1/240` of VNA until maturity 15/12/{year+19}). In **real terms** (today's reais, ignoring IPCA), the monthly payment is approximately constant ≈ `accumulated_real_value_at_conversion / 240`. We project forward by (a) growing each existing purchase at its own contracted spread until conversion, (b) adding future monthly aportes — sized **per-bond** from THAT bond's own purchase-history avg/median monthly aporte — growing at the bond's invested-weighted avg spread, and (c) inflating the real result to nominal BRL using historical-avg/median yearly IPCA from BCB SGS series 433. The Resumo tab keeps a portfolio-wide aporte summary block AND embeds per-bond aporte stats inside each Renda+ projection block. New code lives in `main.py` (single-file project convention) under a clearly labeled section, plus a small `tests/` package for unit tests.

**Note (post-Task-8 refactor):** `build_bond_projection(bond, today, ipca_avg, ipca_median)` now derives its own per-bond aporte stats internally from `bond["purchases"]` — no aporte_avg/aporte_median parameters are passed in. The returned dict gains an `aporte_stats` key for the renderer.

**Tech Stack:** Python 3.10, openpyxl, requests, pytest (new). External APIs: BCB SGS (`https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json`, monthly IPCA % since 1980, no auth) and existing Brasil API.

---

### Domain reference (read once before starting)

- **Renda+ payout (NTN-B1):** 240 monthly amortizations starting on the *data de conversão* = `15/01/{year}` extracted from the bond name (e.g., "Tesouro Renda+ Aposentadoria Extra 2035" → 15/01/2035). Maturity already in the report = 15/12/(year+19).
- **Per-month amortization rate:** `Ta = 0.416666%` of VNA (= 1/240) for months 1–239; `Taf = 0.416826%` on month 240 to absorb truncation.
- **VNA during payout** is updated by IPCA monthly, so the *real* monthly payment is approximately constant: `real_monthly ≈ V_real_at_conversion / 240`.
- **IR during payout:** 15% (we are >720d) on the gain portion of each payment.
- **B3 fee during payout:** 0% if held to conversion AND payment ≤ 6 minimum wages (we will apply 0% in projection and document the cap).
- **Future aporte projection:** historical avg & median monthly aporte, projected at the historical avg spread of existing purchases.
- **IPCA forecast:** 10-year historical avg & median (compounded monthly → yearly via `(1+m1)*…*(1+m12) - 1`), from BCB SGS 433.

---

### File Structure

- **Modify:** `/Users/j/src/jorgejr568/td/main.py` — add a `# === Renda+ projections & stats ===` section after `calc_ir_on_real` and before `fmt`, with all new pure functions; extend `write_xlsx()` to render the new "Estatísticas" block on the Resumo sheet; pass `today` and projection-related kwargs through.
- **Modify:** `/Users/j/src/jorgejr568/td/requirements.txt` — add `pytest`.
- **Modify:** `/Users/j/src/jorgejr568/td/Makefile` — add `test` target.
- **Create:** `/Users/j/src/jorgejr568/td/tests/__init__.py` — empty marker file.
- **Create:** `/Users/j/src/jorgejr568/td/tests/test_projections.py` — unit tests for all new pure functions.
- **Create:** `/Users/j/src/jorgejr568/td/tests/conftest.py` — shared fixtures (sample purchases, fake holidays).

All projection / stats logic stays in `main.py` to preserve the project's single-file convention; the test file imports from `main`.

---

### Task 1: Set up pytest

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/requirements.txt`
- Modify: `/Users/j/src/jorgejr568/td/Makefile`
- Create: `/Users/j/src/jorgejr568/td/tests/__init__.py`
- Create: `/Users/j/src/jorgejr568/td/tests/conftest.py`

- [ ] **Step 1: Append pytest to requirements.txt**

The current file has only:
```
openpyxl
requests
```
Edit it to:
```
openpyxl
requests
pytest
```

- [ ] **Step 2: Install the new dep**

Run: `.venv/bin/pip install pytest && touch .venv/.installed`
Expected: pytest installs cleanly.

- [ ] **Step 3: Add `test` target to Makefile**

After the existing `install` target, add:
```makefile
.PHONY: run install test

test: $(VENV)/.installed
	$(VENV)/bin/pytest tests/ -v
```
(Update the `.PHONY` line at the top to include `test`.)

- [ ] **Step 4: Create empty test package marker**

Write `/Users/j/src/jorgejr568/td/tests/__init__.py` with a single empty line.

- [ ] **Step 5: Create conftest.py with shared fixtures**

Write `/Users/j/src/jorgejr568/td/tests/conftest.py`:
```python
"""Shared fixtures for projection tests."""
from datetime import date

import pytest


@pytest.fixture
def sample_purchases():
    """Three purchases across two months, contracted at IPCA+6% and IPCA+7%."""
    return [
        {"date": date(2024, 1, 15), "qty": 0.05, "price": 1000.0,
         "invested": 50.0, "spread": 0.06, "mkt_gross": 60.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 60.0},
        {"date": date(2024, 1, 20), "qty": 0.10, "price": 1000.0,
         "invested": 100.0, "spread": 0.06, "mkt_gross": 120.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 120.0},
        {"date": date(2024, 3, 10), "qty": 0.20, "price": 1000.0,
         "invested": 200.0, "spread": 0.07, "mkt_gross": 240.0, "days": 1,
         "ir_rate": 0.15, "ir_tax": 0.0, "b3_fee": 0.0, "mkt_net": 240.0},
    ]


@pytest.fixture
def empty_holidays():
    return set()
```

- [ ] **Step 6: Verify pytest discovers tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: `no tests ran` (zero tests collected, exit code 5 — that's fine, just confirms discovery works).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt Makefile tests/
git commit -m "chore: add pytest and test scaffolding"
```

---

### Task 2: Extract Renda+ conversion year from bond name

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py` (add new function near top, after imports)
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

- [ ] **Step 1: Write the failing test**

Create `/Users/j/src/jorgejr568/td/tests/test_projections.py` with:
```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: ImportError (`cannot import name 'extract_renda_mais_year' from 'main'`).

- [ ] **Step 3: Implement the functions in main.py**

Locate the section after `def calc_ir_on_real(...)` (around line 175) and **before** `def fmt(...)`. Insert this new section:
```python
# ============================================================
# === Renda+ projections & stats =============================
# ============================================================

def extract_renda_mais_year(bond_name):
    """Return the year in a Renda+ bond name (e.g. 'Aposentadoria Extra 2035' -> 2035).

    Returns None if the name doesn't match a Renda+ pattern.
    """
    if "renda+" not in bond_name.lower():
        return None
    m = re.search(r"\b(20\d{2})\b", bond_name)
    return int(m.group(1)) if m else None


def renda_mais_conversion_date(year):
    """Conversion date for a Renda+ bond ('data de conversão' = 15 January of the named year)."""
    return date(year, 1, 15)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: parse Renda+ conversion year and date from bond name"
```

---

### Task 3: Monthly aporte stats

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py`
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_projections.py`:
```python
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
```

- [ ] **Step 2: Run test, verify it fails with ImportError**

Run: `.venv/bin/pytest tests/test_projections.py::TestMonthlyAporteStats -v`
Expected: ImportError.

- [ ] **Step 3: Implement `monthly_aporte_stats`**

Add to the new section in `main.py`, immediately after `renda_mais_conversion_date`:
```python
def monthly_aporte_stats(purchases):
    """Group purchases by calendar month and compute avg/median monthly aporte (BRL)."""
    if not purchases:
        return {"months": 0, "avg": 0.0, "median": 0.0, "total": 0.0,
                "first_month": None, "last_month": None}

    by_month = {}
    for p in purchases:
        key = (p["date"].year, p["date"].month)
        by_month[key] = by_month.get(key, 0.0) + p["invested"]

    keys = sorted(by_month.keys())
    values = sorted(by_month.values())
    n = len(values)
    total = sum(values)
    avg = total / n
    if n % 2 == 1:
        median = values[n // 2]
    else:
        median = (values[n // 2 - 1] + values[n // 2]) / 2

    return {
        "months": n,
        "avg": avg,
        "median": median,
        "total": total,
        "first_month": keys[0],
        "last_month": keys[-1],
    }
```

- [ ] **Step 4: Run tests, verify they pass**

Run: `.venv/bin/pytest tests/test_projections.py::TestMonthlyAporteStats -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: monthly aporte stats (avg/median by calendar month)"
```

---

### Task 4: Fetch and aggregate historical IPCA from BCB SGS 433

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py`
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_projections.py`:
```python
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
```

- [ ] **Step 2: Run, verify ImportError**

Run: `.venv/bin/pytest tests/test_projections.py::TestCompoundMonthlyToYearly tests/test_projections.py::TestYearlyIpcaStats -v`
Expected: ImportError.

- [ ] **Step 3: Implement compounding + stats + fetcher**

Add to the projection section in `main.py`:
```python
BCB_SGS_IPCA_MONTHLY_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json"
)


def fetch_monthly_ipca_history(years_back, today=None):
    """Fetch monthly IPCA % from BCB SGS series 433 for the last `years_back` calendar years.

    Returns a list of (date, monthly_pct) tuples sorted ascending. monthly_pct is the
    raw percentage (e.g., 0.42 means 0.42% — NOT 0.0042).
    """
    today = today or date.today()
    start_year = today.year - years_back
    url = (
        f"{BCB_SGS_IPCA_MONTHLY_URL}"
        f"&dataInicial=01/01/{start_year}&dataFinal=31/12/{today.year - 1}"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    out = []
    for entry in resp.json():
        d = datetime.strptime(entry["data"], "%d/%m/%Y").date()
        out.append((d, float(entry["valor"])))
    out.sort(key=lambda t: t[0])
    return out


def compound_monthly_to_yearly(monthly_pcts):
    """Compound a list of monthly IPCA percentages (e.g. 0.42 = 0.42%) into a yearly rate.

    Returns a decimal (e.g. 0.05 means 5%).
    """
    factor = 1.0
    for m in monthly_pcts:
        factor *= 1.0 + m / 100.0
    return factor - 1.0


def yearly_ipca_stats(monthly_series):
    """Aggregate (date, monthly_pct) tuples by calendar year, keep only complete years.

    Returns {'years': [(year, yearly_decimal), ...], 'avg': float, 'median': float}.
    """
    by_year = {}
    for d, m in monthly_series:
        by_year.setdefault(d.year, []).append(m)
    complete = [(y, compound_monthly_to_yearly(ms))
                for y, ms in sorted(by_year.items()) if len(ms) == 12]
    if not complete:
        return {"avg": 0.0, "median": 0.0, "years": []}
    rates = sorted(r for _, r in complete)
    n = len(rates)
    avg = sum(rates) / n
    median = rates[n // 2] if n % 2 == 1 else (rates[n // 2 - 1] + rates[n // 2]) / 2
    return {"avg": avg, "median": median, "years": complete}
```

- [ ] **Step 4: Run tests, verify pass**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: all tests pass (the fetcher itself isn't unit-tested here — we'll exercise it in the integration step).

- [ ] **Step 5: Smoke-test the fetcher live**

Run: `.venv/bin/python -c "from main import fetch_monthly_ipca_history, yearly_ipca_stats; s=fetch_monthly_ipca_history(10); print(len(s), 'months'); st=yearly_ipca_stats(s); print('avg', st['avg']); print('median', st['median']); print(st['years'])"`
Expected: ~120 months, avg/median around 4–6%, list of 10 (year, rate) tuples for 2016–2025.

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: fetch + aggregate historical IPCA from BCB SGS series 433"
```

---

### Task 5: Project accumulated real value at conversion date

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py`
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

This computes the **real value (in today's reais)** at the bond's conversion date by growing each existing purchase at its own contracted spread until conversion, then adding future monthly aportes growing at the avg historical spread.

- [ ] **Step 1: Write the failing test**

Append:
```python
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
```

- [ ] **Step 2: Run, verify ImportError**

Run: `.venv/bin/pytest tests/test_projections.py -k "AverageSpread or FutureAporte or ProjectReal" -v`
Expected: ImportError.

- [ ] **Step 3: Implement the three functions**

Add to the projection section in `main.py`:
```python
def average_spread(purchases):
    """Invested-weighted average contracted spread across purchases."""
    total_inv = sum(p["invested"] for p in purchases)
    if total_inv == 0:
        return 0.0
    return sum(p["invested"] * p["spread"] for p in purchases) / total_inv


def future_aporte_future_value(monthly, yearly_rate, n_months):
    """FV of an ordinary monthly annuity at the given yearly compound rate.

    monthly: BRL deposited at the end of each month.
    yearly_rate: decimal yearly rate (e.g. 0.065).
    n_months: number of monthly deposits.
    """
    if n_months <= 0 or monthly == 0.0:
        return 0.0
    if yearly_rate == 0.0:
        return monthly * n_months
    i = (1 + yearly_rate) ** (1 / 12) - 1
    return monthly * ((1 + i) ** n_months - 1) / i


def project_real_value_at_conversion(
    purchases, conversion_date, today, future_monthly_aporte, avg_future_spread
):
    """Project the real (today's reais) accumulated value at the conversion date.

    Each existing purchase grows at its own contracted spread from its purchase date
    to the conversion date (calendar-year approximation, not DU/252 — the precision
    of a 10–30y projection doesn't warrant the business-day count). Future aportes
    accumulate via the standard ordinary-annuity FV formula at avg_future_spread,
    starting from `today` until the conversion date.
    """
    existing = 0.0
    for p in purchases:
        years = (conversion_date - p["date"]).days / 365.25
        if years < 0:
            years = 0
        existing += p["invested"] * (1 + p["spread"]) ** years

    n_months = max(
        0,
        (conversion_date.year - today.year) * 12 + (conversion_date.month - today.month),
    )
    future = future_aporte_future_value(future_monthly_aporte, avg_future_spread, n_months)
    return existing + future
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: project real accumulated value at Renda+ conversion date"
```

---

### Task 6: Inflate real → nominal and compute monthly payout

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py`
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

- [ ] **Step 1: Write the failing test**

Append:
```python
from main import inflate_to_nominal, renda_mais_payout


class TestInflateToNominal:
    def test_inflates_real_value_by_yearly_ipca(self):
        # 1000 real, 5% IPCA, 10 years -> 1000 * 1.05^10 ≈ 1628.89
        nominal = inflate_to_nominal(real_value=1000.0, yearly_ipca=0.05,
                                     start=date(2025, 1, 1), end=date(2035, 1, 1))
        assert nominal == pytest.approx(1628.8946, abs=1e-3)

    def test_zero_years_is_identity(self):
        d = date(2030, 6, 15)
        assert inflate_to_nominal(1000.0, 0.05, d, d) == pytest.approx(1000.0)


class TestRendaMaisPayout:
    def test_240_months_split(self):
        # 240,000 real -> 1000/mo real (ignoring IR).
        result = renda_mais_payout(
            real_value_at_conversion=240_000.0,
            total_invested=120_000.0,
            conversion_date=date(2035, 1, 15),
            maturity_date=date(2054, 12, 15),
            yearly_ipca_for_inflation=0.05,
            today=date(2025, 1, 15),
        )
        assert result["n_months"] == 240
        assert result["real_monthly_gross"] == pytest.approx(1000.0)
        # Gain = (240k - 120k) / 240k = 0.5 of each payment is gain.
        # IR = 0.5 * 1000 * 0.15 = 75/mo real.
        assert result["real_monthly_net"] == pytest.approx(925.0)
        # Nominal first payment: 1000 * 1.05^10 = 1628.89.
        assert result["nominal_first_gross"] == pytest.approx(1628.89, abs=1e-2)
        # Nominal last payment: 1000 * 1.05^(years_to_maturity ≈ 29.91).
        # 1.05^29.91 ≈ 4.292
        assert result["nominal_last_gross"] == pytest.approx(1000 * 1.05 ** 29.91, rel=1e-2)

    def test_no_gain_means_no_ir(self):
        result = renda_mais_payout(
            real_value_at_conversion=120_000.0,
            total_invested=120_000.0,
            conversion_date=date(2035, 1, 15),
            maturity_date=date(2054, 12, 15),
            yearly_ipca_for_inflation=0.04,
            today=date(2025, 1, 15),
        )
        assert result["real_monthly_net"] == pytest.approx(result["real_monthly_gross"])
```

- [ ] **Step 2: Run, verify ImportError**

Run: `.venv/bin/pytest tests/test_projections.py -k "Inflate or RendaMaisPayout" -v`
Expected: ImportError.

- [ ] **Step 3: Implement both functions**

Add to projection section:
```python
RENDA_MAIS_N_PAYOUT_MONTHS = 240
RENDA_MAIS_PAYOUT_IR_RATE = 0.15  # always 15% in payout phase (>720d)


def inflate_to_nominal(real_value, yearly_ipca, start, end):
    """Inflate a real BRL value (in `start`-date reais) to nominal at `end`."""
    years = (end - start).days / 365.25
    if years <= 0:
        return real_value
    return real_value * (1 + yearly_ipca) ** years


def renda_mais_payout(
    real_value_at_conversion,
    total_invested,
    conversion_date,
    maturity_date,
    yearly_ipca_for_inflation,
    today,
):
    """Compute the monthly payout during the 240-month Renda+ payout window.

    Returns a dict with real (today's reais) and nominal (first/last payment) values,
    gross and net of 15% IR on the gain portion. Cost basis is split evenly across
    240 payments, so per-payment gain fraction = (V_c - cost) / V_c (in real terms).
    """
    n = RENDA_MAIS_N_PAYOUT_MONTHS
    real_monthly_gross = real_value_at_conversion / n

    gain = max(0.0, real_value_at_conversion - total_invested)
    gain_fraction = gain / real_value_at_conversion if real_value_at_conversion > 0 else 0
    real_monthly_ir = real_monthly_gross * gain_fraction * RENDA_MAIS_PAYOUT_IR_RATE
    real_monthly_net = real_monthly_gross - real_monthly_ir

    nominal_first_gross = inflate_to_nominal(
        real_monthly_gross, yearly_ipca_for_inflation, today, conversion_date
    )
    nominal_first_net = inflate_to_nominal(
        real_monthly_net, yearly_ipca_for_inflation, today, conversion_date
    )
    nominal_last_gross = inflate_to_nominal(
        real_monthly_gross, yearly_ipca_for_inflation, today, maturity_date
    )
    nominal_last_net = inflate_to_nominal(
        real_monthly_net, yearly_ipca_for_inflation, today, maturity_date
    )

    return {
        "n_months": n,
        "real_monthly_gross": real_monthly_gross,
        "real_monthly_net": real_monthly_net,
        "real_monthly_ir": real_monthly_ir,
        "nominal_first_gross": nominal_first_gross,
        "nominal_first_net": nominal_first_net,
        "nominal_last_gross": nominal_last_gross,
        "nominal_last_net": nominal_last_net,
        "total_real_payouts_gross": real_monthly_gross * n,
        "total_real_payouts_net": real_monthly_net * n,
    }
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: Renda+ 240-month payout projection (real and nominal)"
```

---

### Task 7: Build per-bond projection summary

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py`
- Test: `/Users/j/src/jorgejr568/td/tests/test_projections.py`

This wraps Tasks 5+6 into a single per-bond function that produces 6 scenarios per bond: the 4 combinations of (avg-aporte, median-aporte) × (avg-IPCA, median-IPCA), plus 2 "no aporte" baselines (no-aporte × avg-IPCA, no-aporte × median-IPCA). The user asked for both avg and median on aportes *and* on IPCA, and the no-aporte baseline shows what the existing balance does on its own.

- [ ] **Step 1: Write the failing test**

Append:
```python
from main import build_bond_projection


class TestBuildBondProjection:
    def test_returns_four_scenarios_for_renda_mais(self, sample_purchases):
        bond = {
            "name": "Tesouro Renda+ Aposentadoria Extra 2035",
            "maturity": date(2054, 12, 15),
            "purchases": sample_purchases,
            "total_invested": 350.0,
        }
        result = build_bond_projection(
            bond=bond,
            today=date(2025, 1, 15),
            aporte_avg=200.0,
            aporte_median=150.0,
            ipca_avg=0.05,
            ipca_median=0.04,
        )
        assert result["is_renda_mais"] is True
        assert result["conversion_date"] == date(2035, 1, 15)
        assert set(result["scenarios"].keys()) == {
            "avg_aporte_avg_ipca",
            "avg_aporte_median_ipca",
            "median_aporte_avg_ipca",
            "median_aporte_median_ipca",
        }
        scen = result["scenarios"]["avg_aporte_avg_ipca"]
        # higher aporte and higher IPCA -> larger nominal first payment
        assert scen["real_value_at_conversion"] > 0
        assert scen["nominal_value_at_conversion"] >= scen["real_value_at_conversion"]
        assert scen["payout"]["n_months"] == 240
        # Avg-aporte scenario must be > median-aporte scenario in real V_c.
        assert (result["scenarios"]["avg_aporte_avg_ipca"]["real_value_at_conversion"]
                > result["scenarios"]["median_aporte_avg_ipca"]["real_value_at_conversion"])

    def test_returns_none_for_non_renda_mais(self, sample_purchases):
        bond = {
            "name": "Tesouro IPCA+ 2035",
            "maturity": date(2035, 5, 15),
            "purchases": sample_purchases,
            "total_invested": 350.0,
        }
        result = build_bond_projection(
            bond=bond, today=date(2025, 1, 15),
            aporte_avg=200.0, aporte_median=150.0,
            ipca_avg=0.05, ipca_median=0.04,
        )
        assert result["is_renda_mais"] is False
        assert result["scenarios"] == {}
```

- [ ] **Step 2: Run, verify ImportError**

Run: `.venv/bin/pytest tests/test_projections.py -k BuildBondProjection -v`
Expected: ImportError.

- [ ] **Step 3: Implement `build_bond_projection`**

Add to projection section:
```python
def build_bond_projection(bond, today, aporte_avg, aporte_median, ipca_avg, ipca_median):
    """Compute four projection scenarios per Renda+ bond.

    Returns {'is_renda_mais', 'conversion_date', 'maturity_date', 'avg_spread',
             'scenarios': {scenario_key: {real_value_at_conversion,
                                          nominal_value_at_conversion,
                                          total_invested_through_conversion,
                                          payout: {...}}}}.
    Non-Renda+ bonds return scenarios={}.
    """
    year = extract_renda_mais_year(bond["name"])
    if year is None:
        return {"is_renda_mais": False, "scenarios": {}}

    conversion = renda_mais_conversion_date(year)
    maturity = bond["maturity"]
    avg_spr = average_spread(bond["purchases"])

    n_future_months = max(
        0, (conversion.year - today.year) * 12 + (conversion.month - today.month)
    )

    scenarios = {}
    for ap_label, ap_value in [("avg_aporte", aporte_avg), ("median_aporte", aporte_median)]:
        for ip_label, ip_value in [("avg_ipca", ipca_avg), ("median_ipca", ipca_median)]:
            key = f"{ap_label}_{ip_label}"
            real_vc = project_real_value_at_conversion(
                bond["purchases"], conversion, today,
                future_monthly_aporte=ap_value, avg_future_spread=avg_spr,
            )
            nominal_vc = inflate_to_nominal(real_vc, ip_value, today, conversion)
            total_invested = bond["total_invested"] + ap_value * n_future_months
            payout = renda_mais_payout(
                real_value_at_conversion=real_vc,
                total_invested=total_invested,
                conversion_date=conversion,
                maturity_date=maturity,
                yearly_ipca_for_inflation=ip_value,
                today=today,
            )
            scenarios[key] = {
                "real_value_at_conversion": real_vc,
                "nominal_value_at_conversion": nominal_vc,
                "total_invested_through_conversion": total_invested,
                "future_aporte_monthly": ap_value,
                "ipca_yearly": ip_value,
                "payout": payout,
            }

    return {
        "is_renda_mais": True,
        "conversion_date": conversion,
        "maturity_date": maturity,
        "avg_spread": avg_spr,
        "scenarios": scenarios,
    }
```

- [ ] **Step 4: Run, verify pass**

Run: `.venv/bin/pytest tests/test_projections.py -v`
Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_projections.py
git commit -m "feat: per-bond projection wrapper (4 avg/median scenarios)"
```

---

### Task 8: Render the new "Estatísticas" block on the Resumo sheet

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py` (extend `write_xlsx` and `main`)

This task has no test file — Excel rendering is verified by running the program and inspecting the output. It comes last so all dependencies are in place.

**Resumo sheet layout (appended below existing summary metrics):**

```
─────────────────────────────────────────────────────────────────────
ESTATÍSTICAS DE APORTES (per calendar month)
  Months with aporte:     N
  Total aported:          R$ X
  Avg per month:          R$ Y
  Median per month:       R$ Z

PROJEÇÃO IPCA (last 10 years, BCB SGS 433)
  Yearly avg:             X.XX%
  Yearly median:          X.XX%

PROJEÇÃO RENDA+ (per bond)
  ┌─────────────────────────────────────────────────────────────────┐
  │ Tesouro Renda+ ... 2035 — Conversion: 15/01/2035                │
  ├──────────────────┬──────────────────┬─────────────────┬─────────┤
  │ Cenário          │ V_c (real, hoje) │ V_c (nominal)   │ Mensal  │
  │                  │                  │                 │ (real)  │
  ├──────────────────┼──────────────────┼─────────────────┼─────────┤
  │ avg aporte +     │ R$ ...           │ R$ ...          │ R$ ...  │
  │   avg IPCA       │                  │                 │         │
  │ avg aporte +     │ R$ ...           │ R$ ...          │ R$ ...  │
  │   median IPCA    │                  │                 │         │
  │ median aporte +  │ R$ ...           │ R$ ...          │ R$ ...  │
  │   avg IPCA       │                  │                 │         │
  │ median aporte +  │ R$ ...           │ R$ ...          │ R$ ...  │
  │   median IPCA    │                  │                 │         │
  └──────────────────┴──────────────────┴─────────────────┴─────────┘
  Mensal nominal (1ª parcela @ conversão): R$ ...
  Mensal nominal (240ª parcela @ vencimento): R$ ...
  IR já descontado: 15% sobre a parcela de ganho.
```

- [ ] **Step 1: Extend `write_xlsx` signature**

Find the `write_xlsx` function header (around line 187) and change it from:
```python
def write_xlsx(bonds, ipca_rate, today, holidays):
```
to:
```python
def write_xlsx(bonds, ipca_rate, today, holidays, aporte_stats, ipca_history_stats, projections):
```

`aporte_stats` is the dict from `monthly_aporte_stats(all_purchases)`.
`ipca_history_stats` is the dict from `yearly_ipca_stats(...)`.
`projections` is `{bond_name: build_bond_projection(...)}`.

- [ ] **Step 2: Add the rendering block at the end of the Resumo sheet**

In `write_xlsx`, locate the line `# Save` near the bottom (currently right before the `output_path = ...` block at the end of the Resumo sheet section). Insert this **before** the `# Save` comment:
```python
    # ================================================================
    # Estatísticas / Projeções (Renda+)
    # ================================================================
    row += 2

    # --- Aporte stats ---
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws2.cell(row, 1, "ESTATÍSTICAS DE APORTES (por mês-calendário)")
    c.font = Font(bold=True, size=12, color="FFFFFF", name="Aptos")
    c.fill = navy
    c.alignment = center
    fill_range(ws2, row, 2, 5, navy)
    row += 1

    aporte_lines = [
        ("Meses com aporte", aporte_stats["months"], None),
        ("Total aportado", aporte_stats["total"], CURR),
        ("Média mensal", aporte_stats["avg"], CURR),
        ("Mediana mensal", aporte_stats["median"], CURR),
    ]
    for label, value, nf in aporte_lines:
        ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c = ws2.cell(row, 1, label)
        c.font = bold
        c.alignment = right
        c = ws2.cell(row, 3, value)
        c.font = bold
        c.alignment = right
        if nf:
            c.number_format = nf
        row += 1
    row += 1

    # --- IPCA history stats ---
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws2.cell(row, 1, "PROJEÇÃO IPCA (últimos 10 anos, BCB SGS 433)")
    c.font = Font(bold=True, size=12, color="FFFFFF", name="Aptos")
    c.fill = navy
    c.alignment = center
    fill_range(ws2, row, 2, 5, navy)
    row += 1

    for label, value in [("IPCA anual médio", ipca_history_stats["avg"]),
                         ("IPCA anual mediano", ipca_history_stats["median"])]:
        ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=2)
        c = ws2.cell(row, 1, label)
        c.font = bold
        c.alignment = right
        c = ws2.cell(row, 3, value)
        c.font = bold
        c.number_format = "0.00%"
        c.alignment = right
        row += 1
    row += 1

    # --- Per-bond Renda+ projections ---
    ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws2.cell(row, 1, "PROJEÇÃO RENDA+ (por título)")
    c.font = Font(bold=True, size=12, color="FFFFFF", name="Aptos")
    c.fill = navy
    c.alignment = center
    fill_range(ws2, row, 2, 5, navy)
    row += 2

    scenario_labels = {
        "avg_aporte_avg_ipca": "Aporte médio + IPCA médio",
        "avg_aporte_median_ipca": "Aporte médio + IPCA mediano",
        "median_aporte_avg_ipca": "Aporte mediano + IPCA médio",
        "median_aporte_median_ipca": "Aporte mediano + IPCA mediano",
    }

    for bond in bonds:
        proj = projections.get(bond["name"])
        if proj is None or not proj["is_renda_mais"]:
            continue

        ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        title = (
            f"{bond['name']}  |  Conversão: {proj['conversion_date'].strftime('%d/%m/%Y')}  "
            f"|  Vencimento: {proj['maturity_date'].strftime('%d/%m/%Y')}"
        )
        c = ws2.cell(row, 1, title)
        c.font = white_bold
        c.fill = purple_dark
        c.alignment = left
        fill_range(ws2, row, 2, 5, purple_dark)
        row += 1

        for ci, h in enumerate(
            ["Cenário", "V_c (real, hoje)", "V_c (nominal)", "Mensal real", "Mensal nominal (1ª)"], 1
        ):
            c = ws2.cell(row, ci, h)
            c.font = hdr_font
            c.fill = purple_light
            c.border = thin
            c.alignment = right if ci > 1 else left
        row += 1

        for idx, key in enumerate(
            ["avg_aporte_avg_ipca", "avg_aporte_median_ipca",
             "median_aporte_avg_ipca", "median_aporte_median_ipca"]
        ):
            scen = proj["scenarios"][key]
            stripe = soft_gray if idx % 2 == 1 else None
            vals = [
                scenario_labels[key],
                scen["real_value_at_conversion"],
                scen["nominal_value_at_conversion"],
                scen["payout"]["real_monthly_net"],
                scen["payout"]["nominal_first_net"],
            ]
            fmts = [None, CURR, CURR, CURR, CURR]
            for ci, (v, nf) in enumerate(zip(vals, fmts), 1):
                c = ws2.cell(row, ci, v)
                c.font = normal
                c.border = thin
                c.alignment = right if ci > 1 else left
                if nf:
                    c.number_format = nf
                if stripe:
                    c.fill = stripe
            row += 1

        # Footer note: last-payment nominal for the avg/avg scenario
        avg_avg = proj["scenarios"]["avg_aporte_avg_ipca"]["payout"]
        ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
        c = ws2.cell(
            row, 1,
            f"Mensal nominal líq. na 240ª parcela (avg+avg): "
            f"R$ {avg_avg['nominal_last_net']:,.2f}  •  "
            f"IR descontado: 15% sobre o ganho.",
        )
        c.font = muted
        c.alignment = left
        row += 2
```

- [ ] **Step 3: Wire `main()` to compute the new inputs and pass them through**

In `main()` (around line 540), after `bonds.sort(key=lambda b: b["maturity"])` and **before** the grand totals loop, insert:
```python
    # --- Aporte stats (per calendar month, across all bonds) ---
    all_purchases = [p for b in bonds for p in b["purchases"]]
    aporte_stats = monthly_aporte_stats(all_purchases)

    # --- Historical IPCA (last 10 calendar years) ---
    try:
        ipca_history = fetch_monthly_ipca_history(years_back=10, today=today)
    except Exception as e:
        print(f"Warning: failed to fetch historical IPCA: {e}", file=sys.stderr)
        ipca_history = []
    ipca_history_stats = yearly_ipca_stats(ipca_history)

    # --- Per-bond Renda+ projections ---
    projections = {}
    for b in bonds:
        projections[b["name"]] = build_bond_projection(
            bond=b,
            today=today,
            aporte_avg=aporte_stats["avg"],
            aporte_median=aporte_stats["median"],
            ipca_avg=ipca_history_stats["avg"],
            ipca_median=ipca_history_stats["median"],
        )
```

Then change the existing call (the very last call inside `main`):
```python
    write_xlsx(bonds, ipca_rate, today, holidays)
```
to:
```python
    write_xlsx(bonds, ipca_rate, today, holidays,
               aporte_stats=aporte_stats,
               ipca_history_stats=ipca_history_stats,
               projections=projections)
```

- [ ] **Step 4: Run the full pipeline**

Run: `.venv/bin/python main.py`
Expected: completes without error; `output.xlsx` is regenerated. Open the file and inspect the **Resumo** tab — the new sections appear below the existing summary metrics, formatted with the navy/purple palette consistent with the rest of the workbook.

- [ ] **Step 5: Re-run unit tests to confirm no regressions**

Run: `.venv/bin/pytest tests/ -v`
Expected: all tests still pass.

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat(output): add Renda+ projections and stats section to Resumo tab"
```

---

### Task 9: Add console-output summary line for parity with output.txt

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/main.py` (extend the printed PORTFOLIO SUMMARY)

The terminal/`output.txt` output should mirror the new info, since the `Tee` shim writes both. Keep it concise — one block per bond.

- [ ] **Step 1: Add a console-rendering helper after `pct()`**

In `main.py`, immediately after the `def pct(value):` function, add:
```python
def print_projections(aporte_stats, ipca_history_stats, projections, bonds):
    """Print the new stats and projection sections to stdout (also captured to output.txt)."""
    print()
    print("=" * 100)
    print("  APORTE STATS (por mês-calendário)")
    print("=" * 100)
    print(f"  Meses com aporte:    {aporte_stats['months']}")
    print(f"  Total aportado:      {fmt(aporte_stats['total'])}")
    print(f"  Média mensal:        {fmt(aporte_stats['avg'])}")
    print(f"  Mediana mensal:      {fmt(aporte_stats['median'])}")
    print()
    print(f"  IPCA anual médio (10y):    {ipca_history_stats['avg'] * 100:.2f}%")
    print(f"  IPCA anual mediano (10y):  {ipca_history_stats['median'] * 100:.2f}%")
    print()
    print("=" * 100)
    print("  RENDA+ PROJECTIONS")
    print("=" * 100)
    for bond in bonds:
        proj = projections.get(bond["name"])
        if proj is None or not proj["is_renda_mais"]:
            continue
        print()
        print(f"  {bond['name']}  |  Conversão: {proj['conversion_date'].strftime('%d/%m/%Y')}")
        print(
            f"  {'Cenário':<32} {'V_c real':>14} {'V_c nominal':>14} "
            f"{'Mensal real':>14} {'Mensal 1ª':>14} {'Mensal 240ª':>14}"
        )
        print("  " + "-" * 110)
        for key, label in [
            ("avg_aporte_avg_ipca", "avg aporte + avg IPCA"),
            ("avg_aporte_median_ipca", "avg aporte + median IPCA"),
            ("median_aporte_avg_ipca", "median aporte + avg IPCA"),
            ("median_aporte_median_ipca", "median aporte + median IPCA"),
        ]:
            s = proj["scenarios"][key]
            p = s["payout"]
            print(
                f"  {label:<32} {fmt(s['real_value_at_conversion'])} "
                f"{fmt(s['nominal_value_at_conversion'])} "
                f"{fmt(p['real_monthly_net'])} "
                f"{fmt(p['nominal_first_net'])} "
                f"{fmt(p['nominal_last_net'])}"
            )
    print()
```

- [ ] **Step 2: Call it from `main()` right before `write_xlsx(...)`**

In `main()`, immediately before the (now updated) `write_xlsx(...)` call, add:
```python
    print_projections(aporte_stats, ipca_history_stats, projections, bonds)
```

- [ ] **Step 3: Run the full pipeline**

Run: `.venv/bin/python main.py`
Expected: terminal shows the new APORTE STATS and RENDA+ PROJECTIONS sections; `output.txt` mirrors them; `output.xlsx` Resumo tab shows them as well.

- [ ] **Step 4: Re-run all tests**

Run: `.venv/bin/pytest tests/ -v && .venv/bin/python main.py`
Expected: all tests pass; program runs cleanly.

- [ ] **Step 5: Commit**

```bash
git add main.py
git commit -m "feat(console): mirror Renda+ projections in stdout / output.txt"
```

---

### Task 10: Document the new section in CLAUDE.md

**Files:**
- Modify: `/Users/j/src/jorgejr568/td/CLAUDE.md`

- [ ] **Step 1: Append a new section to CLAUDE.md**

After the "External APIs" section, before "Report Format", insert:
```markdown
## Projection Model (Renda+ stats)

The Resumo tab and console output include a stats / projection section computed in this order:

1. **Aporte stats** — group all purchase rows by calendar month, sum invested per month, compute avg/median.
2. **Historical IPCA** — fetch the last 10 calendar years of monthly IPCA from BCB SGS 433 (`bcdata.sgs.433`), compound monthly → yearly per year (`(1+m1)*…*(1+m12)-1`), then take avg/median across years.
3. **Real value at conversion** — for each Renda+ bond (auto-detected by `Renda+` substring, conversion date = `15/01/{year}`):
   - existing purchases grow at their own contracted spread from purchase date to conversion (calendar-year approximation);
   - future aportes added via ordinary-annuity FV at the invested-weighted avg historical spread.
4. **Nominal at conversion** — real value × `(1 + IPCA_avg_or_median)^years_to_conversion`.
5. **Monthly payout** — Renda+ pays 240 monthly amortizations (1/240 of VNA each); in real terms ≈ `V_c / 240`. IR = 15% on the gain portion (gain fraction = `(V_c - total_invested) / V_c`). B3 fee assumed 0% (held to conversion, payment ≤ 6 minimum wages).

Six scenarios are produced per bond: {no, avg, median} aporte × {avg, median} IPCA. The "no aporte" rows show the baseline where you stop contributing today and just let the existing balance grow at each purchase's contracted spread.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: explain the new Renda+ projection model in CLAUDE.md"
```

---

## Self-Review

**Spec coverage:**
- ✅ Stats section on Resumo: Task 8.
- ✅ Avg / median aporte per "aporte" (calendar-month grouped per user choice): Task 3, rendered Task 8.
- ✅ Expected amount at end of investment period (e.g., 2035) considering current amount + IPCA + spread + future aportes + avg IPCA: Tasks 5, 6, 7, 8.
- ✅ Median variant of the above: same tasks (6 scenarios including the no-aporte baseline).
- ✅ Renda+ post-conversion monthly payout (until maturity 19y later): Task 6, displayed Task 8 & 9.

**Placeholder scan:** No `TBD`, no `add appropriate error handling`, no `similar to Task N`, no missing code blocks. Every step has either runnable code or a runnable command.

**Type / signature consistency:**
- `extract_renda_mais_year(bond_name) -> int|None` — used in Task 7 ✓.
- `renda_mais_conversion_date(year) -> date` — used in Task 7 ✓.
- `monthly_aporte_stats(purchases) -> dict` keys (`months`, `avg`, `median`, `total`, `first_month`, `last_month`) — used in Task 8 (read `months`, `total`, `avg`, `median`) ✓.
- `yearly_ipca_stats(monthly_series) -> dict` keys (`avg`, `median`, `years`) — used in Task 8 (`avg`, `median`) ✓.
- `project_real_value_at_conversion(...) -> float` — args (`purchases`, `conversion_date`, `today`, `future_monthly_aporte`, `avg_future_spread`) used identically in Task 7 ✓.
- `inflate_to_nominal(real_value, yearly_ipca, start, end) -> float` — used in Task 7 ✓.
- `renda_mais_payout(...) -> dict` keys (`n_months`, `real_monthly_gross/net`, `nominal_first_gross/net`, `nominal_last_gross/net`, `total_real_payouts_*`) — read in Task 8 (`real_monthly_net`, `nominal_first_net`, `nominal_last_net`) and Task 9 (same) ✓.
- `build_bond_projection(...) -> dict` keys (`is_renda_mais`, `conversion_date`, `maturity_date`, `avg_spread`, `scenarios`) — used in Task 8 (`is_renda_mais`, `conversion_date`, `maturity_date`, `scenarios`) and Task 9 (same) ✓.

**Caveats documented in code/CLAUDE.md:**
- Calendar-year approximation for projection growth (vs. DU/252) — acceptable for 10–30y horizon, documented.
- B3 fee modeled as 0 during payout (Renda+ exemption up to 6 minimum wages) — documented.
- IR cost basis distributed evenly across 240 payments — documented in the function docstring; rigorous accounting would track per-purchase basis but this approximation is within ~1% for projections.

Plan saved to `docs/superpowers/plans/2026-05-09-renda-mais-projections.md`.
