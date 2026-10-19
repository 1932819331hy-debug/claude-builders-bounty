# Claude Code Bash safety hook

A small Python standard-library `PreToolUse` hook that denies a limited set of destructive Bash commands before Claude Code runs them. It leaves ordinary commands to Claude Code's normal permission flow.

## Install

From this directory, run one command:

```sh
python3 install.py
```

The installer copies `command_guard.py` to `~/.claude/hooks/command_guard.py` and merges a `PreToolUse` / `Bash` entry into `~/.claude/settings.json`. Existing settings and hook groups are preserved, and the installer refuses unsafe symlink or conflicting hook paths. It does not configure project-level settings. Review the installer and resulting settings before using it. Restart Claude Code after installation. The configuration sets `onFailure: "block"` so a missing, failed, or timed-out command hook fails closed; current Claude Code documentation says this field requires Claude Code v2.1.295 or later.

## What it checks

- `rm` with both a recursive option (`-r`, `-R`, `--recursive`) and a force option (`-f`, `--force`), including combined short flags
- `git push` with `--force`, `-f`, or `--force-with-lease`
- `DROP TABLE` and `TRUNCATE` in direct SQL arguments to common clients (`psql`, `mysql`, `mariadb`, `sqlite3`, `sqlcmd`, and `duckdb`)
- `DELETE FROM` without an outer `WHERE` in those recognized SQL inputs; a `WHERE` inside a comment, quoted value, or nested subquery does not count
- Static SQL in simple `echo`/`printf` pipelines and literal here-documents sent to a recognized client, including SQLite's `-cmd` option

The hook understands common shell command separators, a small set of transparent launchers (`sudo`, `env`, `command`, `exec`, and similar), `bash/sh -c`, `eval`, and command substitutions. Unknown SQL stdin sources, including arbitrary pipelines and input redirections to recognized clients, are denied when they cannot be statically checked. Detection is intentionally bounded and is not a full Bash or SQL parser.

## Block behavior and logs

Claude Code sends hook input as JSON on stdin, including `tool_name`, `tool_input.command`, and `cwd`. For a block, this hook writes a clear reason to stderr and exits with code 2, which current Claude Code hooks documentation specifies as blocking a `PreToolUse` tool call. On a normal command it exits 0 with empty output, leaving the usual permission checks in effect. The hook never emits an `allow` decision.

Blocked attempts are written as JSON Lines to `~/.claude/hooks/blocked.log`, with a UTC timestamp, attempted command, project path, and reason. The log file is created with mode `0600`; the path is fixed and is not derived from the incoming project path. Password-, token-, secret-, key-, and bearer-shaped values are redacted heuristically, command and project strings are length-limited, and control characters are escaped. Redaction is best-effort, so the log is not a safe place for arbitrary secrets. Retention is bounded to 1 MiB; when full, the file is truncated to retain the newest blocked attempt and mark that truncation occurred. If logging fails, the command is still denied and Claude receives a log-failure notice.

## Limits

This is defense in depth, not a sandbox or a guarantee that dangerous operations cannot happen. It only examines Claude Code `Bash` tool input. It does not provide a complete shell interpreter, and obfuscated or dynamically generated commands, shell functions and aliases, unrecognized wrappers, other shells/tools, direct file/database APIs, SQL loaded through client-specific file flags, interactive database sessions, and unsupported SQL clients may bypass these checks. Complex quoting or shell syntax can also lead to conservative blocks or missed cases. Keep Claude Code permissions and operating-system safeguards enabled, and review commands that affect important data.

## Tests

Tests use command strings and JSON fixtures; they never run the fixture commands or install into the real `~/.claude` directory.

```sh
python3 -m unittest -v
```

## Protocol references

- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks): `PreToolUse` input fields, command-hook output, exit code 2 blocking behavior, and `onFailure`
- [Issue #3 acceptance criteria](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3)
