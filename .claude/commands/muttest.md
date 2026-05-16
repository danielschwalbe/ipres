Run full mutation testing on all modules in `src/ipres/`.

Steps:
1. Run `source .venv/bin/activate && mutmut run` from the repo root.
2. Run `mutmut results` and capture the output.
3. For each surviving mutant, run `mutmut show <id>` to display the diff.
4. Report a summary:
   - Total mutants generated, killed, survived, timed out
   - For each survivor: the diff and your assessment (equivalent or fixable — and if fixable, what test would catch it)