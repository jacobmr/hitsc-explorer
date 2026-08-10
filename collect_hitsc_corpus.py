#!/usr/bin/env python3
"""
collect_hitsc_corpus.py
-----------------------
Downloads full HIT Standards Committee (HITSC) meeting transcripts from the
Internet Archive Wayback Machine.

WHY THIS SCRIPT EXISTS
  ONC's original meeting pages (healthit.hhs.gov, later healthit.gov) were
  reorganized when the committee was folded into HITAC (21st Century Cures Act).
  Pre-2018 materials are now behind a gated portal (onc-hitac.com). The Wayback
  Machine still holds the original transcript PDFs at their original URLs.
  This script enumerates and pulls them.

REQUIREMENTS
  Python 3.8+, `requests`  (pip install requests)
  Run this from a normal machine/network. It will NOT work behind a proxy that
  blocks web.archive.org.

WHAT IT DOES
  1. Sweeps the Wayback CDX index for both ONC domains.
  2. Keeps only textual transcripts of full HITSC committee meetings -- not
     the HIT Policy Committee (a sibling body), and not workgroup/
     subcommittee/task-force sessions, which ONC named two different ways
     across the committee's life (see FILENAME ERAS below).
  3. Downloads the raw archived file (id_ modifier = original bytes, no IA chrome).
  4. Writes manifest.csv logging every file, its original URL, and capture date.

FILENAME ERAS
  ONC renamed these files four times in six years. The full-committee
  transcripts look like:

    2009        HITstandards_transcript_062309-1.pdf     (MMDDYY, no separators)
                standards_transcript.pdf                 (no date at all)
    2010-2012   2010-02-24_standards_transcript_draft.pdf
                2010-03-24_standards_final_transcript.pdf
                2010-05-26-standards-transcript.pdf      (hyphens)
                20100120_standards_transcript_draft.pdf  (YYYYMMDD)
                2010_10_27_standards_transcript_draft.pdf
    2011-2013   2011-11-16_HITSC_Final_Transcript.pdf    ("standards" -> "hitsc")
                2012-10-17_hitsc_transcript.pdf
    2014-2015   HITSC_Transcript_Final_2014-02-18.pdf    (date moved to the end)

  Workgroup transcripts sit a code between "standards"/"hitsc" and
  "transcript" -- ps (privacy & security), si (standards & interoperability),
  co (certification & adoption), cq (clinical quality), ct (certification
  testing), vtf (vocabulary task force), nwhin, cpe, pghd, and combinations
  ("co_vtf", "ps_nwhin"). In the 2014-2015 era ONC dropped the shared prefix
  and gave each workgroup its own acronym instead (ASA_, CSWG_, ICTWG_,
  ISATF_, APISWG_, CQWG_, DPROVTF_), so those never match on "standards" or
  "hitsc" at all.

TUNING
  - --start / --end (YYYY-MM-DD) restrict to meeting dates parsed out of each
    filename. Files where no date could be parsed are kept regardless.
  - Widen/narrow MAIN_COMMITTEE_TRANSCRIPT if you find the filter misses or
    over-collects.
"""

import argparse, csv, os, re, sys, time, json
from datetime import date
import requests

OUTDIR = "hitsc_corpus"
SLEEP = 0.5                          # be polite to archive.org
CDX = "http://web.archive.org/cdx/search/cdx"
DRY_RUN = False                       # True: only write candidates.csv, no downloads

DOMAINS = ["healthit.hhs.gov", "healthit.gov"]

# Matches "standards_transcript", "standards_transcript_final",
# "standards_final_transcript", "HITstandards_transcript", "hitsc_transcript",
# "HITSC_Final_Transcript", "HITSC_Transcript_Draft_2015-03-18", etc -- i.e.
# full committee transcripts (naming shifted from "standards_..." to
# "hitsc_..." around 2011-2012) -- but NOT "standards_ps_transcript",
# "standards_si_transcript", "hitsc_cqwg_transcript", etc, where a workgroup
# code sits between "standards"/"hitsc" and "transcript".
#
# Applied to the BASENAME only: many of these live under portal paths that
# themselves contain "standards", which would otherwise pull in every
# workgroup file stored beside them.
MAIN_COMMITTEE_TRANSCRIPT = re.compile(
    r"(?:hit)?(?:standards|hitsc)(?:[-_]?(?:committee|final|faca|draft))*[-_]?transcript"
)

# Workgroup/subcommittee/hearing codes seen tacked on as a *suffix* right
# after "transcript" -- MAIN_COMMITTEE_TRANSCRIPT alone doesn't catch these
# since the code comes after, not between, "standards"/"hitsc" and
# "transcript".
WORKGROUP_SUFFIX = re.compile(
    r"transcript[-_](mu|qum|ie|ca|pg|sp|psp|ps|si|co|cq|ct|vtf|erx|sig|pm|"
    r"nwhin|nhin|ac|hie|cpe|pghd|tiger|hearing|session)\b"
)

FILETYPES = (".pdf", ".txt", ".doc", ".docx")   # no .mp3: text transcripts only

def cdx_query(domain, ext):
    """Return list of (original_url, timestamp, mimetype) for a domain, restricted
    to one file extension so we don't have to pull (and filter client-side) the
    entire site index in one shot."""
    params = {
        "url": domain,
        "matchType": "domain",
        "collapse": "digest",       # drop identical re-captures (of the same URL)
        "fl": "original,timestamp,mimetype,statuscode,digest",
        "filter": [f"original:.*\\{ext}$", "statuscode:200"],
        "output": "json",
        "limit": "200000",
    }
    for attempt in range(3):
        try:
            r = requests.get(CDX, params=params, timeout=180)
            r.raise_for_status()
            rows = r.json()
            break
        except (requests.exceptions.RequestException, json.JSONDecodeError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    if not rows:
        return []
    header = rows[0]
    return [dict(zip(header, row)) for row in rows[1:]]

def parse_meeting_date(url):
    """Best-effort extraction of the meeting date embedded in the filename
    (e.g. "2012-02-29_standards_transcript_final.pdf",
    "20100120_standards_transcript_draft.pdf",
    "HITSC_Transcript_Final_2014-02-18.pdf", or the 2009-era MMDDYY
    "HITstandards_transcript_062309-1.pdf"). Returns None if no date could be
    parsed -- "standards_transcript.pdf" carries none at all, and is dated
    from the text inside it at build time."""
    base = url.split("/")[-1]
    m = re.search(r"(\d{4})[-_](\d{2})[-_](\d{2})", base)
    if not m:
        m = re.search(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)", base)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass
    # 2009-era MMDDYY: "..._062309-1.pdf" -> 2009-06-23
    m = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", base)
    if m:
        mo, dy, yr = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= dy <= 31 and 9 <= yr <= 17:
            try:
                return date(2000 + yr, mo, dy)
            except ValueError:
                pass
    return None

def wanted(url, start=None, end=None):
    u = url.lower()
    if not u.endswith(FILETYPES):
        return False
    base = u.split("/")[-1]
    if not MAIN_COMMITTEE_TRANSCRIPT.search(base):
        return False
    if WORKGROUP_SUFFIX.search(base):
        return False
    if start or end:
        d = parse_meeting_date(url)
        if d is not None:
            if start and d < start:
                return False
            if end and d > end:
                return False
    return True

def safe_name(url, ts):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", url.split("/")[-1]) or "file"
    return f"{ts[:8]}__{base}"

def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=date.fromisoformat, default=None,
                    help="only keep meetings on/after this date (YYYY-MM-DD)")
    p.add_argument("--end", type=date.fromisoformat, default=None,
                    help="only keep meetings on/before this date (YYYY-MM-DD)")
    return p.parse_args()

def main(start=None, end=None):
    os.makedirs(OUTDIR, exist_ok=True)
    # One entry per content digest: many different portal redirect URLs serve the
    # same underlying document, and Wayback archives each URL separately, so
    # dedup on content (digest) rather than on URL to get one file per document.
    by_digest = {}
    for dom in DOMAINS:
        for ext in FILETYPES:
            print(f"[CDX] sweeping {dom} ({ext}) ...", file=sys.stderr)
            try:
                caps = cdx_query(dom, ext)
            except Exception as e:
                print(f"  ! CDX failed for {dom} {ext}: {e}", file=sys.stderr)
                continue
            print(f"  {len(caps)} captures returned", file=sys.stderr)
            for c in caps:
                url, ts, digest = c["original"], c["timestamp"], c["digest"]
                if not wanted(url, start, end):
                    continue
                existing = by_digest.get(digest)
                if existing is None or ts < existing[1]:
                    by_digest[digest] = (url, ts, c.get("mimetype", ""))
            time.sleep(SLEEP)

    candidates = list(by_digest.values())

    if DRY_RUN:
        with open(os.path.join(OUTDIR, "candidates.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["original_url", "capture_timestamp", "mimetype"])
            w.writerows(sorted(candidates, key=lambda t: t[1]))
        print(f"\nDRY RUN. {len(candidates)} candidates -> {OUTDIR}/candidates.csv "
              f"(set DRY_RUN = False to download)", file=sys.stderr)
        return

    manifest = []
    for url, ts, _ in candidates:
        # HTTPS, not HTTP: archive.org refuses port 80 once it decides you have
        # been asking for a while, which shows up as a wave of ECONNREFUSED
        # partway through an otherwise healthy run.
        raw = f"https://web.archive.org/web/{ts}id_/{url}"
        out = os.path.join(OUTDIR, safe_name(url, ts))
        if os.path.exists(out):
            manifest.append([ts, url, out, os.path.getsize(out)])
            continue
        for attempt in range(5):
            try:
                resp = requests.get(raw, timeout=120)
                if resp.status_code == 200 and resp.content:
                    with open(out, "wb") as f:
                        f.write(resp.content)
                    manifest.append([ts, url, out, len(resp.content)])
                    print(f"  saved {out} ({len(resp.content)} bytes)", file=sys.stderr)
                    break
                if resp.status_code in (429, 503, 504):
                    time.sleep(5 * (attempt + 1))
                    continue
                break                      # 404 etc: no point retrying
            except Exception as e:
                if attempt == 4:
                    print(f"  ! download failed {url}: {e}", file=sys.stderr)
                else:
                    time.sleep(5 * (attempt + 1))   # exponential-ish backoff
        time.sleep(SLEEP)

    with open(os.path.join(OUTDIR, "manifest.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["capture_timestamp", "original_url", "local_path", "bytes"])
        w.writerows(manifest)
    print(f"\nDone. {len(manifest)} files -> {OUTDIR}/  (see manifest.csv)", file=sys.stderr)

if __name__ == "__main__":
    args = parse_args()
    main(start=args.start, end=args.end)
