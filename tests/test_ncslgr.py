"""Parser tests for the NCSLGR real-ASL loader (no network — a synthetic EAF fixture)."""
from aslgloss.data import parse_ncslgr_eaf

# Minimal ELAN/EAF: two English sentences; gloss tokens whose spans fall inside each; a
# `negative` NMM tier overlapping only the second sentence; a third English span with no gloss.
EAF = """<?xml version="1.0" encoding="UTF-8"?>
<ANNOTATION_DOCUMENT>
  <TIME_ORDER>
    <TIME_SLOT TIME_SLOT_ID="ts1" TIME_VALUE="0"/>
    <TIME_SLOT TIME_SLOT_ID="ts2" TIME_VALUE="100"/>
    <TIME_SLOT TIME_SLOT_ID="ts3" TIME_VALUE="200"/>
    <TIME_SLOT TIME_SLOT_ID="ts4" TIME_VALUE="300"/>
    <TIME_SLOT TIME_SLOT_ID="ts5" TIME_VALUE="400"/>
    <TIME_SLOT TIME_SLOT_ID="ts6" TIME_VALUE="500"/>
  </TIME_ORDER>
  <TIER TIER_ID="English translation">
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts1" TIME_SLOT_REF2="ts3">
      <ANNOTATION_VALUE>I saw it.</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts3" TIME_SLOT_REF2="ts5">
      <ANNOTATION_VALUE>I have no pets.</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts5" TIME_SLOT_REF2="ts6">
      <ANNOTATION_VALUE>Silent sentence.</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
  </TIER>
  <TIER TIER_ID="main gloss">
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts1" TIME_SLOT_REF2="ts2">
      <ANNOTATION_VALUE>IX-1p</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts2" TIME_SLOT_REF2="ts3">
      <ANNOTATION_VALUE>SEE</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts3" TIME_SLOT_REF2="ts4">
      <ANNOTATION_VALUE>fs-PET</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts4" TIME_SLOT_REF2="ts5">
      <ANNOTATION_VALUE>NONE</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
  </TIER>
  <TIER TIER_ID="negative">
    <ANNOTATION><ALIGNABLE_ANNOTATION TIME_SLOT_REF1="ts3" TIME_SLOT_REF2="ts5">
      <ANNOTATION_VALUE>neg</ANNOTATION_VALUE></ALIGNABLE_ANNOTATION></ANNOTATION>
  </TIER>
</ANNOTATION_DOCUMENT>
"""


def test_parse_pairs_and_span_containment():
    recs = parse_ncslgr_eaf(EAF)
    # The third English span has no gloss tokens inside it -> dropped.
    assert len(recs) == 2
    assert recs[0] == {"text": "I saw it.", "gloss": "IX-1p SEE"}
    assert recs[1] == {"text": "I have no pets.", "gloss": "fs-PET NONE"}


def test_signing_nmm_tier_overlap():
    recs = parse_ncslgr_eaf(EAF, include_nmm=True)
    # `negative` tier overlaps only the second sentence's span.
    assert recs[0]["signing_nmm"]["negation"] is False
    assert recs[1]["signing_nmm"]["negation"] is True
    # Tiers absent from the file default to False, not a KeyError.
    assert recs[0]["signing_nmm"]["wh_question"] is False
