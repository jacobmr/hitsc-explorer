"""Keyword-family topic definitions. Each family is a list of compiled
regexes; an utterance is tagged with the family if any regex matches.

Case matters for acronyms (HIE, MU, HL7) to avoid false hits on ordinary
words; phrases match case-insensitively.

These families are tuned to the HIT *Standards* Committee, whose remit was
the technical layer — vocabularies, content and transport standards, testing
and certification criteria — rather than the policy questions its sibling
HITPC handled. The overlapping families (nhin, hie, direct, meaningful_use,
privacy_security, interoperability) are kept so the two corpora stay
comparable.
"""

import re


def _ci(p):
    return re.compile(p, re.I)


def _cs(p):
    return re.compile(p)


TOPICS = {
    # --- shared with the HITPC corpus, for cross-committee comparison ---
    "nhin": [
        _cs(r"\bNH?w?IN\b"),          # NHIN / NwIN typo forms
        _cs(r"\bNwHIN\b"),
        _ci(r"nationwide health information network"),
        _ci(r"national health information network"),
        _cs(r"\bCONNECT\b"),          # federal NHIN CONNECT software
        _ci(r"\bexchange program\b"),
    ],
    "hie": [
        _cs(r"\bHIEs?\b"),
        _ci(r"health information exchange"),
        _ci(r"\bRHIOs?\b"),
        _ci(r"regional health information organi[sz]ation"),
    ],
    "direct": [
        _ci(r"\bdirect project\b"),
        _ci(r"\bNH?w?IN direct\b"),
        _ci(r"\bdirect (protocol|messag\w+|exchange|address\w*)\b"),
        _cs(r"\bXDR\b"), _cs(r"\bXDM\b"),
        _ci(r"\bS/?MIME\b"),
    ],
    "interoperability": [
        _ci(r"interoperab"),
    ],
    "meaningful_use": [
        _ci(r"meaningful use"),
        _cs(r"\bMU\b"), _cs(r"\bMU-?[123]\b"),
        _ci(r"stage (one|two|three|1|2|3)\b"),
    ],
    "privacy_security": [
        _ci(r"\bprivacy\b"),
        _ci(r"\bsecurity\b"),
        _ci(r"tiger team"),
        _ci(r"\bHIPAA\b"),
        _ci(r"\bconsent\b"),
    ],
    "info_blocking": [
        _ci(r"information blocking"),
        _ci(r"data blocking"),
        _ci(r"data hoarding"),
    ],

    # --- the standards committee's own subject matter ---
    "vocabulary": [
        _cs(r"\bSNOMED(?:[ -]CT)?\b"),
        _cs(r"\bLOINC\b"),
        _cs(r"\bRxNorm\b"),
        _cs(r"\bICD-?(9|10|11)\b"),
        _cs(r"\bCPT\b"), _cs(r"\bNDC\b"), _cs(r"\bUCUM\b"), _cs(r"\bUMLS\b"),
        _ci(r"\bvocabular\w+"),
        _ci(r"\bterminolog\w+"),
        _ci(r"\bcode sets?\b"),
        _ci(r"value sets?"),
    ],
    "content_standards": [
        _cs(r"\bHL7\b"),
        _cs(r"\bCCDA?\b"), _cs(r"\bC-CDA\b"), _cs(r"\bCDA\b"),
        _cs(r"\bCCR\b"), _cs(r"\bCCOW\b"),
        _cs(r"\bQRDA\b"), _cs(r"\bX12\b"), _cs(r"\bNCPDP\b"),
        _cs(r"\bDICOM\b"),
        _ci(r"consolidated cda"),
        _ci(r"continuity of care (document|record)"),
        _ci(r"\btemplates?\b.{0,20}\bCDA\b"),
    ],
    "fhir_api": [
        _ci(r"\bFHIR\b"),
        _cs(r"\bAPIs?\b"),
        _ci(r"application programming interface"),
        _ci(r"\bRESTful?\b"),
        _cs(r"\bOAuth\b"), _cs(r"\bOpenID\b"),
        _ci(r"\bSMART\b.{0,15}\b(on FHIR|platform|app)"),
        _ci(r"\bargonaut\b"),
    ],
    "transport": [
        _cs(r"\bSOAP\b"), _cs(r"\bSMTP\b"), _cs(r"\bREST\b"),
        _cs(r"\bTLS\b"), _cs(r"\bSSL\b"),
        _cs(r"\bIHE\b"),
        _cs(r"\bXCA\b"), _cs(r"\bXCPD\b"), _cs(r"\bPIX\b"), _cs(r"\bPDQ\b"),
        _ci(r"transport standard"),
        _ci(r"\bpush (and|or|vs\.?) pull\b"),
    ],
    "testing_certification": [
        _ci(r"certif"),
        _ci(r"\bCCHIT\b"),
        _cs(r"\bNIST\b"),
        _ci(r"test (tool|script|procedure|harness|case|method|bed)"),
        _ci(r"\bATLs?\b"), _ci(r"\bACBs?\b"),
        _ci(r"authorized (testing|certification) bod"),
        _ci(r"certification criteri"),
        _ci(r"\bconformance\b"),
        _ci(r"\bvalidat(?:or|ion) tool\b"),
    ],
    "standards_process": [
        _ci(r"\bSDOs?\b"),
        _ci(r"standards development organi[sz]ation"),
        _cs(r"\bANSI\b"), _cs(r"\bISO\b"), _cs(r"\bW3C\b"), _cs(r"\bIETF\b"),
        _ci(r"\bS&I framework\b"), _ci(r"standards (and|&) interoperability framework"),
        _ci(r"\bballot(?:ing|ed)?\b"),
        _ci(r"implementation guide"),
        _ci(r"\bharmoni[sz]ation\b"),
        _ci(r"standards advisory"),
        _ci(r"\bISA\b"),
    ],
    "maturity_adoption": [
        _ci(r"standards? (maturity|readiness)"),
        _ci(r"maturity (model|matrix|criteria|level)"),
        _ci(r"\bpilot(?:s|ed|ing)?\b"),
        _ci(r"real[- ]world (use|testing|deployment)"),
        _ci(r"\bemerging standard"),
    ],
    "quality_measures": [
        _ci(r"quality measur"),
        _ci(r"clinical quality"),
        _cs(r"\beCQMs?\b"), _cs(r"\bCQMs?\b"),
        _cs(r"\bQDM\b"), _cs(r"\bHQMF\b"),
    ],
    "patient_matching": [
        _ci(r"patient (matching|identit|identifier)"),
        _ci(r"\bmaster patient index\b"), _cs(r"\bMPI\b"),
        _ci(r"record local[iz]?ation"),
        _ci(r"unique (patient )?identifier"),
    ],
    "provenance_segmentation": [
        _ci(r"\bprovenance\b"),
        _ci(r"data segmentation"),
        _cs(r"\bDS4P\b"),
        _ci(r"\bmetadata\b"),
        _ci(r"\bdigital signature"),
    ],
    "usability_safety": [
        _ci(r"\busabilit\w+"),
        _ci(r"patient safety"),
        _ci(r"\bhuman factors\b"),
        _ci(r"\bsafety[- ]enhanced design\b"),
    ],
    "patient_engagement": [
        _ci(r"patient engagement"),
        _ci(r"patient access"),
        _ci(r"blue button"),
        _ci(r"view,? download,? (and |& )?transmit"),
        _cs(r"\bVDT\b"),
        _ci(r"patient portal"),
        _cs(r"\bPHRs?\b"),
        _ci(r"personal health record"),
        _ci(r"patient[- ]generated (health )?data"), _cs(r"\bPGHD\b"),
    ],
    "eprescribing": [
        _ci(r"e-?prescrib"),
        _cs(r"\bEPCS\b"),
        _ci(r"\bformulary\b"),
        _ci(r"\bmedication reconciliation\b"),
        _ci(r"\bSurescripts\b"),
    ],
    "public_health": [
        _ci(r"public health (reporting|agenc|department|surveillance)"),
        _ci(r"immuni[sz]ation registr"),
        _ci(r"syndromic surveillance"),
        _ci(r"\breportable lab"),
        _cs(r"\bELR\b"), _cs(r"\bIIS\b"),
    ],
    # Companies named aloud in the transcripts, listed in descending order of
    # how often they actually appear in this corpus. The list is derived from
    # the corpus rather than assumed: HITSC was a standards body, and the
    # vendors it argued about are not the ones the policy committee did.
    # Surescripts (62), Cerner (56), Google (36) and Microsoft (27) all lead
    # Epic (16) here. Names that never appear are left out.
    "vendor_mention": [
        _ci(r"\bSurescripts\b"),
        _ci(r"\bCerner\b"),
        _cs(r"\bGoogle\b"),
        _cs(r"\bMicrosoft\b"), _ci(r"\bHealthVault\b"),
        _ci(r"\bathenahealth\b"),
        _cs(r"\bEpic\b"), _cs(r"\bEPIC\b"),
        _ci(r"CommonWell"),
        _ci(r"\bCovisint\b"),
        _cs(r"\bApple\b"),
        _ci(r"first ?databank"),
        _ci(r"\bSiemens\b"),
        _cs(r"\bIBM\b"),
        _ci(r"\bRelayHealth\b"),
        _ci(r"\bAllscripts\b"),
        _ci(r"\bMcKesson\b"),
        _ci(r"\bAxolotl\b"),
        _ci(r"eClinicalWorks"),
        _cs(r"\bOracle\b"),
        _ci(r"\bGE Healthcare\b"),
        _ci(r"intelligent medical objects"),
        _ci(r"\bMeditech\b"),
        _ci(r"\bCentricity\b"),
        _ci(r"\bgreenway\b"),
        _ci(r"\bLabCorp\b"),
        _ci(r"\bOptum\b"),
        _ci(r"\bMultum\b"),
    ],
}


def tag(text):
    """Return set of topic keys matching this text."""
    found = set()
    for topic, patterns in TOPICS.items():
        for rx in patterns:
            if rx.search(text):
                found.add(topic)
                break
    return found
