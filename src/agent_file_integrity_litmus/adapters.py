from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from .core import FIXTURES, PROMPT, Result, create_fixture, render_markdown, score_fixture


NATIVE_EDIT_PROMPT = (
    PROMPT
    + "\nUse only the client's built-in file read and edit or patch tools. "
    "Do not use shell commands, scripts, Python, Perl, Vim, sed, or binary editors. "
    "If a file cannot be edited safely, leave it unchanged and explain the limitation."
)


@dataclass(frozen=True)
class Completed:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


@dataclass(frozen=True)
class AdapterRun:
    adapter: str
    client_version: str
    command: list[str]
    returncode: int
    timed_out: bool
    workspace: Path
    artifacts: Path
    results: list[Result]

    @property
    def passed(self) -> int:
        return sum(result.status == "PASS" for result in self.results)


def run_adapter(
    adapter: str,
    output: Path,
    *,
    codex_bin: str = "codex",
    opencode_bin: str = "opencode",
    timeout_seconds: int = 600,
) -> AdapterRun:
    if adapter not in {"codex-cli", "opencode-cli"}:
        raise ValueError(f"unsupported adapter: {adapter}")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    create_fixture(workspace)
    artifacts.mkdir(parents=True)
    _init_repository(workspace)

    if adapter == "codex-cli":
        executable = _resolve_executable(codex_bin)
        last_message = artifacts / "last-message.txt"
        command = [
            executable,
            "exec",
            "--ephemeral",
            "--ignore-user-config",
            "-C",
            str(workspace.resolve()),
            "-s",
            "workspace-write",
            "--json",
            "-o",
            str(last_message.resolve()),
            "-",
        ]
        completed = _run(command, input_text=NATIVE_EDIT_PROMPT, timeout_seconds=timeout_seconds)
    elif adapter == "opencode-cli":
        executable = _resolve_executable(opencode_bin)
        command = [
            executable,
            "run",
            "--dir",
            str(workspace.resolve()),
            "--pure",
            "--format",
            "json",
            "--dangerously-skip-permissions",
            NATIVE_EDIT_PROMPT,
        ]
        completed = _run(command, input_text=None, timeout_seconds=timeout_seconds)
        (artifacts / "last-message.txt").write_text(
            _extract_opencode_text(completed.stdout), encoding="utf-8"
        )
    (artifacts / "stdout.jsonl").write_text(completed.stdout, encoding="utf-8")
    (artifacts / "stderr.txt").write_text(completed.stderr, encoding="utf-8")
    run = AdapterRun(
        adapter=adapter,
        client_version=_client_version(executable),
        command=command,
        returncode=completed.returncode,
        timed_out=completed.timed_out,
        workspace=workspace.resolve(),
        artifacts=artifacts.resolve(),
        results=score_fixture(workspace),
    )
    _snapshot_post_edit_files(workspace, artifacts)
    _write_report(run)
    return run


def _resolve_executable(value: str) -> str:
    resolved = value if os.sep in value else shutil.which(value)
    if resolved is None or not Path(resolved).is_file():
        raise FileNotFoundError(f"executable not found: {value}")
    return str(Path(resolved).resolve())


def _run(command: list[str], *, input_text: str | None, timeout_seconds: int) -> Completed:
    env = os.environ.copy()
    env.setdefault("TERM", "xterm-256color")
    try:
        completed = subprocess.run(
            command,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
        return Completed(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired as exc:
        return Completed(
            124,
            _coerce_text(exc.stdout),
            _coerce_text(exc.stderr) + f"\nTimed out after {timeout_seconds} seconds.\n",
            timed_out=True,
        )


def _client_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    text = completed.stdout.strip() or completed.stderr.strip()
    return text.splitlines()[0] if text else "unknown"


def _init_repository(workspace: Path) -> None:
    (workspace / ".gitignore").write_text(".litmus/\n", encoding="utf-8")
    commands = [
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        [
            "git",
            "-c",
            "user.name=agent-file-integrity-litmus",
            "-c",
            "user.email=agent-file-integrity-litmus@example.invalid",
            "commit",
            "-q",
            "-m",
            "litmus baseline",
        ],
    ]
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=workspace,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"{' '.join(command)} failed: {completed.stderr.strip()}")


def _write_report(run: AdapterRun) -> None:
    payload = {
        "adapter": run.adapter,
        "client_version": run.client_version,
        "command": run.command,
        "returncode": run.returncode,
        "timed_out": run.timed_out,
        "workspace": str(run.workspace),
        "passed": run.passed,
        "total": len(run.results),
        "results": [asdict(result) for result in run.results],
    }
    (run.artifacts / "report.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    heading = (
        "# Adapter result\n\n"
        f"Adapter: `{run.adapter}`  \n"
        f"Client: `{run.client_version}`  \n"
        f"Process return code: `{run.returncode}`  \n"
        f"Timed out: `{'yes' if run.timed_out else 'no'}`\n\n"
    )
    (run.artifacts / "report.md").write_text(
        heading + render_markdown(run.results, run.workspace), encoding="utf-8"
    )


def _snapshot_post_edit_files(workspace: Path, artifacts: Path) -> None:
    post = artifacts / "post-edit-files"
    post.mkdir()
    for name in FIXTURES:
        source = workspace / name
        if source.is_file():
            shutil.copy2(source, post / name)


def _extract_opencode_text(stdout: str) -> str:
    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        part = event.get("part")
        if not isinstance(part, dict) or part.get("type") != "text":
            continue
        text = part.get("text")
        if isinstance(text, str):
            messages.append(text)
    return ("\n".join(messages).strip() or stdout.strip()) + "\n"


def _coerce_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
