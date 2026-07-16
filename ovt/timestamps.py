"""Timestamp normalisation across sources.

Different platforms and devices report time in different formats and zones.
For cross-referencing (e.g. does the EXIF capture time precede the first
social media appearance?) everything is converted to timezone-aware UTC.
"""

from datetime import datetime, timezone, timedelta


# Formats seen in EXIF data, platform exports, and archive services
KNOWN_FORMATS = [
    "%Y:%m:%d %H:%M:%S",        # EXIF
    "%Y-%m-%dT%H:%M:%S%z",      # ISO 8601 with offset
    "%Y-%m-%dT%H:%M:%SZ",       # ISO 8601 Zulu
    "%Y-%m-%d %H:%M:%S",        # generic
    "%a %b %d %H:%M:%S %z %Y",  # legacy Twitter API
    "%d/%m/%Y %H:%M",           # manual notes, UK convention
]


def normalise(value, assume_tz_offset_hours=None):
    """Parse a timestamp string into aware UTC datetime.

    Naive timestamps (no zone info) are assumed UTC unless an offset is
    given. The assumption is recorded in the returned dict so it appears
    in the evidence report rather than being silently applied.
    """
    parsed = None
    matched_format = None
    for fmt in KNOWN_FORMATS:
        try:
            parsed = datetime.strptime(value.strip(), fmt)
            matched_format = fmt
            break
        except ValueError:
            continue

    if parsed is None:
        raise ValueError(f"Unrecognised timestamp format: {value!r}")

    assumption = None
    if parsed.tzinfo is None:
        if assume_tz_offset_hours is not None:
            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=assume_tz_offset_hours)))
            assumption = f"naive timestamp, offset UTC{assume_tz_offset_hours:+d} assumed"
        else:
            parsed = parsed.replace(tzinfo=timezone.utc)
            assumption = "naive timestamp, UTC assumed"

    return {
        "input": value,
        "utc": parsed.astimezone(timezone.utc),
        "matched_format": matched_format,
        "assumption": assumption,
    }


def sequence_check(events):
    """Order a list of (label, normalised_timestamp) pairs chronologically
    and flag any that share an identical UTC time.

    Returns the ordered list; useful for building a claim timeline.
    """
    ordered = sorted(events, key=lambda e: e[1]["utc"])
    flagged = []
    for (label_a, a), (label_b, b) in zip(ordered, ordered[1:]):
        if a["utc"] == b["utc"]:
            flagged.append((label_a, label_b))
    return ordered, flagged
