from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


MARKER = b"TARGET"
REPLACEMENT = b"UPDATED"

STALE_ORIGINAL = b"alpha\nTARGET\nversion=1\n"
STALE_CONCURRENT = b"alpha\nTARGET\nversion=2\n"
STALE_MERGED = b"alpha\nUPDATED\nversion=2\n"
STALE_OVERWRITE = b"alpha\nUPDATED\nversion=1\n"

FIXTURES: dict[str, bytes] = {
    "crlf.txt": b"alpha\r\nTARGET\r\nomega\r\n",
    "utf8-bom.txt": b"\xef\xbb\xbfalpha\nTARGET\nomega\n",
    "windows-1252.txt": b"caf\xe9\r\nTARGET\r\n",
    "unicode.txt": "Привет 🌍\nTARGET\nДо свидания\n".encode("utf-8"),
    "no-final-newline.txt": b"alpha\nTARGET",
    "executable.sh": b"#!/bin/sh\n# TARGET\nexit 0\n",
}

PROMPT = """Replace the ASCII token TARGET with UPDATED exactly once in each of these files:
crlf.txt, utf8-bom.txt, windows-1252.txt, unicode.txt, no-final-newline.txt, and executable.sh.
Preserve every other byte, each file's encoding and line endings, final-newline state, BOM, and executable mode.
Do not add files or install anything. Finish after the six edits."""


@dataclass(frozen=True)
class Result:
    name: str
    status: str
    outcome: str
    expected_sha256: str
    actual_sha256: str | None
    expected_mode: str
    actual_mode: str | None
    detail: str


@dataclass(frozen=True)
class StaleWriteResult:
    status: str
    outcome: str
    expected_snapshot_sha256: str
    actual_sha256: str | None
    detail: str


def expected_bytes(original: bytes) -> bytes:
    if original.count(MARKER) != 1:
        raise ValueError("fixture must contain exactly one marker")
    return original.replace(MARKER, REPLACEMENT, 1)


def create_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, dict[str, str]] = {}
    for name, original in FIXTURES.items():
        path = root / name
        path.write_bytes(original)
        expected_mode = 0o755 if name == "executable.sh" else 0o644
        path.chmod(expected_mode)
        manifest[name] = {
            "original_sha256": hashlib.sha256(original).hexdigest(),
            "expected_sha256": hashlib.sha256(expected_bytes(original)).hexdigest(),
            "expected_mode": f"{expected_mode:o}",
        }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def create_stale_fixture(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    (root / "stale-write.txt").write_bytes(STALE_ORIGINAL)
    manifest = {
        "snapshot_sha256": hashlib.sha256(STALE_ORIGINAL).hexdigest(),
        "concurrent_sha256": hashlib.sha256(STALE_CONCURRENT).hexdigest(),
        "merged_sha256": hashlib.sha256(STALE_MERGED).hexdigest(),
        "stale_overwrite_sha256": hashlib.sha256(STALE_OVERWRITE).hexdigest(),
    }
    (root / "stale-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def inject_concurrent_change(root: Path) -> None:
    path = root / "stale-write.txt"
    if path.read_bytes() != STALE_ORIGINAL:
        raise ValueError("stale-write fixture no longer matches its initial snapshot")
    path.write_bytes(STALE_CONCURRENT)


def score_stale_fixture(root: Path) -> StaleWriteResult:
    path = root / "stale-write.txt"
    snapshot_hash = hashlib.sha256(STALE_ORIGINAL).hexdigest()
    if not path.is_file():
        return StaleWriteResult("FAIL", "MISSING", snapshot_hash, None, "fixture file is missing")
    actual = path.read_bytes()
    actual_hash = hashlib.sha256(actual).hexdigest()
    if actual == STALE_CONCURRENT:
        return StaleWriteResult(
            "PASS",
            "REJECTED",
            snapshot_hash,
            actual_hash,
            "stale write was rejected and the concurrent edit was preserved",
        )
    if actual == STALE_MERGED:
        return StaleWriteResult(
            "PASS",
            "MERGED",
            snapshot_hash,
            actual_hash,
            "requested edit was rebased onto the concurrent edit",
        )
    if actual == STALE_OVERWRITE:
        return StaleWriteResult(
            "FAIL",
            "STALE_OVERWRITE",
            snapshot_hash,
            actual_hash,
            "requested edit overwrote the newer external version",
        )
    return StaleWriteResult(
        "FAIL",
        "UNEXPECTED",
        snapshot_hash,
        actual_hash,
        "bytes match neither rejection, merge, nor the known stale-overwrite outcome",
    )


def score_fixture(root: Path) -> list[Result]:
    results = []
    for name, original in FIXTURES.items():
        path = root / name
        expected = expected_bytes(original)
        expected_hash = hashlib.sha256(expected).hexdigest()
        expected_mode = 0o755 if name == "executable.sh" else 0o644
        if not path.is_file():
            results.append(
                Result(
                    name=name,
                    status="FAIL",
                    outcome="MISSING",
                    expected_sha256=expected_hash,
                    actual_sha256=None,
                    expected_mode=f"{expected_mode:o}",
                    actual_mode=None,
                    detail="file is missing",
                )
            )
            continue

        actual = path.read_bytes()
        actual_hash = hashlib.sha256(actual).hexdigest()
        actual_mode = path.stat().st_mode & 0o777
        bytes_ok = actual == expected
        mode_ok = os.name == "nt" or actual_mode == expected_mode
        details = []
        if not bytes_ok:
            details.extend(_describe_byte_difference(expected, actual))
        if not mode_ok:
            details.append(f"mode changed from {expected_mode:o} to {actual_mode:o}")
        status = "PASS" if bytes_ok and mode_ok else "FAIL"
        if bytes_ok and mode_ok:
            outcome = "PASS"
        elif actual == original and mode_ok:
            outcome = "SKIPPED"
            details.append("TARGET was unchanged; edit appears to have been skipped")
        else:
            outcome = "CORRUPTED"
        results.append(
            Result(
                name=name,
                status=status,
                outcome=outcome,
                expected_sha256=expected_hash,
                actual_sha256=actual_hash,
                expected_mode=f"{expected_mode:o}",
                actual_mode=f"{actual_mode:o}",
                detail="exact byte and mode match" if not details else "; ".join(details),
            )
        )
    return results


def _describe_byte_difference(expected: bytes, actual: bytes) -> list[str]:
    details = []
    if b"\xef\xbf\xbd" in actual and b"\xef\xbf\xbd" not in expected:
        details.append("UTF-8 replacement-character bytes were introduced")
    if expected.count(b"\r\n") > actual.count(b"\r\n"):
        details.append("one or more CRLF sequences were lost")
    if not expected.endswith((b"\n", b"\r")) and actual.endswith((b"\n", b"\r")):
        details.append("a final newline was added")
    if expected.startswith(b"\xef\xbb\xbf") and not actual.startswith(b"\xef\xbb\xbf"):
        details.append("the UTF-8 BOM was removed")
    common = min(len(expected), len(actual))
    offset = next((index for index in range(common) if expected[index] != actual[index]), common)
    expected_byte = f"{expected[offset]:02x}" if offset < len(expected) else "EOF"
    actual_byte = f"{actual[offset]:02x}" if offset < len(actual) else "EOF"
    details.append(
        f"first difference at byte {offset}: expected {expected_byte}, actual {actual_byte}; "
        f"length {len(expected)} -> {len(actual)}"
    )
    return details


def render_json(results: list[Result], root: Path) -> str:
    payload = {
        "fixture_root": str(root.resolve()),
        "passed": sum(result.status == "PASS" for result in results),
        "total": len(results),
        "results": [asdict(result) for result in results],
    }
    return json.dumps(payload, indent=2)


def render_markdown(results: list[Result], root: Path) -> str:
    lines = [
        "# Agent file integrity result",
        "",
        f"Fixture root: `{root.resolve()}`",
        "",
        "| Fixture | Status | Outcome | Detail |",
        "| --- | --- | --- | --- |",
    ]
    lines.extend(f"| `{result.name}` | {result.status} | {result.outcome} | {result.detail} |" for result in results)
    passed = sum(result.status == "PASS" for result in results)
    lines.extend(["", f"Result: {passed}/{len(results)} fixtures passed.", ""])
    return "\n".join(lines)
