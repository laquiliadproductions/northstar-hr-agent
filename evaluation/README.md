# Section 9 Evaluation

This directory contains the evaluation set and measured results for the
Northstar Analytics Agentic RAG application.

## Evaluation artifacts

- `northstar_section9_evaluation_set.json` contains 25 machine-readable
  cases with gold answers and expected agent behavior.
- `results/section9_final_report.json` is the consolidated grading
  summary.
- `results/section9_consolidated_partial_results.json` contains the
  latest successful observation for 23 cases and safe rate-limit
  failures for TOOL-05 and SAFE-02.
- `results/section9_ablation_results.json` compares retrieval `top_k=3`
  and `top_k=5`.
- `results/section9_tool_retry_results.json` records targeted workflow
  retries.
- `results/section9_rate_limit_stress_results.json` and
  `results/section9_rate_limit_paced_results.json` document safe
  behavior when the external model quota was exhausted.

## Commands

Run local automated tests with `pytest -q`.

Run a complete paced baseline with:

`python scripts/run_evaluation.py --mode baseline --delay-seconds 35 --service-retries 1 --retry-backoff-seconds 75 --output evaluation/results/section9_baseline_results.json`

Run selected cases with a separate output path so the baseline is not
overwritten:

`python scripts/run_evaluation.py --mode baseline --case-id TOOL-05 --case-id SAFE-02 --delay-seconds 35 --output evaluation/results/section9_final_retry_results.json`

Run the retrieval comparison with:

`python scripts/run_evaluation.py --mode ablation --output evaluation/results/section9_ablation_results.json`

## Current status

The automated test suite passes 62 tests. Saved results contain
successful observations for 23 of 25 evaluation cases. TOOL-05 and
SAFE-02 remain pending because the Groq free-tier daily token quota was
exhausted. The application returned safe service-unavailable responses
without unauthorized actions.
