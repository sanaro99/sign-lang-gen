"""Dataset loaders.

ASLG-PC12 (achrafothman/aslg_pc12, ~87.7k pairs) is our bring-up + evaluation corpus.

CAVEAT WE MUST NOT FORGET: its glosses are RULE-GENERATED from POS-tagged English,
not written by Deaf signers. High BLEU here does not demonstrate real ASL quality.
See ATTRIBUTION.md §4 and Yin et al. (ACL 2021), Desai et al. (LREC-COLING 2024).

NCSLGR (Boston University / Neidle, the ASLLRP family) is a small corpus of REAL,
Deaf-produced ASL gloss (~1,874 English–gloss sentence pairs) that — unlike the gated
ASLLRP Sign Bank — is publicly mirrored and can be used locally right now. Its gloss uses
true ASLLRP conventions (`fs-X`, `IX-1p`, `POSS-`, `#loan`, `DCL:`/`BCL:` depiction, `5"..."`),
so it is the right real-ASL testbed for the Phase-B prompt — NOT a drop-in for the ASLG-PC12
baseline (running the ASLG-PC12-style prompt against it scores near-zero on *notation* alone).
Licence terms are not explicitly stated on the BU page; we treat it exactly like ASLLRP —
local research/education use only, gitignored, NEVER committed. See docs/datasets.md.

ASLLRP (the paper's actual source, human-annotated) is licensed for research and education
only and MAY NOT BE REDISTRIBUTED — never commit it to this repo.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path

from ..config import DATA_DAI, DATA_PROCESSED, DATA_RAW

try:  # harden XML parsing against XXE / billion-laughs (EAF files are trusted, but cheap)
    from defusedxml.ElementTree import fromstring as _xml_fromstring
except ImportError:  # pragma: no cover - fallback if defusedxml is not installed
    _xml_fromstring = ET.fromstring


@dataclass
class Example:
    """One English sentence paired with its ASL gloss."""
    text: str
    gloss: str
    source: str = "aslg_pc12"
    doc_id: str | None = None   # set when we build paragraph-level test sets
    sent_idx: int | None = None


def load_aslg_pc12(split: str = "train", limit: int | None = None) -> list[Example]:
    """Load ASLG-PC12 English–gloss pairs from Hugging Face into Example objects.

    Remember its glosses are rule-generated, not from Deaf signers (see the module docstring).
    `limit` truncates for quick bring-up.
    """
    from datasets import load_dataset

    ds = load_dataset("achrafothman/aslg_pc12", split=split)
    if limit:
        ds = ds.select(range(min(limit, len(ds))))
    return [
        Example(text=r["text"].strip(), gloss=r["gloss"].strip(), source="aslg_pc12")
        for r in ds
    ]


# NCSLGR ELAN annotations (no video), mirrored by DePaul; parsed by the canonical
# sign-language-processing loader from these same two tiers.
NCSLGR_ANNOTATIONS_URL = "http://asl.cs.depaul.edu/corpus/elanBUcorpus.zip"
NCSLGR_GLOSS_TIER = "main gloss"
NCSLGR_TEXT_TIER = "English translation"
# Signing-based NMM tiers present in the EAF files. These describe the SIGNING, not the
# English text, so they are NOT valid gold for our text-derived NMM labels (the paper's
# Step 4 corrected labels away from signing toward the English) — useful only as a
# comparison. See docs/datasets.md and docs/nmm_annotation_rubric.md.
NCSLGR_NMM_TIERS = {
    "yes_no_question": "yes-no question",
    "wh_question": "wh question",
    "conditional": "conditional/when",
    "negation": "negative",
}


def _ncslgr_time_slots(root: ET.Element) -> dict[str, int]:
    """Map ELAN TIME_SLOT_ID -> ordering value (real TIME_VALUE when present, else slot index)."""
    slots: dict[str, int] = {}
    order = root.find("TIME_ORDER")
    if order is None:
        return slots
    for idx, ts in enumerate(order.findall("TIME_SLOT")):
        sid = ts.get("TIME_SLOT_REF") or ts.get("TIME_SLOT_ID")
        val = ts.get("TIME_VALUE")
        slots[sid] = int(val) if val is not None else idx
    return slots


def _ncslgr_tier_spans(root: ET.Element, name: str, slots: dict[str, int]):
    """Return [(start, end, value)] for a named tier, ordered by start time."""
    spans = []
    for tier in root.findall("TIER"):
        if tier.get("TIER_ID") != name:
            continue
        for ann in tier.iter("ALIGNABLE_ANNOTATION"):
            s, e = ann.get("TIME_SLOT_REF1"), ann.get("TIME_SLOT_REF2")
            val = ann.findtext("ANNOTATION_VALUE") or ""
            if s in slots and e in slots and val.strip():
                spans.append((slots[s], slots[e], val.strip()))
    return sorted(spans)


def parse_ncslgr_eaf(xml_text: str, include_nmm: bool = False) -> list[dict]:
    """Parse one NCSLGR ELAN (.eaf) file into English-text / ASL-gloss sentence dicts.

    Each English-translation span defines a sentence; its gloss is the concatenation of the
    `main gloss` tokens whose time span falls inside it (the pairing used by the canonical
    NCSLGR loader). With `include_nmm=True`, attach a `signing_nmm` dict of booleans from the
    signing-based NMM tiers — NOT gold for our text labels (see NCSLGR_NMM_TIERS).
    """
    root = _xml_fromstring(xml_text)
    slots = _ncslgr_time_slots(root)
    gloss = _ncslgr_tier_spans(root, NCSLGR_GLOSS_TIER, slots)
    texts = _ncslgr_tier_spans(root, NCSLGR_TEXT_TIER, slots)
    nmm_spans = (
        {label: _ncslgr_tier_spans(root, tier, slots) for label, tier in NCSLGR_NMM_TIERS.items()}
        if include_nmm else {}
    )

    out = []
    for s, e, text in texts:
        toks = [t for (gs, ge, t) in gloss if gs >= s and ge <= e]
        if not toks:
            continue
        rec = {"text": text, "gloss": " ".join(toks)}
        if include_nmm:
            rec["signing_nmm"] = {
                label: any(gs < e and ge > s for (gs, ge, _t) in spans)
                for label, spans in nmm_spans.items()
            }
        out.append(rec)
    return out


def _ncslgr_corpus_dir(cache_dir: Path | None = None) -> Path:
    """Download (once) and extract the NCSLGR ELAN annotation zip; return the eaf directory.

    Cached under data/raw/ (gitignored). Annotations only — no video is fetched.
    """
    import io
    import urllib.request
    import zipfile

    cache_dir = cache_dir or DATA_RAW
    eaf_dir = cache_dir / "ncslgr" / "elanBUcorpus"
    if eaf_dir.is_dir() and any(eaf_dir.glob("*.eaf")):
        return eaf_dir
    eaf_dir.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(NCSLGR_ANNOTATIONS_URL, timeout=180) as resp:  # noqa: S310
        blob = resp.read()
    zipfile.ZipFile(io.BytesIO(blob)).extractall(eaf_dir.parent)
    return eaf_dir


def load_ncslgr(include_nmm: bool = False, cache_dir: Path | None = None) -> list[Example]:
    """Load NCSLGR real-ASL English–gloss pairs (~1,874) into Example objects.

    Downloads the ELAN annotations to gitignored data/raw/ on first use (no video).
    Gloss uses true ASLLRP conventions — do NOT score it with the ASLG-PC12 prompt
    (notation mismatch); it is the real-ASL testbed for the Phase-B prompt. `include_nmm`
    keeps the signing-based NMM tiers for comparison (they are not text-NMM gold).
    """
    eaf_dir = _ncslgr_corpus_dir(cache_dir)
    examples: list[Example] = []
    for eaf in sorted(eaf_dir.glob("*.eaf")):
        doc_id = eaf.stem
        xml_text = eaf.read_text(encoding="utf-8")
        for sent_idx, rec in enumerate(parse_ncslgr_eaf(xml_text, include_nmm=include_nmm)):
            examples.append(Example(
                text=rec["text"].strip(), gloss=rec["gloss"].strip(),
                source="ncslgr", doc_id=doc_id, sent_idx=sent_idx,
            ))
    return examples


# ASLLRP DAI 2 export: each downloaded collection is a .zip containing xml_extract_*.xml
# (the SignStream 3 annotations), a .ssc file, and a nested video zip — we read only the XML.
# Sentence-type NON_MANUAL tiers map to the paper's four NMM labels. As with NCSLGR these mark
# the SIGNING, so the paper's Step 4 re-labels them to the English text — treat as a starting
# point / comparison, not final gold. "conditional/when" conflates true conditionals with
# temporal "when"; we keep only value == "conditional" for the `conditional` label.
ASLLRP_NMM_TIERS = {
    "yes_no_question": ("yes-no question", None),   # None = any value counts
    "wh_question": ("wh question", None),
    "conditional": ("conditional/when", "conditional"),
    "negation": ("negative", None),
}


def _dai_text(el: ET.Element | None) -> str:
    """DAI wraps tag text in single quotes (e.g. 'DISCUSS'); unwrap and strip."""
    if el is None or el.text is None:
        return ""
    return el.text.strip().strip("'").strip()


def parse_dai_xml(xml_text: str, include_nmm: bool = False) -> list[dict]:
    """Parse one ASLLRP DAI 2 `xml_extract_*.xml` into English-text / ASL-gloss sentence dicts.

    Each `<UTTERANCE>` is one sentence: `text` = `<TRANSLATION>`, `gloss` = its `<SIGN><LABEL>`
    tokens in document order (already chronological in the DAI export; safer than frame-sorting
    since many signs carry no dominant-hand frame). With `include_nmm=True`, attach `signing_nmm`
    booleans from the sentence-type NON_MANUAL tiers (see ASLLRP_NMM_TIERS — signing-based, not
    text gold). Utterances with an empty translation or no gloss are skipped.
    """
    root = _xml_fromstring(xml_text)
    out = []
    for utt in root.iter("UTTERANCE"):
        text = _dai_text(utt.find("TRANSLATION"))
        manuals = utt.find("MANUALS")
        toks = [_dai_text(s.find("LABEL")) for s in manuals.iter("SIGN")] if manuals is not None else []
        toks = [t for t in toks if t]
        if not text or not toks:
            continue
        rec = {"text": text, "gloss": " ".join(toks)}
        if include_nmm:
            present = {(_dai_text(nm.find("LABEL")), _dai_text(nm.find("VALUE")))
                       for nm in utt.iter("NON_MANUAL")}
            rec["signing_nmm"] = {
                label: any(tier == lab and (val is None or val == v) for (lab, v) in present)
                for label, (tier, val) in ASLLRP_NMM_TIERS.items()
            }
        out.append(rec)
    return out


def _dai_xml_members(path: Path):
    """Yield (collection_id, xml_text) from a DAI export: a directory of .zip/.xml, one .zip, or one .xml."""
    import zipfile

    path = Path(path)
    if path.is_dir():
        sources = sorted(path.glob("*.zip")) + sorted(path.glob("*.xml"))
    else:
        sources = [path]
    for src in sources:
        if src.suffix.lower() == ".zip":
            with zipfile.ZipFile(src) as z:
                for name in z.namelist():
                    if name.lower().endswith(".xml") and "xml_extract" in name.lower():
                        yield src.stem, z.read(name).decode("utf-8", "replace")
        elif src.suffix.lower() == ".xml":
            yield src.stem, src.read_text(encoding="utf-8", errors="replace")


def load_asllrp(path: str | Path = DATA_DAI, include_nmm: bool = False) -> list[Example]:
    """Load ASLLRP DAI 2 English–gloss pairs (real, Deaf-produced ASL) into Example objects.

    `path` is a DAI export: a directory of downloaded collection zips (default `data/dai/`), a
    single collection `.zip`, or an extracted `xml_extract_*.xml`. This is the paper's actual
    Module-1 source — its Step-1 extraction. Full faithful reproduction still needs the later
    preprocessing (clean to 1,843 pairs; the 3,915-entry Sign Bank dictionary; 80/20 split) —
    see docs/faithful_reproduction_plan.md Phase A. NEVER commit ASLLRP data (licence forbids
    redistribution); it lives under gitignored data/.
    """
    examples: list[Example] = []
    for coll_id, xml_text in _dai_xml_members(path):
        for sent_idx, rec in enumerate(parse_dai_xml(xml_text, include_nmm=include_nmm)):
            examples.append(Example(
                text=rec["text"].strip(), gloss=rec["gloss"].strip(),
                source="asllrp", doc_id=coll_id, sent_idx=sent_idx,
            ))
    if not examples:
        raise FileNotFoundError(
            f"No ASLLRP DAI utterances found under {path}. Expected collection .zip files "
            "(each with an xml_extract_*.xml) from https://dai.cs.rutgers.edu/dai/s/dai."
        )
    return examples


def save_example_pool(examples: list[Example], path: Path | None = None) -> Path:
    """Write Examples to a JSONL file (one JSON object per line); returns the path written."""
    path = path or (DATA_PROCESSED / "example_pool.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for e in examples:
            f.write(json.dumps(asdict(e)) + "\n")
    return path


def load_example_pool(path: str | Path) -> list[Example]:
    """Read a JSONL file written by `save_example_pool` back into Examples."""
    with Path(path).open() as f:
        return [Example(**json.loads(line)) for line in f if line.strip()]
