# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment

- Python 3.10.13 (managed via asdf)
- Virtual environment at `.venv/` — **always** use `.venv` for all Python/pip operations
- Run: `.venv/bin/python main.py` or `make run`
- Install deps: `.venv/bin/pip install -r requirements.txt` or `make install`

## What This Project Does

Calculates the **real accrued value** of Tesouro Direto (Brazilian government bonds) investments using the contracted rate (IPCA + spread), and compares it against the market value from the official analytical extract reports. This reveals how much value the investor holds beyond what the current market price reflects.

## Architecture

Single-file application (`main.py`) with three logical sections:

1. **Data ingestion** — `parse_xlsx()` reads Tesouro Direto "Extrato Analítico" XLSX files from `reports/`. Each file contains one bond type with purchase rows (date, qty, price, rate, market values, IR, B3 fees).

2. **Calculation engine** — Uses the **DU/252 convention** (Brazilian fixed income standard): rates compound over *dias úteis* (business days), not calendar days. Holidays are fetched from Brasil API (`/api/feriados/v1/<year>`). The IPCA rate comes from Brasil API (`/api/taxas/v1`).

3. **Output** — Three outputs are generated simultaneously:
   - Terminal (stdout) — detailed text report
   - `output.txt` — copy of terminal output (via stdout tee)
   - `output.xlsx` — styled workbook with "Detalhe" (all bonds) and "Resumo" (portfolio summary) sheets

## Key Domain Concepts

- **DU/252**: `invested * (1 + rate) ^ (du / 252)` — business days exclude weekends and national holidays
- **Contracted rate**: `(1 + IPCA) * (1 + spread) - 1` — the real yearly rate locked at purchase
- **Gap**: difference between real net value (what you're entitled to at maturity) and market net value (what you'd get if you sold today)
- **IR bracket**: taken from the report itself (column 10), applied to gains only

## External APIs

Both from [Brasil API](https://brasilapi.com.br):
- `GET /api/taxas/v1` — current IPCA rate
- `GET /api/feriados/v1/{year}` — national holidays (fetched for each year in the investment range)

## Report Format (reports/*.xlsx)

Row 1: bond name prefixed with "EXTRATO ANALÍTICO - "
Row 4: maturity date as "VENCIMENTO: DD/MM/YYYY"
Row 8+: purchase data rows until "Total" row. Key columns: A=date, B=qty, C=price, D=invested, E=rate string ("IPCA + X,XX%"), H=gross value, I=days, J=IR rate, K=IR tax, M=B3 fee, O=net value.
