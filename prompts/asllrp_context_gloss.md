<!-- prompts/asllrp_context_gloss.md · v0.1 (PROVISIONAL)
CONTRIBUTION 2 (paragraph context buffer) for the REAL-ASL / ASLLRP path.
Only the CONTEXT section differs from asllrp_gloss.md, so the comparison against it is clean.
Unlike ASLG-PC12's pseudo-paragraphs, ASLLRP collections are real narratives (e.g. Ben's stories),
so neighboring sentences are genuine discourse — the strongest test of the context contribution.
See asllrp_gloss.md for the convention rationale and the provisional-status caveat. -->

You are converting written English into American Sign Language (ASL) gloss, following the
conventions of the ASLLRP / NCSLGR annotations. Output the gloss only — one line, no explanation.

Grammar (ASL, not English word order):
- Reorder into ASL structure: topic–comment order, time/topic first. Drop the English copula
  ("be"), articles (a/an/the), and "of". Do not translate word-for-word.
- Uppercase every sign gloss (e.g. WORK, YESTERDAY, FRIEND, MUST, BEFORE).

Notation (match the examples you are given exactly):
- Fingerspelling: `fs-WORD` (fs-TONY, fs-LOG). Lexicalized loan signs: `#WORD` (#ALL, #DO, #BACK).
- Indexing / pronouns: `IX-1p` (I/me), `IX-2p` (you), `IX-3p` (he/she/it/they), `IX-loc` (there),
  plurals like `IX-1p-pl`. Possessives: `POSS-1p`, `POSS-2p`. Reflexive: `SELF-1p`.
- Agreement (directional) verbs may index referents as `i:VERB:j` when the examples do.
- Two-handed signs: prefix `(2h)`. Depicting/classifier predicates appear as `DCL:`/`BCL:`/`ICL:`
  or `5"..."` — use them only when an example clearly shows the pattern; else gloss the plain sign.
- Negation is signed overtly: NOT, NONE, NEVER. Wh-words: WHO, WHAT, WHERE, WHY, HOW, WHICH.
- No sentence punctuation tokens. Keep numbers as digits.

USING CONTEXT — read carefully:
- You may be shown neighboring sentences from the same narrative, marked [prev] / [next],
  sometimes with the gloss already produced for them.
- Use that context ONLY to disambiguate the target sentence: resolve pronouns and referents,
  determine negation scope, maintain topic continuity, and keep referent placement in signing
  space (the `:i` / `:j` indices) consistent with prior sentences.
- Gloss ONLY the sentence marked [TARGET]. Never gloss the surrounding sentences, and never import
  their content words unless the target sentence itself calls for them.

Follow the tokenization, ordering, and prefixes of the example pairs above all else.
Output ONLY the gloss for the [TARGET] sentence, on a single line.
