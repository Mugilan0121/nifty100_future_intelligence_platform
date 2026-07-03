# Sprint 2 Retrospective

## Sprint Objective

Sprint 2 focused on building a production-ready financial analytics engine for the Nifty 100 project by implementing financial KPIs, CAGR calculations, cash flow analytics, validation checks, unit testing, and database integration.

---

## Work Completed

### Profitability Ratios
- Net Profit Margin
- Operating Profit Margin
- Return on Equity (ROE)
- Return on Capital Employed (ROCE)

### Leverage Ratios
- Debt to Equity Ratio
- Interest Coverage Ratio

### Efficiency Ratio
- Asset Turnover Ratio

### CAGR Engine
- Revenue CAGR
- PAT CAGR
- EPS CAGR

Implemented support for:
- Normal CAGR
- Turnaround cases
- Decline-to-loss
- Both negative values
- Zero base values
- Insufficient historical data

### Cash Flow KPIs
- Free Cash Flow
- CapEx
- CFO Quality
- CapEx Intensity
- FCF Conversion
- Capital Allocation Classification

### Composite Quality Score
Integrated profitability, leverage and growth metrics into a single composite score for company comparison.

---

## Formula Decisions

- Used reusable functions for all KPI calculations.
- Kept financial calculations independent for unit testing.
- Stored computed KPIs in the financial_ratios SQLite table.
- Used five-year historical data for CAGR calculations.
- Preserved historical company-year records instead of only latest-year values.

---

## Edge Cases Handled

- Division by zero
- Zero sales
- Zero interest expense
- Debt-free companies
- Negative equity
- CAGR turnaround scenarios
- Zero starting values
- Missing historical data

---

## Validation

- financial_ratios table successfully populated.
- Total rows generated: 1184.
- All KPI columns populated.
- Unit Tests: 64 Passed / 0 Failed.
- Validation log generated for manual review.

---

## Lessons Learned

- Modular KPI functions improve maintainability.
- Unit testing helps identify schema mismatches early.
- Historical financial data requires careful handling for CAGR calculations.
- Validation logs are useful for comparing computed KPIs with source data.

---

## Sprint Outcome

Sprint 2 completed successfully with all KPI calculations implemented, validated, tested, and stored in SQLite for downstream analytics.