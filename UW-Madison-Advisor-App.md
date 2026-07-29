# Design Spec — UW–Madison Application Advisor

Status: **draft for review**. Nothing built yet.

## 1. Problem

A high school senior has grades, a course history, a curriculum of some rigor, and a list of
extracurriculars. They want to know what to apply for at UW–Madison.

The original framing was "recommend 1-3 bachelor programs." **Research into how UW–Madison
actually admits students dissolves most of that question**, and §6 explains why: of ~232
undergraduate majors and certificates, only **four** accept applications. For everything else
you are admitted to the university and declare a major later.

So the real decisions a senior faces are narrower and sharper:

1. Am I likely to be admitted to UW–Madison at all?
2. Should I spend my one first-choice slot on a direct-entry program, and which?
3. If I list engineering, what second choice do I have to name?
4. For a major I actually want that is gated *after* enrollment, what's the real path?

This app answers those four. It does not pretend to rank 232 majors by fit.

## 2. Scope

**In scope**
- Manual entry of a student's academic profile: grades, courses taken, curriculum rigor,
  extracurriculars, residency.
- An admission-likelihood band for the university, calibrated to published UW–Madison data.
- Direct-entry recommendation: whether to use the first-choice slot on one of the four
  programs, and which.
- The required engineering second-choice recommendation.
- Declaration-path explanation for gated majors (Computer Sciences being the important case).
- Outcome annotations per program: earnings, occupational growth, from public federal data.

**Out of scope (v1)**
- **Middle school grades.** Cut deliberately — see §11.
- Other institutions, including other UW System campuses. One institution, by §14 decision 2.
- Essays, recommendations, test prep, interview coaching.
- Cost, financial aid, scholarship matching.
- Transcript OCR or document upload. Manual entry only in v1 (§10).
- A self-reported interest inventory. Downgraded to a tiebreaker and deferred; §7 explains why
  it earns less here than it would at a different institution.

## 3. Architecture

```
                                    ┌──> AdmitBand         ─┐
Manual entry ──> StudentProfile ──> │                       │
                       │            ├──> DirectEntryAdvice ─┤
                       │            │                       ├──> Report
                 Normalizer         ├──> DeclarationPath   ─┤
                       │            │                       │
                       └──────────> └──> Prospects         ─┘
                                          ▲
Program catalog (curated JSON) ───────────┤
CDS / Scorecard / BLS  (ETL, offline) ────┘
```

Four parts, one canonical input type and one canonical program type between them:

- **StudentProfile** — the single canonical record for the student (§4). Everything downstream
  sees only this.
- **Normalizer** — pure functions: grade scale conversion, GPA computation, rigor scoring.
  No I/O.
- **Program catalog** — curated JSON, one record per program (§5). Committed to the repo, not
  fetched at runtime.
- **Four advisors** — `AdmitBand`, `DirectEntryAdvice`, `DeclarationPath`, `Prospects`. Each is
  a pure function of `(StudentProfile, Program[])`. Each returns a verdict **plus the facts that
  produced it**, because §12 requires every output be traceable to a rule.

The ETL that builds the catalog from public sources is a **separate offline script**, not part
of the request path. Federal data updates annually; there is no reason to hit an API while a
student waits, and a spec'd app that silently depends on a live third-party endpoint fails in
the field.

There are no abstractions beyond this. Four advisors exist because there are genuinely four
questions (§1). Nothing is pluggable.

## 4. Canonical schema — `StudentProfile`

| Field | Required | Notes |
|---|---|---|
| `residency` | yes | `wisconsin` \| `minnesota_reciprocity` \| `out_of_state` \| `international`. Load-bearing — §7 |
| `courses` | yes | `Course[]`, see below |
| `school_ap_offerings` | yes | Count of AP/IB/honors courses **the school offers**. The denominator in §11 |
| `activities` | no | `Activity[]`, see below |
| `test_scores` | no | SAT/ACT. Optional by design — UW–Madison is test-optional for 2025-26 |
| `graduation_year` | yes | Guards against stale catalog data |
| `intended_fields` | no | Optional free-text or picklist. Tiebreaker only (§7) |

`Course`:

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `subject` | yes | `english` \| `math` \| `science` \| `social_studies` \| `foreign_language` \| `other` |
| `level` | yes | `regular` \| `honors` \| `ap` \| `ib` \| `dual_enrollment` |
| `grade` | yes | Letter or numeric; normalized per §11 |
| `year` | yes | 9-12. Senior-year rigor is scored separately (§11) |

`Activity`:

| Field | Required | Notes |
|---|---|---|
| `name` | yes | |
| `category` | yes | Constrained picklist, not free text — keeps §7 deterministic |
| `years` | yes | Duration is the commitment signal |
| `leadership` | no | Boolean. CDS rates leadership explicitly |

## 5. Canonical schema — `Program`

| Field | Notes |
|---|---|
| `name` | e.g. "Computer Sciences, BS" |
| `cip_code` | **The join key** for every external dataset (§9) |
| `school` | Letters & Science, Engineering, Business, Education, Music, … |
| `pathway` | `direct_entry` \| `declaration_gated` \| `open` — the core taxonomy (§6) |
| `declaration_requirements` | Structured, only for `declaration_gated`. See §8 |
| `median_earnings` | From College Scorecard, by CIP |
| `occupation_outlook` | From BLS via CIP→SOC crosswalk |
| `source_urls` | Every field above must cite where it came from |
| `as_of` | Date. Catalog data goes stale annually and must say so |

`source_urls` and `as_of` are not bookkeeping. §12 forbids stating a requirement the app cannot
attribute, and a student challenged by a counselor needs to see the source.

## 6. The pathway taxonomy

This is the domain insight the whole app rests on. UW–Madison programs fall into three
mechanically different categories, and conflating them is the failure mode that makes college
advice apps useless.

### `direct_entry` — four programs, admitted from high school

Verified: **Business** (Wisconsin School of Business BBA), **Engineering** (College of
Engineering), **Dance** (School of Education), **Music** (School of Music).

To be considered, the student **must list that program as their first-choice major** on the
application. This is the only place where a major choice mechanically affects the application.

Denial outcomes, verified:

| Program | If not directly admitted |
|---|---|
| Business | Admitted as **pre-business in Letters & Science**; may apply to the BBA as a current student. ~half the BBA cohort is direct-admit from high school |
| Dance / Music | Failed audition by the decision date → admitted as **Undecided** in the respective school |
| Engineering | **No alternative pathway is stated on the direct-entry page.** See §15 — this is the open question that matters most |

Engineering additionally requires the applicant to **list a second-choice major outside the
College of Engineering**. That is a mandatory application field, so it is a real output of this
app, not advice.

### `declaration_gated` — admitted to the university, then must qualify

Computer Sciences is the load-bearing example. Requirements verified from the university guide:

- **2.250 GPA or higher** among major-declaration-eligible coursework
- GPA calculation includes **UW–Madison courses only**, counting all attempts up to the first
  passed attempt
- **BC or higher** in one of COMP SCI 300, COMP SCI/E C E 354, or COMP SCI 400
- Credit for COMP SCI 300 and MATH 222

**Read the second bullet again: UW–Madison courses only.** A 4.0 applicant with five APs and a
3.1 applicant with none arrive at this gate on identical footing. Nothing in `StudentProfile`
predicts it. §8 governs what the app is allowed to say here.

### `open` — declare freely

The large majority. No gate worth modeling; the app should say so plainly rather than invent a
fit score.

## 7. Admission probability — bands, not percentages

**The app must not output a probability percentage.** A number like "63% likely" carries false
precision the underlying data cannot support, and it is being handed to a 17-year-old making an
irreversible decision. Output is a band — `likely` / `possible` / `unlikely` — plus the specific
facts that placed the student in it.

Inputs, per the Common Data Set and UW–Madison's stated holistic-review factors:

| Factor | CDS weight (verified) | Modeled how |
|---|---|---|
| Academic record, GPA | **Very important** | Normalized GPA vs. published distribution |
| Course rigor | Emphasized in holistic review | §11 rigor score |
| Academic trend | Emphasized | Slope of GPA across grades 9-12 |
| Extracurriculars, leadership | Highly valued | Count + duration + leadership flags |
| Essay | **Important** | **Not modeled.** Out of scope (§2) — and declared as a known gap in the output |
| Test scores | **Considered** only | Bonus if submitted; never a penalty if absent |
| **Residency** | **Important** | Separate calibration per residency class |

Residency is the input most often missing from tools like this and it materially changes the
answer — out-of-state applicants need a stronger profile than headline figures imply. It is
required in §4 for that reason.

**Calibration must come from the CDS itself**, at [data.wisc.edu](https://data.wisc.edu/admissions/),
not from a secondary aggregator. Noted in §15: the aggregate admit rate is reported as 45%, but
27,527 admits against 63,537 applications computes to **43.3%**. Two sources, one number, and we
should use neither until the CDS is read directly.

Because the essay is rated *important* and is not modeled, **every admission band must state
that it excludes essay and recommendation quality.** An app that quietly omits an
officially-important factor is overclaiming.

## 8. Declaration-gated majors — the honesty requirement

This is the app's most valuable output and the one most likely to be built wrong.

For a `declaration_gated` program, the app **must not** produce a fit score, a match
percentage, or a likelihood of successful declaration. The gate is post-enrollment UW
coursework; the input data has no bearing on it. Any number here would be fabricated.

Instead the app states:

1. The actual requirement, quoted, with its source URL and `as_of` date
2. That high school performance does not factor into it
3. What the student would need to do after enrolling
4. Which prerequisite chain that implies — for CS, reaching MATH 222, which depends on incoming
   math placement, which **is** something high school data speaks to

Point 4 is the one legitimate bridge from the input data, and it is genuinely useful: a student
whose transcript stops at Algebra II has a longer road to MATH 222 than one arriving with
calculus credit. That is a real, sourceable, deterministic statement.

Telling a student "your profile cannot predict this, here is the actual gate" is more useful
than a confident fake number, and it is the only version compatible with §12.

## 9. Prospects module

All four requested signals are served by free federal data. **CIP code is the join key.**

| Signal | Source | Notes |
|---|---|---|
| Admission probability | Common Data Set | §7 |
| Median earnings, debt by program | **College Scorecard** (Dept. of Ed) | Program-level by CIP × institution. Free API |
| Program enrollment, completions | **IPEDS** (NCES) | By CIP |
| Occupational growth | **BLS Employment Projections** | 10-year projections, bridged via the **NCES CIP→SOC crosswalk** |

### On field durability

Requested, and included — but implemented as **BLS 10-year occupational projections**, which
are sourced, dated and revised annually. **Not** as an AI-displacement forecast.

No credible per-major automation forecast to 2040 exists. Publishing an invented one to a
17-year-old choosing a degree is the kind of output this spec exists to prevent. If automation
exposure is wanted specifically, the defensible form is task-composition data — routine vs.
non-routine task share per occupation — presented as **exposure**, never as prediction.

## 10. Input entry

Manual entry only in v1. A form: courses with subject/level/grade/year, activities, residency,
optional test scores, and the school's AP/IB offering count.

Transcript upload is deferred, not because it's hard but because it is the only part of this app
that needs a model (§13), and v1 should prove the advice logic is correct before adding an
extraction layer that can silently corrupt its inputs.

The school-offerings count is the one field students will resist entering. It is required
anyway, because §11 is unfair without it.

## 11. Grade normalization and rigor scoring

### Grades

Letter and numeric scales normalized to a 4.0 unweighted GPA plus a separately-tracked weighted
GPA. Both are reported — schools compute weighting inconsistently, and collapsing to one number
hides that.

Also computed: **GPA slope across grades 9-12.** Academic trend is an emphasized holistic factor
and an upward trajectory is a real signal.

### Why middle school grades are excluded

Middle school GPA has no predictive power for program fit once high school grades are present —
high school subsumes it. What middle school actually determines is the high school math track a
student landed in, and that is already visible in the course history.

Including it would add a data-entry burden and a privacy surface over younger minors' records
for no modeled benefit. Excluded by decision (§14), revisitable if trajectory turns out to
matter more than expected.

### Rigor, scored against opportunity

Rigor is scored as advanced courses taken **relative to advanced courses the school offers**,
never as an absolute count.

This is the fairness core of the app. An absolute AP count ranks a student at a school offering
25 APs above an equally strong student at a school offering three. Admissions offices evaluate
rigor relative to opportunity; if this app does not, it systematically penalizes students for
their school district.

Also scored:
- **Highest math level reached** — the single most useful predictor for STEM readiness and the
  input to §8's MATH 222 reasoning
- **Core subject depth** — years in each of English, math, science, social studies, foreign
  language
- **Senior-year rigor**, separately — a lightened senior schedule is something admissions
  notices

## 12. Output requirements

- **Every verdict cites the rule and data that produced it.** No unexplained rankings.
- **Bands, never percentages**, for admission likelihood (§7).
- **No fabricated scores for `declaration_gated` programs** (§8).
- **Named gaps.** Any officially-important factor the app does not model — the essay, above all
  — is stated in the output, not omitted.
- **Show the near-misses.** If a direct-entry program was not recommended, say which and why.
  "Not recommended because X" is more actionable than a bare recommendation, and it is what
  stops the app from being a black box the student can't argue with.
- **`as_of` dates surfaced.** Requirements change annually.
- **Advisory framing throughout.** The app is one input to a decision owned by the student and
  their counselor.

## 13. On using an LLM here (CLAUDE.md Rule 5)

**Recommendation: no LLM in v1. None.**

Every decision in this app is a deterministic function of structured inputs and a curated
catalog: GPA arithmetic, rigor ratios, prerequisite satisfaction, threshold comparison,
band assignment, table lookup. Code answers all of it, reproducibly, and §12 requires the
reasoning be traceable to a rule — which a generated ranking cannot be.

The tempting build is "put the transcript and activity list into a model, ask for three majors."
That would be wrong twice over: it is a routing and threshold problem, not a judgment call, and
the model would be selecting programs — the one thing it must never do.

Where a model earns its place later, all of it optional:

| Use | Legitimate? | Which v |
|---|---|---|
| Transcript PDF/photo → structured `Course[]` | Yes — **extraction** | v2, §10 |
| Free-text activity description → `category` | Yes — **classification** | v2, only if the picklist proves inadequate |
| Ranked output → readable prose rationale | Yes — **drafting** | v2, and only over a ranking code already produced |
| Choosing or ranking programs | **No** | never |
| Estimating admission likelihood | **No** | never |

The catalog, scoring, and advice paths stay deterministic in every version.

## 14. Decisions

| # | Question | Answer |
|---|---|---|
| 1 | Education system | **US** — GPA, AP/IB, optional SAT/ACT |
| 2 | Institution | **UW–Madison** (flagship, not Milwaukee or other UW System campuses) |
| 3 | Catalog scope | **One full institution** |
| 4 | Inputs | Grades, extracurriculars, courses taken, curriculum rigor — **plus residency**, added in §7 |
| 5 | Middle school grades | **Excluded** (§11) |
| 6 | Interest inventory | **Deferred.** Tiebreaker at most — only four direct-entry options to choose among (§7) |
| 7 | Prospects signals | Earnings, occupational growth, admission probability — **all three included** |
| 8 | Field durability | Included, as **BLS projections only**, not automation forecasts (§9) |
| 9 | Admission output form | **Bands, not percentages** (§7) |
| 10 | Language | **Python** — matches the existing app in this repo |
| 11 | Interface | Local web UI, matching `SAP-User-Role-App.md` §9 conventions |
| 12 | LLM in v1 | **No** (§13) |

### Scope note on the original ask

"Recommend 1-3 bachelor programs" is answered, but not as originally imagined. With four
direct-entry programs and one first-choice slot, the output is a first-choice recommendation, a
required engineering second choice where applicable, and declaration-path guidance for gated
majors. Recommending "1-3 of 232" would be inventing distinctions the admissions process does
not make.

## 15. Open questions and remaining risk

| # | Question | Why it matters | Where to resolve |
|---|---|---|---|
| 1 | **What happens to an engineering applicant denied direct entry?** The direct-entry page states no alternative pathway, unlike Business and Dance/Music | This is the highest-stakes unknown in the spec. If denial risks university admission, the core §8 recommendation inverts from "be ambitious" to "this is a real gamble" | UW–Madison Admissions, directly |
| 2 | Real admit rate | 45% reported vs. 43.3% computed (§7) | The CDS at data.wisc.edu |
| 3 | Actual **major** count | "232 undergraduate majors and certificates" — certificates are not majors, so catalog size is unknown | UW–Madison guide |
| 4 | Is Nursing direct entry? | The direct-entry page lists only four programs, implying no, but this was **not confirmed** | School of Nursing admissions |
| 5 | Published GPA distribution by residency | §7 cannot be calibrated without it, and it may not be published at that granularity | CDS |
| 6 | Which majors besides CS are declaration-gated, and their requirements | Determines how much of §8 applies. Curation effort scales with this | Per-program guide pages |

### Remaining risk, not a question

**Question 1 can invalidate §8's central recommendation.** The spec currently assumes no penalty
for listing a direct-entry program first, which is supported for Business, Dance and Music and
**unsupported for Engineering** — the program most students would be gambling on. Confirm with
Admissions **before** building the direct-entry advisor. It is the one prerequisite that changes
the app's main output rather than merely refining it.

Secondary risk: the catalog is manual curation that goes stale annually. This app is only as
honest as its `as_of` dates, which is why they are mandatory in §5 and surfaced in §12.

## 16. Testing approach (CLAUDE.md Rule 9)

Tests encode intent. **No test hits a live external API** — the ETL is offline (§3) and the
catalog is a committed fixture.

Fairness and normalization:
- A student with 3 of 3 available APs scores **at least as high on rigor** as one with 5 of 25.
  This is §11's whole point and it regresses silently into an absolute count.
- Identical profiles differing only in `residency` produce **different** bands. If they don't,
  §7's residency handling is dead code.
- An upward GPA trend scores above a flat one at equal final GPA — encodes "academic trend."

The honesty requirements — these are the high-stakes tests:
- A `declaration_gated` program **never** returns a numeric fit or likelihood score. A
  regression here is the app fabricating a prediction it has no basis for (§8).
- Two students with wildly different transcripts get the **same** CS declaration guidance,
  because the gate is UW coursework only. If transcript quality moves this output, §8 is broken.
- Every admission band output **contains the essay-not-modeled disclosure** (§12).
- Every verdict carries a non-empty rule citation and `as_of` date.
- No output anywhere contains a probability percentage (§7).

Direct-entry logic:
- An engineering first choice **always** yields a second-choice recommendation outside the
  College of Engineering — it is a required application field, so omitting it produces an
  unsubmittable application.
- A student not recommended for direct-entry business still sees the pre-business L&S pathway,
  not a bare rejection.

## 17. Build order

**Step 0, before any of it:** resolve §15 question 1 with UW–Madison Admissions. It can invert
the direct-entry recommendation, and building §8 first risks building it backwards.

1. `StudentProfile` + `Program` schemas and the Normalizer (pure; no catalog, no data sources)
2. Rigor and GPA scoring, including the offerings-relative denominator (§11) — fully testable
3. Program catalog: hand-curate the **four direct-entry programs plus CS** first. Five records
   exercise all three pathway types
4. `DirectEntryAdvice` + `DeclarationPath` — the two advisors with real logic
5. `AdmitBand`, once the CDS is read and §15 questions 2 and 5 are resolved
6. Offline ETL for Scorecard and BLS; expand the catalog
7. `Prospects`
8. Local web UI over the above

Steps 1-4 need no external data at all and cover the app's most valuable output. The UI is
deliberately last — a thin shell over logic that already works.

## 18. Sources

Verified 2026-07-29. Every claim in §6 and §7 traces to one of these.

- [UW–Madison direct entry programs](https://admissions.wisc.edu/direct-entry/) — the four direct-entry programs, first-choice requirement, Business pre-business fallback, Dance/Music undecided fallback, mandatory engineering second choice
- [What we look for in applicants](https://admissions.wisc.edu/can-i-get-in-to-uw-madison/) — holistic review factors
- [Academics / do you have my major](https://admissions.wisc.edu/do-you-have-my-major/) — program listing
- [Wisconsin School of Business — high school students](https://business.wisc.edu/undergraduate/admissions/high-school-students) — ~half of BBA cohort direct-admit from high school
- [Computer Sciences, BS — how to get in](https://guide.wisc.edu/undergraduate/letters-science/computer-sciences/computer-sciences-bs/) — 2.250 GPA, UW-courses-only calculation, BC requirement, MATH 222
- [UW–Madison Data, Academic Planning & Institutional Research](https://data.wisc.edu/admissions/) — Common Data Set location
- [College Scorecard](https://collegescorecard.ed.gov/data/) — program-level earnings by CIP
- [IPEDS](https://nces.ed.gov/ipeds/) — completions by CIP
- [BLS Employment Projections](https://www.bls.gov/emp/) — 10-year occupational projections
- [NCES CIP–SOC crosswalk](https://nces.ed.gov/ipeds/cipcode/resources.aspx) — CIP to occupation bridge

Aggregate admit rate figures (45% reported, 43.3% computed) came from secondary aggregators and
are **explicitly not trusted** pending §15 question 2.
