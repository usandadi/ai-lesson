# Intel Corporation — Company Profile & Due Diligence

**Research date:** 2026-07-29. Findings reflect sources available on that date. Confidence markers: `(filed)` = SEC filing or company release, `(company-stated)` = company communication, `(press estimate)` = third-party reporting, `(unverified)` = single weak source, `(derived)` = calculated here.

---

## Snapshot

| Field | Value |
|---|---|
| Legal name | Intel Corporation |
| Ticker | NASDAQ: INTC |
| Founded | 1968 |
| HQ | Santa Clara, California, USA |
| Status | Public |
| Employees | ~85,100 as of 2025-12-27 (filed); ~84,600 as of March 2026 (press estimate) |
| Sector | Semiconductors — CPUs, data center/AI silicon, contract chip manufacturing |
| Market cap | ~$425B as of 2026-07-29 (press estimate; sources range $413B–$468B) |
| CEO | Lip-Bu Tan (since March 2025) |
| One-liner | Designs and manufactures x86 CPUs and AI data center silicon, and is building a contract foundry to fabricate chips for other companies — including its own competitors. |

---

## Business model

Intel earns revenue across four reported segments. It is one of very few chip companies that both designs and manufactures ("IDM"), which is the central fact of the investment case: the design business funds a capital-intensive manufacturing business that is not yet self-sustaining.

**Q2 2026 segment revenue** (filed):

| Segment | Revenue | YoY |
|---|---|---|
| Client Computing and Physical AI Group | $8.9B | +13% |
| Data Center and AI | $6.3B | +59% |
| Intel Foundry | $5.8B | +31% |
| All other | $0.7B | −33% |
| **Total** | **$16.1B** | **+25%** |

**FY2025 segment revenue** (filed): Client Computing $32.2B, Intel Foundry $17.8B, Data Center and AI $16.9B, All other $3.6B. Total $52.9B.

Note that Intel Foundry revenue is largely *internal* — Intel manufacturing chips for Intel. External foundry revenue is the thing that matters strategically and is not broken out in these headline figures. Treat "Foundry $5.8B, +31%" as mostly an internal transfer number, not evidence of third-party traction. `(derived from segment structure)`

Revenue model: product sales to OEMs (Dell, HP, Lenovo) and hyperscalers for CPUs; wafer/packaging services for foundry customers; no meaningful subscription component. Customer concentration is not broken out in the sources reviewed — see Open questions.

---

## Market & competitors

| Competitor | Where it competes | Position |
|---|---|---|
| AMD | x86 CPUs, client and server | Primary share threat; taking share continuously |
| Nvidia | Data center AI accelerators | Dominant in AI training; now also an Intel *investor and partner* |
| TSMC | Contract foundry | Dominant leading-edge foundry; the benchmark Intel Foundry must beat |
| Samsung Foundry | Contract foundry | Third player, also sub-scale vs TSMC |
| Arm-based vendors (Qualcomm, Ampere, in-house hyperscaler silicon) | Client and server CPUs | Structural erosion of x86 as an architecture |

**Share data is conflicting across sources and periods — do not treat any single number as settled:**

- Intel "still takes just over 71%" of the server processor market, AMD 28.8% (press estimate, earlier 2026)
- Intel's server share "slips to 67%" as AMD and Arm widen the gap (press estimate)
- AMD reached "46% of server x86 CPU revenue" while Intel holds ~70% of consumer PC share (press estimate, mid-2026)
- Intel desktop share 66.8% in Q1 2026, down from 72% a year earlier; AMD 33.2% (press estimate)
- Intel 74.4% of all x86 client+server units, AMD 25.6% (press estimate)

The spread is partly explained by **units vs revenue** (AMD sells richer server parts, so its revenue share far exceeds its unit share) and partly by differing quarters. The consistent direction across every source: Intel is losing share in both client and server, with server the more severe.

**Differentiation:** x86 installed base and software compatibility; US-based leading-edge manufacturing capacity (increasingly a policy asset, not just a technical one); advanced packaging (EMIB reported at 98% yields — press estimate).

**Where it looks weak:** no competitive answer to Nvidia in AI training. Its AI accelerator strategy has pivoted to *inference* with Crescent Island, a design using cheaper LPDDR5X memory instead of HBM in a 350W air-cooled envelope — a deliberate move to a different, less contested part of the market rather than a head-on challenge. Customer sampling targeted for H2 2026 (company-stated), so it is not yet revenue.

---

## Financials

**Q2 2026** (filed, quarter ended 2026-06-27):

| Metric | GAAP | Non-GAAP |
|---|---|---|
| Revenue | $16.1B (+25% YoY) | — |
| Gross margin | 40.4% (+12.9pp YoY) | 41.8% (+12.1pp YoY) |
| Operating income | $1.796B (11.1%) | $2.770B (17.2%) |
| Net income (loss) | **$(11.033)B** | $2.197B |
| Diluted EPS | $(2.16) | $0.42 |

The $13B gap between GAAP and non-GAAP net income is almost entirely one item: a **$12.529B non-operating mark-to-market loss on "Escrowed Shares"** — a derivative liability arising from the US Government warrant agreement under the CHIPS Act Secure Enclave program, worth $2.45 of the $2.16 loss per share (filed). This is a *non-cash accounting consequence of Intel's own share price rising*, not operational deterioration. See Risks for why it still matters.

Beating expectations materially: revenue $16.1B vs $14.42B expected, non-GAAP EPS $0.42 vs $0.21 expected (press estimate). Described as Intel's fastest revenue growth in over 15 years.

**Balance sheet, as of 2026-06-27** (filed): cash and equivalents $12.874B; short-term investments $16.853B; total debt $50.537B ($1.988B short-term, $48.549B long-term); total assets $202.439B. Net debt roughly $20.8B against liquid assets of $29.7B `(derived)`.

**Cash flow, six months ended 2026-06-27** (filed): operating cash flow $8.102B; capex $6.192B gross, less $167M government incentives.

**Q3 2026 guidance** (filed): revenue $15.8–16.8B; GAAP gross margin 41.0% / non-GAAP 42.0%; GAAP EPS $0.31 / non-GAAP $0.38.

**FY2025** (filed): revenue $52.9B, flat YoY. GAAP gross margin 34.8%, non-GAAP 36.7%. GAAP operating margin (4.2)%. GAAP net loss attributable to Intel $(0.3)B. GAAP EPS $(0.06), non-GAAP $0.42. Q4 2025 revenue $13.7B, down 4% YoY.

> **Conflict flagged, not averaged:** a secondary source states Intel's 2025 operating loss was $10.3B (vs $13.3B in 2024). That is irreconcilable with the company's own reported (4.2)% operating margin on $52.9B revenue, which implies roughly $2.2B. The $10.3B figure almost certainly refers to the **Intel Foundry segment** operating loss rather than the consolidated company, but this was not confirmed in the sources reviewed. Use the filed consolidated figure; treat $10.3B as `(unverified)` and segment-level until checked against the FY2025 10-K segment note.

**Capital structure changes since Aug 2025** — Intel raised substantial external capital at prices far below today's:

| Investor | Amount | Price/share | Stake | Date |
|---|---|---|---|---|
| US Government | $8.9B | $20.47 | 433.3M shares, 9.9% non-voting | Closed 2025-08-27 |
| SoftBank | $2.0B | $23.00 | ~2% (5th-largest holder) | Announced 2025-08-19 |
| Nvidia | $5.0B | $23.28 | 217.4M shares, ~5% | Closed Jan 2026 |

Against a market cap of ~$425B today, all three bought in at roughly $20–23. The shares have re-rated several-fold since `(derived from sourced prices)`. Existing shareholders were diluted ~17% at prices that now look extremely cheap — a material judgment on the prior board's negotiating position, though it reflected genuine distress at the time.

---

## Leadership & ownership

- **CEO: Lip-Bu Tan**, appointed March 2025. Previously CEO of Cadence Design Systems for 12 years; founder and chairman of an international semiconductor-focused VC firm. Named to TIME's 100 Most Influential People in 2026. Deep EDA and semiconductor-investing background rather than a manufacturing-operations background.
- **CFO: David Zinsner** — quoted in 2026 on foundry node strategy (press estimate); continuity from the prior regime.
- Tan has hired senior executives from **Qualcomm and Arm** to run the data center and AI divisions (press estimate) — a deliberate import of non-x86 leadership.
- **Notable holders:** US Government ~9.9% non-voting; Nvidia ~5%; SoftBank ~2%. This is an unusual register for a company of this size — a sovereign, a direct competitor, and a leveraged AI investor all on the cap table.
- Predecessor **Pat Gelsinger** departed before Tan's appointment; the foundry capex program that strained the balance sheet is attributed to him in reporting.

---

## Recent developments (last ~12 months)

- **2025-08-19** — SoftBank agrees to invest $2B at $23.00/share.
- **2025-08-22 / closed 2025-08-27** — US Government takes 9.9% non-voting stake for $8.9B ($5.7B from previously awarded but unpaid CHIPS Act grants, $3.2B from the Secure Enclave secure-chips program). 274.6M shares delivered to Commerce; 158.7M placed in escrow, released as Secure Enclave funds are disbursed. Government also holds a warrant for an additional 5% **if Intel ceases to be majority owner of its foundry business**.
- **2025-09-12** — Altera sale closes: 51% to Silver Lake for $4.46B, valuing Altera at $8.75B versus the ~$17B Intel paid in 2015. First major divestiture under Tan.
- **2025-10** — Intel 18A enters high-volume manufacturing.
- **2025-12-19** — Nvidia receives FTC clearance for its $5B investment.
- **Jan 2026** — Nvidia investment closes (217.4M shares at $23.28). Partnership covers custom x86 CPUs for Nvidia AI platforms using NVLink-C2C, and integrated x86 + RTX GPU chiplet SoCs for consumer PCs using Intel EMIB packaging.
- **Jan 2026 (CES)** — Panther Lake / Core Ultra Series 3 launched: first client platform on Intel 18A.
- **Mar 2026 (MWC) / Jun 2026 (Computex)** — Xeon 6+ "Clearwater Forest" launched, 288 E-cores, first 18A data center CPU.
- **2026** — Crescent Island inference GPU detailed (Xe3P, LPDDR5X, 350W); customer sampling targeted H2 2026; successor "Jaguar Shores" indicated for 2027.
- **2026-07-23** — Q2 2026 results: fastest growth in 15+ years, $11B GAAP loss from the escrow mark-to-market.
- **2026-07-26** — New layoff round centered on the **data center group**, despite that segment growing 59% YoY (press estimate). Cumulative reductions of 25,000+ under Tan; headcount from ~125,000 toward a stated target of ~75,000, with ~$1B further opex reduction targeted in 2026 (press estimate).

---

## Risks & red flags

1. **18A yields are not yet profitable.** 18A entered high-volume manufacturing in Oct 2025, but yields reportedly remain below profitable levels and may not hit target cost thresholds until end of 2026 at the earliest (press estimate). Intel is shipping its flagship products on a node that may still be losing money per wafer.
2. **External foundry demand is unproven and back-loaded.** Only *two* prospective 14A customers are expected to make **binding** commitments in H2 2026, with more decisions slipping into H1 2027 (press estimate). Named interest (Tesla "Terafab", plus reported AMD/Nvidia/OpenAI design wins) is largely at PDK/design-win stage — not committed volume. The entire foundry thesis rests on conversions that have not happened yet.
3. **The government stake is a live commercial liability, not just symbolism.** Intel has itself warned shareholders that the US Government's 10% stake could harm international sales (press estimate) — directly relevant given China and other non-US markets. The 5% warrant contingent on foundry majority ownership also constrains Intel's ability to spin off or sell down Foundry, which is one obvious route to value realization.
4. **The escrow derivative creates recurring GAAP volatility that is inversely tied to good news.** Because the escrowed-share liability is marked to market, *a rising Intel share price produces large GAAP losses.* Q2 2026 alone: $12.5B. Expect continued headline losses that do not reflect operations, and note the reverse — a falling share price would produce flattering GAAP gains. Any GAAP-based screen or covenant will misread this company.
5. **Persistent share loss in the core franchise.** Every source reviewed shows AMD gaining in both client and server, with Arm and hyperscaler in-house silicon eroding x86 structurally. Q2's growth was cyclical/AI-driven; it does not reverse the share trend.
6. **Capital intensity against a leveraged balance sheet.** $50.5B total debt, ~$6.2B capex in six months, and a manufacturing build-out that must be funded through the cycle. Liquidity is adequate today ($29.7B liquid) but there is limited room for a demand downturn mid-build.
7. **Cutting into a growing business.** Layoffs in the data center group while that segment grows 59% YoY is either disciplined efficiency or a mis-timed cut into the one franchise that is working. This is worth watching, not yet judgeable.
8. **Execution concentration in one unproven CEO tenure.** Tan's record — divestitures, external capital, senior hires from Arm/Qualcomm — is 16 months old. The strategy is coherent but almost entirely unrealized in the numbers.

---

## Open questions

Things a decision would actually hinge on that could not be verified from these sources:

1. **What is *external* Intel Foundry revenue, separately from internal wafer transfers?** This is the single most important number for the foundry thesis and it is not in the headline segment reporting. Source: FY2025 10-K segment footnote and quarterly 10-Q segment disclosures.
2. **What is the Intel Foundry segment operating loss for FY2025 and Q2 2026?** Needed to resolve the $10.3B conflict flagged above and to know whether foundry losses are narrowing. Source: 10-K/10-Q segment note.
3. **Who are the two prospective 14A customers expected to commit in H2 2026, and what volume?** Determines whether the foundry business becomes real. Source: Foundry Direct Connect announcements, earnings calls.
4. **Customer concentration.** No disclosure reviewed on revenue share from largest customers. Source: 10-K risk factors and concentration note.
5. **Current stock price and share count.** Market cap sources disagree by ~13% ($413B–$468B); the price is inferred here rather than read directly. Source: live quote plus 10-Q cover-page share count.
6. **Full escrow mechanics.** How many of the 158.7M escrowed shares remain, and the sensitivity of the derivative to share price. Source: 10-Q derivative liability footnote.
7. **Mobileye.** Analysts expect a sell-down or exit; nothing confirmed. Source: 8-K filings, Mobileye disclosures.
8. **Was FY2025 gross margin improvement structural or driven by the impairment comparison?** FY2025 GAAP gross margin was 34.8%; Q2 2026 was 40.4%. Source: 10-Q MD&A.

---

## Sources

- [Intel Q2 2026 press release (intc.com)](https://www.intc.com/news-events/press-releases/detail/1776/intel-reports-second-quarter-2026-financial-results) — Q2 2026 revenue, margins, GAAP/non-GAAP net income, segment revenue, balance sheet, capex, Q3 guidance, escrowed-shares mark-to-market
- [Intel Q2 2026 Form 8-K (SEC)](https://www.sec.gov/Archives/edgar/data/0000050863/000005086326000155/q226earningsrelease.htm) — filed earnings release
- [Intel Q2 2026 Form 10-Q (SEC)](https://www.sec.gov/Archives/edgar/data/0000050863/000005086326000157/intc-20260627.htm) — quarterly filing (not yet read in detail; source for open questions 1, 2, 5, 6)
- [Intel Q4/FY2025 press release (intc.com)](https://www.intc.com/news-events/press-releases/detail/1759/intel-reports-fourth-quarter-and-full-year-2025-financial) — FY2025 revenue, margins, operating margin, net loss, segment revenue, Q4 2025 revenue
- [Intel FY2025 Form 10-K (SEC)](https://www.sec.gov/Archives/edgar/data/50863/000005086326000011/intc-20251227.htm) — annual filing (source for unresolved segment questions)
- [Intel Reports Fourth-Quarter and Full-Year 2025 / Yahoo Finance analysis](https://finance.yahoo.com/news/intel-lost-money-again-2025-172300022.html) — FY2025 loss commentary, $10.3B operating loss figure (conflicting, flagged)
- [CNBC — Intel Q2 2026 earnings report](https://www.cnbc.com/2026/07/23/intel-intc-earnings-report-q2-2026.html) — beat vs expectations, segment growth
- [Yahoo Finance — Intel Q2 2026 fastest growth since 2011](https://finance.yahoo.com/markets/stocks/articles/intel-q2-2026-earnings-revenue-205531105.html) — growth framing
- [Intel appoints Lip-Bu Tan as CEO (Intel Newsroom)](https://newsroom.intel.com/corporate/intel-appoints-lip-bu-tan-chief-executive-officer) — CEO appointment, background
- [Lip-Bu Tan biography (Intel Newsroom)](https://newsroom.intel.com/biography/lip-bu-tan) — Cadence tenure, VC background
- [CNN — Intel was on the brink of downfall](https://www.cnn.com/2026/06/07/business/intel-ai-race-ceo) — Tan's 2026 actions, Qualcomm/Arm hires, divestiture
- [CNBC — US government takes 10% stake in Intel](https://www.cnbc.com/2025/08/22/intel-goverment-equity-stake.html) — $8.9B, 9.9% stake
- [Manufacturing Dive — US government 10% stake](https://www.manufacturingdive.com/news/us-government-10-percent-stake-intel-chips-funding-8-9-billion/758518/) — funding split, share counts, escrow, foundry warrant
- [Tom's Hardware — Intel warns on government stake and international sales](https://www.tomshardware.com/pc-components/cpus/intel-warns-shareholders-that-the-us-governments-10-percent-stake-could-hurt-companys-international-sales) — Intel's own risk disclosure
- [SoftBank Group — $2B Intel investment agreement](https://group.softbank/en/news/press/20250819) — $2B at $23.00/share
- [NVIDIA Newsroom — NVIDIA and Intel to develop AI infrastructure and PC products](https://nvidianews.nvidia.com/news/nvidia-and-intel-to-develop-ai-infrastructure-and-personal-computing-products) — partnership scope
- [The Tech Portal — Nvidia completes $5B Intel investment](https://thetechportal.com/2025/12/29/nvidia-completes-5bn-investment-in-intel-that-will-result-in-co-developed-ai-chips) — close, share count, price
- [Tom's Hardware — Nvidia/Intel x86 RTX SOCs](https://www.tomshardware.com/pc-components/cpus/nvidia-and-intel-announce-jointly-developed-intel-x86-rtx-socs-for-pcs-with-nvidia-graphics-also-custom-nvidia-data-center-x86-processors-nvidia-buys-usd5-billion-in-intel-stock-in-seismic-deal) — technical scope, NVLink-C2C, EMIB
- [Tom's Hardware — Intel sells 51% of Altera to Silver Lake](https://www.tomshardware.com/tech-industry/intel-sells-51-percent-of-altera-fpga-business-to-silver-lake-for-usd4-46-billion) — $4.46B, $8.75B valuation vs $17B purchase price
- [Calcalist — After Altera, is Intel preparing to sell Mobileye?](https://www.calcalistech.com/ctechnews/article/r16waps0kl) — Mobileye as non-core, 2017 $15.3B acquisition
- [Winbuzzer — Intel's 18A and 14A bets face make-or-break year](https://winbuzzer.com/2026/03/17/intels-18a-14a-roadmap-2026-foundry-panther-lake-xcxwbn/) — 18A HVM Oct 2025, yields below profitable levels
- [WCCFTech — Intel 14A/18A and advanced packaging opportunities](https://wccftech.com/intel-gives-rundown-on-14a-18a-and-advanced-packaging-opportunities/) — binding commitments expected H2 2026
- [WCCFTech — Intel Foundry design wins, EMIB yields](https://wccftech.com/intel-foundry-snags-amd-nvidia-openai-as-design-wins-on-18a-14a-nodes/) — reported design wins, 98% EMIB yields
- [Borecraft — Intel's post-18A roadmap hangs on landing 14A customers](https://borecraft.com/2026/06/17/intels-post-18a-roadmap-hangs-on-landing-14a-foundry-customers/) — Tesla Terafab, 14A maturity claims
- [Intel unveils Panther Lake architecture (intc.com)](https://www.intc.com/news-events/press-releases/detail/1752/intel-unveils-panther-lake-architecture-first-ai-pc) — first 18A client platform
- [TechTimes — Xeon 6 Plus Clearwater Forest launch](https://www.techtimes.com/articles/317620/20260602/intel-xeon-6-plus-clearwater-forest-launches-288-cores-18a-node-hits-data-center.htm) — 288 cores, first 18A data center CPU
- [Tom's Hardware — Intel roadmaps: 14A, Nova Lake, Diamond Rapids, AI accelerators](https://www.tomshardware.com/tech-industry/semiconductors/intel-chip-roadmap-2026-2028) — Crescent Island, Jaguar Shores, LPDDR5X inference strategy
- [Tom's Hardware — AMD reaches 46% of server x86 CPU revenue](https://www.tomshardware.com/pc-components/cpus/amd-reaches-46-percent-of-server-x86-cpu-revenue-intel-still-controls-70-percent-of-the-consumer-pc-market-share) — share data
- [TechPowerUp — Intel's server share slips to 67%](https://www.techpowerup.com/338409/intels-server-share-slips-to-67-as-amd-and-arm-widen-the-gap) — conflicting share data
- [The Register — AMD takes a third of server CPU market](https://www.theregister.com/systems/2026/06/04/amd-takes-a-third-of-server-cpu-market-as-shipments-grow/5251283) — share data
- [Business Stats — Intel vs AMD x86 share 2026](https://businesstats.com/worldwide-x86-intel-amd-market-share/) — AMD record 29.2%, desktop share
- [GuruFocus — INTC market cap](https://www.gurufocus.com/term/mktcap/INTC) — $425.2B as of 2026-07-29
- [Trading Economics / CompaniesMarketCap / Bullfincher](https://companiesmarketcap.com/intel/marketcap/) — conflicting market cap figures ($413B / $436B / $468B)
- [StockAnalysis — INTC employee count](https://stockanalysis.com/stocks/intc/employees/) — 85,100 as of 2025-12-27
- [Revelio Labs — Intel headcount](https://www.reveliolabs.com/companies/intel/employees) — 84,629 as of March 2026
- [Final Round AI — Intel layoffs tracker](https://www.finalroundai.com/tech-layoffs/intel) — 26,400+ cuts 2025–2026
- [TradingKey — Intel job cuts ahead of earnings](https://www.tradingkey.com/analysis/stocks/us-stocks/262044014-intel-announces-fresh-layoffs-ahead-earnings-tradingkey) — July 2026 data center layoffs
- [ClavePrep — Intel layoffs 2026](https://claveprep.com/blog/intel-layoffs-2026-career-transition-guide) — headcount trajectory toward ~75,000, $1B opex target (press estimate, weak source)
