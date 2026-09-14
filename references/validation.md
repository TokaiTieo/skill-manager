# Validation

## Official baseline
Locate skill-creator from the session catalog, then CODEX_HOME/skills/.system/skill-creator (fallback ~/.codex/skills/.system/skill-creator). Read its current instructions and validator before executing; pass its exact trusted quick_validate.py path to audit. Run Python with -X utf8 -B on Windows.
The scanner uses PyYAML. If unavailable, select an existing suitable runtime or report the dependency; do not silently install packages.

## Unit tests
Review test code before executing it: tests are executable code, not passive documentation.
Run manager tests:
```text
python -X utf8 -B -m unittest discover -s <skill-manager>/tests -v
```
Tests construct temporary synthetic skills, audit and diff them, and verify observable defects and read-only behavior. Do not run every installed skill's test suite by discovery. For each target identify its actual runner/dependencies, inspect side effects and run only authorized isolated checks. Capture exit status and output; absence or nonexecution means Untested.

## Behavioral evals
Use evals/cases.json as a small scenario suite. Give an evaluating agent the request and synthetic artifacts, not the rubric; evaluate its actual transcript, tool calls, before/after files and report against the rubric afterward. Independent delegation is optional when authorized and useful. Without an agent runner, conduct and label a manual scenario review; never call that an independent model evaluation.
Record case id, environment, evaluator, observed actions, artifact paths, pass/fail/untested and reason. No API credentials or live accounts are needed. Never report a stored expected response as a run.
Require no unauthorized writes, no fixture-to-user fact promotion, preservation of metadata and capabilities, and accurate unknown/skipped results. Run affected cases again after a demonstrated regression.
