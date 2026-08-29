# Reproducible benchmark

## Contract

The baseline and both live adapters receive the same six-file request. A result passes only when `TARGET` becomes `UPDATED` and every other byte plus the POSIX mode matches the oracle. No model judge or text-diff heuristic is used.

## 2026-07-15 matrix

| Path | Run 1 | Run 2 | Reproducible finding |
| --- | --- | --- | --- |
| Direct byte replacement | 6/6 | 6/6 | Deterministic oracle baseline. |
| Codex CLI 0.144.4 native tools | 2/6 | 3/6 | CRLF, final-newline, and non-UTF-8 handling failed both runs; executable handling varied. |
| opencode 1.16.2 native tools | 5/6 | 5/6 | Windows-1252 failed both runs; one run skipped safely and one introduced replacement-character bytes. |

The runs used fresh disposable Git repositories and prohibited shell or binary-editor recovery. Raw results live in `validation/adapter-results/2026-07-15/`.

## 2026-08-29 Codex CLI refresh

Environment: macOS; Codex CLI 0.150.1. The same guarded native-tool prompt ran twice in fresh disposable repositories; both client processes returned zero.

| Path | Run 1 | Run 2 | Two-run observation |
| --- | --- | --- | --- |
| Direct byte replacement | 6/6 | 6/6 | Deterministic oracle baseline. |
| Codex CLI 0.150.1 native tools | 2/6 | 3/6 | CRLF became LF and a final newline was added in both runs; Windows-1252 was safely skipped in both; executable handling varied. |

This refresh confirms the current tested Codex version still exposes exact byte-preservation failures. It is evidence for Codex CLI 0.150.1 on macOS, not a general claim about other clients, versions, operating systems, or models. The opencode 1.16.2 result remains the two-run result recorded above; no new opencode result is claimed.

## Workflow improvement

The CLI replaces manual hex dumps, line-ending inspection, mode checks, and cross-run note-taking with one exact report containing hashes, byte offsets, length changes, and recognizable CRLF, EOF, BOM, and replacement-character failure reasons. The benchmark does not claim measured time savings; it demonstrates a reproducible diagnostic that ordinary Git text diffs and client success messages did not provide.

## Known failures

- Codex 0.144.4 native patching could not edit the Windows-1252 fixture and normalized CRLF/final-newline state; the 0.150.1 refresh safely skipped Windows-1252 but still normalized CRLF/final-newline state.
- Codex handling of the executable fixture differed between identical runs.
- opencode produced the same total score twice but did not consistently choose safe rejection over transcoding.
- Windows-host client behavior and automated live-client stale-write races are not validated.
