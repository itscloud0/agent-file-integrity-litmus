# Validation Results

## 2026-07-14 targeted probe

Environment: macOS; Codex CLI 0.144.1; opencode 1.16.2.

| Path | Result | Observation |
| --- | --- | --- |
| Direct byte replacement | 6/6 PASS | Meaningful deterministic baseline. |
| opencode native Read/Edit | 5/6 | Windows-1252 `e9` became UTF-8 `ef bf bd`; other byte/mode oracles passed. |
| Codex native apply_patch | intermediate failure | Could not read Windows-1252; edited CRLF line became LF; final newline was added. |
| Codex final agent outcome | 6/6 PASS | Agent detected violations and repaired them with Vim binary-mode commands. |

The fixture distinguishes native tool behavior from the final agent outcome. Raw disposable workspaces remain local under `.automation/tmp/flagship-file-integrity-validation/` for this run only.

Concurrent-write rejection and Windows-host behavior remain `UNKNOWN`.

## 2026-07-15 guarded adapter matrix

Environment: macOS; Codex CLI 0.144.4; opencode 1.16.2. Each adapter ran twice in a fresh committed disposable repository. The prompt allowed only built-in read/edit/patch tools and prohibited shell, scripts, and binary-editor recovery.

| Adapter run | Exact score | Stable observations |
| --- | --- | --- |
| Codex run 1 | 2/6 | CRLF became LF, final newline was added, Windows-1252 and executable remained unedited. |
| Codex run 2 | 3/6 | Same CRLF, final-newline, and Windows-1252 failures; executable passed. |
| opencode run 1 | 5/6 | Windows-1252 was safely skipped after the client detected replacement-character decoding. |
| opencode run 2 | 5/6 | Windows-1252 was edited and corrupted from one legacy byte to UTF-8 replacement-character bytes. |

All four client processes returned zero. The exact-byte oracle caught failures that the final client messages sometimes described as successful. Raw stdout, stderr, reports, and exact post-edit snapshots are stored under `validation/adapter-results/2026-07-15/`.

The deterministic stale-write oracle passes its rejection baseline and distinguishes `REJECTED`, `MERGED`, and `STALE_OVERWRITE`. Automated live-client timing remains out of scope because neither adapter exposes a stable hook between native read and write calls.

Remote package, byte-oracle, and stale-oracle validation passed on Windows for Python 3.10–3.12 in GitHub Actions run `29433201249`. Live Windows-host Codex/opencode behavior remains `UNKNOWN` and is not claimed by v0.1.

## 2026-08-29 Codex CLI 0.150.1 benchmark refresh

Selection evidence: the installed Codex CLI advanced from the version in the public benchmark (`0.144.4`) to `0.150.1`. The repository's demand ledger records repeated public reports of coding-agent encoding, line-ending, and stale-write damage; refreshing the current client gives maintainers and client authors current reproducible diagnostic evidence.

User outcome: a maintainer testing Codex CLI 0.150.1 on macOS can reproduce the exact byte-level result and distinguish corruption from a safe skipped edit without relying on a model success message or text diff.

Environment and method: macOS; Codex CLI 0.150.1; two fresh disposable Git repositories; the guarded prompt allowed only built-in read/edit/patch tools and prohibited shell, scripts, and binary-editor recovery. Both client processes returned zero.

| Run | Exact score | Observations |
| --- | --- | --- |
| Codex run 1 | 2/6 | CRLF became LF; a final newline was added; Windows-1252 and the executable edit were safely left unchanged. |
| Codex run 2 | 3/6 | CRLF became LF; a final newline was added; Windows-1252 was safely left unchanged; the executable edit passed. |

The deterministic byte oracle therefore confirms current Codex 0.150.1 failures for CRLF and final-newline preservation, safe skips for Windows-1252 in both runs, and variable executable handling. This evidence is bounded to the tested client/version/host and does not claim behavior for other clients, models, or operating systems. No new opencode result, Windows-host result, automatic stale-write race, or product-adoption claim is made. Raw captures remain local and the reviewed summary is committed.
