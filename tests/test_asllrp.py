"""Parser tests for the ASLLRP DAI 2 loader (no network/zip — a synthetic XML fixture)."""
from aslgloss.data import parse_dai_xml

# Minimal DAI 2 xml_extract: two utterances (one wh-question + negation, one plain), and a third
# with an empty translation that must be skipped. Values are single-quoted as in real exports.
DAI = """<?xml version='1.0' encoding='utf-8'?>
<SIGNSTREAM_DAI>
  <COLLECTIONS><COLLECTION ID='1' NAME='Test'>
    <TEMPORAL-PARTITIONS><TEMPORAL-PARTITION><SEGMENT-TIERS><SEGMENT-TIER>
      <UTTERANCES>
        <UTTERANCE ID='1' START_FRAME='0' END_FRAME='9'>
          <TRANSLATION>'Why did no one leave?'</TRANSLATION>
          <MANUALS>
            <SIGN ID='1'><LABEL>'WHY'</LABEL><SIGN_TYPE>'Lexical Signs'</SIGN_TYPE></SIGN>
            <SIGN ID='2'><LABEL>'NONE'</LABEL><SIGN_TYPE>'Lexical Signs'</SIGN_TYPE></SIGN>
            <SIGN ID='3'><LABEL>'LEAVE'</LABEL><SIGN_TYPE>'Lexical Signs'</SIGN_TYPE></SIGN>
          </MANUALS>
          <NON_MANUALS>
            <NON_MANUAL ID='9'><LABEL>'wh question'</LABEL><VALUE>'whq'</VALUE></NON_MANUAL>
            <NON_MANUAL ID='10'><LABEL>'negative'</LABEL><VALUE>'negation'</VALUE></NON_MANUAL>
            <NON_MANUAL ID='11'><LABEL>'conditional/when'</LABEL><VALUE>'when'</VALUE></NON_MANUAL>
          </NON_MANUALS>
        </UTTERANCE>
        <UTTERANCE ID='2'>
          <TRANSLATION>'I saw it.'</TRANSLATION>
          <MANUALS>
            <SIGN ID='4'><LABEL>'IX-1p'</LABEL><SIGN_TYPE>'Lexical Signs'</SIGN_TYPE></SIGN>
            <SIGN ID='5'><LABEL>'SEE'</LABEL><SIGN_TYPE>'Lexical Signs'</SIGN_TYPE></SIGN>
          </MANUALS>
          <NON_MANUALS/>
        </UTTERANCE>
        <UTTERANCE ID='3'>
          <TRANSLATION>''</TRANSLATION>
          <MANUALS><SIGN ID='6'><LABEL>'X'</LABEL></SIGN></MANUALS>
        </UTTERANCE>
      </UTTERANCES>
    </SEGMENT-TIER></SEGMENT-TIERS></TEMPORAL-PARTITION></TEMPORAL-PARTITIONS>
  </COLLECTION></COLLECTIONS>
</SIGNSTREAM_DAI>
"""


def test_parse_utterances_text_and_gloss():
    recs = parse_dai_xml(DAI)
    # The empty-translation utterance is dropped; document order preserved; quotes stripped.
    assert len(recs) == 2
    assert recs[0] == {"text": "Why did no one leave?", "gloss": "WHY NONE LEAVE"}
    assert recs[1] == {"text": "I saw it.", "gloss": "IX-1p SEE"}


def test_signing_nmm_mapping():
    recs = parse_dai_xml(DAI, include_nmm=True)
    nmm = recs[0]["signing_nmm"]
    assert nmm["wh_question"] is True
    assert nmm["negation"] is True
    # "conditional/when" with value "when" (temporal) must NOT count as conditional.
    assert nmm["conditional"] is False
    assert nmm["yes_no_question"] is False
    # Second utterance has no sentence-type tiers -> all False.
    assert recs[1]["signing_nmm"] == {
        "yes_no_question": False, "wh_question": False, "conditional": False, "negation": False,
    }
