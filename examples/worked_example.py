"""End-to-end example: verifying the claimed time and place of an image.

Scenario (synthetic): an image is shared on social media with the claim
that it was taken on 12 March 2026 in location X. We register the image
as evidence, extract its metadata, build a timeline from the EXIF capture
time and the first observed social media post, and produce a report.

Replace sample.jpg with any image of your own to run this.
"""

from ovt import CustodyLog, extract, normalise, sequence_check, EvidenceReport


def main():
    log = CustodyLog(analyst="S. Syed")

    # 1. Register the artifact before touching it
    evidence_id = log.register(
        "examples/sample.jpg",
        source="Public social media post (archived URL in case notes)",
        notes="Downloaded via archive service, original quality",
    )

    # 2. Extract metadata, logging the action
    meta = extract("examples/sample.jpg")
    log.log_action(evidence_id, "metadata_extraction", "EXIF via Pillow")

    # 3. Build the claim timeline
    events = []
    if meta["capture_time"]:
        events.append((
            f"EXIF capture time ({evidence_id})",
            normalise(meta["capture_time"]),
        ))
    events.append((
        "First observed social media post",
        normalise("2026-03-12T14:03:00Z"),
    ))
    events.append((
        "Claimed event time (per post caption)",
        normalise("12/03/2026 09:30", assume_tz_offset_hours=2),
    ))
    ordered, clashes = sequence_check(events)

    # 4. Assemble the report
    report = EvidenceReport(
        title="Image verification: claimed 12 March 2026 sighting",
        analyst="S. Syed",
        case_ref="DEMO-001",
    )
    report.add_artifact(evidence_id, meta)
    report.add_timeline(ordered)

    if meta["capture_time"]:
        report.add_finding(
            "EXIF capture time is consistent with the claimed event time.",
            confidence="probable",
            supporting_evidence=[evidence_id],
        )
    else:
        report.add_finding(
            "No EXIF capture time present; consistent with platform re-upload. "
            "Claimed time cannot be corroborated from metadata alone.",
            confidence="unsupported",
            supporting_evidence=[evidence_id],
        )

    # 5. Verify integrity before finalising, then save
    log.verify(evidence_id, "examples/sample.jpg")
    path = report.save("examples/demo_report.md", custody_log=log)
    print(f"Report written to {path}")


if __name__ == "__main__":
    main()
