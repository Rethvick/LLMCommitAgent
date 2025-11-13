import argparse
import os
import re
import subprocess
import sys
import requests
from typing import Optional

DEFAULT_MODEL = "openai/gpt-4.1-mini-2025-04-14"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"

CONVENTIONAL_TYPES = [
    "feat", "fix", "docs", "style", "refactor", "perf",
    "test", "chore", "build", "ci", "revert"
]

SYSTEM_PROMPT = (
    "You are Commit Message Agent. Generate a clean, accurate Conventional Commit message.\n\n"
    "Format:\n"
    "<type>(<scope>): <summary <=72 chars>\n"
    "\n"
    "<body up to 200 words, bullets allowed>\n"
    "\n"
    "<optional footer like Closes #123>\n\n"
    f"Types: {', '.join(CONVENTIONAL_TYPES)}.\n"
    "Use imperative mood.\n"
    "If tests were changed, mention in body.\n"
    "If diff has issue ID (#123 or ABC-123), include a footer.\n"
    "DO NOT repeat the diff.\n"
)

# --------------------------
# Git utilities
# --------------------------
def run_cmd(cmd: list[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return out.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def get_staged_diff(max_size=200_000) -> str:
    diff = run_cmd(["git", "diff", "--staged", "--no-color"])
    if not diff:
        diff = run_cmd(["git", "diff", "--no-color"])
    if not diff:
        return ""

    if len(diff) > max_size:
        names = run_cmd(["git", "diff", "--staged", "--name-status"])
        return "[TRUNCATED DIFF]\n" + names

    return diff.strip()

def get_diff_from_file(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# --------------------------
# Helpers
# --------------------------
def detect_issue_numbers(diff: str) -> Optional[str]:
    m = re.search(r"([A-Z]{2,}-\d+)|#\d+", diff)
    return m.group(0) if m else None

def sanitize(msg: str) -> str:
    if not msg:
        return ""
    lines = [l.rstrip() for l in msg.strip().splitlines()]
    if lines and len(lines[0]) > 120:
        lines[0] = lines[0][:117] + "..."
    return "\n".join(lines)

# --------------------------
# OpenRouter HTTP call
# --------------------------
def call_openrouter(prompt: str, model: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    url = f"{OPENROUTER_BASE}/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 500,
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=40)
    data = resp.json()

    if "choices" not in data:
        raise RuntimeError(str(data))

    return data["choices"][0]["message"]["content"].strip()

# --------------------------
# Commit message generation
# --------------------------
def generate_message(diff: str, model: str) -> str:
    if not diff.strip():
        return "chore: empty commit\n\nNo changes detected."

    issue = detect_issue_numbers(diff)
    prompt = "Git diff:\n" + diff
    if issue:
        prompt += f"\n\nIssue detected: {issue} (Add 'Closes {issue}' in footer)"

    response = call_openrouter(prompt, model)
    return sanitize(response)

# --------------------------
# CLI
# --------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff-file")
    parser.add_argument("--write-file")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    try:
        diff = get_diff_from_file(args.diff_file) if args.diff_file else get_staged_diff()
        message = generate_message(diff, args.model)
    except Exception as e:
        print("Error generating commit message:", e, file=sys.stderr)
        sys.exit(1)

    if args.write_file:
        with open(args.write_file, "w", encoding="utf-8") as f:
            f.write(message + "\n")
        print(f"Wrote commit message to {args.write_file}")
    else:
        print(message)

if __name__ == "__main__":
    main()
