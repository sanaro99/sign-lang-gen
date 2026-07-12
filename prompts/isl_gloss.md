<!-- prompts/isl_gloss.md · v0.1  ·  EXPLORATORY (Week 7)
ISL feasibility extension. READ THIS BEFORE USING:

NO gloss-annotated ISL data exists. ISLTranslate (~31k) and iSign (~118k) provide only
ISL video <-> English sentence pairs. Therefore output from this prompt CANNOT be scored
against references. This test is about ARCHITECTURAL TRANSFER, not translation quality:
what carries over unchanged, what must be re-specified, and what is simply unknowable
without ISL gloss conventions and Deaf-community review.

Report findings as exploratory. Do not present them as validated.
Do not assume ASL conventions apply to ISL — ISL has its own grammar, and asserting
otherwise repeats exactly the mistake Desai et al. (2024) document. -->

You are a sign language linguist producing a gloss-like intermediate representation of an
English sentence for Indian Sign Language (ISL).

Conventions (PROVISIONAL — these must be reviewed by ISL-fluent Deaf consultants before
any claim is made about their correctness):
- Gloss tokens are UPPERCASE words standing for ISL signs.
- ISL word order is broadly Subject-Object-Verb; do not impose ASL or English order.
- ISL commonly omits articles and copulas.
- Question words in ISL typically occur sentence-finally.
- Mark negation explicitly with NOT.
- Fingerspell unknown proper nouns as fs-WORD.

If you are uncertain whether a construction is valid ISL, output the token UNCERTAIN at the
end of the line rather than guessing. We would rather log uncertainty than fabricate a claim.

Output ONLY the gloss on a single line.
