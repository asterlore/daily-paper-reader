"""Accepted-author score 7+ supplements original DPR recommendations."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
spec = importlib.util.spec_from_file_location("dpr_select_papers", ROOT / "src" / "5.select_papers.py")
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


def paper(pid, score, status=None):
    value = {"id": pid, "llm_score": score, "llm_tags": ["query:virtual-cell"]}
    if status is not None:
        value["acceptance"] = {
            "status": status, "venue_type": "journal",
            "evidence": "Accepted for publication in Test Journal",
        }
    return value


class AuthorAcceptedSelectionTests(unittest.TestCase):
    def test_standard_keeps_original_picks_and_adds_accepted_seven(self):
        papers = [
            paper("2610.00001v1", 9),
            paper("2610.00002v1", 7.0, "accepted_claim"),
            paper("2610.00003v1", 6.9, "accepted_claim"),
            paper("2610.00004v1", 7.5),
        ]
        original = [papers[0]]
        quick, count = selector.include_author_accepted_quick(original, papers, [])
        self.assertEqual(count, 1)
        self.assertEqual({p["id"] for p in quick}, {"2610.00001v1", "2610.00002v1"})

    def test_no_duplicate_accepted_deep_paper(self):
        papers = [paper("2610.10000v1", 9.0, "published_claim")]
        quick, count = selector.include_author_accepted_quick([], papers, papers)
        self.assertEqual(count, 0)
        self.assertEqual(quick, [])

    def test_version_deduplication(self):
        papers = [paper("2610.20000v1", 7.0, "accepted_claim")]
        quick, count = selector.include_author_accepted_quick(
            [paper("2610.20000v2", 8.0)], papers, []
        )
        self.assertEqual(count, 0)
        self.assertEqual(len(quick), 1)

    def test_skims_adds_accepted_seven_below_eight_threshold(self):
        papers = [
            paper("2610.30000v1", 9.0),
            paper("2610.30001v1", 7.0, "accepted_claim"),
            paper("2610.30002v1", 7.2, "published_claim"),
            paper("2610.30003v1", 7.2),
            paper("2610.30004v1", 6.9, "accepted_claim"),
        ]
        result = selector.process_mode_all_quick_min_score(papers, "skims", 8.0)
        self.assertEqual(result["deep_dive"], [])
        self.assertEqual({p["id"] for p in result["quick_skim"]},
                         {"2610.30000v1", "2610.30001v1", "2610.30002v1"})
        self.assertEqual(result["stats"]["author_claim_7plus_added"], 2)


if __name__ == "__main__":
    unittest.main()
