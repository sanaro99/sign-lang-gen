<!-- prompts/asllrp_gloss.md · v0.1 (PROVISIONAL)
Real-ASL (ASLLRP-convention) text->gloss prompt. Our re-implementation of Module 1
(Zhang et al., CHI 2025) for the REAL-ASL path — distinct from baseline_gloss.md, which
imitates the synthetic ASLG-PC12 pseudo-gloss.
No Apple code or prompt text was used; conventions are described from the ASLLRP annotation
guidelines and observed directly in the NCSLGR corpus (see docs/gloss_conventions.md,
docs/datasets.md). This is NOT a transcription of the paper's prompt.
Prompts are SOURCE CODE: version them, log the hash with every run.

WHY THIS EXISTS: NCSLGR gloss (and ASLLRP gloss) use real conventions (fs-, IX-, POSS-, #loan,
classifier/depicting constructions) and real ASL grammar (topic-comment, dropped copula). Scoring
those references with the ASLG-PC12 prompt fails on NOTATION alone, not quality. This prompt targets
the real conventions so BLEU on NCSLGR/ASLLRP is meaningful.
STATUS: PROVISIONAL testbed prompt. Full depicting constructions (DCL:/BCL:/ICL:, 5"...") are hard to
generate faithfully; treat any BLEU from this prompt as preliminary until reviewed. The few-shot
examples you are given (real NCSLGR/ASLLRP pairs) are the primary teacher of the notation. -->

You are converting written English into American Sign Language (ASL) gloss, following the
conventions of the ASLLRP / NCSLGR annotations. Output the gloss only — one line, no explanation.

Grammar (ASL, not English word order):
- Reorder into ASL structure: topic–comment order, time/topic first. Drop the English copula
  ("be"), articles (a/an/the), and "of". Do not translate word-for-word.
- Uppercase every sign gloss (e.g. WORK, YESTERDAY, FRIEND, MUST, BEFORE).

Notation (match the examples you are given exactly):
- Fingerspelling: `fs-WORD` for spelled names/loanwords (fs-TONY, fs-LOG).
- Lexicalized loan signs: `#WORD` (#ALL, #DO, #BACK).
- Indexing / pronouns: `IX-1p` (I/me), `IX-2p` (you), `IX-3p` (he/she/it/they), `IX-loc` (there),
  plurals like `IX-1p-pl`. Possessives: `POSS-1p` (my), `POSS-2p` (your). Reflexive: `SELF-1p`.
- Agreement (directional) verbs may index start/end referents as `i:VERB:j` when the examples do.
- Two-handed signs: prefix `(2h)` (e.g. `(2h)GROW-UP`).
- Depicting / classifier predicates appear as `DCL:`, `BCL:`, `ICL:`, or `5"..."` in the references.
  Use them only when an example clearly shows the pattern; otherwise gloss the plain lexical sign.
- Negation is signed overtly: NOT, NONE, NEVER. Wh-words: WHO, WHAT, WHERE, WHY, HOW, WHICH.
- No sentence punctuation tokens. Keep numbers as digits.

Follow the tokenization, ordering, and prefixes of the example pairs you are given above all else.
