"""Chain-of-custody logging for digital evidence.

Every artifact that enters an investigation gets hashed (SHA-256) and
recorded in an append-only JSON log. Any subsequent action taken on the
artifact (analysis, export, transformation) is logged against that hash,
so the provenance of every finding in the final report can be traced back
to an exact file state.
"""

import hashlib
import json
import os
from datetime import datetime, timezone


class CustodyLog:
    def __init__(self, log_path="evidence_store/custody_log.json", analyst=None):
        self.log_path = log_path
        self.analyst = analyst or os.environ.get("USER", "unknown")
        self._entries = []
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                self._entries = json.load(f)

    @staticmethod
    def hash_file(path, chunk_size=65536):
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    def register(self, path, source, notes=""):
        """Register a new artifact. Returns its evidence ID."""
        digest = self.hash_file(path)
        registrations = [e for e in self._entries if e["action"] == "registered"]
        evidence_id = f"E{len({e['sha256'] for e in registrations}) + 1:04d}"

        existing = [e for e in registrations if e["sha256"] == digest]
        if existing:
            evidence_id = existing[0]["evidence_id"]

        self._append({
            "evidence_id": evidence_id,
            "action": "registered",
            "file": os.path.basename(path),
            "sha256": digest,
            "source": source,
            "notes": notes,
        })
        return evidence_id

    def log_action(self, evidence_id, action, notes=""):
        known = {e["evidence_id"] for e in self._entries}
        if evidence_id not in known:
            raise ValueError(f"Unknown evidence ID: {evidence_id}")
        self._append({
            "evidence_id": evidence_id,
            "action": action,
            "notes": notes,
        })

    def verify(self, evidence_id, path):
        """Re-hash a file and confirm it matches its registration hash."""
        registered = [
            e for e in self._entries
            if e["evidence_id"] == evidence_id and e["action"] == "registered"
        ]
        if not registered:
            raise ValueError(f"No registration found for {evidence_id}")
        current = self.hash_file(path)
        ok = current == registered[0]["sha256"]
        self._append({
            "evidence_id": evidence_id,
            "action": "integrity_check",
            "notes": "match" if ok else f"MISMATCH: current hash {current}",
        })
        return ok

    def entries(self, evidence_id=None):
        if evidence_id is None:
            return list(self._entries)
        return [e for e in self._entries if e["evidence_id"] == evidence_id]

    def _append(self, entry):
        entry["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        entry["analyst"] = self.analyst
        self._entries.append(entry)
        os.makedirs(os.path.dirname(self.log_path) or ".", exist_ok=True)
        with open(self.log_path, "w") as f:
            json.dump(self._entries, f, indent=2)
