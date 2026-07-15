from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_file_integrity_litmus.core import (
    FIXTURES,
    STALE_MERGED,
    STALE_OVERWRITE,
    create_fixture,
    create_stale_fixture,
    expected_bytes,
    inject_concurrent_change,
    score_fixture,
    score_stale_fixture,
)


class FixtureTests(unittest.TestCase):
    def test_create_preserves_fixture_bytes_and_modes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            create_fixture(root)
            for name, original in FIXTURES.items():
                self.assertEqual((root / name).read_bytes(), original)
            if os.name != "nt":
                self.assertEqual((root / "executable.sh").stat().st_mode & 0o777, 0o755)

    def test_byte_safe_replacement_passes_all_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            create_fixture(root)
            for name, original in FIXTURES.items():
                (root / name).write_bytes(expected_bytes(original))
            results = score_fixture(root)
            self.assertEqual([result.status for result in results], ["PASS"] * len(FIXTURES))

    def test_non_utf8_transcoding_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            create_fixture(root)
            for name, original in FIXTURES.items():
                (root / name).write_bytes(expected_bytes(original))
            (root / "windows-1252.txt").write_bytes("caf�\r\nUPDATED\r\n".encode("utf-8"))
            result = next(result for result in score_fixture(root) if result.name == "windows-1252.txt")
            self.assertEqual(result.status, "FAIL")
            self.assertIn("replacement-character", result.detail)

    def test_added_final_newline_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            create_fixture(root)
            for name, original in FIXTURES.items():
                (root / name).write_bytes(expected_bytes(original))
            path = root / "no-final-newline.txt"
            path.write_bytes(path.read_bytes() + b"\n")
            result = next(result for result in score_fixture(root) if result.name == path.name)
            self.assertEqual(result.status, "FAIL")
            self.assertIn("final newline", result.detail)

    def test_existing_directory_is_not_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            root.mkdir()
            with self.assertRaises(FileExistsError):
                create_fixture(root)

    def test_stale_write_rejection_preserves_concurrent_edit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "stale"
            create_stale_fixture(root)
            inject_concurrent_change(root)
            result = score_stale_fixture(root)
            self.assertEqual((result.status, result.outcome), ("PASS", "REJECTED"))

    def test_stale_write_merge_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "stale"
            create_stale_fixture(root)
            inject_concurrent_change(root)
            (root / "stale-write.txt").write_bytes(STALE_MERGED)
            result = score_stale_fixture(root)
            self.assertEqual((result.status, result.outcome), ("PASS", "MERGED"))

    def test_stale_overwrite_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "stale"
            create_stale_fixture(root)
            inject_concurrent_change(root)
            (root / "stale-write.txt").write_bytes(STALE_OVERWRITE)
            result = score_stale_fixture(root)
            self.assertEqual((result.status, result.outcome), ("FAIL", "STALE_OVERWRITE"))


if __name__ == "__main__":
    unittest.main()
