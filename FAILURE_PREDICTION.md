# Failure prediction with LSTM and a hybrid RNN

Status: proposed next phase, not a trained or deployed feature. The repository contains no suitable labeled training dataset or validated model artifact. Prediction should remain advisory until tested on representative task histories.

## Define the target first

At each completed node, estimate the probability that the current run will finish with a workflow failure. Code execution failure followed by successful reflection is a recovered run, not a failed run. Track it as a separate auxiliary outcome. Treat user rejection and disconnected/cancelled runs separately from workflow failures so the model does not learn authorization or transport behavior as execution quality.

Use one run identifier per attempt. `task_id` alone is insufficient because tasks can be rerun. Each prediction consumes only the prefix available at that moment; final status and future errors must never enter the input features.

## Data collection

Persist append-only events for node starts/completions: run ID, sequence index, node type, elapsed duration, retry count, structured error category, tool type, configured provider/model, approval state, and schema version. Duration is only known after completion. Label closed runs with success, workflow failure, interruption, or rejection. Current task rows store the latest snapshot; reflection rows cover errors only. Neither captures complete event sequences or all historical attempts.

Avoid storing raw goals, generated code, credentials, or full exception traces in the training dataset. Use structured metadata and explicitly selected numeric features. Derive provider error categories from actual responses rather than scanning private prompt text.

## Compare candidates

| Candidate | Inputs | Purpose |
|---|---|---|
| Constant prevalence / rules | Existing stage and error counts | Establish a useful minimum baseline |
| Logistic regression / boosted trees | Prefix aggregates and static metadata | Check whether sequence modeling is necessary |
| Small unidirectional LSTM | Ordered event prefixes | Model changes in error/retry/duration patterns |
| Hybrid LSTM + dense branch | LSTM sequence representation plus static metadata | Combine progression with configuration context |

An LSTM is already an RNN variant. Here, “hybrid RNN” means an LSTM sequence branch combined with a small dense branch for static metadata, followed by a calibrated binary output. Stacking vanilla RNN and LSTM layers has no established benefit for this repository. Do not use a bidirectional model over future events for online predictions.

Proposed architecture: node/tool/error embeddings and scaled observed numeric features → masked LSTM → concatenate static configuration features → dense layer → failure probability. Keep model size small because the current workflow is short and bounded.

## Evaluation and release criteria

Split runs chronologically, group all prefixes of a run together, and keep related attempts/template families from leaking across splits. Fit encoders/scalers on training data only. Reserve a later untouched test period. Assess failure-class precision-recall, recall at an acceptable false-alert rate, probability calibration, inference latency, and results per provider/task category. Accuracy alone can look excellent when nearly all tasks succeed.

Choose a minimum dataset size based on observed failure prevalence and uncertainty, not an arbitrary number of total tasks. If there are too few failures, continue gathering data and report the model as unavailable. Synthetic data can test plumbing, but cannot establish predictive performance.

Run the candidate in shadow mode, compare with baselines, and select warning thresholds on validation data. The serving response should include availability, probability, prediction point, model version, and training cutoff. Show “insufficient data” or “prediction unavailable” when appropriate. Do not let the model bypass human approval or automatically increase retries/cost budgets.

## References

- Hochreiter and Schmidhuber, Long Short-Term Memory: https://www.bioinf.jku.at/publications/older/2604.pdf
- scikit-learn, time-ordered evaluation: https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html (use chronological run grouping; task events are not necessarily equally spaced).
