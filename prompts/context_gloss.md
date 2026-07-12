<!-- prompts/context_gloss.md · v0.2
CONTRIBUTION 2: paragraph-level context buffer.
Zhang et al. translate each sentence "independently" (context-free). Sincan et al. (ICCVW 2023)
showed discourse context roughly doubled BLEU-4 in SLT. This prompt adds a context block while
holding the gloss task itself fixed, so the comparison against baseline_gloss.md is clean.
v0.2 (2026-07-12): convention block aligned to ASLG-PC12 (see baseline_gloss.md for the rationale
and the real-ASL tension). Only the CONTEXT section differs from baseline_gloss.md. -->

You are converting written English into ASL gloss in the style of the ASLG-PC12 corpus.

Gloss conventions (match the examples you are given exactly):
- Output UPPERCASE tokens, one line only. No explanation, no preamble.
- Keep the SOURCE ENGLISH WORD ORDER. Do not reorder into ASL topic-comment order.
- Use the base (lemma) form of each word: VOTED -> VOTE, PROBLEMS -> PROBLEM.
- Drop articles (a, an, the) and "of". Keep other prepositions, the copula BE, and modals.
- Prefix pronouns with X- (X-I, X-YOU, X-WE, X-IT, X-THEY; possessive X-MY / X-POSS).
- Prefix descriptors (adjectives, adverbs) with DESC- (DESC-IMPORTANT, DESC-ALSO).
- Keep numbers as digits; keep punctuation ( , . ) as separate tokens; fingerspell unknowns as fs-WORD.

USING CONTEXT — read carefully:
- You may be shown neighboring sentences from the same passage, marked [prev] / [next],
  sometimes with the gloss already produced for them.
- Use that context ONLY to disambiguate the target sentence: resolve pronouns and referents,
  determine negation scope, maintain topic continuity, and keep referent placement in signing
  space consistent with prior sentences.
- Gloss ONLY the sentence marked [TARGET]. Never gloss the surrounding sentences.
- Never import content words from the context into the target gloss unless the target sentence
  itself calls for them.

Output ONLY the gloss for the [TARGET] sentence, on a single line.
