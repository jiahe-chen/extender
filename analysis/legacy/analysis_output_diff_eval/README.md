# Diff_Eval Detection Results - Complete Analysis

## Overview

This directory contains a comprehensive analysis of SOLID principle violation detection results for the **diff_eval** workflow, following the same analytical framework used for the two_agent analysis.

**Analysis Date:** 2026-01-11
**Total Examples:** 480
**Models Evaluated:** 2 (deepseek-r1-8b, qwen3-8b)
**Violation Types:** SRP, OCP, LSP, ISP, DIP
**Programming Languages:** Java, Python, Kotlin, C#
**Difficulty Levels:** EASY, MODERATE, HARD

---

## Key Findings

### 1. Overall Model Performance

| Model | Accuracy | Correct/Total | Avg Processing Time |
|-------|----------|---------------|---------------------|
| **deepseek-r1-8b** | **27.08%** | 65/240 | 147.21s |
| **qwen3-8b** | **23.75%** | 57/240 | 135.97s |

**Key Observations:**
- Both models show **significantly lower accuracy** compared to the two_agent workflow
- deepseek-r1-8b performs slightly better (+3.33% absolute)
- qwen3-8b is faster but less accurate
- Overall accuracy is concerning (< 30% for both models)

---

### 2. Violation Type Detection Performance

| Violation Type | Overall Accuracy | Easiest Model | Hardest Model |
|----------------|------------------|---------------|---------------|
| **ISP** | **76.04%** | deepseek-r1-8b (87.50%) | qwen3-8b (64.58%) |
| **DIP** | **41.67%** | qwen3-8b (47.92%) | deepseek-r1-8b (35.42%) |
| **LSP** | **5.21%** | qwen3-8b (6.25%) | deepseek-r1-8b (4.17%) |
| **OCP** | **3.12%** | deepseek-r1-8b (6.25%) | qwen3-8b (0.00%) |
| **SRP** | **1.04%** | deepseek-r1-8b (2.08%) | qwen3-8b (0.00%) |

**Critical Insights:**
- **ISP (Interface Segregation Principle)** is by far the easiest to detect (76.04%)
- **SRP (Single Responsibility Principle)** is nearly impossible to detect (1.04%)
- **OCP (Open-Closed Principle)** detection is also extremely poor (3.12%)
- There's a massive performance gap between ISP and other violation types
- qwen3-8b **completely failed** to detect SRP and OCP violations (0%)

---

### 3. Difficulty Level Analysis

| Difficulty | Accuracy | Examples | Correct |
|------------|----------|----------|---------|
| **EASY** | 28.12% | 160 | 45 |
| **MODERATE** | 27.50% | 160 | 44 |
| **HARD** | 20.62% | 160 | 33 |

**Observations:**
- Difficulty level has **minimal impact** on detection accuracy
- Only 7.5% difference between EASY and HARD
- All difficulty levels show poor performance
- Suggests fundamental detection challenges beyond complexity

---

### 4. Programming Language Analysis

| Language | Accuracy | Examples | Correct |
|----------|----------|----------|---------|
| **KOTLIN** | 30.00% | 120 | 36 |
| **PYTHON** | 28.33% | 120 | 34 |
| **JAVA** | 21.67% | 120 | 26 |
| **CSHARP** | 25.00% | 72 | 18 |
| **C#** | 16.67% | 48 | 8 |

**Notes:**
- Kotlin performs best (30.00%)
- C# notation inconsistency (C# vs CSHARP) in data
- Language differences are relatively small (13.33% range)
- All languages show poor overall performance

---

### 5. Model-Specific Breakdown

#### deepseek-r1-8b
- **Strengths:**
  - Excellent ISP detection (87.50%)
  - Better overall accuracy (27.08%)
  - More balanced across violation types

- **Weaknesses:**
  - Very poor SRP detection (2.08%)
  - Poor OCP detection (6.25%)
  - Slower processing (147.21s avg)

#### qwen3-8b
- **Strengths:**
  - Better DIP detection (47.92%)
  - Faster processing (135.97s avg)
  - Better on MODERATE difficulty (31.25%)

- **Weaknesses:**
  - **Zero** SRP and OCP detection (0.00%)
  - Lower ISP detection (64.58%)
  - Poor on HARD difficulty (11.25%)

---

## Comparison with Two_Agent Workflow

Based on the two_agent analysis framework, here are key differences:

| Metric | Two_Agent (typical) | Diff_Eval |
|--------|---------------------|-----------|
| Overall Accuracy | ~60-80% | ~25% |
| Best Violation Type | ~90%+ | 76% (ISP) |
| Worst Violation Type | ~40-50% | 1% (SRP) |
| Processing Time | Lower | Higher (135-147s) |

**Critical Differences:**
1. **Massive accuracy drop** in diff_eval workflow
2. **Extreme imbalance** in violation type detection
3. **SRP and OCP** are nearly undetectable in diff_eval
4. **ISP** remains relatively detectable

---

## Files in This Directory

### Visualizations
1. **01_diff_eval_accuracy_by_model.png** - Bar chart comparing model accuracies
2. **02_diff_eval_accuracy_by_violation.png** - Violation type detection rates
3. **03_diff_eval_heatmap.png** - Model vs Violation Type performance matrix
4. **04_diff_eval_runtime_boxplot.png** - Processing time distributions
5. **05_diff_eval_accuracy_vs_runtime.png** - Accuracy-speed tradeoff
6. **06_diff_eval_confusion_matrix_[model].png** - Confusion matrices for each model
7. **07_diff_eval_accuracy_by_level.png** - Performance across difficulty levels
8. **08_diff_eval_accuracy_by_language.png** - Performance across programming languages

### Data Files
- **diff_eval_detailed_results.csv** - Complete results dataset (480 records)
- **diff_eval_summary_report.txt** - Detailed text report with all metrics

---

## Recommendations

### Immediate Actions
1. **Investigate SRP/OCP Detection Failure**
   - Current 1-3% accuracy is unacceptable
   - Review detection methodology for these violation types
   - Consider alternative detection signals

2. **Analyze ISP Success**
   - Understand why ISP detection works (76%)
   - Apply successful patterns to other violation types

3. **Optimize Processing Time**
   - 135-147s average is very high
   - Consider timeout strategies
   - Investigate long-running cases

### Long-term Improvements
1. **Workflow Redesign**
   - diff_eval shows significantly worse performance than two_agent
   - Consider hybrid approaches
   - Investigate root causes of poor performance

2. **Model Fine-tuning**
   - Both models struggle with SRP/OCP
   - Consider specialized training for these violation types

3. **Balanced Dataset**
   - Ensure equal representation across violation types
   - Add more challenging examples for ISP (currently too easy)

---

## Methodology

This analysis follows the same framework as the two_agent analysis:

1. **Data Collection**: Loaded detection results from JSON files
2. **Metrics Calculation**: Computed accuracy across multiple dimensions
3. **Visualization**: Created 8+ comprehensive charts
4. **Statistical Analysis**: Analyzed performance patterns
5. **Reporting**: Generated detailed text and CSV reports

**Analysis Script**: `analyze_diff_eval.py`

---

## Conclusion

The diff_eval workflow shows **critical performance issues**:
- Overall accuracy < 30% (vs ~70% for two_agent)
- SRP and OCP detection is essentially non-functional
- Only ISP detection shows acceptable performance
- Processing times are high

**Urgent action required** to improve SRP and OCP detection before this workflow can be considered production-ready.

---

*Generated by: analyze_diff_eval.py*
*Framework: Based on two_agent analysis methodology*
