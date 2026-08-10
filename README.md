# HITSC Transcript Explorer

Interactive explorer for the meeting transcripts of the **HIT Standards Committee** (HITSC) — the federal advisory committee to ONC created by the HITECH Act — covering 68 full-committee meetings from May 2009 through December 2015.

HITSC was the technical half of the pair. Where its sibling the HIT Policy Committee argued about what the incentive program should require, this committee argued about whether the standards existed to require it: which vocabularies, which content and transport specifications, which test tools, and — over and over — whether a given standard was mature enough to be named in a certification rule.

The transcripts vanished from public view when ONC reorganized its sites after the 21st Century Cures Act folded both committees into HITAC. This project recovers them from the Internet Archive's Wayback Machine, parses them into a structured, speaker-attributed database, and layers analysis on top.

It is a fork of [healthbjk/hitpc-explorer](https://github.com/healthbjk/hitpc-explorer), which did the same for the Policy Committee. The database schema and app are shared, so the two corpora can be compared directly; the collector, topic families and speaker tables are specific to this committee.

## What's inside

- **`hitsc.db`** — SQLite database: 68 meetings, 21,399 speaker-attributed utterances (2.28M words), 263 normalized speakers, keyword topic tags, and full-text search (FTS5).
- **`app.py`** — Streamlit app: **Speakers** (leaderboard → per-person record: activity vs the committee average, topic mix, position analysis, every quote, and how others referred to them), **Topics** (trend charts), **Search** (full-text), and **Meetings & Transcripts** (full transcript of any meeting, downloadable, with a link back to the original ONC source).
- **`pipeline/`** — the full reproducible pipeline: Wayback CDX discovery (`collect_hitsc_corpus.py`), text extraction, transcript parsing (three transcription-vendor grammars), speaker normalization, and topic tagging.

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py
```

The app runs entirely off the committed `hitsc.db` — no other data needed.

## Rebuild from scratch (optional)

```bash
# 1. Re-download the transcript corpus from the Wayback Machine (~30 min)
.venv/bin/python collect_hitsc_corpus.py        # writes hitsc_corpus/
# 2. Rebuild the database
.venv/bin/python -m pipeline.build_db           # writes hitsc.db
```

Requires `pdftotext` (poppler) on PATH for step 2.

An optional third step adds LLM analysis (meeting summaries, per-speaker position analyses, and a narrative of the standards agenda) to the same database. It needs `ANTHROPIC_API_KEY` and costs real money; the app degrades gracefully without it.

```bash
.venv/bin/python -m pipeline.llm_pass
```

## Finding the right files

ONC renamed these documents four times in six years, and the full-committee transcripts sit among several hundred workgroup and task-force transcripts in the same directories. The collector's filter is built around that:

| Era | Full-committee transcript looks like |
|---|---|
| 2009 | `HITstandards_transcript_062309-1.pdf` (MMDDYY), and one file with no date at all |
| 2010–2012 | `2010-02-24_standards_transcript_draft.pdf`, also `20100120_…`, `2010_10_27_…`, `2010-05-26-standards-transcript.pdf` |
| 2011–2013 | `2011-11-16_HITSC_Final_Transcript.pdf` — "standards" gives way to "hitsc" |
| 2014–2015 | `HITSC_Transcript_Final_2014-02-18.pdf` — the date moves to the end |

Workgroup transcripts carry a code *between* the committee name and "transcript" — `standards_ps_` (privacy & security), `_si_` (standards & interoperability), `_co_` (certification & adoption), `_cq_` (clinical quality), `_ct_` (certification testing), `_vtf_` (vocabulary task force), `_nwhin_`, `_pghd_`, and combinations. In the 2014–2015 era ONC dropped the shared prefix entirely and gave each workgroup its own acronym (`ASA_`, `CSWG_`, `ICTWG_`, `ISATF_`, `APISWG_`, `CQWG_`, `DPROVTF_`), so those never match on "standards" or "hitsc" at all.

The filter is applied to the **basename only**. Many of these files live under portal paths that themselves contain "standards", which would otherwise pull in every workgroup document stored beside them.

## How the counts reconcile

**96 documents ≠ 68 meetings.** The Wayback sweep recovered 96 distinct documents (deduplicated by content digest, since the Archive stores the same file under many portal redirect URLs). ONC published most meetings twice — a draft and a final transcript — so 27 files are second versions of a meeting already counted. Collapsing them yields **68 unique meetings**, finals preferred over drafts.

**Dates come from the transcript, not the filename.** Every meeting date is verified against the date printed inside the document. Here 67 of 68 filenames agreed. The exception is `standards_transcript.pdf`, which carries no date at all in its name; the text inside dates it to **2009-05-15**, the committee's first meeting.

**Coverage.** May 2009 – December 2015, roughly monthly: 2009: 5 · 2010: 11 · 2011: 12 · 2012: 11 · 2013: 10 · 2014: 10 · 2015: 9. Twelve months in that span have no meeting in the corpus (2009-10 through 2009-12, 2010-07, 2012-12, 2013-05, 2013-10, 2014-01, 2014-10, 2015-02, 2015-07, 2015-10) — some because the committee did not meet, some because no transcript survives at the URLs the Archive captured. The two are not distinguished here.

**Nothing after 2015.** HITSC continued into 2016 — workgroup transcripts from that year survive (e.g. `ISATF_Transcript_Final_2016-04-15.pdf`) — but no 2016 full-committee transcript appears anywhere in the Wayback index for either ONC domain. Treat December 2015 as the end of the recoverable record, not the end of the committee.

**Attendance is measured against tenure.** A speaker's "meetings spoke at" is out of the meetings held between their first and last recorded remark, not out of all 68, because most members served only part of the committee's life.

## Notes

- Transcripts are public U.S. government records (FACA committee proceedings).
- Speaker attribution is parsed from transcript headers; name variants are normalized. The variants that matter were found by looking for near-duplicate surnames in the built database, not assumed in advance — "Jaime"/"James" Ferguson, "Mark"/"Marc" Overhage, "Christopher"/"Cris" Ross, "Rich"/"Richard" Elmore, "Johnathan"/"Jonathan" Coleman all split without them. Same-surname pairs that are genuinely different people (Robert and Elise Anthony; Jodi and James Daniel; Cris, Ron and Clarke Ross) are left separate.
- Topic families are tuned to this committee's subject matter — vocabularies, content standards, FHIR/APIs, transport, testing and certification, standards process, maturity — rather than the policy questions HITPC handled. The `vendor_mention` family is built from companies actually named in these transcripts, in descending order of how often they appear: Surescripts (62), Cerner (56), Google (36), Microsoft (27), athenahealth (20), Epic (16). The Policy Committee corpus gives Epic a topic family of its own; that would be a poor fit here.
- Three transcription-vendor grammars appear across the corpus (em-dash headers, comma headers, and bare-name headers); the parser detects which is in use per file.
- One 2011 document is a `.doc` the extractor skips; the same meeting is present as a PDF.
