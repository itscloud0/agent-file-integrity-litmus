# Agent File Integrity Litmus

Agent File Integrity Litmus is a byte-preservation test for coding-agent edits. It helps coding-agent client authors and teams with CRLF, BOM, legacy encodings, Unicode, or executable scripts verify that a tiny agent edit does not corrupt unrelated bytes or file metadata.

## Install

Python 3.10 or newer is required. To install the public `v0.2.0` release without cloning the repository:

```bash
python3 -m pip install "git+https://github.com/itscloud0/agent-file-integrity-litmus.git@v0.2.0"
```

For an isolated command-line install with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install "git+https://github.com/itscloud0/agent-file-integrity-litmus.git@v0.2.0"
```

For a one-off fixture run without a persistent install:

```bash
uvx --from "git+https://github.com/itscloud0/agent-file-integrity-litmus.git@v0.2.0" \
  agent-file-integrity-litmus fixtures
```

## Quickstart

```bash
PYTHONPATH=src python -m agent_file_integrity_litmus.cli create /tmp/file-integrity-fixture
```

Give the printed prompt to the coding agent being tested, with `/tmp/file-integrity-fixture` as its workspace. Then score the result:

```bash
PYTHONPATH=src python -m agent_file_integrity_litmus.cli score /tmp/file-integrity-fixture --format markdown
```

The scorer checks exact bytes and POSIX file mode. It does not rely on a model judge. Each result keeps the expected and actual SHA-256 hashes and reports an outcome: `PASS` for an exact edit, `SKIPPED` when `TARGET` is unchanged, `CORRUPTED` when the edit changed bytes or mode incorrectly, or `MISSING` when a fixture file is absent.

To run a supported client in a fresh disposable Git repository, explicitly opt in to live model calls:

```bash
PYTHONPATH=src python -m agent_file_integrity_litmus.cli run \
  --adapter codex-cli \
  --allow-live \
  --repetitions 2 \
  --output /tmp/file-integrity-codex
```

Use `opencode-cli` for opencode. Each run stores client stdout/stderr, an exact score report, and post-edit file snapshots under `artifacts/`. Without `--allow-live`, the command makes no model call.

## Stale-write fixture

The separate stale-write oracle distinguishes safe rejection or merge from overwriting a newer external edit:

```bash
PYTHONPATH=src python -m agent_file_integrity_litmus.cli stale-create /tmp/stale-write
# Let the client read stale-write.txt, but pause before its write.
PYTHONPATH=src python -m agent_file_integrity_litmus.cli stale-inject /tmp/stale-write
# Let the client attempt TARGET -> UPDATED, then score it.
PYTHONPATH=src python -m agent_file_integrity_litmus.cli stale-score /tmp/stale-write
```

`REJECTED` and `MERGED` pass. `STALE_OVERWRITE` fails. The guarded live adapters do not automate the pause because Codex and opencode do not expose a stable hook between native read and write calls.

## What it catches

- CRLF-to-LF drift on edited lines;
- lost or duplicated UTF-8 BOMs;
- legacy-encoding transcoding and replacement characters;
- unrelated Unicode changes;
- added or removed final newlines;
- executable-bit changes.

## Current status

The deterministic byte-safe baseline passes 6/6. In two native-tool-only runs, opencode 1.16.2 scored 5/6 both times but alternated between safely skipping and corrupting Windows-1252. Codex CLI 0.144.4 scored 2/6 and 3/6: CRLF and no-final-newline failed both times, Windows-1252 remained unedited, and executable-script handling varied. See `BENCHMARK.md` for the exact matrix.

## Limitations

- Guarded adapters currently cover Codex CLI and opencode CLI only and consume the user's configured model quota when explicitly enabled.
- Automated live-client stale-write races are out of scope until a client exposes a stable read/write hook.
- Live client validation ran on macOS. Windows-host client behavior remains unverified.
- The executable-mode check is skipped on Windows.
- This tool diagnoses behavior. It does not repair a coding-agent client or replace Git attributes, EditorConfig, or an encoding-safe edit tool.

## Comparison

Git attributes and EditorConfig declare repository policy. Client-specific edit implementations and safe edit servers try to preserve files. Agent File Integrity Litmus instead runs the same byte-level fixture contract against real coding-agent edit paths so their behavior can be compared and turned into reproducible bug evidence.
