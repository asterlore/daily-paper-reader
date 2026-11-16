#!/usr/bin/env python3
"""Classify author-declared acceptance/publication in arXiv metadata.

No publisher lookups or language-model requests. This is author-reported evidence,
not independent verification. Missing declarations mean unknown, NOT rejected.
"""
from __future__ import annotations

import re
from typing import Any, Dict

# Require explicit outcome words (not just a journal/conference name or a DOI).
_OUTCOME = re.compile(
    r"\b(accepted(?:\s+for\s+publication|\s+to|\s+at|\s+by|\s+in)?|"
    r"to\s+appear\s+(?:in|at)|forthcoming\s+(?:in|at)|"
    r"published\s+(?:in|at)|appeared\s+(?:in|at)|"
    r"in\s+press|conditionally\s+accepted|"
    r"presented\s+at)\b",
    re.I,
)
_NEGATIVE = re.compile(
    r"\b(not\s+accepted|was\s+rejected|rejected\s+(?:by|from)|"
    r"not\s+yet\s+accepted|not\s+published|"
    r"submitted|under\s+review|in\s+submission|withdrawn)\b",
    re.I,
)
_WORKSHOP = re.compile(r"\b(workshop|workshops|workshop\s+track|\bws\b)\b", re.I)
_JOURNAL = re.compile(
    r"\b(journal|transactions|nature|science|cell|bioinformatics|"
    r"genome\s+biology|plos|bmc|npj|briefings\s+in|"
    r"patterns|computational\s+biology|scientific\s+reports|"
    r"frontiers\s+in|journal\s+of|j\.)\b",
    re.I,
)
_CONFERENCE = re.compile(
    r"\b(conference|proceedings|symposium|congress|"
    r"neurips|nips|iclr|icml|aaai|ijcai|acl|emnlp|naacl|"
    r"cvpr|iccv|eccv|kdd|www|recomb|ismb|ismbeccb|"
    r"icassp|miccai|aistats|uai|colt|sigir|icde|vldb|"
    r"ecml|pkdd)\b",
    re.I,
)
_SUBMISSION = re.compile(r"\b(submitted|submission|under review|not accepted|rejected)\b", re.I)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _classify_venue(text: str) -> str:
    if _WORKSHOP.search(text):
        return "workshop"
    if _JOURNAL.search(text):
        return "journal"
    if _CONFERENCE.search(text):
        return "conference"
    return "unspecified"


def detect_author_declaration(paper: Dict[str, Any]) -> Dict[str, str]:
    """Returns status, venue_type, evidence, evidence_source, and verification."""
    comment = _clean(paper.get("comment"))
    journal_ref = _clean(paper.get("journal_ref"))
    unknown = {
        "status": "not_declared",
        "venue_type": "unspecified",
        "evidence": "",
        "evidence_source": "",
        "verification": "author_claim_only",
    }

    # A journal_ref normally denotes a bibliographic publication citation,
    # but never treat submission/under-review text as an accepted reference.
    if journal_ref and not _SUBMISSION.search(journal_ref):
        venue = _classify_venue(journal_ref)
        if venue != "unspecified" or bool(re.search(r"\b\d{4}\b", journal_ref)):
            return {
                "status": "published_claim",
                "venue_type": venue,
                "evidence": journal_ref,
                "evidence_source": "journal_ref",
                "verification": "author_claim_only",
            }

    # Split to avoid 'submitted to X; accepted at Y' being treated as negative
    # for the entire comment. Avoid spanning across sentence boundaries.
    for fragment in re.split(r"[;\n]+|(?<=[.!?])\s+(?=[A-Z])", comment):
        part = fragment.strip()
        if not part:
            continue
        match = _OUTCOME.search(part)
        if not match:
            continue
        prefix = part[:match.start()]
        if re.search(r"\b(not|never|wasn't|isn't)\s*$", prefix, re.I):
            continue
        if re.search(r"\bnot\s+(?:yet\s+)?accepted\b", part, re.I):
            continue
        if re.search(r"\b(rejected|withdrawn)\b", part, re.I):
            continue
        # Exclude statuses that are only submissions (and lack an outcome).
        outcome = match.group(0).lower()
        status = "published_claim" if re.search(r"published|appeared|presented", outcome) else "accepted_claim"
        return {
            "status": status,
            "venue_type": _classify_venue(part),
            "evidence": part[:500],
            "evidence_source": "comment",
            "verification": "author_claim_only",
        }

    return unknown


def is_author_declared_accepted(paper: Dict[str, Any]) -> bool:
    return detect_author_declaration(paper)["status"] in {"accepted_claim", "published_claim"}
