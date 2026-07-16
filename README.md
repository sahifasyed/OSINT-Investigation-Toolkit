# OSINT Investigation and Verification Toolkit

Python tooling for image-based OSINT verification with forensic
chain-of-custody logging. Built out of the methodology from my
undergraduate dissertation (forensic OSINT across six case studies in
three conflict zones), presented at the Bath Lovelace Colloquium 2026
and accepted at RATSIF 2026, Riga.

The problem this addresses: most OSINT write-ups can't show *how* they
know what they know. Findings get shared without provenance, artifacts
get modified between analysis and publication, and timestamps from
different platforms get compared without normalising timezones. This
toolkit makes the boring-but-critical parts of verification systematic.

## What it does

- **Chain of custody** (`ovt/custody.py`) — every artifact is SHA-256
  hashed on registration; every subsequent action is logged against it
  in an append-only record. Integrity can be re-verified at any point,
  and tampering shows up as a logged mismatch.
- **Metadata extraction** (`ovt/metadata.py`) — pulls the EXIF fields
  that matter for verification (capture time, device, editing software,
  GPS) and explicitly records their *absence*, since stripped metadata
  is itself a signal that an image passed through a social platform.
- **Timestamp normalisation** (`ovt/timestamps.py`) — parses the formats
  used by EXIF, ISO 8601, legacy platform APIs, and manual notes into
  timezone-aware UTC. Where a timezone has to be assumed, the assumption
  is recorded and surfaces in the final report instead of being silently
  applied.
- **Evidence reports** (`ovt/report.py`) — Markdown reports combining
  artifacts, a normalised timeline, findings with explicit confidence
  levels (confirmed / probable / possible / unsupported), and the full
  custody log.

## Quick start

```
pip install -r requirements.txt
python examples/worked_example.py
python examples/fr02_krynky_case_study.py
```

`worked_example.py` shows the full live workflow on any image you supply.
`fr02_krynky_case_study.py` reconstructs a real case from my dissertation:
FR-02, in which combat footage recirculated on X in February 2025 as
"current" Ukrainian operations was traced through a five-tier provenance
chain to a documented FPV strike near Krynky on 8 January 2024 —
authentic footage, false temporal context. The script rebuilds the
timeline with the toolkit's timestamp normaliser and generates the full
evidence report (`examples/fr02_report.md`), including the SHA-256
recorded at original collection.

## Confidence standard

Findings use four levels, applied conservatively:

| Level | Meaning |
|---|---|
| confirmed | Independently corroborated by two or more unrelated sources |
| probable | Strong single-source evidence, nothing contradicting |
| possible | Consistent with evidence but alternatives remain plausible |
| unsupported | Cannot be corroborated from available material |

## Ethics and scope

This toolkit is for verification of publicly available material. It does
not collect data, scrape platforms, or profile individuals. The example
case is synthetic. Anything resembling investigation of a real person
should only happen within a lawful, authorised context.

## Tests

`tests/test_core.py` covers custody registration, tamper detection,
duplicate handling, timestamp parsing and timeline ordering. Run with
`python -m pytest tests/`.

