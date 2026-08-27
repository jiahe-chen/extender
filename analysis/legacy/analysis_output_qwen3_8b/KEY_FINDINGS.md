# qwen3-8b (diff_eval) Analysis - Key Findings

## Executive Summary

This analysis evaluates the **qwen3-8b** model using the **diff_eval** workflow for SOLID principle violation detection, comparing it against **two_agent** and **langgraph** approaches.

---

## Overall Performance

### Accuracy Rankings
1. **langgraph**: 55.08% (Best)
2. **two_agent**: 49.58%
3. **diff_eval (qwen3-8b)**: 46.67%

### Processing Time Rankings
1. **langgraph**: 1.54s avg (Fastest - 88x faster than diff_eval)
2. **two_agent**: 8.75s avg
3. **diff_eval (qwen3-8b)**: 135.95s avg (Slowest)

---

## Detailed Performance Analysis

### By Violation Type

| Violation | diff_eval | langgraph | two_agent | Best Approach |
|-----------|-----------|-----------|-----------|---------------|
| **ISP**   | **77.08%** | 47.92% | 38.75% | **diff_eval** ✓ |
| **OCP**   | 54.17% | **93.75%** | 59.58% | **langgraph** |
| **DIP**   | 47.92% | 30.00% | **41.67%** | **diff_eval** |
| **SRP**   | 47.92% | 72.50% | **89.17%** | **two_agent** |
| **LSP**   | 6.25% | 31.25% | 18.75% | **langgraph** |

**Key Insights:**
- ✅ **diff_eval excels at ISP detection** (77.08% - significantly better than others)
- ✅ **diff_eval is competitive on DIP** (47.92%)
- ❌ **diff_eval struggles with LSP** (only 6.25% - major weakness)
- ❌ **diff_eval underperforms on SRP** compared to two_agent (47.92% vs 89.17%)

### By Difficulty Level

| Level | diff_eval | langgraph | two_agent | Best Approach |
|-------|-----------|-----------|-----------|---------------|
| **EASY** | **73.75%** | 66.75% | 55.00% | **diff_eval** ✓ |
| **MODERATE** | 47.50% | **52.25%** | 49.50% | **langgraph** |
| **HARD** | 18.75% | **46.25%** | 44.25% | **langgraph** |

**Key Insights:**
- ✅ **diff_eval performs best on EASY cases** (73.75%)
- ⚠️ **Performance drops significantly with difficulty**:
  - EASY → MODERATE: -26.25% (73.75% → 47.50%)
  - MODERATE → HARD: -28.75% (47.50% → 18.75%)
- ❌ **diff_eval struggles with HARD cases** (only 18.75% vs 46.25% for langgraph)

### By Programming Language

| Language | Accuracy | Examples | Notes |
|----------|----------|----------|-------|
| CSHARP | 55.56% | 36 | Best performance |
| JAVA | 48.33% | 60 | Average |
| PYTHON | 48.33% | 60 | Average |
| KOTLIN | 43.33% | 60 | Below average |
| C# | 33.33% | 24 | Worst performance |

**Note:** C# and CSHARP appear to be duplicate labels in the dataset.

---

## Strengths of diff_eval (qwen3-8b)

1. **ISP Detection Excellence**: 77.08% accuracy - best among all approaches
2. **EASY Case Performance**: 73.75% accuracy - outperforms both competitors
3. **Consistent on DIP**: Competitive performance (47.92%)

---

## Weaknesses of diff_eval (qwen3-8b)

1. **LSP Detection Failure**: Only 6.25% accuracy - critical weakness
2. **Processing Time**: 135.95s avg - 88x slower than langgraph, 15.5x slower than two_agent
3. **Hard Case Performance**: Only 18.75% accuracy - less than half of competitors
4. **Scalability Issues**: Very slow processing makes it impractical for large-scale analysis

---

## Comparative Analysis

### Accuracy vs Speed Trade-off

```
langgraph:  55.08% accuracy @ 1.54s  → Best balance (35.8% accuracy per second)
two_agent:  49.58% accuracy @ 8.75s  → Good balance (5.7% accuracy per second)
diff_eval:  46.67% accuracy @ 135.95s → Poor balance (0.34% accuracy per second)
```

### When to Use Each Approach

**Use langgraph when:**
- You need the best overall accuracy (55.08%)
- Speed is critical (1.54s avg)
- Working with OCP violations (93.75% accuracy)
- Handling HARD cases (46.25% accuracy)

**Use two_agent when:**
- You need excellent SRP detection (89.17% accuracy)
- You want a balance of speed and accuracy
- Working with moderate difficulty cases

**Use diff_eval (qwen3-8b) when:**
- ISP detection is the primary concern (77.08% accuracy)
- Working primarily with EASY cases (73.75% accuracy)
- Processing time is not a constraint
- **NOT recommended for production use due to speed issues**

---

## Recommendations

### For diff_eval Improvement

1. **Critical: Fix LSP Detection**
   - Current 6.25% accuracy is unacceptable
   - Investigate why the model fails on Liskov Substitution Principle
   - Consider specialized prompting or examples for LSP

2. **Optimize Processing Time**
   - 135.95s avg is too slow for practical use
   - Consider:
     - Reducing iteration count (currently 5)
     - Optimizing the unified_llm selection method
     - Using a faster model variant
     - Implementing early stopping

3. **Improve Hard Case Performance**
   - 18.75% accuracy on HARD cases needs significant improvement
   - Add more sophisticated reasoning steps
   - Provide more context or examples for complex violations

4. **Enhance SRP Detection**
   - Currently 47.92% vs 89.17% for two_agent
   - Study two_agent's approach to SRP detection
   - Incorporate successful patterns

### General Recommendations

1. **Use langgraph as the default approach** for most use cases
2. **Consider ensemble methods** combining diff_eval's ISP strength with langgraph's overall performance
3. **Investigate why diff_eval excels at ISP** - this insight could improve other approaches
4. **Address the C# vs CSHARP labeling inconsistency** in the dataset

---

## Conclusion

While **diff_eval (qwen3-8b)** shows promise in specific areas (ISP detection, EASY cases), its **slow processing time** (135.95s) and **poor performance on LSP** (6.25%) and **HARD cases** (18.75%) make it unsuitable for production use in its current form.

**langgraph** remains the recommended approach with the best balance of accuracy (55.08%) and speed (1.54s), making it **88x faster** while being **8.42% more accurate** than diff_eval.

The **ISP detection capability** of diff_eval (77.08%) is noteworthy and should be studied to potentially enhance other approaches.

---

## Files Generated

### Visualizations (12 charts)
1. `01_qwen3_overall_accuracy.png` - Overall accuracy
2. `02_qwen3_accuracy_by_violation.png` - Performance by violation type
3. `03_qwen3_accuracy_by_level.png` - Performance by difficulty
4. `04_qwen3_accuracy_by_language.png` - Performance by language
5. `05_qwen3_confusion_matrix.png` - Confusion matrix
6. `06_qwen3_processing_time_dist.png` - Processing time distribution
7. `07_comparison_overall_accuracy.png` - Overall comparison
8. `08_comparison_by_violation.png` - Violation type comparison
9. `09_comparison_by_level.png` - Difficulty level comparison
10. `10_comparison_processing_time.png` - Processing time comparison
11. `11_comparison_accuracy_vs_time.png` - Accuracy vs time scatter
12. `12_comparison_heatmaps.png` - Performance heatmaps

### Data Files
- `qwen3_8b_detailed_results.csv` - Raw results (240 examples)
- `qwen3_8b_comprehensive_report.txt` - Detailed text report

---

**Analysis Date:** 2026-01-27
**Total Examples Analyzed:** 240 (qwen3-8b) + 2400 (comparison data)
**Script:** `analyze_qwen3_8b_comprehensive.py`
