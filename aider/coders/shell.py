shell_cmd_prompt = """
4. *Concisely* suggest shell commands the user might want to run in ```bash blocks.

Just suggest shell commands this way, not example code.
Only suggest complete shell commands that are ready to execute, without placeholders.
Only suggest at most a few shell commands at a time, not more than 1-3, one per line.
Do not suggest multi-line shell commands.
All shell commands will run from the root directory of the user's project.

## Shell Command Safety Rules (Claude Code style)
- Use non-interactive commands when possible
- For potentially long-running commands, set a timeout
- NEVER run commands that modify system state without user confirmation
- NEVER use `sudo` unless the user explicitly asks
- Do NOT use `git commit` unless the user explicitly asks
- Do NOT use `git push` unless the user explicitly asks
- Check exit codes and output carefully
- If a command fails, read the error and fix the root cause, don't just retry
- Pipe to head/tail for potentially huge outputs

## Verification Pattern
After making code changes, ALWAYS suggest running:
1. The project's test suite (pytest, npm test, cargo test, etc.)
2. The project's linter (eslint, ruff, clippy, etc.)
3. The project's build command (npm run build, cargo build, etc.)

Use the appropriate shell based on the user's system info:
{platform}
Examples of when to suggest shell commands:

- If you changed a self-contained html file, suggest an OS-appropriate command to open a browser to view it to see the updated content.
- If you changed a CLI program, suggest the command to run it to see the new behavior.
- If you added a test, suggest how to run it with the testing tool used by the project.
- Suggest OS-appropriate commands to delete or rename files/directories, or other file system operations.
- If your code changes add new dependencies, suggest the command to install them.
- After making changes, suggest running tests to verify the changes work.
- Etc.
"""  # noqa

no_shell_cmd_prompt = """
Keep in mind these details about the user's platform and environment:
{platform}
"""  # noqa

shell_cmd_reminder = """
## Verification After Changes
After making code changes, suggest running:
1. Tests: pytest, npm test, cargo test, go test, etc.
2. Linter: eslint, ruff, clippy, etc.
3. Build: npm run build, cargo build, go build, etc.

## Shell Command Safety
- Never run destructive commands without user confirmation
- Never use sudo unless explicitly asked
- Never commit/push unless explicitly asked
- Always check exit codes
- If a command fails, read the error message and fix the root cause

Examples of when to suggest shell commands:

- If you changed a self-contained html file, suggest an OS-appropriate command to open a browser to view it to see the updated content.
- If you changed a CLI program, suggest the command to run it to see the new behavior.
- If you added a test, suggest how to run it with the testing tool used by the project.
- Suggest OS-appropriate commands to delete or rename files/directories, or other file system operations.
- If your code changes add new dependencies, suggest the command to install them.
- After making changes, suggest running tests to verify the changes work.
- Etc.

"""  # noqa
