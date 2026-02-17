<h1 align="center">
  <br>
  <img src="https://img.shields.io/badge/%20-Tesouro_Real-7B1FA2?style=for-the-badge&labelColor=7B1FA2&color=F3E5F5" alt="Tesouro Real" height="40">
  <br>
</h1>

<p align="center">
  <strong>See the true value of your Brazilian government bonds.</strong>
  <br>
  <sub>Calculate real accrued returns using your contracted rate — not just the market price.</sub>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-0A1F44?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/openpyxl-1B3A7A?style=flat-square" alt="openpyxl">
  <img src="https://img.shields.io/badge/requests-1B3A7A?style=flat-square" alt="requests">
  <img src="https://img.shields.io/badge/Brasil_API-2E7D32?style=flat-square" alt="Brasil API">
</p>

---

## What is this?

When you buy a Tesouro Direto IPCA+ bond, you lock in a rate like **IPCA + 6.38%**. But the broker only shows you the *market value* — what you'd get if you sold today. That number fluctuates with interest rate expectations and says nothing about your contracted return.

**Tesouro Real** calculates what your investment is *actually worth* based on the rate you locked in, and shows you the **gap** — how much more value you hold than the market currently reflects.

> **Gap** = Real net value (what you're entitled to at maturity) − Market net value (what you'd get selling today)

---

## Supported Bond Types

<p>
  <img src="https://img.shields.io/badge/Tesouro_IPCA+-2E7D32?style=flat-square" alt="IPCA+">
  <img src="https://img.shields.io/badge/Tesouro_RendA+-7B1FA2?style=flat-square&logoColor=white" alt="RendA+">
  <img src="https://img.shields.io/badge/Tesouro_Educa+-EF6C00?style=flat-square" alt="Educa+">
</p>

Any IPCA-indexed bond from the Tesouro Direto analytical extract.

---

## How It Works

For each purchase row in your extract:

1. Counts **business days (DU)** from purchase date to today, excluding weekends and national holidays
2. Builds the **contracted yearly rate**: `(1 + IPCA) * (1 + spread) - 1`
3. Compounds: `invested × (1 + rate) ^ (DU ÷ 252)` — the **DU/252** convention
4. Deducts **IR** (bracket from report) and **B3 fees** → net real value
5. Compares against market net value → **gap**

---

## Getting Started

### Prerequisites

- Python 3.10+
- Tesouro Direto "Extrato Analitico" XLSX files — download from your broker or [tesourodireto.com.br](https://www.tesourodireto.com.br/)

### Setup

```bash
python -m venv .venv
make install
```

### Run

```bash
make run
```

Or directly:

```bash
.venv/bin/python main.py
```

---

## Input

Place your analytical extract XLSX files in `reports/`. Each file contains one bond type:

| Row | Content |
|-----|---------|
| 1 | Bond name (`EXTRATO ANALITICO - ...`) |
| 4 | Maturity (`VENCIMENTO: DD/MM/YYYY`) |
| 8+ | Purchase rows until `Total` |

Columns per purchase: date, qty, unit price, invested, rate (`IPCA + X,XX%`), gross value, days, IR rate, IR tax, B3 fee, net value.

---

## Output

Three outputs are generated simultaneously:

| Output | Description |
|--------|-------------|
| **Terminal** | Detailed per-bond report with gains and portfolio summary |
| `output.txt` | Copy of terminal output |
| `output.xlsx` | Styled workbook — **Detalhe** (all bonds) + **Resumo** (portfolio summary) |

<details>
<summary><strong>Terminal output example</strong></summary>

```
====================================================================================================
  Tesouro RendA+ 2065  |  Maturity: 15/12/2065
====================================================================================================
  Date         Qty       Invested           Rate    DU     Real Value       Real Net        Mkt Net
----------------------------------------------------------------------------------------------------
  03/01/2025   0.38   R$       500.00   IPCA+7.47%  278   R$     583.21   R$     570.44   R$     512.30
  ...

  Real gross gain: R$      83.21  ( 16.64%)
  Real net gain:   R$      70.44  ( 14.09%)
  Market net gain: R$      12.30  (  2.46%)
  You're leaving on the table (real net - mkt net): R$      58.14
```

</details>

---

## API Dependencies

Both from [Brasil API](https://brasilapi.com.br):

| Endpoint | Purpose |
|----------|---------|
| `GET /api/taxas/v1` | Current annual IPCA rate |
| `GET /api/feriados/v1/{year}` | National holidays for DU calculation |

---

## License

MIT
