-- Q1. Total companies
SELECT COUNT(*) AS company_count
FROM companies;

-- Q2. Row count per table
SELECT 'companies' AS table_name, COUNT(*) FROM companies
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow;

-- Q3. Companies with most P&L records
SELECT company_id, COUNT(*) AS records
FROM profitandloss
GROUP BY company_id
ORDER BY records DESC
LIMIT 10;

-- Q4. Companies with least P&L records
SELECT company_id, COUNT(*) AS records
FROM profitandloss
GROUP BY company_id
ORDER BY records ASC
LIMIT 10;

-- Q5. Year coverage in Profit & Loss
SELECT MIN(year) AS earliest_year,
       MAX(year) AS latest_year
FROM profitandloss;

-- Q6. Missing company references check
SELECT DISTINCT p.company_id
FROM profitandloss p
LEFT JOIN companies c
ON p.company_id = c.id
WHERE c.id IS NULL;

-- Q7. Balance Sheet coverage
SELECT company_id,
       COUNT(*) AS balance_sheet_records
FROM balancesheet
GROUP BY company_id
ORDER BY balance_sheet_records DESC;

-- Q8. Cash Flow coverage
SELECT company_id,
       COUNT(*) AS cashflow_records
FROM cashflow
GROUP BY company_id
ORDER BY cashflow_records DESC;

-- Q9. Documents count by company
SELECT company_id,
       COUNT(*) AS document_count
FROM documents
GROUP BY company_id
ORDER BY document_count DESC
LIMIT 10;

-- Q10. Sector distribution
SELECT broad_sector,
       COUNT(*) AS company_count
FROM sectors
GROUP BY broad_sector
ORDER BY company_count DESC;