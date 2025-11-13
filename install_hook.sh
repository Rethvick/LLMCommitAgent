#!/usr/bin/env bash
set -e

HOOK_DIR=".git/hooks"
HOOK_FILE="$HOOK_DIR/prepare-commit-msg"

if [ ! -d ".git" ]; then
  echo "Not a git repository. Run this from the root of the repo."
  exit 1
fi

mkdir -p "$HOOK_DIR"

cat > "$HOOK_FILE" <<'EOF'
#!/usr/bin/env bash
# Git hook: prepare-commit-msg
# Auto-generate commit message using commitdoc.py

COMMIT_MSG_FILE="$1"
COMMIT_SOURCE="$2"

# Skip for merge commits, template commits, or if message already exists
if [ -n "$COMMIT_SOURCE" ]; then
  exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"

# You can override provider globally:
#   export COMMITDOC_PROVIDER=openrouter
PROVIDER="${COMMITDOC_PROVIDER:-openrouter}"

# Default model for OpenRouter; override if needed:
#   export COMMITDOC_MODEL="anthropic/claude-3.5-sonnet"
MODEL="${COMMITDOC_MODEL:-gpt-4o-mini}"

python3 "$REPO_ROOT/commitdoc.py" \
  --provider "$PROVIDER" \
  --model "$MODEL" \
  --write-file "$COMMIT_MSG_FILE" || exit 0

exit 0
EOF

chmod +x "$HOOK_FILE"
echo "prepare-commit-msg hook installed successfully."
