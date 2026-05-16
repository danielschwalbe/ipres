Run full mutation testing on all modules in `src/ipres/`.

Arguments: $ARGUMENTS (optional flag `--fix`)

Steps:
1. Run `source .venv/bin/activate && mutmut run` from the repo root.
2. Run `mutmut results` and capture the output.
3. For each surviving mutant, run `mutmut show <id>` to display the diff.
4. Classify each survivor:
   - **Fixable**: the mutant changes observable behaviour and a test can distinguish it from the original.
   - **Equivalent**: the mutant is functionally identical for all reachable inputs (e.g. `P <= 0` → `P < 0` when `P=0` already returns zeros).

If `--fix` is NOT set: report a summary with the classification for each survivor and stop.

If `--fix` IS set, act on the classification:
- **Fixable**: write a focused pytest function in the appropriate test file (`tests/<Module>Tests.py` or `tests/test_<module>.py`) that fails on the mutant and passes on the original. Follow the existing test style in that file. Use a concrete minimal example — compute the expected result by hand and document the reasoning in the test's docstring.
- **Equivalent**: add `# pragma: no mutate` to the exact source line(s) that were mutated (in `src/ipres/`). Do not add a comment explaining why — the pragma is self-documenting in this context.
After all fixes are applied, report what was done (tests added, pragmas added) and which mutants remain equivalent.