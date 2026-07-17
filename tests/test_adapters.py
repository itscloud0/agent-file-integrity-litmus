from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_file_integrity_litmus.adapters import run_adapter
from agent_file_integrity_litmus.core import FIXTURES


class AdapterTests(unittest.TestCase):
    def test_unknown_adapter_is_rejected_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            with self.assertRaisesRegex(ValueError, "unsupported adapter"):
                run_adapter("unknown", output)
            self.assertFalse(output.exists())

    def test_true_executable_produces_raw_artifacts_and_failed_score(self) -> None:
        true_bin = Path("/usr/bin/true")
        if not true_bin.exists():
            self.skipTest("/usr/bin/true is unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "run"
            result = run_adapter("codex-cli", output, codex_bin=str(true_bin))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.passed, 0)
            self.assertTrue((result.artifacts / "report.json").is_file())
            self.assertTrue((result.artifacts / "stdout.jsonl").is_file())
            self.assertTrue((result.artifacts / "post-edit-files" / "crlf.txt").is_file())
            self.assertTrue((result.workspace / ".git").is_dir())
            report = json.loads((result.artifacts / "report.json").read_text(encoding="utf-8"))
            self.assertEqual([item["outcome"] for item in report["results"]], ["SKIPPED"] * len(FIXTURES))
            self.assertTrue(all(item["expected_sha256"] and item["actual_sha256"] for item in report["results"]))


if __name__ == "__main__":
    unittest.main()
