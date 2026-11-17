"""Tests for the arXiv author-declaration filter (no network or LLM)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from arxiv_acceptance import detect_author_declaration, is_author_declared_accepted


class ArxivAcceptanceTests(unittest.TestCase):
    def check(self, comment="", journal_ref="", status="not_declared", venue="unspecified"):
        result = detect_author_declaration({"comment": comment, "journal_ref": journal_ref})
        self.assertEqual(result["status"], status)
        self.assertEqual(result["venue_type"], venue)
        self.assertEqual(result["verification"], "author_claim_only")
        return result

    def test_conference_accepted(self):
        self.check("Accepted at NeurIPS 2026", status="accepted_claim", venue="conference")

    def test_workshop_accepted(self):
        self.check("Accepted by NeurIPS 2026 AI for Drug Discovery Workshop",
                   status="accepted_claim", venue="workshop")

    def test_journal_accepted(self):
        self.check("Accepted for publication in Nature Methods",
                   status="accepted_claim", venue="journal")

    def test_journal_published(self):
        self.check("Published in Genome Biology", status="published_claim", venue="journal")

    def test_to_appear(self):
        self.check("To appear in Proceedings of ICML 2026",
                   status="accepted_claim", venue="conference")

    def test_journal_reference(self):
        d = self.check(journal_ref="Bioinformatics 42 (2026), 101-110",
                       status="published_claim", venue="journal")
        self.assertEqual(d["evidence_source"], "journal_ref")

    def test_no_declaration(self):
        self.check("")
        self.check("Submitted to NeurIPS 2026")
        self.check("Under review at Nature Methods")
        self.check("Rejected from ICLR")
        self.check("Not accepted at NeurIPS 2026")
        self.check("Not yet accepted for publication in Nature Methods")
        self.check("Not published in Nature")
        self.check("Presented at NeurIPS 2026")
        self.check("Extended version of our workshop submission")

    def test_doi_is_not_proof(self):
        self.assertFalse(is_author_declared_accepted({"doi": "10.1000/foo"}))

    def test_multiple_statements(self):
        self.check("Submitted to ICLR 2026; Accepted at NeurIPS 2026",
                   status="accepted_claim", venue="conference")

    def test_missing_is_not_rejected(self):
        d = self.check(journal_ref="")
        self.assertEqual(d["status"], "not_declared")


if __name__ == "__main__":
    unittest.main()
