# Comprehensive Analysis Report: Qwen3-8B Performance Comparison

**Date:** 2026-01-29
**Models Compared:** Context-Managed Diff vs Diff vs LLM-Only
**Total Examples:** 240 per system

---

## Executive Summary

This report compares three different approaches for SOLID principle violation detection using the Qwen3-8B model:

1. **Context-Managed Diff** - New approach with structural analysis and context management
2. **Diff** - Previous diff-based evaluation approach (v10)
3. **LLM-Only** - Direct LLM analysis without diff context (LangGraph)

### Key Findings

| Metric | Context-Managed | Diff | LLM-Only | Winner |
|--------|----------------|------|----------|--------|
| **Overall Accuracy** | 66.7% | 46.7% | **73.3%** | LLM-Only |
| **Avg Processing Time** | 132.55s | 135.95s | **1.79s** | LLM-Only |
| **Best at DIP** | **89.6%** | 47.9% | 25.0% | Context-Managed |
| **Best at LSP** | **79.2%** | 6.2% | 60.4% | Context-Managed |
| **Best at OCP** | 37.5% | 54.2% | **97.9%** | LLM-Only |
| **Best at SRP** | 60.4% | 47.9% | **83.3%** | LLM-Only |
| **Best at ISP** | 66.7% | 77.1% | **100.0%** | LLM-Only |

**Recommendation:**
- Use **LLM-Only** for general-purpose detection (best overall accuracy and speed)
- Use **Context-Managed Diff** specifically for DIP and LSP violations (significantly better)
- Consider a **hybrid approach** that routes to the best system per violation type

---

## 1. Overall Performance Metrics

### Accuracy Comparison

```
Context-Managed Diff:  66.7% ████████████████████████████████████████████████████████████████████
Diff:                  46.7% ███████████████████████████████████████████████
LLM-Only:              73.3% █████████████████████████████████████████████████████████████████████████████
```

**Analysis:**
- LLM-Only achieves the highest overall accuracy (73.3%)
- Context-Managed Diff shows 42.9% improvement over Diff
- Context-Managed Diff still lags LLM-Only by 6.6 percentage points

### Processing Time Comparison

| System | Mean | Median | Std Dev | Min | Max | P95 |
|--------|------|--------|---------|-----|-----|-----|
| Context-Managed | 132.55s | 103.50s | 119.46s | 23.30s | 1015.84s | 278.16s |
| Diff | 135.95s | 112.00s | 104.13s | 21.69s | 667.27s | 298.23s |
| LLM-Only | **1.79s** | **1.66s** | **0.57s** | **0.69s** | **4.62s** | **2.81s** |

**Critical Insight:** LLM-Only is **74x faster** than Context-Managed Diff on average!

### Time by Difficulty Level

| Level | Context-Managed | Diff | LLM-Only | CM/LLM Ratio |
|-------|----------------|------|----------|--------------|
| EASY | 44.72s | 38.77s | 1.31s | **34x slower** |
| MODERATE | 115.81s | 129.28s | 1.73s | **67x slower** |
| HARD | 237.11s | 239.81s | 2.34s | **101x slower** |

**Key Observation:** The performance gap widens dramatically with difficulty level.

---

## 2. Accuracy by Violation Type

### Detailed Breakdown

| Violation | Context-Managed | Diff | LLM-Only | CM vs Diff | CM vs LLM |
|-----------|----------------|------|----------|------------|-----------|
| **DIP** | **89.6%** ✓ | 47.9% | 25.0% | **+41.7%** | **+64.6%** |
| **ISP** | 66.7% | 77.1% | **100.0%** ✓ | -10.4% | -33.3% |
| **LSP** | **79.2%** ✓ | 6.2% | 60.4% | **+72.9%** | **+18.8%** |
| **OCP** | 37.5% | 54.2% | **97.9%** ✓ | -16.7% | -60.4% |
| **SRP** | 60.4% | 47.9% | **83.3%** ✓ | +12.5% | -22.9% |

### Violation-Specific Insights

#### DIP (Dependency Inversion Principle)
- **Context-Managed dominates** with 89.6% accuracy
- Diff-based approaches excel at detecting concrete dependencies
- LLM-Only struggles (25.0%) - likely confuses DIP with SRP

#### ISP (Interface Segregation Principle)
- **LLM-Only achieves perfect 100%** accuracy
- ISP violations are structurally obvious (fat interfaces)
- Context-Managed underperforms (66.7%) - may be over-analyzing

#### LSP (Liskov Substitution Principle)
- **Context-Managed excels** with 79.2% accuracy
- Diff v10 catastrophically fails (6.2%) - likely a bug
- LSP requires understanding inheritance hierarchies (diff helps)

#### OCP (Open/Closed Principle)
- **LLM-Only dominates** with 97.9% accuracy
- Context-Managed struggles (37.5%) - may be too focused on diffs
- OCP violations are conceptual (extension points)

#### SRP (Single Responsibility Principle)
- **LLM-Only leads** with 83.3% accuracy
- Context-Managed moderate (60.4%)
- SRP is about cohesion - direct code analysis works better

---

## 3. Accuracy by Difficulty Level

| Level | Context-Managed | Diff | LLM-Only | CM vs Diff | CM vs LLM |
|-------|----------------|------|----------|------------|-----------|
| **EASY** | 73.8% | 73.8% | **78.8%** | 0.0% | -5.0% |
| **MODERATE** | **65.0%** | 47.5% | 72.5% | **+17.5%** | -7.5% |
| **HARD** | **61.3%** | 18.8% | 68.8% | **+42.5%** | -7.5% |

### Key Observations

1. **EASY examples:** All systems perform similarly (~74-79%)
2. **MODERATE examples:** Context-Managed shows improvement over Diff (+17.5%)
3. **HARD examples:** Context-Managed dramatically outperforms Diff (+42.5%)
   - Diff collapses to 18.8% on hard examples (critical failure)
   - Context-Managed maintains 61.3% (much more robust)

**Conclusion:** Context-Managed Diff is significantly more robust on difficult examples compared to Diff.

---

## 4. Accuracy by Programming Language

| Language | Count | Context-Managed | Diff | LLM-Only | CM vs Diff |
|----------|-------|----------------|------|----------|------------|
| **CSHARP** | 60 | 68.3% | 46.7% | **78.3%** | +21.7% |
| **JAVA** | 60 | 70.0% | 48.3% | **78.3%** | +21.7% |
| **KOTLIN** | 60 | **70.0%** | 43.3% | **70.0%** | +26.7% |
| **PYTHON** | 60 | 58.3% | 48.3% | **66.7%** | +10.0% |

### Language-Specific Insights

- **Consistent improvement:** Context-Managed outperforms Diff across all languages
- **Python is hardest:** All systems show lower accuracy on Python
- **Kotlin parity:** Context-Managed matches LLM-Only on Kotlin (70.0%)
- **C# and Java:** Similar patterns across both languages

---

## 5. Error Analysis

### Error Rates by System

| System | Total Errors | Error Rate | Errors by Difficulty |
|--------|--------------|------------|---------------------|
| Context-Managed | 80 / 240 | 33.3% | Easy: 26.2%, Moderate: 35.0%, Hard: 38.8% |
| Diff | 128 / 240 | **53.3%** | Easy: 26.2%, Moderate: 52.5%, **Hard: 81.2%** |
| LLM-Only | 64 / 240 | **26.7%** | Easy: 21.2%, Moderate: 27.5%, Hard: 31.2% |

### Error Distribution by Violation Type

#### Context-Managed Diff Errors
```
DIP:  5/48 (10.4%) ████████
ISP: 16/48 (33.3%) ████████████████████████████████
LSP: 10/48 (20.8%) ████████████████████
OCP: 30/48 (62.5%) ██████████████████████████████████████████████████████████████
SRP: 19/48 (39.6%) ███████████████████████████████████████
```

**Weakest:** OCP (62.5% error rate)
**Strongest:** DIP (10.4% error rate)

#### Diff Errors
```
DIP: 25/48 (52.1%) ████████████████████████████████████████████████████
ISP: 11/48 (22.9%) ██████████████████████
LSP: 45/48 (93.8%) █████████████████████████████████████████████████████████████████████████████████████████████
OCP: 22/48 (45.8%) ██████████████████████████████████████████████
SRP: 25/48 (52.1%) ████████████████████████████████████████████████████
```

**Critical Failure:** LSP (93.8% error rate - system is broken for LSP)

#### LLM-Only Errors
```
DIP: 36/48 (75.0%) ███████████████████████████████████████████████████████████████████████████
ISP:  0/48 (0.0%)  [PERFECT]
LSP: 19/48 (39.6%) ███████████████████████████████████████
OCP:  1/48 (2.1%)  ██
SRP:  8/48 (16.7%) ████████████████
```

**Perfect:** ISP (0% error rate)
**Weakest:** DIP (75.0% error rate)

### Top Misclassification Patterns

#### Context-Managed Diff
1. **OCP → DIP** (19 times) - Confuses extension points with dependencies
2. **SRP → DIP** (16 times) - Misidentifies responsibility as dependency
3. **ISP → LSP** (15 times) - Confuses interface segregation with substitutability
4. **OCP → SRP** (10 times) - Confuses extensibility with responsibility
5. **LSP → DIP** (6 times) - Confuses inheritance with dependency

#### Diff
1. **LSP → ISP** (34 times) - Massive confusion between LSP and ISP
2. **SRP → DIP** (16 times) - Same as Context-Managed
3. **DIP → ISP** (13 times) - Confuses dependencies with interfaces
4. **OCP → DIP** (12 times) - Same as Context-Managed
5. **ISP → DIP** (9 times) - Interface confusion

#### LLM-Only
1. **DIP → SRP** (26 times) - Consistently misidentifies DIP as SRP
2. **DIP → OCP** (8 times) - Confuses dependencies with extensibility
3. **LSP → OCP** (6 times) - Confuses substitutability with extensibility
4. **LSP → ISP** (5 times) - Minor confusion
5. **LSP → SRP** (5 times) - Minor confusion

### Error Pattern Insights

**Common Confusion Pairs:**
- **DIP ↔ SRP:** Most systems struggle to distinguish dependency from responsibility
- **LSP ↔ ISP:** Inheritance and interface concepts overlap
- **OCP ↔ DIP:** Extension points vs dependencies

**System-Specific Issues:**
- **Context-Managed:** Over-focuses on dependencies (many → DIP errors)
- **Diff:** Broken LSP detection (93.8% error rate)
- **LLM-Only:** Cannot distinguish DIP from SRP (75% DIP error rate)

---

## 6. Structural Analysis (Context-Managed Diff Only)

### Overview

The Context-Managed Diff system includes a **structural pre-check** that analyzes code structure before LLM evaluation. This aims to:
1. Skip obviously irrelevant violation types
2. Reduce LLM calls and processing time
3. Improve accuracy by focusing on relevant violations

### Structural Check Statistics

| Metric | Value |
|--------|-------|
| Examples with structural checks | 239 / 240 (99.6%) |
| Total structural skips | 451 |
| Average skips per example | 1.9 |
| False negatives (missed violations) | 13 |
| False negative rate | 5.4% |

### Violations Skipped by Structural Analysis

```
ISP: 180 times (39.9%) ████████████████████████████████████████
LSP: 160 times (35.5%) ███████████████████████████████████
DIP:  62 times (13.7%) ██████████████
OCP:  28 times (6.2%)  ██████
SRP:  21 times (4.7%)  █████
```

### Structural Check Effectiveness

**Most Frequently Skipped:**
1. **ISP (180 times)** - Correctly identifies when no interfaces exist
2. **LSP (160 times)** - Correctly identifies when no inheritance exists

**Least Frequently Skipped:**
3. **SRP (21 times)** - SRP can exist in any code (rarely skippable)

### False Negatives Analysis

The structural check incorrectly marked 13 violations as "not detected":

| Violation | False Negatives | Total Examples | FN Rate |
|-----------|----------------|----------------|---------|
| **LSP** | 9 | 48 | 18.8% |
| **SRP** | 3 | 48 | 6.3% |
| **DIP** | 1 | 48 | 2.1% |
| **ISP** | 0 | 48 | 0.0% |
| **OCP** | 0 | 48 | 0.0% |

**Critical Issue:** LSP has 18.8% false negative rate in structural checks
- Structural analysis may miss subtle inheritance violations
- Needs improvement in detecting LSP violations

### Structural Check Impact on Performance

**Positive Impact:**
- Successfully skips 451 irrelevant checks (1.9 per example)
- Reduces unnecessary LLM analysis
- Perfect precision for ISP and OCP (0% false negatives)

**Negative Impact:**
- 18.8% false negative rate for LSP is concerning
- May be causing the 20.8% error rate for LSP in Context-Managed
- Needs refinement for LSP detection

**Recommendation:**
- Keep structural checks for ISP, OCP, DIP (low false negative rates)
- Disable or improve structural checks for LSP (high false negative rate)
- Consider making structural checks more conservative (fewer skips, fewer false negatives)

---

## 7. Processing Time Deep Dive

### Time Distribution Analysis

#### Context-Managed Diff
- **Mean:** 132.55s
- **Median:** 103.50s (mean > median indicates right-skewed distribution)
- **Std Dev:** 119.46s (high variance)
- **Max:** 1015.84s (extreme outlier - 17 minutes!)
- **P95:** 278.16s (95% complete within 4.6 minutes)

**Issues:**
- High variance indicates inconsistent performance
- Extreme outliers (1015s) suggest timeout or retry issues
- Median is more representative than mean

#### Diff
- **Mean:** 135.95s
- **Median:** 112.00s
- **Std Dev:** 104.13s (slightly lower variance than Context-Managed)
- **Max:** 667.27s (11 minutes - still very high)
- **P95:** 298.23s

**Issues:**
- Similar problems to Context-Managed
- Slightly more consistent (lower std dev)

#### LLM-Only
- **Mean:** 1.79s
- **Median:** 1.66s
- **Std Dev:** 0.57s (very consistent)
- **Max:** 4.62s (worst case is still excellent)
- **P95:** 2.81s

**Advantages:**
- Extremely fast and consistent
- No outliers or timeout issues
- Scales linearly with difficulty

### Time vs Accuracy Trade-off

| System | Accuracy | Avg Time | Accuracy per Second |
|--------|----------|----------|---------------------|
| LLM-Only | 73.3% | 1.79s | **40.9% / second** |
| Context-Managed | 66.7% | 132.55s | 0.5% / second |
| Diff | 46.7% | 135.95s | 0.3% / second |

**Conclusion:** LLM-Only provides the best accuracy-per-second by a massive margin (80x better than Context-Managed).

---

## 8. Recommendations

### Immediate Actions

1. **Use LLM-Only as Default**
   - Best overall accuracy (73.3%)
   - 74x faster than diff-based approaches
   - Consistent performance across difficulty levels

2. **Fix LSP Detection in Diff Systems**
   - Diff has 93.8% error rate on LSP (critical bug)
   - Context-Managed has 18.8% false negative rate in structural checks for LSP
   - Investigate and fix LSP detection logic

3. **Investigate Timeout Issues**
   - Context-Managed has 1015s max time (17 minutes)
   - Diff has 667s max time (11 minutes)
   - Implement proper timeouts and retry logic

### Hybrid Approach Strategy

Consider routing to the best system per violation type:

| Violation | Recommended System | Accuracy | Reason |
|-----------|-------------------|----------|--------|
| **DIP** | Context-Managed | 89.6% | 64.6% better than LLM-Only |
| **ISP** | LLM-Only | 100.0% | Perfect accuracy |
| **LSP** | Context-Managed | 79.2% | 18.8% better than LLM-Only |
| **OCP** | LLM-Only | 97.9% | 60.4% better than Context-Managed |
| **SRP** | LLM-Only | 83.3% | 22.9% better than Context-Managed |

**Expected Hybrid Performance:**
- **Accuracy:** 89.6% (weighted average)
- **Time:** ~27s average (assuming 20% DIP+LSP use Context-Managed)

### Long-term Improvements

1. **Improve Context-Managed Diff**
   - Fix LSP structural check false negatives
   - Reduce processing time (investigate bottlenecks)
   - Improve OCP detection (currently 37.5%)

2. **Improve LLM-Only**
   - Add DIP-specific prompting (currently 25.0%)
   - Provide examples of DIP vs SRP distinction

3. **Optimize Structural Checks**
   - Make LSP checks more conservative
   - Add confidence scores to structural checks
   - Allow LLM override of structural decisions

4. **Add Ensemble Methods**
   - Combine predictions from multiple systems
   - Use voting or confidence-weighted averaging
   - Potentially achieve >80% accuracy

---

## 9. Conclusion

### Summary of Findings

1. **LLM-Only is the clear winner** for general-purpose SOLID violation detection
   - Highest overall accuracy (73.3%)
   - Fastest processing time (1.79s)
   - Most consistent performance

2. **Context-Managed Diff has niche advantages**
   - Excellent for DIP detection (89.6%)
   - Strong for LSP detection (79.2%)
   - More robust on hard examples than Diff

3. **Diff (v10) has critical issues**
   - LSP detection is broken (6.2% accuracy)
   - Collapses on hard examples (18.8% accuracy)
   - Should not be used in production

4. **Structural analysis shows promise but needs work**
   - Successfully skips 451 irrelevant checks
   - 18.8% false negative rate for LSP is too high
   - Needs refinement before production use

### Final Recommendation

**For Production Use:**
- **Primary:** Use LLM-Only for all violations
- **Optional:** Add Context-Managed Diff for DIP and LSP if accuracy is critical and time is not a constraint
- **Avoid:** Do not use Diff (v10) - it has critical bugs

**For Research:**
- Investigate hybrid ensemble methods
- Improve Context-Managed Diff processing time
- Fix LSP structural check false negatives
- Add DIP-specific improvements to LLM-Only

---

## Appendix: Detailed Statistics

### Confusion Matrix Summary

#### Context-Managed Diff Top 10 Errors
| Actual | Predicted | Count | % of Errors |
|--------|-----------|-------|-------------|
| OCP | DIP | 19 | 23.8% |
| SRP | DIP | 16 | 20.0% |
| ISP | LSP | 15 | 18.8% |
| OCP | SRP | 10 | 12.5% |
| LSP | DIP | 6 | 7.5% |

#### Diff Top 10 Errors
| Actual | Predicted | Count | % of Errors |
|--------|-----------|-------|-------------|
| LSP | ISP | 34 | 26.6% |
| SRP | DIP | 16 | 12.5% |
| DIP | ISP | 13 | 10.2% |
| OCP | DIP | 12 | 9.4% |
| ISP | DIP | 9 | 7.0% |

#### LLM-Only Top 10 Errors
| Actual | Predicted | Count | % of Errors |
|--------|-----------|-------|-------------|
| DIP | SRP | 26 | 40.6% |
| DIP | OCP | 8 | 12.5% |
| LSP | OCP | 6 | 9.4% |
| LSP | ISP | 5 | 7.8% |
| LSP | SRP | 5 | 7.8% |

---

**Report Generated:** 2026-01-29
**Analysis Tool:** comprehensive_analysis.py
**Data Sources:**
- Context-Managed Diff: `result/local/diff_eval/qwen3-8b/detection_results.json`
- Diff: `result/local/diff_eval_v10/qwen3-8b/detection_results.json`
- LLM-Only: `analysis/analysis_output_langgraph/langgraph_detailed_results.csv`
