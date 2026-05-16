Run mutation testing on lines changed since the base branch.

Arguments: $ARGUMENTS (optional base branch name, default: `main`; optional flag `--fix`)
Example: `main --fix` or just `--fix` (base defaults to `main`)

Steps:
1. Parse $ARGUMENTS: strip `--fix` if present (note whether it was set), use the remaining first word as the base branch, or `main` if empty.
2. Run `git diff <base>...HEAD -- src/ipres/` from the repo root. If the output is empty, report "No changes in src/ipres/ compared to <base>" and stop.
3. Save the patch to a temp file, e.g. `/tmp/muttest-diff.patch`.
4. Run `source .venv/bin/activate && mutmut run --use-patch-file /tmp/muttest-diff.patch`.
5. Run `mutmut results` and capture the output.
6. For each surviving mutant, run `mutmut show <id>` to display the diff.
7. Delete the temp patch file.
8. Classify each survivor:
   - **Fixable**: the mutant changes observable behaviour and a test can distinguish it from the original.
   - **Equivalent**: the mutant is functionally identical for all reachable inputs.

If `--fix` is NOT set: report a summary with the classification for each survivor (including which files were in the diff) and stop.

If `--fix` IS set, act on the classification:
- **Fixable**: write a focused pytest function in the appropriate test file (`tests/<Module>Tests.py` or `tests/test_<module>.py`) that fails on the mutant and passes on the original. Follow the existing test style in that file. Use a concrete minimal example — compute the expected result by hand and document the reasoning in the test's docstring.
- **Equivalent**: add `# pragma: no mutate` to the exact source line(s) that were mutated (in `src/ipres/`). Do not add a comment explaining why — the pragma is self-documenting in this context.
After all fixes are applied, report what was done (tests added, pragmas added) and which mutants remain equivalent.
