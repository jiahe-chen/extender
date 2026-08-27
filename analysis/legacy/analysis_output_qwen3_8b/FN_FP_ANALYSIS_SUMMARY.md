# False Negative (FN) and False Positive (FP) Analysis Summary

## 📊 Overview

This analysis examines where each approach (diff_eval, two_agent, langgraph) makes mistakes - specifically looking at **False Negatives** (missed detections) and **False Positives** (incorrect detections).

---

## 🎯 Key Findings

### Overall Error Rates

| Approach | Total Examples | Correct | Incorrect | Error Rate |
|----------|---------------|---------|-----------|------------|
| **langgraph** | 1200 | 661 (55.08%) | 539 (44.92%) | 44.92% |
| **two_agent** | 1200 | 595 (49.58%) | 605 (50.42%) | 50.42% |
| **diff_eval** | 240 | 112 (46.67%) | 128 (53.33%) | **53.33%** |

---

## 🔴 False Negatives (FN) - Missed Detections

### FN Rate by Violation Type

| Violation | diff_eval | langgraph | two_agent | Worst Performer |
|-----------|-----------|-----------|-----------|-----------------|
| **LSP** | **93.75%** (45/48) | 81.25% (195/240) | 81.25% (195/240) | **diff_eval** 🔴 |
| **ISP** | 22.92% (11/48) | **61.25%** (147/240) | **61.25%** (147/240) | langgraph/two_agent |
| **DIP** | 52.08% (25/48) | 58.33% (140/240) | **70.00%** (168/240) | **two_agent** 🔴 |
| **SRP** | 52.08% (25/48) | **10.83%** (26/240) | 10.83% (26/240) | diff_eval |
| **OCP** | 45.83% (22/48) | 40.42% (97/240) | **6.25%** (15/240) | diff_eval |

### Critical Insights - Where FNs Occur

#### diff_eval (qwen3-8b):
- **🔴 LSP is catastrophic**: 93.75% FN rate (45 out of 48 missed!)
  - **34 LSP cases misclassified as ISP** (most common error)
  - Fails across ALL difficulty levels (13 EASY, 16 MODERATE, 16 HARD)

- **✅ ISP is strong**: Only 22.92% FN rate (best among all approaches)
  - Only 11 out of 48 missed
  - Most errors on HARD cases (9 out of 11)

- **⚠️ DIP & SRP moderate**: ~52% FN rate
  - DIP: Often confused with ISP (13 cases) or SRP (8 cases)
  - SRP: Often confused with DIP (16 cases)

#### langgraph:
- **🔴 LSP is very difficult**: 81.25% FN rate
  - 76 LSP cases misclassified as SRP
  - 33 LSP cases misclassified as OCP

- **🔴 DIP is problematic**: 58.33% FN rate
  - 118 DIP cases misclassified as SRP (massive confusion!)

- **✅ SRP is excellent**: Only 10.83% FN rate
  - Best performance on SRP among all approaches

#### two_agent:
- **🔴 LSP is very difficult**: 81.25% FN rate (same as langgraph)

- **🔴 DIP is worst**: 70.00% FN rate (highest among all)
  - Major confusion with other violation types

- **✅ OCP is excellent**: Only 6.25% FN rate
  - Best OCP detection among all approaches

---

## 🟡 False Positives (FP) - Incorrect Detections

### FP Count by Violation Type

| Violation | diff_eval FP | langgraph FP | two_agent FP | Notes |
|-----------|--------------|--------------|--------------|-------|
| **ISP** | **58** | 11 | 28 | diff_eval over-detects ISP |
| **DIP** | 43 | 59 | **199** | two_agent massively over-detects DIP |
| **SRP** | 13 | **171** | 26 | langgraph over-detects SRP |
| **OCP** | 8 | 15 | 143 | diff_eval rarely over-detects OCP |

### Critical Insights - Where FPs Occur

#### diff_eval (qwen3-8b):
- **🔴 ISP over-detection**: 58 false positives
  - **34 are actually LSP** (LSP → ISP confusion)
  - 13 are actually DIP
  - This explains why ISP has high accuracy but also high FP

- **⚠️ DIP over-detection**: 43 false positives
  - 16 are actually SRP
  - 12 are actually OCP

#### langgraph:
- **🔴 SRP over-detection**: 171 false positives (massive!)
  - 76 are actually LSP
  - 118 are actually DIP
  - Tends to default to SRP when uncertain

- **⚠️ DIP over-detection**: 59 false positives
  - 22 are actually LSP
  - 20 are actually OCP

#### two_agent:
- **🔴 DIP over-detection**: 199 false positives (extreme!)
  - Massive tendency to classify everything as DIP
  - 93 are actually LSP
  - 52 are actually SRP

---

## 📈 FN/FP by Difficulty Level

### False Negative Rate by Difficulty

| Difficulty | diff_eval | langgraph | two_agent |
|------------|-----------|-----------|-----------|
| **EASY** | 26.25% (21/80) | 33.25% (80/240) | 45.00% (108/240) |
| **MODERATE** | 52.50% (42/80) | 47.75% (115/240) | 50.50% (121/240) |
| **HARD** | **81.25%** (65/80) | 53.75% (129/240) | 55.75% (134/240) |

**Key Insight**:
- **diff_eval struggles dramatically with HARD cases** (81.25% FN rate)
- langgraph and two_agent maintain more consistent performance across difficulty levels
- diff_eval's performance degrades sharply: EASY (26%) → MODERATE (53%) → HARD (81%)

---

## 🎯 Most Common Misclassifications

### diff_eval (qwen3-8b) Top 10:
1. **LSP → ISP**: 34 times 🔴 (Critical issue)
2. **SRP → DIP**: 16 times
3. **DIP → ISP**: 13 times
4. **OCP → DIP**: 12 times
5. **ISP → DIP**: 9 times
6. **DIP → SRP**: 8 times
7. **LSP → DIP**: 6 times
8. **SRP → ISP**: 6 times
9. **OCP → ISP**: 5 times
10. **OCP → SRP**: 5 times

**Pattern**: LSP is almost always misclassified as ISP (34/45 = 75.6% of LSP errors)

### langgraph Top Misclassifications:
1. **DIP → SRP**: 118 times 🔴 (Massive confusion)
2. **LSP → SRP**: 76 times 🔴
3. **ISP → SRP**: 47 times
4. **LSP → OCP**: 33 times

**Pattern**: Strong bias toward classifying things as SRP

### two_agent Top Misclassifications:
1. **LSP → DIP**: 93 times 🔴 (Massive confusion)
2. **SRP → DIP**: 52 times 🔴
3. **OCP → DIP**: 49 times 🔴
4. **ISP → DIP**: 44 times 🔴

**Pattern**: Extreme bias toward classifying things as DIP

---

## 💡 Actionable Insights

### For diff_eval (qwen3-8b):

**Critical Issues to Fix:**
1. **LSP → ISP confusion** (34 cases)
   - The model cannot distinguish between Liskov Substitution and Interface Segregation
   - Need better prompts/examples to differentiate these two principles
   - Consider adding specific LSP detection patterns

2. **HARD case performance** (81.25% FN rate)
   - Model gives up too easily on complex cases
   - Need more sophisticated reasoning for difficult violations
   - Consider increasing iteration count or adding specialized hard-case handling

3. **Processing time** (135.95s avg)
   - While fixing accuracy, also optimize speed
   - Current approach is impractical for production

**Strengths to Leverage:**
1. **ISP detection** (77.08% accuracy, only 22.92% FN)
   - Study what makes ISP detection successful
   - Apply similar patterns to other violation types

2. **EASY case performance** (73.75% accuracy)
   - The model works well on straightforward cases
   - Focus improvement efforts on MODERATE and HARD cases

### For langgraph:

**Issues:**
1. **SRP over-detection** (171 FPs)
   - Too aggressive in classifying things as SRP
   - Need better discrimination between SRP and other violations

2. **DIP → SRP confusion** (118 cases)
   - Major conceptual confusion between these principles

### For two_agent:

**Issues:**
1. **DIP over-detection** (199 FPs)
   - Extreme bias toward DIP classification
   - Need to reduce false positive rate

2. **DIP detection accuracy** (70% FN rate)
   - Paradoxically, while over-detecting DIP, also missing many real DIP cases

---

## 📊 Visualization Files Generated

1. **[13_confusion_matrix_comparison.png](analysis_output_qwen3_8b/13_confusion_matrix_comparison.png)** - Side-by-side confusion matrices (counts)
2. **[14_confusion_matrix_comparison_normalized.png](analysis_output_qwen3_8b/14_confusion_matrix_comparison_normalized.png)** - Normalized confusion matrices (percentages)
3. **[15_fn_fp_comparison.png](analysis_output_qwen3_8b/15_fn_fp_comparison.png)** - FN and FP counts by violation type
4. **[16_fn_fp_by_difficulty.png](analysis_output_qwen3_8b/16_fn_fp_by_difficulty.png)** - FN/FP rates by difficulty level
5. **[17_misclassification_matrix_diff_eval.png](analysis_output_qwen3_8b/17_misclassification_matrix_diff_eval.png)** - Where diff_eval's FNs go
6. **[17_misclassification_matrix_langgraph.png](analysis_output_qwen3_8b/17_misclassification_matrix_langgraph.png)** - Where langgraph's FNs go
7. **[17_misclassification_matrix_two_agent.png](analysis_output_qwen3_8b/17_misclassification_matrix_two_agent.png)** - Where two_agent's FNs go

---

## 🎓 Conclusion

### The LSP Problem
**All three approaches struggle with LSP detection**, but diff_eval is by far the worst (93.75% FN rate). This suggests LSP violations are inherently difficult to detect, possibly because:
- LSP violations are subtle and require deep understanding of inheritance hierarchies
- LSP is often confused with ISP (interface-related issues)
- The examples may not provide enough context to distinguish LSP from other violations

### Approach-Specific Biases
- **diff_eval**: Biased toward ISP (58 FPs), struggles with LSP
- **langgraph**: Biased toward SRP (171 FPs), good at SRP detection
- **two_agent**: Biased toward DIP (199 FPs), good at OCP detection

### Recommendation
**Use an ensemble approach** that combines:
- diff_eval for ISP detection (77.08% accuracy)
- two_agent for OCP detection (93.75% accuracy)
- langgraph for SRP detection (89.17% accuracy)
- **All approaches need improvement on LSP** (best is langgraph at 31.25%)

---

**Analysis Date:** 2026-01-27
**Total Examples Analyzed:** 2,640 (240 diff_eval + 1200 langgraph + 1200 two_agent)
