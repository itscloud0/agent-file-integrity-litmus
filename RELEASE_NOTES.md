# v0.2.0 release notes

Report classifications now distinguish an unchanged `TARGET` from a changed-but-corrupted fixture while retaining exact expected and actual SHA-256 hashes. Missing fixture files are reported explicitly as `MISSING`.

The JSON, Markdown, and adapter reports expose `PASS`, `SKIPPED`, `CORRUPTED`, or `MISSING` outcomes. The exit status remains failing for skipped, corrupted, or missing edits.

# v0.1.0 release notes

Initial release for exact byte-preservation testing of coding-agent edits.

Included:

- CRLF, UTF-8 BOM, Windows-1252, Unicode, no-final-newline, and executable-mode fixtures;
- deterministic JSON and Markdown scoring with byte-level failure diagnostics;
- guarded Codex CLI and opencode CLI adapters with explicit live-call opt-in;
- raw client capture and exact post-edit snapshots;
- a manual stale-write oracle that distinguishes rejection, merge, and stale overwrite;
- reproducible two-run Codex/opencode benchmark artifacts.

Known limitations:

- live client validation currently covers macOS only;
- automated live-client stale-write timing is not supported;
- executable-mode checks are skipped on Windows;
- the tool diagnoses client behavior and does not repair files or clients.
