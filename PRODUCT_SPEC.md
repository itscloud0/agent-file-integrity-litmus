# Agent File Integrity Litmus — Product Spec

## User and job

Target users are coding-agent client authors, extension authors, Windows-heavy teams, and maintainers of repositories containing CRLF, BOM, legacy encodings, non-ASCII text, or executable scripts.

The job is to determine in 5–30 minutes whether a coding agent can make a small requested edit without changing unrelated bytes, line endings, encoding, BOM, trailing-newline state, or file mode.

## Product boundary

The primary surface is a local CLI that creates harmless fixtures and scores the edited files against exact byte and mode oracles. The user runs the same printed prompt through the coding-agent client being evaluated, then runs `score`.

This is not an editor, formatter, linter, Git policy manager, generic coding benchmark, or runtime guard. Client-specific upstream fixes remain upstream work.

## Version 0.1 scope

- CRLF preservation.
- UTF-8 BOM preservation.
- Windows-1252 byte preservation.
- UTF-8 non-ASCII preservation.
- final-newline preservation.
- executable-mode preservation on POSIX.
- JSON and Markdown scoring output.

The stale-write surface is a deterministic three-step fixture and oracle. Live adapter automation is intentionally out of scope for v0.1 because neither tested client exposes a stable hook between its read and write tool calls; sleep or shell choreography would test the workaround rather than the client edit path.

## Success and kill criteria

Success requires deterministic local scoring, at least three unrelated real-world cases, two client ecosystems, a meaningful byte-safe baseline, documented failures, and a demonstrated workflow improvement over manual hex/diff inspection. The stale-write oracle must distinguish rejection, merge, and overwrite, but v0.1 does not claim automated live-client race coverage.

Kill or narrow the project if existing client-neutral suites cover the same byte/file-mode matrix, adapters require brittle UI automation, results mostly measure model prompt-following instead of client edit paths, or the useful outcome belongs only in upstream regression tests.
