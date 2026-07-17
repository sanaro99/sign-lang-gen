# NMM gold-label annotation rubric

Operational definitions for hand-labeling the four non-manual-marker (NMM) categories on
**English sentences**. This replicates the paper's ground-truth correction step: Zhang et al.'s
four researchers re-labeled their test set so labels reflect the **text content** (their original
XML labels tracked the *signing* and misaligned with the English). Our labels play the same role
for our test split. Tooling: `scripts/nmm_annotation.py`; scoring: `scripts/evaluate.py`.

---

## In plain words

The system looks at an English sentence and predicts four yes/no facts about it — is it a yes/no
question, is it a "wh" question, does it contain an "if", does it contain a negation. To grade
those predictions we need answer keys written by people. This page is the instruction sheet those
people follow, so that two annotators working separately give (mostly) the same answers, and so a
reader can audit exactly what we counted as "negation" or "a question."

---

## Ground rules

1. **Judge the English text only.** Not how you'd sign it, not the reference gloss, not intent.
   (This mirrors the paper's correction: e.g. a sentence whose *signing* contains negation but
   whose English doesn't is labeled **0** for negation.)
2. **Form over function.** Label the grammatical form on the page, not the pragmatics
   ("Could you pass the salt?" is in *form* a yes/no question → 1, even though it's a request).
3. Labels are independent — any subset can be 1 (a wh-question can contain negation, etc.).
4. Work **independently**; do not discuss items until the agreement step. Disagreements are
   adjudicated together afterwards (that discussion is the point of the protocol — Cohen's κ is
   computed on the pre-discussion sheets).
5. Multi-sentence items: label 1 if **any** sentence in the item has the feature.

## The four labels

### `yes_no_question` — polar question form
**1 if** the item contains a direct question answerable by yes/no: subject–auxiliary inversion
("Did the kids play…?", "Is mom sick?"), a tag question ("…, isn't she?"), or a
question-marked declarative ("You're coming?").
**0 for** embedded/indirect polar clauses that aren't themselves questions
("I wonder whether he left." — statement), and for wh-questions.
*Edge:* alternative questions with polar form ("Do you want tea or coffee?") → **1** (form-based);
flag in adjudication notes if unsure.

### `wh_question` — content question form
**1 if** the item contains a direct question built on who / what / when / where / why / which /
whose / how ("Which college did Mary go to?", "Why do you hate video games?").
**0 for** embedded wh-clauses that aren't questions ("Tell me where he went.",
"I know what you did."), relative clauses ("The man who left…"), and exclamatives
("What a day!").
*Edge:* rhetorical wh-questions → **1** (form-based).

### `conditional` — conditional clause present
**1 if** the item contains a conditional subordinate construction: "if" clauses
("If John eats spinach, he will get sick."), "unless", "provided (that)", "as long as"
(conditional sense), "suppose/supposing", inverted conditionals ("Had I known…").
**0 for** temporal "when/whenever" clauses ("When I go to the park, I feel calm." — habitual
time, not condition), "if" meaning "whether" after verbs of asking/knowing ("I don't know if he
left." — embedded question → 0), and concessive "even if"… *Edge:* "even if" → **1**
(still conditional in form); imperative-or-else ("Stop, or I'll shoot.") → **0** (no conditional
clause); flag if unsure.

### `negation` — overt clausal negation marker
**1 if** the item contains an explicit negation word negating a clause or noun phrase:
not / -n't / never / no + noun ("no pets") / none / nothing / nobody / no one / neither / nor
("Mother isn't sick today.", "I don't have any pets.").
**0 for** everything that is merely *negative in meaning*:
- negative sentiment or attitude — the paper's own false-positive analysis: "Why do you **hate**
  video games?", "My sister **blamed** me but I am **innocent**!" are all **0**;
- inherently negative verbs/prepositions: refuse, deny, fail to, lack, **against**
  ("voted against" → **0** — this was our own earlier edge case);
- affixal negation: unhappy, impossible, careless → **0**;
- "without" → **0** (flag in notes if it feels clause-negating).
Rationale: the NMM this label drives is the negation marker (headshake/brow), which accompanies
overt negative signs (NOT, NONE, NEVER) — not sentiment.

## Protocol (mirrors the paper's multi-annotator correction)

1. `python scripts/nmm_annotation.py sheets --n <N>` → one blank CSV per annotator under
   gitignored `data/annotations/`.
2. Each annotator fills every label cell with 0/1, independently, rubric open.
3. `python scripts/nmm_annotation.py agreement <sheet1> <sheet2>` → per-label **Cohen's κ**,
   raw agreement, and the disagreement list (also written as a blank adjudication sheet).
   Report κ per label in the write-up. If κ < 0.6 for any label, revise this rubric's edge
   cases and re-annotate a fresh batch rather than adjudicating your way out.
4. Adjudicate disagreements **together**, filling `nmm_adjudication.csv`; record recurring
   edge-case decisions back into this rubric (append below, dated).
5. `python scripts/nmm_annotation.py merge <sheet1> <sheet2> --adjudicated <adj.csv>` →
   `data/processed/nmm_gold.jsonl`. `scripts/evaluate.py` then reports NMM P/R/F1
   automatically (macro + per-label in `results/nmm_summary.csv`).

## Honesty constraints

- **Our gold labels are not the paper's gold labels.** Their test set (ASLLRP, ~369 sentences,
  4 annotators) differs from ours (ASLG-PC12 split, our annotators). NMM P/R is comparable in
  *protocol*, not in *data* — say so wherever the numbers appear side by side
  (paper targets: macro precision 0.91 / recall 0.97; per-label y/n-Q .98/.93, wh-Q .93/.98,
  negation .79/1.00, conditional .95/~.95).
- Sheets contain corpus sentence text (ASLG-PC12, "no known license") → they stay under
  gitignored `data/`, never committed.
- κ values and annotator count go in the report's methods section; a gold set without a reported
  κ is not a gold set.

## Adjudicated edge-case decisions (append here, dated)

*(none yet)*
