"""Normalize raw speaker headers into canonical people and organizations.

Raw headers vary per era and transcription vendor:
    "John Halamka – Harvard Medical School – Chief Information Officer"
    "John Halamka, MD, MS – CIO – Beth Israel Deaconess Medical Center"
    "John Halamka, BIDMC"
    "Dr. John Halamka"
"""

import re

from .parse import DASH_SPLIT

HONORIFICS = re.compile(r"^(Dr|Mr|Ms|Mrs|Prof)\.?\s+", re.I)

CREDENTIALS = {
    "md", "phd", "ph.d", "ph.d.", "mph", "mba", "jd", "rn", "ms", "ma", "msc",
    "scm", "mhs", "mpa", "facp", "fache", "faap", "facmi", "abfp", "faafp",
    "cphims", "pmp", "llm", "rn-bc", "msn", "bsn", "md(hon)", "np", "pa",
    "esq", "cpa", "mssw", "mhsa", "dr", "iii", "jr", "sr", "unac/uhcp",
}

# Explicit person aliases: transcription typos and nickname variants that the
# automatic (last name + first-name prefix) merge can't catch.
NAME_ALIASES = {
    # Transcription spellings of HITSC regulars.
    "john halumka": "John Halamka",
    "john halamke": "John Halamka",
    "dixie backer": "Dixie Baker",
    # NB: alias values skip NICKNAMES expansion, so they must be given in the
    # already-expanded form ("Wesley", not "Wes") or the alias and the plain
    # spelling key to two different people.
    "wes rischel": "Wesley Rishel",
    "arian malec": "Arien Malec",
    "aryan malec": "Arien Malec",
    "orien malec": "Arien Malec",
    "doug fridsman": "Douglas Fridsma",
    "douglas fridsman": "Douglas Fridsma",
    "david mccalley": "David McCallie",
    "david mccallie jr": "David McCallie",
    # Ross, Ferguson, Overhage, Elmore and Coleman each appear under two
    # spellings in the corpus and would otherwise split into two people.
    # ("Ron Ross" and "Clarke Ross" are different men and stay separate.)
    "kris ross": "Cris Ross",
    "chris ross": "Cris Ross",          # not the Christopher nickname
    "christopher ross": "Cris Ross",
    "becky kush": "Rebecca Kush",
    "jamie ferguson": "James Ferguson",
    "jaime ferguson": "James Ferguson",
    "mark overhage": "Marc Overhage",
    "j marc overhage": "Marc Overhage",
    "johnathan coleman": "Jonathan Coleman",
    "farzad mostashari": "Farzad Mostashari",
    "fazad mostashari": "Farzad Mostashari",
    "michelle consolazio nelson": "Michelle Consolazio",  # married name mid-tenure
    "terry cullen": "Theresa Cullen",
    "andy wiesenthal": "Andrew Wiesenthal",
    "unidentified speaker": "(unidentified)",
    "unidentified male": "(unidentified)",
    "unidentified female": "(unidentified)",
    "unidentified participant": "(unidentified)",
}

NICKNAMES = {
    "judy": "judith", "mike": "michael", "bob": "robert", "rob": "robert",
    "bill": "william", "dave": "david", "tom": "thomas", "dick": "richard",
    "rick": "richard", "jim": "james", "joe": "joseph", "chris": "christopher",
    "chuck": "charles", "ted": "theodore", "tony": "anthony", "liz": "elizabeth",
    "beth": "elizabeth", "kathy": "katherine", "kate": "katherine",
    "deb": "deborah", "debbie": "deborah", "steve": "steven", "greg": "gregory",
    "doug": "douglas", "dan": "daniel", "matt": "matthew", "pat": "patricia",
    "stan": "stanley", "wes": "wesley", "jamie": "james", "becky": "rebecca",
    "andy": "andrew", "ken": "kenneth", "jon": "jonathan", "rich": "richard",
}

# Organization canonicalization: first regex that matches wins.
ORG_RULES = [
    (re.compile(r"\bepic\b", re.I), "Epic"),
    (re.compile(r"\bcerner\b", re.I), "Cerner"),
    # HITSC leadership and long-serving members.
    (re.compile(r"beth israel|\bbidmc\b", re.I), "Beth Israel Deaconess"),
    (re.compile(r"harvard", re.I), "Harvard"),
    (re.compile(r"\bhca\b|hospital corporation of america", re.I), "HCA"),
    (re.compile(r"\bsaic\b|science applications", re.I), "SAIC"),
    (re.compile(r"martin,? blanck", re.I), "Martin, Blanck & Associates"),
    (re.compile(r"\bgartner\b", re.I), "Gartner"),
    (re.compile(r"relayhealth", re.I), "RelayHealth"),
    (re.compile(r"\bmayo\b", re.I), "Mayo Clinic"),
    (re.compile(r"regenstrief", re.I), "Regenstrief Institute"),
    (re.compile(r"\bsiemens\b", re.I), "Siemens"),
    (re.compile(r"\btenet\b", re.I), "Tenet Healthcare"),
    (re.compile(r"blue ?cross|bcbs", re.I), "BlueCross BlueShield"),
    (re.compile(r"surescripts", re.I), "Surescripts"),
    (re.compile(r"deloitte", re.I), "Deloitte"),
    (re.compile(r"genetic alliance", re.I), "Genetic Alliance"),
    (re.compile(r"\bcdisc\b", re.I), "CDISC"),
    (re.compile(r"aurora health", re.I), "Aurora Health Care"),
    (re.compile(r"\bpremier\b", re.I), "Premier Inc."),
    (re.compile(r"golden living", re.I), "Golden Living"),
    (re.compile(r"\bhimss\b", re.I), "HIMSS"),
    (re.compile(r"intelligent medical objects|\bimo\b", re.I),
     "Intelligent Medical Objects"),
    (re.compile(r"healthwise", re.I), "Healthwise"),
    (re.compile(r"geisinger", re.I), "Geisinger"),
    (re.compile(r"healthbridge", re.I), "HealthBridge"),
    (re.compile(r"\bhl7\b|health level ?seven", re.I), "HL7"),
    (re.compile(r"\bnist\b|national institute of standards", re.I), "NIST"),
    (re.compile(r"\bdo[dD]\b|department of defense|military health", re.I), "DoD"),
    (re.compile(r"indian health service|\bihs\b", re.I), "IHS"),
    # ONC appears under many labels: the office, its sub-offices, and the
    # National Coordinator post itself (Blumenthal/Mostashari/DeSalvo).
    (re.compile(r"office of the national coordinator|\bonc\b"
                r"|national coordinator"
                r"|office of (policy|planning|the chief privacy)"
                r"|federal advisory committee program"
                r"|^office of the\b", re.I), "ONC"),
    # CMS's Office of E-Health Standards & Services ran the incentive program.
    (re.compile(r"centers for medicare|\bcms\b|office of e-?health", re.I), "CMS"),
    (re.compile(r"department of hhs|health (and|&) human services|\bhhs\b", re.I), "HHS"),
    (re.compile(r"veterans (affairs|administration)|\bva\b(?!\w)", re.I), "VA"),
    (re.compile(r"centers for disease|\bcdc\b", re.I), "CDC"),
    (re.compile(r"social security", re.I), "SSA"),
    (re.compile(r"center for democracy", re.I), "Center for Democracy & Technology"),
    (re.compile(r"national partnership", re.I), "National Partnership for Women & Families"),
    (re.compile(r"intermountain", re.I), "Intermountain Healthcare"),
    (re.compile(r"kindred", re.I), "Kindred Healthcare"),
    (re.compile(r"brigham|partners healthcare", re.I), "Brigham & Women's / Partners"),
    (re.compile(r"massachusetts ehealth", re.I), "Massachusetts eHealth Collaborative"),
    (re.compile(r"markle", re.I), "Markle Foundation"),
    (re.compile(r"kaiser", re.I), "Kaiser Permanente"),
    (re.compile(r"aetna", re.I), "Aetna"),
    (re.compile(r"wellpoint", re.I), "WellPoint"),
    (re.compile(r"intel\b", re.I), "Intel"),
    (re.compile(r"microsoft", re.I), "Microsoft"),
    (re.compile(r"\boracle\b", re.I), "Oracle"),
    (re.compile(r"\bibm\b", re.I), "IBM"),
    (re.compile(r"university of minnesota", re.I), "University of Minnesota"),
    (re.compile(r"johns hopkins|bloomberg school", re.I), "Johns Hopkins"),
    (re.compile(r"vanderbilt", re.I), "Vanderbilt"),
    (re.compile(r"\bmitre\b", re.I), "MITRE"),
    (re.compile(r"american medical association|\bama\b", re.I),
     "American Medical Association"),
    (re.compile(r"american hospital association|\baha\b", re.I),
     "American Hospital Association"),
    (re.compile(r"national cancer|\bnci\b", re.I), "NCI"),
    (re.compile(r"national library of medicine|\bnlm\b", re.I),
     "National Library of Medicine"),
    (re.compile(r"altarum", re.I), "Altarum"),
    (re.compile(r"national quality|\bnqf\b", re.I), "National Quality Forum"),
]

TITLE_WORDS = {
    "director", "officer", "president", "vp", "vice", "chief", "chair",
    "chairman", "dean", "advisor", "adviser", "founder", "ceo", "cio", "cmio",
    "coo", "cto", "lead", "professor", "manager", "consultant", "architect",
    "internist", "physician", "entrepreneur", "businessman", "senior",
    "executive", "fellow", "analyst", "specialist", "liaison", "cofounder",
    "co-founder", "representative", "legislator", "partner", "principal",
}


def _clean_name(name):
    name = HONORIFICS.sub("", name.strip())
    # Drop credential tokens after commas: "Paul Tang, MD, MS" -> "Paul Tang"
    parts = [p.strip() for p in name.split(",")]
    kept = [parts[0]]
    for p in parts[1:]:
        if p.lower().replace(".", "") not in {c.replace(".", "") for c in CREDENTIALS}:
            kept.append(p)
    name = kept[0]
    # Strip stray middle-initial-only periods and collapse space
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _title_score(seg):
    words = re.split(r"[\s,&/]+", seg.lower())
    return sum(1 for w in words if w in TITLE_WORDS)


def normalize_org(seg):
    for rx, canon in ORG_RULES:
        if rx.search(seg):
            return canon
    return re.sub(r"\s+", " ", seg).strip(" .")


def split_header(raw):
    """raw header -> (clean person name, org_guess or None)."""
    raw = raw.strip()
    segs = [s.strip(" .") for s in DASH_SPLIT.split(raw) if s.strip(" .")]
    if len(segs) >= 2:
        name = _clean_name(segs[0])
        rest = segs[1:]
        # Headers carry name/title/org in no fixed order and sometimes list
        # several. Prefer a segment naming an organization we recognize;
        # otherwise fall back to whichever reads least like a job title.
        for seg in rest:
            if any(rx.search(seg) for rx, _canon in ORG_RULES):
                return name, seg
        return name, sorted(rest, key=_title_score)[0]
    # Comma style: "Judy Sparrow, ONC"
    if "," in raw:
        name_part, org_part = raw.split(",", 1)
        cleaned = _clean_name(name_part)
        org = org_part.strip()
        if org.lower().replace(".", "") in {c.replace(".", "") for c in CREDENTIALS}:
            org = None
        return cleaned, org
    return _clean_name(raw), None


class SpeakerRegistry:
    """Accumulates raw headers, resolves canonical people."""

    def __init__(self):
        self.people = {}   # key -> dict(name, orgs Counter)

    @staticmethod
    def _key_for(name):
        low = re.sub(r"\s+", " ", name.lower().replace(".", "")).strip()
        if low in NAME_ALIASES:
            return NAME_ALIASES[low].lower()
        toks = low.split()
        # Drop a leading initial so "J. Marc Overhage" keys the same as
        # "Marc Overhage" (people appear both ways across transcripts).
        if len(toks) > 2 and len(toks[0].rstrip(".")) == 1:
            toks = toks[1:]
        if len(toks) >= 2:
            first, last = toks[0], toks[-1]
            first = NICKNAMES.get(first, first)
            return f"{first} {last}"
        return low

    @staticmethod
    def _usable_org(org):
        """Reject fragments left behind when a long org name wrapped onto the
        next line ("Office of the", "National") so a complete variant wins."""
        if not org or len(org) < 3:
            return False
        toks = org.split()
        if toks[-1].lower() in {"of", "the", "for", "and", "&", "in", "on", "at", "to"}:
            return False
        return not (len(toks) == 1 and toks[0].lower() in
                    {"national", "office", "center", "department", "university"})

    def observe(self, raw_header):
        from collections import Counter
        name, org = split_header(raw_header)
        key = self._key_for(name)
        rec = self.people.setdefault(key, {"names": Counter(), "orgs": Counter()})
        rec["names"][name] += 1
        if org:
            canon = normalize_org(org)
            if self._usable_org(canon):
                rec["orgs"][canon] += 1
        return key

    def resolve(self):
        """key -> (canonical display name, canonical org, is_gov_staff).

        is_gov_staff marks ONC/HHS/CMS program staff and contractors — the
        officials who ran the incentive program and briefed the committee —
        as distinct from its appointed members. Federal *members* (e.g. VHA,
        CDC) are not staff and stay unflagged.
        """
        out = {}
        low_key_alias = {v.lower(): v for v in NAME_ALIASES.values()}
        for key, rec in self.people.items():
            if key in low_key_alias:
                display = low_key_alias[key]
            else:
                display = rec["names"].most_common(1)[0][0]
            # Line-wrapping in the source PDFs truncates long org names, so a
            # speaker can accumulate both a recognized org and a fragment of a
            # job title. Prefer a canonical organization over an unrecognized
            # string, then fall back to the most frequent.
            known = {canon for _rx, canon in ORG_RULES}
            org = max(rec["orgs"].items(),
                      key=lambda kv: (kv[0] in known, kv[1]))[0] if rec["orgs"] else ""
            is_staff = org in ("ONC", "HHS", "CMS", "Altarum")
            out[key] = (display, org, is_staff)
        return out
