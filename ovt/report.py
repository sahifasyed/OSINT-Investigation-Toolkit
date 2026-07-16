"""Structured evidence report generation.

Produces a Markdown report combining artifact metadata, the normalised
event timeline, analyst assessments, and the full chain-of-custody log.
Markdown is deliberate: it renders on GitHub, converts cleanly to PDF,
and diffs well under version control.
"""

from datetime import datetime, timezone


CONFIDENCE_LEVELS = ("confirmed", "probable", "possible", "unsupported")


class EvidenceReport:
    def __init__(self, title, analyst, case_ref=""):
        self.title = title
        self.analyst = analyst
        self.case_ref = case_ref
        self.artifacts = []
        self.timeline = []
        self.findings = []

    def add_artifact(self, evidence_id, metadata, notes=""):
        self.artifacts.append({
            "evidence_id": evidence_id,
            "metadata": metadata,
            "notes": notes,
        })

    def add_timeline(self, ordered_events):
        self.timeline = ordered_events

    def add_finding(self, statement, confidence, supporting_evidence):
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"confidence must be one of {CONFIDENCE_LEVELS}")
        self.findings.append({
            "statement": statement,
            "confidence": confidence,
            "evidence": supporting_evidence,
        })

    def render(self, custody_log=None):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        lines = [
            f"# {self.title}",
            "",
            f"**Case reference:** {self.case_ref or 'n/a'}  ",
            f"**Analyst:** {self.analyst}  ",
            f"**Report generated:** {now}",
            "",
            "## Artifacts",
            "",
        ]

        for a in self.artifacts:
            m = a["metadata"]
            dims = f" {m.get('dimensions')}" if m.get("dimensions") else ""
            lines += [
                f"### {a['evidence_id']} — {m.get('file', 'unknown')}",
                "",
                f"- Format: {m.get('format')}{dims}",
                f"- EXIF present: {m.get('exif_present')}",
                f"- Capture time (as reported): {m.get('capture_time') or 'not present'}",
                f"- Device: {m.get('device') or 'not present'}",
                f"- Software: {m.get('software') or 'not present'}",
                f"- GPS: {m.get('gps') or 'not present'}",
            ]
            if a["notes"]:
                lines.append(f"- Notes: {a['notes']}")
            lines.append("")

        if self.timeline:
            lines += ["## Timeline (all times UTC)", ""]
            for label, ts in self.timeline:
                assumption = f" *({ts['assumption']})*" if ts["assumption"] else ""
                lines.append(f"- `{ts['utc'].strftime('%Y-%m-%d %H:%M:%S')}` — {label}{assumption}")
            lines.append("")

        if self.findings:
            lines += ["## Findings", ""]
            for i, f in enumerate(self.findings, 1):
                lines += [
                    f"**{i}. {f['statement']}**  ",
                    f"Confidence: {f['confidence']} — Evidence: {', '.join(f['evidence'])}",
                    "",
                ]

        if custody_log is not None:
            lines += ["## Chain of custody", ""]
            lines.append("| Time (UTC) | Evidence | Action | Analyst | Notes |")
            lines.append("|---|---|---|---|---|")
            for e in custody_log.entries():
                lines.append(
                    f"| {e['timestamp_utc'][:19]} | {e['evidence_id']} "
                    f"| {e['action']} | {e['analyst']} | {e.get('notes', '')} |"
                )
            lines.append("")

        lines += [
            "---",
            "*All artifacts were obtained from publicly available sources. "
            "Assessments reflect the confidence standard defined in the project README.*",
        ]
        return "\n".join(lines)

    def save(self, path, custody_log=None):
        with open(path, "w") as f:
            f.write(self.render(custody_log))
        return path
