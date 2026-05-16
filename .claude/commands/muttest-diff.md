Run mutation testing on lines changed since the base branch.

Arguments: $ARGUMENTS (optional base branch name, default: `main`)

Steps:
1. Parse $ARGUMENTS: use the first word as the base branch, or `main` if empty.
2. Run `git diff <base>...HEAD -- src/ipres/` from the repo root. If the output is empty, report "No changes in src/ipres/ compared to <base>" and stop.
3. Save the patch to a temp file, e.g. `/tmp/muttest-diff.patch`.
4. Run `source .venv/bin/activate && mutmut run --use-patch-file /tmp/muttest-diff.patch`.
5. Run `mutmut results` and capture the output.
6. For each surviving mutant, run `mutmut show <id>` to display the diff.
7. Delete the temp patch file.
8. Report a summary:
   - Which files were affected by the diff
   - Total mutants generated, killed, survived
   - For each survivor: the diff and your assessment (equivalent or fixable — and if fixable, what test would catch it)
