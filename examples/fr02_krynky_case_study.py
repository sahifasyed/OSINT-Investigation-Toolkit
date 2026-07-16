"""Case study: FR-02 — combat footage recirculation (Russia-Ukraine).

Reconstruction of a verification case from my dissertation,
"Disinformation Patterns Across Regional Conflicts: A Forensic OSINT
Analysis" (UWE Bristol, 2026). A video recirculated on X in February
2025 claimed to show current Ukrainian FPV drone strikes. Verification
traced the footage to a documented strike near Krynky on 8 January 2024
by the Griffin 501 UAV Unit — authentic footage, false temporal context.

The original artifact hash below is the SHA-256 recorded at collection
in the dissertation's chain-of-custody log (Table 7). Post identifiers
are anonymised in line with the dissertation's ethics approach; all
sources are public and the claim was independently debunked.

Run:  python examples/fr02_krynky_case_study.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ovt.timestamps import normalise, sequence_check
from ovt.report import EvidenceReport


# Artifact as documented at collection (dissertation Table 7).
# The metadata dict is entered manually here because the case study
# reconstructs a completed investigation rather than re-running it.
ARTIFACT = {
    "file": "RU-UA-2025-02-UKRCASE01.mp4",
    "format": "MP4 video (embedded from TikTok, reposted to X)",
    "dimensions": None,
    "exif_present": False,
    "capture_time": None,
    "device": None,
    "software": None,
    "gps": None,
    "sha256_at_collection": "e54b81218a75573b17f095b671105ba86d9bf89019d3d1193897c2f961de6fbd",
}


def build_timeline():
    """Five-tier provenance chain (dissertation Figure 13)."""
    events = [
        ("Tier 1 — original publication: Griffin 501 UAV Unit, "
         "501st Marine Infantry Battalion (Telegram)",
         normalise("2024-01-08 12:00:00", assume_tz_offset_hours=2)),
        ("Tier 2 — first amplification: Ukrainian activist repost "
         "(Telegram + X, same day)",
         normalise("2024-01-08 18:00:00", assume_tz_offset_hours=2)),
        ("Tier 3 — independent media republication: verified outlet "
         "on X, 173.4K views",
         normalise("2024-01-09T17:19:00Z")),
        ("Tier 4 — corroboration: UK MoD via Janes confirms ~90% "
         "Russian equipment loss at Krynky incl. FPV strikes",
         normalise("2024-01-15 12:00:00")),
        ("Tier 5 — MIS-CONTEXTUALISED REDISTRIBUTION: anonymised X "
         "account, embedded TikTok, no date attribution, 14.7K views",
         normalise("2025-02-17 06:22:00")),
    ]
    return sequence_check(events)


def main():
    ordered, _ = build_timeline()

    report = EvidenceReport(
        title="FR-02: Combat footage recirculation — Krynky FPV strike",
        analyst="Sahifa Syed",
        case_ref="FR-02 (dissertation, UWE Bristol 2026)",
    )
    report.add_artifact("E0001", ARTIFACT,
                        notes="SHA-256 recorded at collection via certutil; "
                              "reverse image search performed on InVID "
                              "keyframes via Google Lens and Yandex.")
    report.add_timeline(ordered)

    report.add_finding(
        "The footage is authentic combat footage of an FPV drone strike "
        "by the Griffin 501 UAV Unit near Krynky, Kherson region.",
        confidence="confirmed",
        supporting_evidence=[
            "Yandex match: unit's own upload, ~2 years prior",
            "WarSpotting documented loss entry #22965 (T-72, Krynky)",
            "UK MoD / Janes corroboration of the engagement, 15 Jan 2024",
        ],
    )
    report.add_finding(
        "The February 2025 circulation presents the footage as current "
        "operations. The 13-month gap and absence of date attribution "
        "constitute temporal reframing: authentic media, false context.",
        confidence="confirmed",
        supporting_evidence=[
            "Provenance chain tiers 1-4 all date to January 2024",
            "Tier 5 repost caption omits original date entirely",
        ],
    )
    report.add_finding(
        "The redistribution was a deliberate disinformation operation "
        "rather than organic resharing.",
        confidence="possible",
        supporting_evidence=[
            "Attribution limited: anonymised account, no network analysis "
            "performed at artifact level",
        ],
    )

    out = os.path.join(os.path.dirname(__file__), "fr02_report.md")
    report.save(out)
    print(f"Report written to {out}")


if __name__ == "__main__":
    main()
