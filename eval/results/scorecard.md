# SentinelOps Agent Evaluation Scorecard

This scorecard records performance benchmarks (Accuracy, Tool Call Count, Hallucination Rate, Time-to-Diagnosis) of the Ollama-backed SRE agents against synthetic fault injections.

| Timestamp | Scenario | Accuracy | Tool Calls | Hallucinations | Time to Diagnosis |
| --- | --- | --- | --- | --- | --- |
| 2026-07-12 21:56:14 | config_regression | FAIL | 0 | 0 | 6.0s |
| 2026-07-12 21:56:24 | security_group | FAIL | 0 | 0 | 6.0s |
| 2026-07-12 22:00:03 | config_regression | PASS | 0 | 0 | 46.3s |
| 2026-07-12 22:00:27 | security_group | FAIL | 0 | 0 | 16.1s |
| 2026-07-12 22:46:17 | config_regression | PASS | 5 | 0 | 26.2s |
| 2026-07-12 22:46:54 | security_group | PASS | 5 | 0 | 28.2s |
| 2026-10-03 17:03:40 | config_regression | PASS | 6 | 0 | 40.2s |
| 2026-10-03 17:04:24 | security_group | PASS | 6 | 0 | 38.2s |
