"""Quality, latency, and cost metrics.

Targets from Zhang et al. (CHI 2025):
    text -> gloss           BLEU-4 = 0.276
    non-manual detection    precision = 0.91, recall = 0.97

Their numbers were computed on their ASLLRP-derived split with their preprocessing.
Ours will NOT be directly comparable unless we replicate both. Report that plainly.
And remember: BLEU on ASLG-PC12 rewards matching RULE-GENERATED glosses, which is not
the same as ASL quality. This is why the error analysis exists.

Measurement-stack additions (2026-07-18, gap G2 of the architecture map):
  - `normalize_real_asl` — a deliberately lossy "reachable-token" transform for real-ASL
    references (ASLLRP/NCSLGR), whose articulatory/spatial notation is un-generatable from
    English text and pins raw BLEU at a ~0.04 floor (see docs/results_report_asllrp.md §3).
  - `corpus_chrf`, `bleu_components` — chrF and per-n-gram precisions / brevity penalty,
    which discriminate where BLEU-4 floors out.
  - `paired_bootstrap_bleu` — paired bootstrap significance for condition-vs-baseline
    deltas, so no comparison table ships without error bars again.
  - `exact_match`, `rouge_l` — the metrics README promised but were never wired.

`summarize_run` (dead code that read a non-existent `GlossResult.reference`) was removed;
`scripts/evaluate.py` is the single aggregation path.
"""
from __future__ import annotations

import random
import re
import statistics

import sacrebleu
from sklearn.metrics import precision_recall_fscore_support

from ..config import NMM_LABELS


def corpus_bleu(hypotheses: list[str], references: list[str]) -> float:
    """Corpus BLEU-4 (sacrebleu), rescaled to 0–1 to match the paper's 0.276 target.

    Uses `tokenize="none"`: our gloss is already whitespace-tokenized and we want EXACT token
    matching, so hyphenated tokens (`X-I`, `DESC-IMPORTANT`, `fs-WORD`) and punctuation stay whole
    instead of being re-split by sacrebleu's default `13a` tokenizer (which would inflate/deflate
    the score on notation alone). See docs/gloss_conventions.md.
    """
    return sacrebleu.corpus_bleu(hypotheses, [references], tokenize="none").score / 100.0


def bleu_components(hypotheses: list[str], references: list[str]) -> dict:
    """BLEU-4 with its parts: per-n-gram precisions (%) and the brevity penalty.

    docs/results_report_asllrp.md showed the 37 -> 11 -> 3 -> 1 precision cliff is the most
    informative shape when BLEU-4 sits at its floor — so report the parts, not just the product.
    """
    b = sacrebleu.corpus_bleu(hypotheses, [references], tokenize="none")
    return {
        "bleu4": b.score / 100.0,
        "p1": b.precisions[0],
        "p2": b.precisions[1],
        "p3": b.precisions[2],
        "p4": b.precisions[3],
        "brevity_penalty": b.bp,
    }


def corpus_chrf(hypotheses: list[str], references: list[str]) -> float:
    """Corpus chrF (sacrebleu, default chrF2), rescaled to 0–1.

    Character n-grams give partial credit inside tokens (IX-3p vs IX-3p:i, fs-GALLAUDET vs
    ns-GALLAUDET), so chrF discriminates between conditions in exactly the regime where
    exact-token BLEU-4 floors out on notation. Metric-hygiene item from the landscape review §4.
    """
    return sacrebleu.corpus_chrf(hypotheses, [references]).score / 100.0


def exact_match(hypotheses: list[str], references: list[str]) -> float:
    """Fraction of sentences whose whitespace-normalized gloss equals the reference exactly."""
    if not hypotheses:
        return 0.0
    same = sum(" ".join(h.split()) == " ".join(r.split())
               for h, r in zip(hypotheses, references))
    return same / len(hypotheses)


class _SplitTokenizer:
    """Whitespace tokenizer for rouge_score, so gloss notation tokens stay whole
    (its default tokenizer would split `fs-WORD` / `IX-3p` on the hyphen)."""

    def tokenize(self, text: str) -> list[str]:
        return text.split()


def rouge_l(hypotheses: list[str], references: list[str]) -> float:
    """Mean sentence-level ROUGE-L F1 over whole gloss tokens (0–1)."""
    from rouge_score import rouge_scorer

    if not hypotheses:
        return 0.0
    scorer = rouge_scorer.RougeScorer(["rougeL"], tokenizer=_SplitTokenizer())
    scores = [scorer.score(r, h)["rougeL"].fmeasure
              for h, r in zip(hypotheses, references)]
    return statistics.mean(scores)


# ---------------------------------------------------------------------------
# Reachable-token normalization for real-ASL (ASLLRP/NCSLGR) references — G2.
# ---------------------------------------------------------------------------

# ASLLRP classifier families (paper Step 2 drops classifiers as too sparse).
_CLASSIFIER_RE = re.compile(r'^(?:\(\w+\.?\))?(?:D|L|S|B|I|BP|P)CL\b')
# Handedness / alternation prefixes: (2h), (1h), (alt.), ...
_HAND_PREFIX_RE = re.compile(r'^\((?:2h|1h|alt\.?)\)')
# Spatial locus suffixes: :i, :j, :i/j, ... (spatial coreference set up in signing space).
_LOCUS_SUFFIX_RE = re.compile(r':[a-z](?:/[a-z])*$')
# Letter-by-letter fingerspelling: fs-J-O-H-N -> collapse to fs-JOHN.
_FS_LETTERS_RE = re.compile(r'^fs-([A-Z](?:-[A-Z])+)$')


def normalize_real_asl(gloss: str) -> str:
    """Collapse a real-ASL gloss string to the tokens *reachable from English text alone*.

    ASLLRP-family references encode articulatory/spatial/prosodic detail that no text-only model
    can produce (docs/results_report_asllrp.md §3): spatial loci (`IX-3p:i`, `SELF-3p:j`),
    handedness (`(2h)`), prosody/gesture (`5"pause"`), classifiers (`DCL:B"curved"`). Scoring raw
    against these pins BLEU-4 at its noise floor and makes every condition indistinguishable.

    This transform is applied to BOTH hypothesis and reference to yield a SECONDARY
    "reachable-token" score. Rules (each mirrors or extends the paper's own Step-2 cleaning):
      - drop classifier tokens (DCL/LCL/SCL/BCL/ICL/BPCL/PCL...) — paper drops them too
      - drop tokens containing quoted material (gesture/prosody: `5"pause"`, `"what"`)
      - strip handedness prefixes `(2h)`/`(1h)`/`(alt.)` — paper drops these markers
      - strip spatial locus suffixes `:i`, `:j`, `:i/j` (keep the sign, drop the locus)
      - unify name/loan/fingerspelling prefixes: `ns-X`, `#X`, `fs-X-Y-Z` -> `fs-XYZ` form,
        so a correctly chosen name counts regardless of which spelling convention was used
      - strip trailing `+` (repetition/compound continuation) — paper drops repetition marks

    This is deliberately lossy. Report it ALONGSIDE raw BLEU, never instead of it, and never
    compare normalized numbers to the paper's 0.276 (which is on their own cleaning).
    """
    out = []
    for tok in gloss.split():
        if _CLASSIFIER_RE.match(tok):
            continue
        if '"' in tok:
            continue
        t = _HAND_PREFIX_RE.sub("", tok)
        t = _LOCUS_SUFFIX_RE.sub("", t)
        t = t.rstrip("+")
        if t.startswith("ns-"):
            t = "fs-" + t[3:]
        elif t.startswith("#") and len(t) > 1:
            t = "fs-" + t.lstrip("#")
        m = _FS_LETTERS_RE.match(t)
        if m:
            t = "fs-" + m.group(1).replace("-", "")
        if t:
            out.append(t)
    return " ".join(out)


def paired_bootstrap_bleu(hyps_a: list[str], hyps_b: list[str], references: list[str],
                          n_samples: int = 1000, seed: int = 7) -> dict:
    """Paired bootstrap resampling for the BLEU-4 delta between two systems (Koehn 2004).

    Systems A and B must be scored on the SAME sentences in the same order (paired design).
    Returns the observed delta (B - A), a 95% CI on the delta, and a two-sided p-value
    (the probability that the sign of the delta flips under resampling).

    Every condition-vs-baseline comparison must ship with this — a delta without an
    interval is how the n=50 "RAG dominates" artifact happened.
    """
    assert len(hyps_a) == len(hyps_b) == len(references), "paired design requires aligned lists"
    n = len(references)
    if n == 0:
        return {"delta": 0.0, "ci_low": 0.0, "ci_high": 0.0, "p_value": 1.0, "n": 0}

    delta_obs = corpus_bleu(hyps_b, references) - corpus_bleu(hyps_a, references)
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_samples):
        idx = [rng.randrange(n) for _ in range(n)]
        sa = [hyps_a[i] for i in idx]
        sb = [hyps_b[i] for i in idx]
        sr = [references[i] for i in idx]
        deltas.append(corpus_bleu(sb, sr) - corpus_bleu(sa, sr))
    deltas.sort()
    lo = deltas[int(0.025 * n_samples)]
    hi = deltas[min(int(0.975 * n_samples), n_samples - 1)]
    # two-sided p: how often the resampled delta crosses zero against the observed sign
    if delta_obs >= 0:
        p = 2 * sum(d <= 0 for d in deltas) / n_samples
    else:
        p = 2 * sum(d >= 0 for d in deltas) / n_samples
    return {"delta": delta_obs, "ci_low": lo, "ci_high": hi,
            "p_value": min(p, 1.0), "n": n}


def nmm_scores(preds: list[dict], golds: list[dict]) -> dict:
    """Per-label and macro-averaged precision/recall/F1 for the non-manual markers.

    Targets from the paper: precision 0.91, recall 0.97. `preds`/`golds` are dicts keyed by
    NMM_LABELS with boolean values.
    """
    out = {}
    for label in NMM_LABELS:
        y_pred = [int(p.get(label, False)) for p in preds]
        y_true = [int(g.get(label, False)) for g in golds]
        p, r, f1, _ = precision_recall_fscore_support(
            y_true, y_pred, average="binary", zero_division=0
        )
        out[label] = {"precision": p, "recall": r, "f1": f1}
    out["macro"] = {
        m: statistics.mean(out[lab][m] for lab in NMM_LABELS)
        for m in ("precision", "recall", "f1")
    }
    return out
