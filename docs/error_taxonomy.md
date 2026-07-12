# Error Taxonomy (Week 6 structured error analysis)

Gap #3 from our lit review: BLEU on the synthetic ASLG-PC12 corpus says nothing about
whether pronouns or negation survive translation. This taxonomy is how we look at what
BLEU hides — and it is the part of our evaluation that actually speaks to the community
critique (Yin et al. 2021; Desai et al. 2024).

## Categories

| Tag | Definition | Why it's here |
|---|---|---|
| `pronoun_referent` | Pronoun/referent lost or wrongly resolved across sentences | The phenomenon our context buffer is supposed to fix |
| `negation_scope` | Negation dropped, added, or attached to the wrong constituent | Meaning-inverting; the highest-severity error class |
| `gloss_ordering` | Right tokens, wrong order | Guo et al. found LLMs systematically mis-order gloss and needed a CTC correction step — a ready-made hypothesis |
| `topic_comment` | ASL topic-comment flattened into English SVO | The "signed English, not ASL" failure Padden & Humphries warn about |
| `oov_fingerspell` | Gloss outside the permitted vocabulary; fingerspelling mishandled | The paper handled 43 OOV words by fingerspelling |
| `context_leak` | Content from the context buffer leaked into the target gloss | A *risk introduced by our own contribution*. We must report it honestly. |
| `nmm_false_pos` / `nmm_false_neg` | Non-manual marker asserted / missed | The paper's 0.91 / 0.97 are the bar |

## Protocol

1. `tag_errors()` in `src/aslgloss/evaluation/error_analysis.py` runs **heuristic triage** and flags candidates. This is not the analysis.
2. **Two team members independently code each flagged case** plus a random sample of unflagged ones (to catch what the heuristics miss).
3. Report **inter-rater agreement** (Cohen's κ). If κ is low, the category definitions are bad — fix them, don't fudge them.
4. Report errors **by condition**, so we can say whether context actually reduced `pronoun_referent` errors or merely moved BLEU.

## The honest framing

Bigham's chapter makes the point we should carry into the report: *"works on average" is not
good enough, because average accuracy can hide terrible performance for the exact community
the tool is for*. A BLEU gain that leaves negation errors untouched is not an accessibility win.
Report which errors, on what content — not just headline scores.
