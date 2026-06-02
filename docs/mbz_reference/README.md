# Moodle 5.2 reference backup

Provenance material for the `.mbz` builder. **Do not edit** — this is ground
truth, captured as-is.

- `reference-moodle-5.2-course.mbz` — a real Moodle course backup exported from
  the IMS Moodle instance (a throwaway "MBZ template" course). It contains one
  Page and one Quiz — exactly the two activity types our pipeline produces —
  plus the default Announcements forum and an empty question bank.
- `extracted/` — the same backup untarred, so the XML is readable/greppable
  without unpacking.

The schema we derive from this is documented in
[`../mbz_format.md`](../mbz_format.md). When the builder and the doc disagree
with reality, the files here win.

Source Moodle: `moodle_release 5.2+ (Build: 20260501)`, `backup_version
2026042000`.
