# Structural Analysis ON vs OFF — Comparison Report
## diff_eval workflow | qwen3-8b | Top-2 strategy | n=240

---

## 1. Configuration Difference

| Parameter | run_top2 (Struct ON) | run_structure_off_top2 (Struct OFF) |
|-----------|----------------------|--------------------------------------|
| `structural_analysis_enabled` | **True** | **False** |
| `selection_method` | ranking_llm | ranking_llm |
| `max_examples_per_violation` | None (all) | 5 |
| `total_iterations` | 5 | 5 |
| `temperature` | 0.0 | 0.0 |

> **Note**: `max_examples_per_violation=5` in Struct OFF limits the dataset to 5 examples per violation
> type for prompt/context construction, while Struct ON uses all available examples. Both runs operate
> on the same 240 evaluation examples.

---

## 2. Overall Metrics

| Metric | Struct ON | Struct OFF | Δ (OFF − ON) |
|--------|-----------|------------|--------------|
| Pos-1 Accuracy | 60.42% | 58.33% | -2.08pp |
| Hit@2 Accuracy | 83.75% | 85.42% | +1.67pp |
| Hit@any (all_checks) | 92.50% | 93.75% | +1.25pp |
| Pos-2 Only Contribution | 23.33% | 27.08% | +3.75pp |
| MRR@2 | 0.7208 | 0.7188 | -0.0021 |
| Mean Processing Time | 150.6s | 173.0s | +22.4s |

**Key finding**: Removing structural analysis yields **+1.67pp Hit@2** improvement despite
being a simpler pipeline. However, it comes at the cost of +22.4s/example mean processing time.

---

## 3. Hit@2 by Violation Type

| Violation | ON Pos-1 | ON Hit@2 | OFF Pos-1 | OFF Hit@2 | Δ Hit@2 |
|-----------|----------|----------|-----------|-----------|---------|
| SRP | 45.8% | 81.2% | 37.5% | 85.4% | ↑ +4.2pp |
| OCP | 37.5% | 70.8% | 37.5% | 68.8% | ↓ -2.1pp |
| LSP | 75.0% | 77.1% | 75.0% | 77.1% | — +0.0pp |
| ISP | 62.5% | 93.8% | 52.1% | 95.8% | ↑ +2.1pp |
| DIP | 81.2% | 95.8% | 89.6% | 100.0% | ↑ +4.2pp |

**Notable findings**:
- **DIP**: Struct OFF achieves **100% Hit@2** (vs 95.8% for ON), a perfect score — removing structural
  analysis actually benefits DIP detection significantly.
- **OCP**: Struct OFF is slightly worse (-2.1pp), and this is concentrated in HARD examples where
  structural code patterns help disambiguate OCP vs DIP violations.
- **SRP, ISP**: Small improvements with Struct OFF.

---

## 4. Hit@2 by Difficulty Level

| Difficulty | ON Hit@2 | OFF Hit@2 | Δ Hit@2 | N |
|-----------|---------|----------|---------|---|
| EASY | 85.0% | 88.8% | ↑ +3.7pp | 80 |
| MODERATE | 86.2% | 90.0% | ↑ +3.7pp | 80 |
| HARD | 80.0% | 77.5% | ↓ -2.5pp | 80 |

**Key finding**: HARD examples are slightly worse under Struct OFF (-2.5pp), while EASY and MODERATE
improve. This suggests structural analysis provides the most value for complex, hard-to-distinguish violations.

---

## 5. Per-Example Agreement Analysis

| Category | Count | % |
|----------|-------|---|
| Both correct (Hit@2) | 194 | 80.8% |
| Struct ON only correct | 7 | 2.9% |
| Struct OFF only correct | 11 | 4.6% |
| Both wrong | 28 | 11.7% |

**Flip analysis by violation type**:

| Violation | OFF gained | OFF lost | Net |
|-----------|-----------|---------|-----|
| SRP | 3 | 1 | +2 |
| OCP | 5 | 6 | -1 |
| LSP | 0 | 0 | +0 |
| ISP | 1 | 0 | +1 |
| DIP | 2 | 0 | +2 |


---

## 6. Multi-Violation Detection

Without structural analysis, the model detects **more** violations per example on average:

| Stat | Struct ON | Struct OFF |
|------|-----------|------------|
| Mean detected violations | 3.64 | 4.07 |
| Examples with 5/5 detected | 36 | 88 |
| Examples with 0 detected | 4 | 3 |

Struct OFF detects an average of **4.07** violations per example vs
**3.64** for Struct ON. This higher detection rate improves Hit@2
by putting the correct answer in the top-2 more often — but hurts Pos-1 accuracy as the first prediction
is less precise.

---

## 7. Processing Time

| Stat | Struct ON | Struct OFF | Δ |
|------|-----------|------------|---|
| Mean (s) | 150.6 | 173.0 | +22.4 |
| Median (s) | 129.1 | 143.0 | — |

**Counterintuitively, Struct OFF is slower (+22.4s mean)**. This is likely because:
1. With structural analysis disabled, the model relies more heavily on LLM-based reasoning at each iteration.
2. Structural analysis may prune certain code paths early, reducing total token generation.
3. The `max_examples_per_violation=5` setting in Struct OFF could affect internal context management.

---

## 8. Language Comparison

| Language | Struct ON Hit@2 | Struct OFF Hit@2 | Δ | N |
|----------|----------------|-----------------|---|---|
| C# | 95.8% | 95.8% | +0.0pp | 24 |
| CSHARP | 83.3% | 86.1% | +2.8pp | 36 |
| JAVA | 83.3% | 85.0% | +1.7pp | 60 |
| KOTLIN | 91.7% | 88.3% | -3.3pp | 60 |
| PYTHON | 71.7% | 78.3% | +6.7pp | 60 |


**Python gains the most** (+6.7pp) from removing structural analysis, while Kotlin loses slightly (-3.3pp).
C# and CSHARP (same language, split across notations) show no change.

---

## 9. Conclusions

1. **Overall**: Removing structural analysis yields a modest Hit@2 improvement (+1.67pp: 83.75% → 85.42%),
   with perfect DIP detection (100%) being the standout result.

2. **Trade-off — precision vs recall**: Struct OFF detects more violations per example (mean 4.07 vs 3.64),
   improving Hit@2 coverage but lowering Pos-1 accuracy (-2.08pp). The model becomes more "generous"
   in its detections without structural constraints.

3. **HARD examples regress**: Structural analysis genuinely helps for difficult code where subtle
   structural patterns distinguish OCP from DIP violations (-2.5pp Hit@2 for HARD in Struct OFF).

4. **OCP suffers the most**: 6 OCP HARD cases are rescued by structural analysis. The heatmap shows
   Struct ON makes fewer DIP-for-OCP misclassifications in HARD examples.

5. **DIP benefits most**: Structural analysis appears to add noise to DIP detection in some cases —
   removing it achieves a perfect 100% Hit@2 for DIP.

6. **Processing time paradox**: Struct OFF is slower (+22.4s/example), suggesting structural analysis
   helps prune the solution space rather than adding computation.

7. **Recommendation**: For maximum Hit@2 performance across all SOLID principles, Struct OFF is slightly
   preferred (+1.67pp) and simpler to deploy. For OCP and HARD examples specifically, structural analysis
   provides meaningful value. A hybrid approach — structural analysis only for complex/hard examples or
   only during OCP evaluation — could capture the best of both.

---

## 10. Generated Artifacts

### Visualizations
- `00_summary_dashboard.png` — Full metrics dashboard
- `01_overall_metrics.png` — Overall metrics bar comparison
- `02_hit2_by_violation.png` — Hit@2 by SOLID principle
- `03_hit2_by_difficulty.png` — Hit@2 by difficulty level
- `04_flip_analysis.png` — Per-example agreement & flip analysis
- `05_multi_detection.png` — Multi-violation detection distribution
- `06_per_class_metrics.png` — Per-class F1, Precision, Recall (Pos-1)
- `07_prediction_bias_heatmap.png` — Prediction confusion matrices
- `08_processing_time.png` — Processing time distribution
- `09_heatmap_violation_difficulty.png` — Violation × Difficulty heatmap
- `10_language_comparison.png` — Hit@2 by programming language

### Data Files
- `detailed_comparison.csv` — Per-example results for both runs
- `by_violation.csv` — Aggregated metrics by violation type
- `by_difficulty.csv` — Aggregated metrics by difficulty level
