"""LLM analysis pass over hitsc.db using the Claude API.

Produces, incrementally (each item cached in the DB, safe to re-run):
  1. meeting_summaries  — one summary per meeting
  2. speaker_summaries  — a position analysis per prolific speaker
  3. analysis_notes(kind='standards_arc') — how the standards agenda evolved

Requires ANTHROPIC_API_KEY. Run:
  .venv/bin/python -m pipeline.llm_pass                 # everything missing
  .venv/bin/python -m pipeline.llm_pass --meetings 2    # only 2 missing summaries
  .venv/bin/python -m pipeline.llm_pass --skip-meetings # only speakers + notes
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

DB_PATH = Path(__file__).resolve().parent.parent / "hitsc.db"
MODEL = "claude-sonnet-5"
MAX_MEETING_CHARS = 350_000   # ~90k tokens, fits comfortably in context

# Speakers get an analysis if they cleared both bars. Roll-call one-liners
# don't count toward either, hence the word-count floor on the remarks query.
MIN_REMARKS = 60
MIN_WORDS = 15_000

MEETING_PROMPT = """\
You are analyzing a meeting transcript of the US HIT Standards Committee \
(HITSC, a FACA advisory committee to ONC, 2009-2016). Unlike its sibling the \
HIT Policy Committee, this body handled the technical layer: vocabularies, \
content and transport standards, testing and certification criteria. \
Summarize this {date} meeting in markdown with these sections:

**Agenda & key decisions** — what was discussed and recommended to ONC.
**Standards in play** — the specific standards, profiles and implementation \
guides debated (HL7/CDA/C-CDA/FHIR, SNOMED/LOINC/RxNorm, Direct/SOAP/REST, \
IHE profiles, NIST test tooling…), and what was said about each.
**Notable debates** — points of real disagreement, and who took which side. \
Maturity-vs-ambition arguments (is this standard ready to be required?) belong \
here.
**Policy interface** — anything about what HITPC, CMS or the certification \
rule was asking of this committee (say "nothing notable" if absent).

Be specific: name speakers. Keep it under 500 words.

TRANSCRIPT:
{transcript}"""

SPEAKER_PROMPT = """\
Below are the substantive remarks by {name}{org_clause} as a participant in \
the US HIT Standards Committee, {span}, with meeting dates. Write a markdown \
analysis of their participation:

1. **Themes** — the recurring technical topics they engaged on, with their \
position on each and 2-3 short representative quotes (with dates).
2. **Standards posture** — where they pushed for mandating a standard versus \
waiting for maturity, and where their stated views aligned with or diverged \
from the interests of the organization they represented. Be factual and fair; \
distinguish what they said from your interpretation.
3. **Evolution** — how their focus or tone changed across their tenure, if at \
all.

If the remarks are mostly procedural (chairing, roll call, logistics), say so \
plainly rather than manufacturing themes.

REMARKS:
{remarks}"""

STANDARDS_ARC_PROMPT = """\
Below are utterances from US HIT Standards Committee meetings tagged as being \
about content standards, vocabularies, FHIR/APIs, or standards process, with \
speaker names and dates, in chronological order. The recoverable transcript \
record runs May 2009 to December 2015; do not describe anything after it, and \
do not imply the committee ended then. \
Write a markdown narrative of how the committee's technical agenda evolved: \
the early scramble to name standards for Meaningful Use Stage 1, the \
consolidation onto C-CDA and the vocabulary triad (SNOMED/LOINC/RxNorm), the \
transport debates (NwHIN Exchange vs Direct), the arrival of FHIR and APIs \
late in the committee's life, and the recurring argument about standards \
maturity and how much to mandate. Name the main protagonists and what each \
argued. Under 800 words.

Refer to people by the speaker name given in the utterances below, and state \
dates and statutory deadlines only where the transcripts support them.

UTTERANCES:
{utterances}"""


def _client():
    return anthropic.Anthropic()


def _ask(client, prompt, max_tokens=2000):
    resp = client.messages.create(
        model=MODEL, max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    # Not resp.content[0]: current models may put a ThinkingBlock first, which
    # has no .text. Join every text block instead of assuming the shape.
    return "\n".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def summarize_meetings(con, client, limit=None):
    todo = con.execute("""
        SELECT m.id, m.date FROM meetings m
        LEFT JOIN meeting_summaries s ON s.meeting_id = m.id
        WHERE s.meeting_id IS NULL ORDER BY m.date""").fetchall()
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} meetings to summarize", file=sys.stderr)
    for mid, date in todo:
        rows = con.execute("""
            SELECT s.name, u.text FROM utterances u
            JOIN speakers s ON s.id=u.speaker_id
            WHERE u.meeting_id=? ORDER BY u.seq""", (mid,)).fetchall()
        transcript = "\n\n".join(f"{n}: {t}" for n, t in rows)[:MAX_MEETING_CHARS]
        summary = _ask(client, MEETING_PROMPT.format(date=date, transcript=transcript))
        con.execute(
            "INSERT OR REPLACE INTO meeting_summaries VALUES (?,?,?,?)",
            (mid, summary, MODEL, datetime.now(timezone.utc).isoformat()))
        con.commit()
        print(f"  summarized {date}", file=sys.stderr)


def summarize_speakers(con, client, limit=None):
    """One position analysis per prolific speaker.

    Driven by a query rather than a hardcoded roster: HITSC's membership
    turned over heavily across seven years, and who mattered is better read
    off the transcripts than asserted up front.
    """
    todo = con.execute("""
        SELECT s.key, s.name, s.org,
               COUNT(*) AS n, SUM(u.word_count) AS w,
               MIN(m.date) AS first, MAX(m.date) AS last
        FROM utterances u
        JOIN speakers s ON s.id = u.speaker_id
        JOIN meetings m ON m.id = u.meeting_id
        LEFT JOIN speaker_summaries ss ON ss.speaker_key = s.key
        WHERE u.word_count >= 25
          AND ss.speaker_key IS NULL
          AND s.key != '(unidentified)'
        GROUP BY s.key
        HAVING n >= ? AND w >= ?
        ORDER BY w DESC""", (MIN_REMARKS, MIN_WORDS)).fetchall()
    if limit:
        todo = todo[:limit]
    print(f"{len(todo)} speakers to analyze", file=sys.stderr)
    for key, name, org, n, w, first, last in todo:
        rows = con.execute("""
            SELECT m.date, u.text FROM utterances u
            JOIN speakers s ON s.id=u.speaker_id
            JOIN meetings m ON m.id=u.meeting_id
            WHERE s.key = ? AND u.word_count >= 25
            ORDER BY m.date, u.seq""", (key,)).fetchall()
        remarks = "\n\n".join(f"[{d}] {t}" for d, t in rows)
        if len(remarks) > 600_000:
            remarks = (remarks[:300_000]
                       + "\n\n[... middle years trimmed ...]\n\n"
                       + remarks[-300_000:])
        content = _ask(client, SPEAKER_PROMPT.format(
            name=name,
            org_clause=f" ({org})" if org else "",
            span=f"{first[:4]}-{last[:4]}",
            remarks=remarks), max_tokens=4000)
        con.execute(
            "INSERT OR REPLACE INTO speaker_summaries VALUES (?,?,?,?)",
            (key, content, MODEL, datetime.now(timezone.utc).isoformat()))
        con.commit()
        print(f"  analyzed {name} ({n} remarks, {w:,} words)", file=sys.stderr)


def standards_arc(con, client):
    rows = con.execute("""
        SELECT DISTINCT m.date, s.name, u.text FROM utterances u
        JOIN utterance_topics ut ON ut.utterance_id=u.id
             AND ut.topic IN ('content_standards','vocabulary','fhir_api',
                              'standards_process')
        JOIN speakers s ON s.id=u.speaker_id
        JOIN meetings m ON m.id=u.meeting_id
        WHERE u.word_count >= 40
        ORDER BY m.date, u.seq""").fetchall()
    text = "\n\n".join(f"[{d}] {n}: {t}" for d, n, t in rows)
    # Trim from the middle if enormous, keeping early + late years intact.
    if len(text) > 600_000:
        text = text[:300_000] + "\n\n[... middle years trimmed ...]\n\n" + text[-300_000:]
    print(f"standards arc: {len(rows)} utterances, {len(text):,} chars", file=sys.stderr)
    content = _ask(client, STANDARDS_ARC_PROMPT.format(utterances=text), max_tokens=4000)
    con.execute(
        "INSERT INTO analysis_notes (kind, content, model, created_at) VALUES (?,?,?,?)",
        ("standards_arc", content, MODEL, datetime.now(timezone.utc).isoformat()))
    con.commit()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meetings", type=int, default=None,
                    help="summarize at most N missing meetings")
    ap.add_argument("--speakers", type=int, default=None,
                    help="analyze at most N missing speakers")
    ap.add_argument("--skip-meetings", action="store_true")
    ap.add_argument("--skip-speakers", action="store_true")
    ap.add_argument("--skip-notes", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB_PATH)
    client = _client()
    if not args.skip_meetings:
        summarize_meetings(con, client, args.meetings)
    if not args.skip_speakers:
        summarize_speakers(con, client, args.speakers)
    if not args.skip_notes:
        standards_arc(con, client)
    con.close()


if __name__ == "__main__":
    main()
