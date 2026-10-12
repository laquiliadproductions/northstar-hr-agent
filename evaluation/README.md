# Section 9 Evaluation

This directory contains the evaluation set and measured results for the
Northstar Analytics Agentic RAG application.

## Evaluation artifacts

- `northstar_section9_evaluation_set.json` contains 25 machine-readable
  cases with gold answers and expected agent behavior.
- `results/section9_final_report.json` is the consolidated grading
  summary.
- `results/section9_consolidated_final_results.json` contains successful,
  provenance-linked observations for all 25 evaluation cases.
- `results/section9_consolidated_partial_results.json` is an intermediate
  coverage record containing successful observations for 23 cases before
  the two remaining cases were completed.
- `results/section9_ablation_results.json` compares retrieval `top_k=3`
  and `top_k=5`.
- `results/section9_tool_retry_results.json` records targeted workflow
  retries.
- `results/section9_rate_limit_stress_results.json` and
  `results/section9_rate_limit_paced_results.json` preserve operational
  evidence from attempts interrupted when the external model quota was
  exhausted.

## Scoring interpretation

A completed response is scored as pass or fail using the documented
answer and agent-behavior criteria. An attempt that cannot produce a
completed response because of a confirmed external provider quota,
rate limit, timeout, or connectivity failure is classified as
`Not Scored`. The case is rerun when service becomes available.

Operationally interrupted attempts remain preserved as system-reliability
and safe-handling evidence. They are not counted as incorrect answers and
are excluded from final answer-quality and agent-behavior denominators.

The 71.49% gold-answer partial match is a supplementary similarity
measure, not an answer-correctness rate. It measures overlap between the
model-generated response and concise gold wording. Semantically equivalent
wording, citations, explanatory context, and required policy qualifications
can reduce lexical overlap.

Excellent answer accuracy is demonstrated by all 25 cases meeting their
case-specific pass criteria and by 100% groundedness, citation accuracy,
tool-selection accuracy, workflow completion, clarification or escalation
accuracy, and action safety across their applicable cases.

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

The automated test suite passes 63 tests. The final consolidated results
contain successful, provenance-linked observations for all 25 evaluation
cases, with a final pass rate of 100%. Earlier quota-limited runs remain
preserved as operational-interruption and safe-handling evidence.
