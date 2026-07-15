# Security

Agent File Integrity Litmus creates disposable local files and can invoke configured Codex or opencode clients only with explicit `--allow-live` opt-in.

- Use adapter output directories that are safe for the agent to modify.
- Do not place secrets or production files in a fixture workspace.
- Review client stdout/stderr before sharing because a client may include local paths or environment-derived context.
- The tool does not send telemetry. Model/provider data handling is controlled by the invoked client.

Report security issues privately through the repository owner's GitHub security contact after publication. Do not include real credentials or private repository content in a report.
