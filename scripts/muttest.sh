#!/usr/bin/env bash
# Run mutation tests locally.
#
# Usage:
#   muttest.sh [all]              - mutate all modules in src/ipres/ (uses pyproject.toml config)
#   muttest.sh diff [base]        - mutate only lines changed vs base branch (default: main)
#   muttest.sh <path>             - mutate a specific file or directory
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    source "$REPO_ROOT/.venv/bin/activate"
fi

cd "$REPO_ROOT"

MODE="${1:-all}"

case "$MODE" in
    all)
        echo "Mutation testing: all modules in src/ipres/"
        mutmut run
        MUTMUT_EXIT=$?
        ;;
    diff)
        BASE="${2:-main}"
        PATCH_FILE=$(mktemp /tmp/muttest-XXXXXX.patch)
        trap "rm -f '$PATCH_FILE'" EXIT

        git diff "$BASE"...HEAD -- src/ipres/ > "$PATCH_FILE"

        if [[ ! -s "$PATCH_FILE" ]]; then
            echo "No changes in src/ipres/ compared to $BASE."
            exit 0
        fi

        CHANGED_FILES=$(git diff --name-only "$BASE"...HEAD -- src/ipres/ | tr '\n' ' ')
        echo "Mutation testing: changes vs $BASE"
        echo "Affected: $CHANGED_FILES"
        mutmut run --use-patch-file "$PATCH_FILE"
        MUTMUT_EXIT=$?
        ;;
    *)
        echo "Mutation testing: $MODE"
        mutmut run --paths-to-mutate "$MODE"
        MUTMUT_EXIT=$?
        ;;
esac

echo ""
mutmut results
exit $MUTMUT_EXIT
