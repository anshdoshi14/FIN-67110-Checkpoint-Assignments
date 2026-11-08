# Checkpoint 2 — text to paste into Brightspace

Fill the two placeholders AFTER `git push`; do not submit with them intact.

```
Checkpoint 2 — the Verifier
Team: Apple SEC Desk — Ansh Doshi (AD), Zainab Fashola (ZF), Krishmi Akurana Appuhamilage (KA)

Repository commit permalink:
https://github.com/anshdoshi14/FIN-67110-Checkpoint-1/commit/<FULL_40_CHAR_SHA>

Agent team: Python + LangGraph. Fixed node order on every run:
SEC Steps 1–7 → Research Analyst → Financial Analyst → Investment Advisor → Strategy Manager → Verifier.
Code decides routing, inputs, the single retry and what is saved; the Verifier cannot be switched off.

Seeded-error test (Lab 04, known answer):
Saved run copied to runs/COSTCO_WHOLESALE_CORP_NEW_COST_2026-11-05_081340_UTC_SEEDED_EPS_20261105_103900_754262
Diluted EPS seeded from $20.76 to $21.76 with its source line changed to match.
Verifier mark: diluted_eps_current | 21.76 | WRONG | corrected 20.76 —
  10-K 0000909832-26-000093, EarningsPerShareDiluted, period end 2026-08-30;
  10-K L1057: "Net income increased 14% to $9,226, $20.76 per diluted share, compared to $8,099, $18.21 per diluted share in 2025"
Verified report at this commit:
https://github.com/anshdoshi14/FIN-67110-Checkpoint-1/blob/<FULL_40_CHAR_SHA>/runs/COSTCO_WHOLESALE_CORP_NEW_COST_2026-11-05_081340_UTC_SEEDED_EPS_20261105_103900_754262/verified_report.md

Also in the repository: invented-number test (+4-point growth → wrong, recomputed 10.14%), two live COST runs in distinct folders,
persona-based COST and AAPL (partner's pick) runs with three Insight lines each, partner's two manual marks in audits/APPLE_team_manual_review.md.
```

How to get the SHA (PowerShell, repository root):

```powershell
git status --short          # .env must NOT appear
git add -A
git commit -m "Checkpoint 2: fixed graph, compulsory verifier, seeded-error marks, personas, UI"
git push origin main
git rev-parse HEAD          # copy the full 40-character hash into the two <FULL_40_CHAR_SHA> slots
```

Open the permalink in an incognito window to confirm the `verified_report.md` is publicly readable before pasting it into Brightspace.
