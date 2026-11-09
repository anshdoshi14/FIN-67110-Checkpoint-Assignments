# Apple Checkpoint 2 - Team and Manual Review

Complete this worksheet as a team after reviewing the saved Apple run. Do not mark a review as complete unless the named reviewer independently opened the cited saved filing/fact evidence.

## Team roster

- Team name: Apple SEC Desk (Checkpoint 2)

| Member | Initials | Primary responsibility | Completion/date |
|---|---|---|---|
| Ansh Doshi | AD | Runs the SEC desk and Apple agent-team graph; writes the three analyst personas; reviews verifier marks; final review and submission | Personas and manual final review complete 2026-11-05; automated citation Completed by ZF|
| Zainab Fashola | ZF | Partner: selected Apple (AAPL) and peers; manually verifies two core claims in the saved filings; runs the Streamlit UI (`app.py`) without a terminal | Peer selection and two-claim manual check complete 2026-11-05; UI display-fix rerun completed |
| Krishmi Akurana Appuhamilage | KA | Pulls and reconciles peer `facts.json` / `peers.json`; checks fiscal-period alignment and revenue-tag consistency across AAPL/MSFT/GOOGL/ORCL; records missing-tag gaps (e.g., ORCL debt) for the Financial Analyst | Peer reconciliation table complete 2026-11-05 |

## Company and peer selection

- Partner-selected company: **Apple Inc. (AAPL)**
- Selected peer companies: **Microsoft (MSFT), Alphabet (GOOGL), Oracle (ORCL)**
- Rationale for these peers in your own words: All three are large-cap US technology issuers that file 10-Ks with XBRL on EDGAR, so the same evidence pipeline works without special handling. Each overlaps with at least one of Apple's reported revenue streams — Microsoft and Alphabet in consumer platforms, devices, and app/services ecosystems; Alphabet and Microsoft in digital services and advertising-adjacent businesses; Oracle as a pure software-and-cloud comparator that shows how Apple's blended hardware/services operating margin compares to a services-only model. They are deliberately mixed (hardware-heavy, platform, pure software) so that the Financial Analyst's peer-margin comparison surfaces definition and mix differences rather than hiding them.
- Partner confirmation - name/initials: Zainab Fashola / ZF
- Confirmation date: 2026-11-05

### Peer period and revenue-definition reference (from saved `facts.json` / `peers.json`)

| Ticker | Latest 10-K accession | Fiscal year covered | Revenue XBRL tag | Revenue ($m) | Operating income ($m) | Operating margin |
|---|---|---|---|---|---|---|
| AAPL | 0000320193-26-000026 | 2025-09-28 to 2026-09-26 | RevenueFromContractWithCustomerExcludingAssessedTax | 478,834 | 158,063 | 33.01% |
| MSFT | 0001193125-26-323660 | 2025-07-01 to 2026-06-30 | RevenueFromContractWithCustomerExcludingAssessedTax | 331,839 | 155,237 | 46.78% |
| GOOGL | 0001652044-26-000018 | 2025-01-01 to 2025-12-31 | Revenues | 402,836 | 129,039 | 32.03% |
| ORCL | 0001193125-26-277521 | 2025-06-01 to 2026-05-31 | Revenues | 67,357 | 20,606 | 30.59% |

Things to check: none of the four fiscal years line up (GOOGL's latest 10-K ends nine months before Apple's). Two different revenue tags are in use. The saved ORCL facts have no `LongTermDebtNoncurrent` / `LongTermDebtCurrent` values, so no ORCL leverage comparison is supported.

Team notes on the table (KA, 2026-11-05):
- Margins in the table reconcile to the stated revenue and operating income for all four tickers (158,063 / 478,834 = 33.01%; 155,237 / 331,839 = 46.78%; 129,039 / 402,836 = 32.03%; 20,606 / 67,357 = 30.59%).
- Fiscal-year ends span 2025-12-31 to 2026-09-26, a nine-month spread. The Financial Analyst must label each peer margin with its own period and must not describe the comparison as "same period".
- AAPL and MSFT use `RevenueFromContractWithCustomerExcludingAssessedTax`; GOOGL and ORCL use `Revenues`. Both are top-line totals in the saved facts, but the analyst must state the tag per peer rather than treating them as interchangeable without comment.
- ORCL leverage: excluded from the D/E comparison because the two debt tags are absent from the saved facts. This is recorded as a missing-tag gap, not estimated.

## Manual review of saved evidence

Saved Apple data folder: `runs/Apple_Inc_AAPL_2026-11-08_180339_UTC` (latest saved filing/facts run; the review table also documents the 2026-11-05 partner review)

Partner's Initials: ZF
Date: Nov 5 2026
Result: Pass

Arithmetic pre-check (AD, 2026-11-05, from the figures in this worksheet only — this does not replace ZF opening the saved sources):
- Revenue growth: (478,834 − 416,161) / 416,161 = 15.06% — reconciles.
- Q4 revenue growth: (114,477 − 102,466) / 102,466 = 11.72%.
- Annual EPS growth: 8.98 / 7.46 − 1 = 20.4%.
- Term debt/equity: (68,208 + 9,906) / 112,093 = 0.6969x; including $1,997m commercial paper gives total debt/equity of 0.7147x (same-period equity denominator).
- P/E: 344.63 / 8.98 = 38.38x — reconciles.

| Reviewer | Date | Claim or report section checked | Saved source opened (filing/accession/line or XBRL tag) | Result: Correct / Wrong / Needs revision | Notes or correction |
|---|---|---|---|---|---|
| ZF | 2026-11-05 | FY2026 total net sales $478,834m (prior year $416,161m; growth 15.06%) | 10-K 0000320193-26-000026 L1379; XBRL `RevenueFromContractWithCustomerExcludingAssessedTax`, end 2026-09-26 | Correct | Apple reports total net sales only; confirm this is total revenue. Selected as core claim #1 — ZF opened L1379 and the XBRL fact, confirmed the tag value and period end, and found no separate "total revenue" line. |
| ZF | 2026-11-05 | FY2026 GAAP diluted EPS $8.98 (prior year $7.46) | 10-K L1396; XBRL `EarningsPerShareDiluted`, end 2026-09-26 | Correct | Selected as core claim #2 — ZF opened L1396, confirmed the figure is the GAAP diluted line (not basic, not adjusted), and confirmed the fiscal year ended 2026-09-26. |
|  |  | Q4 FY2026 total net sales $114,477m vs $102,466m a year earlier | EX-99.1 (8-K 0000320193-26-000024) L40 |  | The quarter ended 2026-09-26. Growth computes to 11.72%; confirm L40 is the quarterly column, not the fiscal-year column |
|  |  | Q4 FY2026 GAAP diluted EPS $2.10 vs $1.85 | EX-99.1 L57; headline in L12 |  | L12 notes a $0.05 favorable impact from tariff refunds; the desk must present $2.10 as reported GAAP and mention the refund effect rather than adjusting it out |
|  |  | **Term debt/equity** 0.6969x = (68,208 + 9,906) / 112,093; **total debt/equity** including commercial paper = (68,208 + 9,906 + 1,997) / 112,093 | 10-K 0000320193-26-000026, balance sheet and debt note; XBRL `LongTermDebtCurrent` = $9,906m, `LongTermDebtNoncurrent` = $68,208m, and `StockholdersEquity` = $112,093m, all as of 2026-09-26. Commercial paper = $1,997m as of the same date (balance sheet; debt note reports $2.0bn). | calculation reviewed by ZF| Recalculation: $80,111m / $112,093m = 0.714683..., which rounds to 0.7147x at four decimals. The approximately 0.7147x result is confirmed. The 0.6969x figure excludes commercial paper and is term debt/equity; including it is total debt/equity. No reviewer mark is entered here. |
|  |  | P/E 38.38x = 344.63 / 8.98 | `AAPL_price_2026-10-30.md` (close 2026-10-30) + 10-K L1396 |  | Check the price against the team's approved market-data source; note the price date (2026-10-30) post-dates the fiscal year-end (2026-09-26) by about five weeks |

Partner verification record: ZF completed the two selected rows on 2026-11-05 and marked both **Correct** after opening the cited saved 10-K/XBRL sources. The detailed row notes above remain the claim-specific source guide.


## Required partner confirmations

- [ZF] The latest saved 10-K, 10-Q, earnings 8-K, and Exhibit 99.1 were opened and match the Apple run manifest.
- [ZF] At least two numeric claims were independently checked against the cited source.
- [ZF] Fiscal period, units, and definitions were checked for every reviewed numeric claim.
- [ZF] The peer periods and revenue definitions were reviewed; no fiscal-year alignment was assumed.
- [ZF] The closing-price date/value used for P/E was checked against the team's approved market-data source.
- [ZF] Any verifier `wrong` or `unsupported` mark was reviewed and resolved, removed, or retained with an explanation before submission.

## Team reflection

- Weakest workflow step and why: The peer comparison. The pipeline retrieves each peer's latest 10-K independently, so it silently produces four different fiscal periods and two different revenue tags, and it cannot flag when a required tag (ORCL debt) is simply absent. The comparison looks complete in the output table while actually mixing periods and definitions.
- One role likely to fail on a new company: The Financial Analyst, on any company that reports both "net sales" and "total revenue" (or "total net revenues" with a separate product/service split), or whose debt is split across notes payable, finance leases, and term debt. Apple's single "total net sales" line makes the revenue question easy; a bank, insurer, or company with meaningful "other income" would not.
- Concrete improvement to that role: Add a definition pre-check before any calculator call: list every revenue-like tag and every debt-like tag present in `facts.json`, require the analyst to name the one it is using and explain why the others are excluded, and refuse to compute growth, margin, or D/E if more than one candidate tag exists without a stated reason. The same check should emit a peer-period warning whenever fiscal-year ends differ by more than one quarter.
- One financial number a reader could easily misinterpret: The 0.6969x term debt/equity ratio. It excludes $1,997m of commercial paper; total debt/equity including it is 0.7147x, uses balance-sheet equity that is small relative to Apple's market value because of years of buybacks, and is not comparable to ORCL at all because ORCL's debt tags are missing. A reader could take it as a clean, comparable leverage figure when it is a narrowly defined one.

## Final team sign-off

- Student completing final review - name/initials: Ansh Doshi / AD
- Date: Nov 5 2026
- Final disposition: Automated citation corrections completed and the UI display-fix rerun is resolved. 
