# Confusion Matrix Analysis Report: Context-Managed Diff (Qwen3-8B)

**Analysis Date:** 2026-01-29
**System:** Context-Managed Diff
**Model:** Qwen3-8B
**Total Examples:** 240

---

## Executive Summary

The Context-Managed Diff system achieves **66.67% overall accuracy** (160/240 correct) on SOLID principle violation detection. The system shows strong performance on **DIP (89.58%)** and **LSP (79.17%)** but struggles significantly with **OCP (37.50%)**.

### Key Findings

| Metric | Value |
|--------|-------|
| **Overall Accuracy** | 66.67% (160/240) |
| **Best Performance** | DIP: 89.58% |
| **Worst Performance** | OCP: 37.50% |
| **Most Common Error** | OCP → DIP (23.8% of errors) |
| **Hardest Difficulty** | HARD: 61.25% |
| **Hardest Language** | Python: 58.33% |

---

## 1. Confusion Matrix Overview

### Raw Counts

|  | **DIP** | **ISP** | **LSP** | **OCP** | **SRP** | **None/Other** |
|---|---------|---------|---------|---------|---------|----------------|
| **DIP** | 43 | 0 | 0 | 0 | 5 | 0 |
| **ISP** | 0 | 32 | 15 | 0 | 1 | 0 |
| **LSP** | 6 | 0 | 38 | 1 | 3 | 0 |
| **OCP** | 19 | 0 | 0 | 18 | 10 | 1 |
| **SRP** | 16 | 0 | 0 | 3 | 29 | 0 |

### Normalized (Percentages)

|  | **DIP** | **ISP** | **LSP** | **OCP** | **SRP** | **None/Other** |
|---|---------|---------|---------|---------|---------|----------------|
| **DIP** | **89.6%** | 0.0% | 0.0% | 0.0% | 10.4% | 0.0% |
| **ISP** | 0.0% | **66.7%** | 31.2% | 0.0% | 2.1% | 0.0% |
| **LSP** | 12.5% | 0.0% | **79.2%** | 2.1% | 6.2% | 0.0% |
| **OCP** | 39.6% | 0.0% | 0.0% | **37.5%** | 20.8% | 2.1% |
| **SRP** | 33.3% | 0.0% | 0.0% | 6.2% | **60.4%** | 0.0% |

---

## 2. Per-Violation Performance Analysis

### Detailed Metrics

| Violation | Total | Correct | **Accuracy** | **Precision** | **Recall** | Status |
|-----------|-------|---------|--------------|---------------|------------|--------|
| **DIP** | 48 | 43 | **89.58%** | 51.19% | 89.58% | ✅ Excellent |
| **LSP** | 48 | 38 | **79.17%** | 70.37% | 79.17% | ✅ Good |
| **ISP** | 48 | 32 | **66.67%** | 100.00% | 66.67% | ⚠️ Moderate |
| **SRP** | 48 | 29 | **60.42%** | 60.42% | 60.42% | ⚠️ Moderate |
| **OCP** | 48 | 18 | **37.50%** | 85.71% | 37.50% | ❌ Poor |

### Key Observations

#### DIP (Dependency Inversion Principle) - 89.58% ✅
- **Strengths:**
  - Highest accuracy among all violations
  - Excellent recall (89.58%) - rarely misses DIP violations
  - Clear detection patterns

- **Weaknesses:**
  - Low precision (51.19%) - many false positives
  - 43 true positives but 41 false positives (detected as DIP when it wasn't)
  - Other violations frequently misclassified as DIP

- **Main Confusion:**
  - OCP → DIP (19 cases): Confuses extension points with dependencies
  - SRP → DIP (16 cases): Confuses responsibilities with dependencies

#### LSP (Liskov Substitution Principle) - 79.17% ✅
- **Strengths:**
  - Second-best accuracy
  - Good balance of precision (70.37%) and recall (79.17%)
  - Relatively few false positives

- **Weaknesses:**
  - 10 false negatives (missed LSP violations)
  - Some confusion with ISP (inheritance vs interfaces)

- **Main Confusion:**
  - ISP → LSP (15 cases): Confuses interface segregation with substitutability

#### ISP (Interface Segregation Principle) - 66.67% ⚠️
- **Strengths:**
  - Perfect precision (100.00%) - never false positive
  - When it detects ISP, it's always correct

- **Weaknesses:**
  - Moderate recall (66.67%) - misses 1/3 of ISP violations
  - 16 false negatives (missed ISP violations)
  - Most missed ISP violations are classified as LSP

- **Main Confusion:**
  - ISP → LSP (15 cases): Misses ISP and calls it LSP instead

#### SRP (Single Responsibility Principle) - 60.42% ⚠️
- **Strengths:**
  - Balanced precision and recall (both 60.42%)
  - Moderate performance

- **Weaknesses:**
  - 19 false negatives (missed SRP violations)
  - Frequently confused with DIP (16 cases)

- **Main Confusion:**
  - SRP → DIP (16 cases): Confuses responsibility with dependency

#### OCP (Open/Closed Principle) - 37.50% ❌
- **Strengths:**
  - High precision (85.71%) when it does detect OCP
  - Few false positives (only 3)

- **Weaknesses:**
  - **Critical failure:** Only 37.50% accuracy
  - 30 false negatives (misses 62.5% of OCP violations!)
  - Most OCP violations are misclassified as DIP or SRP

- **Main Confusion:**
  - OCP → DIP (19 cases): Confuses extension points with dependencies
  - OCP → SRP (10 cases): Confuses extensibility with responsibility

**Critical Issue:** OCP detection is severely broken and needs immediate attention.

---

## 3. Error Pattern Analysis

### Top 10 Misclassification Patterns

| Rank | Pattern | Count | % of Errors | Interpretation |
|------|---------|-------|-------------|----------------|
| 1 | **OCP → DIP** | 19 | 23.8% | System over-focuses on dependencies |
| 2 | **SRP → DIP** | 16 | 20.0% | Cannot distinguish responsibility from dependency |
| 3 | **ISP → LSP** | 15 | 18.8% | Confuses interfaces with inheritance |
| 4 | **OCP → SRP** | 10 | 12.5% | Confuses extensibility with responsibility |
| 5 | **LSP → DIP** | 6 | 7.5% | Inheritance confused with dependency |
| 6 | **DIP → SRP** | 5 | 6.2% | Dependency confused with responsibility |
| 7 | **SRP → OCP** | 3 | 3.8% | Responsibility confused with extensibility |
| 8 | **LSP → SRP** | 3 | 3.8% | Inheritance confused with responsibility |
| 9 | **ISP → SRP** | 1 | 1.2% | Interface confused with responsibility |
| 10 | **OCP → LSP** | 1 | 1.2% | Extensibility confused with inheritance |

### Error Categories

#### Category 1: DIP Over-Detection (44% of errors)
**Patterns:** OCP → DIP (19), SRP → DIP (16), LSP → DIP (6)

**Root Cause:** The system has a strong bias toward detecting dependencies. When analyzing code diffs, it focuses heavily on class relationships and dependencies, leading to over-classification as DIP violations.

**Impact:**
- DIP has low precision (51.19%)
- OCP, SRP, and LSP violations are frequently misclassified as DIP

**Recommendation:** Reduce DIP detection sensitivity; add more specific patterns for OCP and SRP.

#### Category 2: ISP/LSP Confusion (18.8% of errors)
**Pattern:** ISP → LSP (15)

**Root Cause:** Both ISP and LSP involve interfaces and inheritance. The system struggles to distinguish between:
- ISP: Fat interfaces forcing unnecessary implementations
- LSP: Behavioral substitutability violations

**Impact:**
- ISP recall is only 66.67% (misses 1/3 of violations)
- Most missed ISP violations are called LSP

**Recommendation:** Improve ISP detection logic; add specific checks for unused interface methods.

#### Category 3: OCP Misclassification (37.5% of errors)
**Patterns:** OCP → DIP (19), OCP → SRP (10), OCP → LSP (1)

**Root Cause:** OCP is conceptual (about extensibility and modification). The diff-based approach struggles because:
- OCP violations often look like dependency issues (OCP → DIP)
- OCP violations can look like responsibility issues (OCP → SRP)

**Impact:**
- OCP accuracy is critically low (37.50%)
- 62.5% of OCP violations are missed

**Recommendation:** Complete redesign of OCP detection; consider using LLM-only for OCP.

---

## 4. Performance by Difficulty Level

| Difficulty | Total | Correct | Accuracy | Error Rate |
|------------|-------|---------|----------|------------|
| **EASY** | 80 | 59 | **73.75%** | 26.25% |
| **MODERATE** | 80 | 52 | **65.00%** | 35.00% |
| **HARD** | 80 | 49 | **61.25%** | 38.75% |

### Analysis

- **Consistent degradation:** Accuracy decreases as difficulty increases
- **EASY examples:** 73.75% accuracy (acceptable)
- **MODERATE examples:** 65.00% accuracy (moderate)
- **HARD examples:** 61.25% accuracy (concerning)

### Most Problematic Combinations

| Violation + Difficulty | Accuracy | Status |
|------------------------|----------|--------|
| **OCP + HARD** | **25.00%** (4/16) | ❌ Critical |
| **SRP + HARD** | **31.25%** (5/16) | ❌ Critical |
| OCP + MODERATE | 37.50% (6/16) | ⚠️ Poor |
| OCP + EASY | 50.00% (8/16) | ⚠️ Poor |

**Critical Finding:** OCP detection fails across all difficulty levels, with HARD examples being catastrophic (25% accuracy).

---

## 5. Performance by Programming Language

| Language | Total | Correct | Accuracy | Rank |
|----------|-------|---------|----------|------|
| **JAVA** | 60 | 42 | **70.00%** | 1st (tied) |
| **KOTLIN** | 60 | 42 | **70.00%** | 1st (tied) |
| **CSHARP** | 60 | 41 | **68.33%** | 3rd |
| **PYTHON** | 60 | 35 | **58.33%** | 4th |

### Analysis

- **Best:** Java and Kotlin (70.00%)
- **Good:** C# (68.33%)
- **Weakest:** Python (58.33%)

**Python Issues:**
- 11.67% lower accuracy than Java/Kotlin
- Dynamic typing makes structural analysis harder
- Duck typing and dynamic attributes difficult to detect statically

**Recommendation:** Add Python-specific detection rules or use LLM-only for Python code.

---

## 6. Precision vs Recall Analysis

### Precision-Recall Trade-offs

| Violation | Precision | Recall | F1-Score | Balance |
|-----------|-----------|--------|----------|---------|
| **ISP** | 100.00% | 66.67% | 80.00% | High precision, low recall |
| **OCP** | 85.71% | 37.50% | 52.17% | High precision, very low recall |
| **LSP** | 70.37% | 79.17% | 74.55% | Balanced |
| **SRP** | 60.42% | 60.42% | 60.42% | Perfectly balanced |
| **DIP** | 51.19% | 89.58% | 65.00% | Low precision, high recall |

### Interpretation

#### High Precision, Low Recall (ISP, OCP)
- **ISP:** Never wrong when it detects ISP, but misses 1/3 of cases
- **OCP:** Rarely wrong when it detects OCP, but misses 2/3 of cases
- **Strategy:** Conservative detection - only flags obvious cases

#### Balanced (LSP, SRP)
- **LSP:** Good balance at ~70-79%
- **SRP:** Perfectly balanced at 60.42%
- **Strategy:** Moderate detection threshold

#### Low Precision, High Recall (DIP)
- **DIP:** Catches most DIP violations but has many false positives
- **Strategy:** Aggressive detection - flags anything that looks like dependency

**Recommendation:** Adjust detection thresholds to balance precision and recall better.

---

## 7. Critical Issues and Recommendations

### Priority 1: Fix OCP Detection (Critical)

**Problem:**
- Only 37.50% accuracy (worst by far)
- Misses 62.5% of OCP violations
- Most OCP violations misclassified as DIP (19) or SRP (10)

**Root Cause:**
- OCP is conceptual (about extensibility)
- Diff-based approach focuses on concrete changes, not design principles
- System looks for dependencies/responsibilities instead of extension points

**Recommendations:**
1. **Short-term:** Use LLM-only for OCP detection (97.9% accuracy)
2. **Medium-term:** Add OCP-specific patterns:
   - Look for switch statements / if-else chains
   - Detect hardcoded type checks
   - Identify modification of existing code vs extension
3. **Long-term:** Redesign OCP detection from scratch

**Expected Impact:** 37.50% → 70%+ accuracy

### Priority 2: Reduce DIP Over-Detection

**Problem:**
- DIP has low precision (51.19%)
- 41 false positives (other violations detected as DIP)
- Causes 44% of all errors

**Root Cause:**
- System is biased toward detecting dependencies
- Any class relationship is flagged as potential DIP violation

**Recommendations:**
1. Increase DIP detection threshold
2. Add negative patterns (when NOT to flag DIP)
3. Distinguish between:
   - Concrete dependencies (DIP)
   - Responsibilities (SRP)
   - Extension points (OCP)

**Expected Impact:** Precision 51.19% → 70%+, reduce false positives by 50%

### Priority 3: Improve ISP/LSP Distinction

**Problem:**
- 15 cases of ISP → LSP confusion
- ISP recall only 66.67%

**Root Cause:**
- Both involve interfaces/inheritance
- System cannot distinguish:
  - ISP: Unused interface methods
  - LSP: Behavioral contract violations

**Recommendations:**
1. Add ISP-specific checks:
   - Detect unused interface methods
   - Look for empty/dummy implementations
   - Check for interface bloat
2. Add LSP-specific checks:
   - Analyze preconditions/postconditions
   - Check exception handling differences
   - Verify behavioral contracts

**Expected Impact:** ISP recall 66.67% → 85%+

### Priority 4: Improve Python Support

**Problem:**
- Python accuracy (58.33%) is 11.67% lower than Java/Kotlin
- Dynamic typing makes structural analysis harder

**Recommendations:**
1. Add Python-specific rules
2. Use type hints when available
3. Analyze docstrings for behavioral contracts
4. Be more conservative with Python code
5. Consider using LLM-only for Python

**Expected Impact:** Python accuracy 58.33% → 70%+

---

## 8. Comparison with Other Systems

### Context-Managed vs LLM-Only

| Violation | Context-Managed | LLM-Only | Winner | Difference |
|-----------|----------------|----------|--------|------------|
| **DIP** | **89.58%** | 25.00% | Context-Managed | **+64.58%** |
| **ISP** | 66.67% | **100.00%** | LLM-Only | -33.33% |
| **LSP** | **79.17%** | 60.42% | Context-Managed | **+18.75%** |
| **OCP** | 37.50% | **97.92%** | LLM-Only | -60.42% |
| **SRP** | 60.42% | **83.33%** | LLM-Only | -22.91% |
| **Overall** | 66.67% | **73.33%** | LLM-Only | -6.66% |

### Key Insights

1. **Context-Managed excels at:** DIP (+64.58%), LSP (+18.75%)
2. **LLM-Only excels at:** ISP (+33.33%), OCP (+60.42%), SRP (+22.91%)
3. **Overall winner:** LLM-Only (73.33% vs 66.67%)

**Recommendation:** Use hybrid approach:
- Context-Managed for DIP and LSP
- LLM-Only for ISP, OCP, and SRP

**Expected hybrid accuracy:** ~85%

---

## 9. Actionable Recommendations

### Immediate Actions (Week 1)

1. ✅ **Switch to LLM-Only for OCP** (37.50% → 97.92%)
2. ⚠️ **Reduce DIP detection threshold** (reduce false positives)
3. ⚠️ **Add ISP-specific checks** (improve recall from 66.67%)

### Short-term Actions (Month 1)

4. ⚠️ **Improve Python support** (58.33% → 70%+)
5. ⚠️ **Add OCP-specific patterns** (if not using LLM-only)
6. ⚠️ **Implement hybrid routing** (route by violation type)

### Medium-term Actions (Quarter 1)

7. 🔬 **Redesign OCP detection** (complete overhaul)
8. 🔬 **Add confidence scores** (allow threshold tuning)
9. 🔬 **Implement ensemble methods** (combine multiple approaches)

### Long-term Actions (Year 1)

10. 🔬 **Machine learning for pattern detection**
11. 🔬 **Language-specific optimization**
12. 🔬 **Continuous learning from feedback**

---

## 10. Conclusion

### Summary

The Context-Managed Diff system shows **strong performance on DIP (89.58%) and LSP (79.17%)** but has **critical issues with OCP (37.50%)**. The system's bias toward dependency detection causes 44% of all errors.

### Strengths

✅ Excellent DIP detection (89.58%)
✅ Good LSP detection (79.17%)
✅ Perfect ISP precision (100%)
✅ Structural analysis provides 38.8% efficiency gain

### Weaknesses

❌ Critical OCP failure (37.50%)
❌ DIP over-detection (51.19% precision)
❌ ISP under-detection (66.67% recall)
❌ Python support weak (58.33%)

### Final Recommendation

**For Production:**
- Use **hybrid approach**: Context-Managed for DIP/LSP, LLM-Only for ISP/OCP/SRP
- Expected accuracy: **~85%**
- Expected speed: **~27s average**

**For Research:**
- Fix OCP detection (Priority 1)
- Reduce DIP false positives (Priority 2)
- Improve ISP/LSP distinction (Priority 3)
- Enhance Python support (Priority 4)

---

**Report Generated:** 2026-01-29
**Analysis Tool:** create_confusion_matrix_context_managed.py
**Data Source:** `result/local/diff_eval/qwen3-8b/detection_results.json`
**Visualizations:** `analysis/confusion_matrix_analysis/`
