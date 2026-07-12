# Week 7: ISL Feasibility Extension — scope and honesty constraints

## The binding constraint

**No gloss-annotated ISL data exists.** ISLTranslate (~31k) and iSign (~118k) provide only
ISL video ↔ English sentence pairs. There is no ISL gloss layer anywhere.

Consequences we cannot design around:

1. **We cannot compute BLEU for ISL.** There are no references. Any number we report would be fabricated.
2. Therefore the ISL test is about **architectural transfer**, not translation quality.
3. The signing in both corpora is largely by **interpreters on educational content**, not natural Deaf-community signing. Narrow domain.

## What we can honestly claim

A structured account of **what transfers and what does not**:

| Layer | Transfers? | Evidence needed |
|---|---|---|
| Retrieval infrastructure (embed/index/top-k) | Likely yes — language-agnostic | Build an ISL example pool; show retrieval returns plausible neighbors |
| Paragraph context buffer | Likely yes — the mechanism is prompt-side | Show it assembles correctly on ISL passages |
| Prompt scaffold | Partially — grammar rules must be **rewritten**, not translated | ISL is SOV, question words go final. `prompts/isl_gloss.md` states these as PROVISIONAL |
| Gloss conventions | **No** — none exist for ISL | This is the honest finding |
| Evaluation | **No** — no references | This is the honest finding |

## How we evaluate without references

- **Human spot-checks.** Small n, clearly labeled. Ideally with ISL-fluent reviewers; if we
  cannot arrange that in the timeframe, **say so** rather than substituting our own judgment.
- The **iSign Text2Pose task** is the closest existing generation-direction ISL benchmark and
  is our best fallback target if gloss proves unworkable.

## The trap to avoid

Parthasarathy & Joshi (ICER 2024) found India's accessibility ecosystem is thinner: fewer
trained developers, weaker institutional support, harder to involve people with disabilities.
That makes a transferable pipeline **valuable** — and it also means we must not assume ISL has
ASL's datasets, annotators, or Deaf-community review infrastructure.

Producing confident-looking ISL gloss with no ISL Deaf review would be a textbook instance of
the pattern Desai et al. (2024) criticize: hearing, non-signing researchers solving the wrong
problem with unrepresentative data. **Label everything exploratory. Report the gap as a finding,
not a failure.**
