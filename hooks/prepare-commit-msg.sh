#!/usr/bin/env bash
# Git hook: prepare-commit-msg
# Auto-generates AI commit message via commitdoc.py

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

if [ -n "$COMMIT_SOURCE" ]; then
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"

PROVIDER="${COMMITDOC_PROVIDER:-openrouter}"
MODEL="${COMMITDOC_MODEL:-gpt-4o-mini}"

python3 "$REPO_ROOT/commitdoc.py" \
  --provider "$PROVIDER" \
  --model "$MODEL" \
  --write-file "$COMMIT_MSG_FILE" || true

exit 0
