# Analysis Report: qwen3.5-9b (Local) vs Cloud — Top-2 Strategy
## Dataset: 240 examples | Model: qwen3.5-9b (local) / qwen3.5 (cloud)

---

## 1. Overall Performance Summary

| Config | N | Top-1 Acc | Hit@2 | MRR@2 | Macro-F1 (Top-1) | Macro-F1 (Resolved) | Set-F1@2 | Pos-2 Share | Mean Time (s) |
|--------|---|-----------|-------|-------|-----------------|---------------------|----------|-------------|----------------|
| Diff Eval (9B) | 240 | 70.42% | 87.92% | 0.7917 | 0.7128 | 0.8881 | 0.5875 | 17.50% | 421.9s |
| Single Agent (9B) | 240 | 57.50% | 70.00% | 0.6375 | 0.5747 | 0.6991 | 0.4819 | 12.50% | 9.7s |
| Two Agent (9B) | 240 | 42.08% | 55.83% | 0.4896 | 0.4224 | 0.5759 | 0.4486 | 13.75% | 54.1s |
| Single Agent (Cloud) | 240 | 75.83% | 95.83% | 0.8583 | 0.7404 | 0.9602 | 0.6403 | 20.00% | 5.0s |

---

## 2. Performance by Difficulty Level

| Config | Difficulty | N | Top-1 Acc | Hit@2 | MRR@2 | Pos-2 Share |
|--------|-----------|---|-----------|-------|-------|-------------|
| Diff Eval (9B) | EASY | 80 | 85.00% | 92.50% | 0.8875 | 7.50% |
| Diff Eval (9B) | MODERATE | 80 | 68.75% | 91.25% | 0.8000 | 22.50% |
| Diff Eval (9B) | HARD | 80 | 57.50% | 80.00% | 0.6875 | 22.50% |
| Single Agent (9B) | EASY | 80 | 65.00% | 75.00% | 0.7000 | 10.00% |
| Single Agent (9B) | MODERATE | 80 | 61.25% | 71.25% | 0.6625 | 10.00% |
| Single Agent (9B) | HARD | 80 | 46.25% | 63.75% | 0.5500 | 17.50% |
| Two Agent (9B) | EASY | 80 | 56.25% | 60.00% | 0.5813 | 3.75% |
| Two Agent (9B) | MODERATE | 80 | 36.25% | 62.50% | 0.4938 | 26.25% |
| Two Agent (9B) | HARD | 80 | 33.75% | 45.00% | 0.3937 | 11.25% |
| Single Agent (Cloud) | EASY | 80 | 75.00% | 93.75% | 0.8438 | 18.75% |
| Single Agent (Cloud) | MODERATE | 80 | 78.75% | 98.75% | 0.8875 | 20.00% |
| Single Agent (Cloud) | HARD | 80 | 73.75% | 95.00% | 0.8438 | 21.25% |

---

## 3. Performance by Violation Type

| Config | Violation | N | Top-1 Acc | Hit@2 | MRR@2 | Pos-2 Share |
|--------|-----------|---|-----------|-------|-------|-------------|
| Diff Eval (9B) | SRP | 48 | 87.50% | 95.83% | 0.9167 | 8.33% |
| Diff Eval (9B) | OCP | 48 | 58.33% | 72.92% | 0.6562 | 14.58% |
| Diff Eval (9B) | LSP | 48 | 72.92% | 81.25% | 0.7708 | 8.33% |
| Diff Eval (9B) | ISP | 48 | 72.92% | 97.92% | 0.8542 | 25.00% |
| Diff Eval (9B) | DIP | 48 | 60.42% | 91.67% | 0.7604 | 31.25% |
| Single Agent (9B) | SRP | 48 | 81.25% | 81.25% | 0.8125 | 0.00% |
| Single Agent (9B) | OCP | 48 | 70.83% | 97.92% | 0.8438 | 27.08% |
| Single Agent (9B) | LSP | 48 | 66.67% | 66.67% | 0.6667 | 0.00% |
| Single Agent (9B) | ISP | 48 | 52.08% | 83.33% | 0.6771 | 31.25% |
| Single Agent (9B) | DIP | 48 | 16.67% | 20.83% | 0.1875 | 4.17% |
| Two Agent (9B) | SRP | 48 | 77.08% | 87.50% | 0.8229 | 10.42% |
| Two Agent (9B) | OCP | 48 | 62.50% | 81.25% | 0.7188 | 18.75% |
| Two Agent (9B) | LSP | 48 | 27.08% | 33.33% | 0.3021 | 6.25% |
| Two Agent (9B) | ISP | 48 | 27.08% | 37.50% | 0.3229 | 10.42% |
| Two Agent (9B) | DIP | 48 | 16.67% | 39.58% | 0.2812 | 22.92% |
| Single Agent (Cloud) | SRP | 48 | 100.00% | 100.00% | 1.0000 | 0.00% |
| Single Agent (Cloud) | OCP | 48 | 97.92% | 97.92% | 0.9792 | 0.00% |
| Single Agent (Cloud) | LSP | 48 | 89.58% | 89.58% | 0.8958 | 0.00% |
| Single Agent (Cloud) | ISP | 48 | 39.58% | 100.00% | 0.6979 | 60.42% |
| Single Agent (Cloud) | DIP | 48 | 52.08% | 91.67% | 0.7188 | 39.58% |

---

## 4. Diff Eval — Per-Class Metrics (Top-1 Prediction)

| Class | Precision | Recall | F1 | TP | FP | FN |
|-------|-----------|--------|----|----|----|-----|
| SRP | 0.553 | 0.875 | 0.677 | 42 | 34 | 6 |
| OCP | 0.848 | 0.583 | 0.691 | 28 | 5 | 20 |
| LSP | 0.745 | 0.729 | 0.737 | 35 | 12 | 13 |
| ISP | 0.921 | 0.729 | 0.814 | 35 | 3 | 13 |
| DIP | 0.690 | 0.604 | 0.644 | 29 | 13 | 19 |

---

## 5. Multi-Violation Detection (Diff Eval)

- Examples with 2+ violations detected: **235/240** (97.9%)
- Ground truth detected anywhere in all_checks: **225/240** (93.8%)
- Ground truth in Top-2 predictions: **211/240** (87.9%)
- Detection gap (detected but not surfaced in Top-2): **14** (5.8%)