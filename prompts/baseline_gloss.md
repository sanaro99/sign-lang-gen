<!-- prompts/baseline_gloss.md · v0.2
Our re-implementation of Module 1 (text->gloss) from Zhang et al., CHI 2025 (§3.1, App. B).
No Apple code or prompt text was available; this is written from the paper's method description.
Prompts are SOURCE CODE: version them, and log the hash with every run.

v0.2 (2026-07-12): ALIGNED TO ASLG-PC12 CONVENTIONS for the bring-up baseline.
A real-data check showed ASLG-PC12's "gloss" is rule-generated: it KEEPS English word order and
uses morphological prefixes (X- for pronouns, DESC- for descriptors), lemmatized + uppercased,
with articles/"of" dropped and punctuation kept. It is NOT reordered ASL grammar.
We match those conventions here so BLEU on ASLG-PC12 is meaningful (see docs/gloss_conventions.md
and docs/decision_log.md). IMPORTANT TENSION: this makes the model imitate a synthetic, English-order
pseudo-gloss, NOT real ASL. Real-ASL conventions (topic-comment reordering, dropped copula, IX
indexing) belong to the ASLLRP path and will live in a separate prompt version once DAI access lands. -->

You are converting written English into ASL gloss in the style of the ASLG-PC12 corpus.

Gloss conventions (match the examples you are given exactly):
- Output UPPERCASE tokens, one line only. No explanation, no preamble.
- Keep the SOURCE ENGLISH WORD ORDER. Do not reorder into ASL topic-comment order.
- Use the base (lemma) form of each word: VOTED -> VOTE, PROBLEMS -> PROBLEM, OPPOSED -> OPPOSE.
- Drop articles (a, an, the) and the preposition "of". Keep other prepositions (IN, ON, TO, WITH,
  INTO), the copula BE, and modals (WILL, MUST, SHOULD, CAN).
- Prefix pronouns with X-  :  I -> X-I, you -> X-YOU, we -> X-WE, it -> X-IT, they -> X-THEY.
  Possessives: my -> X-MY, and a possessive marker X-POSS for 's (group's -> GROUP X-POSS).
- Prefix descriptors (adjectives and adverbs) with DESC-  :  important -> DESC-IMPORTANT,
  external -> DESC-EXTERNAL, also -> DESC-ALSO, still -> DESC-STILL.
- Keep numbers as digits (2013). Keep sentence punctuation ( , . ) as separate tokens.
- Fingerspell unknown proper nouns as fs-WORD.

Match the style, tokenization, and prefixes of the examples you are given.
