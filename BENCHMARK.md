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

## Workflow improvement

The CLI replaces manual hex dumps, line-ending inspection, mode checks, and cross-run note-taking with one exact report containing hashes, byte offsets, length changes, and recognizable CRLF, EOF, BOM, and replacement-character failure reasons. The benchmark does not claim measured time savings; it demonstrates a reproducible diagnostic that ordinary Git text diffs and client success messages did not provide.

## Known failures

- Codex native patching could not edit the Windows-1252 fixture and normalized CRLF/final-newline state.
- Codex handling of the executable fixture differed between identical runs.
- opencode produced the same total score twice but did not consistently choose safe rejection over transcoding.
- Windows-host client behavior and automated live-client stale-write races are not validated.
