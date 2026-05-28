#!/usr/bin/env python3
"""
ids.py — Deterministic ID allocation for a .mbz backup.

Moodle remaps every id when a backup is restored, so ids only need to be
*internally consistent and unique within the backup*. We use one incrementing
counter per entity type, all starting at a fixed base. Because allocation is
deterministic, regenerating a .mbz produces byte-stable output and clean diffs.

The one invariant the rest of the builder must preserve (see docs/mbz_format.md):
a quiz activity's contextid == the contextid of its question categories ==
the contexts referenced in its inforef.xml. The allocator hands out the ids;
keeping that invariant is the caller's job.
"""

from __future__ import annotations


class IdAllocator:
    """Per-kind incrementing id counters. `kind` is any string label, e.g.
    'context', 'cmid', 'section', 'question', 'answer', 'qbe' (question bank
    entry), 'qversion', 'category', 'gradeitem', 'gradecategory'."""

    def __init__(self, start: int = 1) -> None:
        self._start = start
        self._counters: dict[str, int] = {}

    def next(self, kind: str) -> int:
        n = self._counters.get(kind, self._start)
        self._counters[kind] = n + 1
        return n

    def peek(self, kind: str) -> int:
        """The id that the next call to next(kind) would return."""
        return self._counters.get(kind, self._start)


def make_stamp(seq: int, host: str = "mbzbuilder.local") -> str:
    """A unique question 'stamp' string in Moodle's `host+digits+suffix` shape.

    The real values are random; ours just need to be unique within the backup,
    so we derive them deterministically from a sequence number."""
    suffix = ""
    n = seq + 1
    while n:
        n, rem = divmod(n - 1, 26)
        suffix = chr(ord("A") + rem) + suffix
    return f"{host}+{seq:010d}+{suffix}"
