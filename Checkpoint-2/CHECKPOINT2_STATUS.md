# Checkpoint 2 — status as of 2026-11-08

**Submission requirement (Brightspace → Checkpoint 2):** a permalink to the commit holding the agent team, with the Verifier's marks on the seeded-error test. Checkpoint scores are 100 complete / 0 incomplete.

## What is done (in this repository)

| Requirement | Status | Evidence |
|---|---|---|
| Seven-step SEC pipeline preserved | Done | `sec_desk.py` unchanged |
| Fixed graph, same node order every run, no model routing | Done | `agent_team.py` — LangGraph edges; `--verify-only` separate |
| Verifier node after the Manager, no skip switch | Done | `verifier_node` in `agent_team.py`; `grep -i skip agent_team.py` finds none |
| Each role sees only task / context / expected output as JSON | Done | `runs/*/nodes/0N_*_input.json` |
| One bounded retry per analyst; no role runs more than twice | Done | `manager_node`; retry files `05_retry_*` |
| Every run saved in its own folder; earlier runs untouched | Done | microsecond-stamped `runs/` folders |
| **Seeded $1 EPS error caught** | **Done — the Checkpoint 2 deliverable** | `runs/..._SEEDED_EPS_20261105_103900_754262/verified_report.md`: `21.76` → **wrong**, corrected `20.76`, 10-K 0000909832-26-000093 `EarningsPerShareDiluted` 2026-08-30 and 10-K L1057 |
| Invented +4-point growth caught | Done | `runs/..._SEEDED_GROWTH_20261105_104648_825055`: `14.14%` → **wrong**, recomputed 10.14% from the two cited revenues |
| Two live COST graphs, distinct folders | Done | `..._081340_UTC` and `..._104149_363370_UTC` |
| Three persona files, company-neutral | Present | `roles/*.md` — see manual step 1 below about authorship |
| Three `Insight:` lines, each with a verifier mark | Done | `..._183409_583754_UTC`, `..._184645_068555_UTC` (COST); `Apple_..._183135_891654_UTC` |
| Manager rejects a part with no Insight or a headline-only Insight | Done | `_insight_restates_headline` in `agent_team.py`; tests |
| Partner's pick run and partner's two manual marks | Done | AAPL chosen by ZF; `audits/APPLE_team_manual_review.md` rows 1–2 marked Correct by ZF on 2026-11-05 |
| Team formed | Done | Apple SEC Desk: Ansh Doshi (AD), Zainab Fashola (ZF), Krishmi Akurana Appuhamilage (KA) |
| Streamlit page | Done | `app.py` |
| Test suite | 40 passed (2026-11-08) | includes four new "too-eager" guards |

## Changed on 2026-11-08 (repository clean-up)

- **Verifier bug fix (`verifier.py`).** A line-sourced claim was marked **wrong** whenever the model's quotation did not match the saved line character-for-character, even when the number itself was on that line (e.g. 939 warehouses on 10-K L734, $20.76 on EX-99.1 L52). Lab 04 says a verifier that flags correct numbers "costs you as much as one that misses". Now: number on the cited line → not wrong, model decides period/definition; number absent from the cited line → wrong; non-numeric claim values (tables, dashes) → unsupported with a plain reason. The seeded-EPS catch is unchanged (re-tested). Four regression tests added.
- **Runs pruned** from 30 folders to the 11 that are evidence (see README index). The removed folders — duplicates, incomplete runs, superseded seeds, a MSFT data pull — are kept locally in `runs_archive.zip`, not in the repository.
- **Documents consolidated.** One `README.md`; Checkpoint 1 documents moved to `docs/`; `PERSONAS_TO_WRITE.md`, `CHECKPOINT2_README.md` and `BRIGHTSPACE_SUBMISSION_TEMPLATE.txt` replaced by this file and `SUBMISSION.md`.

## Still manual — must be done by the student before submitting

1. **Personas in your own words.** The course says "No AI writes a persona: this is the part of the desk that is yours." The current text in `roles/research_analyst.md`, `roles/financial_analyst.md` and `roles/investment_advisor.md` was AI-drafted. Rewrite each six-part block in your own words (keep the technical rules above the `PERSONA START` marker unchanged; name no company). Ten minutes each.
2. **Re-run the Verifier on the saved runs with the fixed code and your API key**, so the committed marks come from the committed verifier:
   `agent_team.py --verify-only runs\<folder>` for `..._081340_UTC`, the two `SEEDED_*` copies, `..._183409_583754_UTC`, `..._184645_068555_UTC`, and `Apple_..._183135_891654_UTC`. Confirm the seeded EPS row still says **wrong → 20.76**.
3. **Optional but recommended:** one fresh COST run and one fresh AAPL run with your rewritten personas (`agent_team.py COST --peers WMT,TGT,BJ --price 904.70 --price-date 2026-09-23`; `agent_team.py AAPL --peers MSFT,GOOGL,ORCL --price 344.63 --price-date 2026-10-30`), then update the README evidence index with the new folder names.
4. **Costco human audit.** `audits/COST_audit.md` has filing-side and report-side values for all rows; every Mark is still `Pending`. Open the 10-K and EX-99.1, enter Correct / Wrong / Unsupported / Missing per row, fill the two counts at the top, and have ZF initial two rows. Rows 9–10 are flagged: the report gives Q4 **net sales** where the worksheet asks for **total revenue**.
5. **Partner UI check.** ZF runs the page (`streamlit run app.py`) on AAPL without a terminal and confirms the verified report shows. Note the date in `audits/APPLE_team_manual_review.md`.
6. **Commit, push, permalink.** `git add -A`, confirm `.env` is not staged, commit, push, `git rev-parse HEAD`, then fill `SUBMISSION.md` and paste into Brightspace. A branch URL (`/tree/main`) is not a permalink; use `/commit/<full SHA>`.

## Open limitations (say these out loud when presenting)

- Live persona runs are not clean: unsupported marks remain for unregistered prose figures and for the supplied price/peer facts, which have no XBRL source by design. The seeded test and the eleven core XBRL/ratio claims are clean.
- The Verifier cannot judge whether a true line answers the right claim, and it skips the Advisor's thesis.
- `quarterly_diluted_eps` in the 081340 run cites a 10-K line that does not contain $6.75; the Verifier correctly marks it wrong. The Financial Analyst should cite EX-99.1 L52 instead.
