---
name: company-research
description: Research a company and produce a sourced profile plus investment/competitive due-diligence report. Use when the user names a company and asks to research, profile, look into, do diligence on, size up, or compare it — e.g. "research Anthropic", "what's the deal with Databricks", "do diligence on Acme Corp before I invest", "who competes with Stripe". Writes a dated markdown report and gives a short verbal digest.
---

# Company Research

Produce a **sourced** report covering both a general company profile and investment/competitive due diligence. Save it to a file, then summarize the headlines in chat.

## Success criteria

A run is done when all of these hold. Loop until they do; do not stop at "I found some stuff."

1. The company is unambiguously identified (right entity, not a same-named one).
2. Every section below is either filled in or explicitly marked `Not found` with what was searched.
3. Every factual claim carries an inline source link. No source, no claim.
4. Every number carries the period it covers ("FY2025 revenue", "as of Q2 2026") and its currency.
5. The report file exists on disk and the chat digest is ≤ 10 lines.

## Step 1 — Pin down the entity before researching

Company names collide constantly. Before any real research, establish: legal/common name, HQ country, industry, and public-vs-private status.

If more than one plausible match exists (e.g. two "Nova Systems", a subsidiary vs its parent), **stop and ask the user which one** — listing the candidates with a distinguishing detail each. Researching the wrong entity wastes the whole run.

Note the status, because it decides what evidence exists:
- **Public** → primary sources exist: annual report / 10-K / 20-F, quarterly filings, investor relations page, earnings calls.
- **Private** → no filings. Expect funding rounds, investor announcements, press, job postings, and estimates. Label estimates as estimates.
- **Subsidiary** → research the parent for financials, the unit for operations. Say which is which.

## Step 2 — Research

Run searches in parallel where they're independent (several WebSearch calls in one message). Then WebFetch the primary sources — the company's own IR page, filings, and about/leadership pages — rather than relying on search snippets.

Source priority, highest first:
1. Company filings and investor relations material.
2. The company's own site (about, product, pricing, careers, newsroom).
3. Reputable financial/trade press and market-data providers.
4. Aggregators (Crunchbase-style profiles, LinkedIn headcount, wikis) — useful for shape, weak for numbers. Treat as unverified unless corroborated.

Do not fill gaps from your own prior knowledge. If a search doesn't support it, it goes in `Not found` or `Open questions`. Your training data is stale by definition and this report is expected to be current.

Cover:

- **Identity & snapshot** — legal name, founded, HQ, status, employee count (with as-of date), one sentence on what they actually do.
- **Business model** — what they sell, to whom, how revenue is earned (licence, usage, subscription, hardware, ads), pricing where public, customer concentration if disclosed.
- **Market & competitors** — market they play in and its rough size, named direct competitors, how this company differentiates, and where it looks weak.
- **Financials** — public: revenue, growth, margins, profitability, cash, debt, market cap. Private: total raised, rounds with dates and leads, last known valuation, any disclosed revenue. Say plainly when a figure is unavailable.
- **Leadership & ownership** — CEO and key executives with tenure, board or major investors, founder involvement, notable departures.
- **Recent developments** — last 12 months, each item dated: launches, funding, M&A, layoffs, leadership changes, legal/regulatory action.
- **Risks & red flags** — concentration, competitive pressure, regulation, litigation, burn vs runway, governance, key-person risk. Include what you found, not a generic risk list.
- **Open questions** — what a decision would actually hinge on that you could not verify, and where that answer would come from.

## Step 3 — Write the report

Path: `research/<company-slug>-<YYYY-MM-DD>.md` in the current project. Use today's date from the session context; if unavailable, run `date +%F`. Dating the file matters — these reports go stale and get re-run.

Use exactly this structure, one section per bullet above, in that order, plus:

- A `## Snapshot` table at the top (name, founded, HQ, status, employees, sector, one-liner).
- A `## Sources` list at the bottom: every URL used, each with what it substantiated.
- A header line stating the research date and that findings reflect sources available on that date.

Mark confidence inline where it isn't obvious: `(filed)`, `(company-stated)`, `(press estimate)`, `(unverified)`.

## Step 4 — Digest in chat

Report the file path, then at most 10 lines: what the company is, the two or three findings that would most change a decision, and the biggest unknown. Do not restate the report.

State outright anything you could not verify or had to skip. A report with three empty sections is a fine outcome for an opaque private company — silently smoothing over the gaps is not.
