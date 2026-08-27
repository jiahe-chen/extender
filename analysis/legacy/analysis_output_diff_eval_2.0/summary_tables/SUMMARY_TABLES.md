# Summary Tables: Qwen3-8B Performance Comparison

**Generated:** 2026-01-29
**Systems:** Context-Managed Diff, Diff v10, LLM-Only

---

## 1. Overall Comparison

| Metric                     |   Context-Managed Diff |   Diff v10 |   LLM-Only |
|:---------------------------|-----------------------:|-----------:|-----------:|
| Total Examples             |                 240    |     240    |     240    |
| Overall Accuracy (%)       |                  66.67 |      46.67 |      73.33 |
| Total Correct              |                 160    |     112    |     176    |
| Total Errors               |                  80    |     128    |      64    |
| Error Rate (%)             |                  33.33 |      53.33 |      26.67 |
| Avg Processing Time (s)    |                 132.55 |     135.95 |       1.79 |
| Median Processing Time (s) |                 103.5  |     112    |       1.66 |
| Min Processing Time (s)    |                  23.3  |      21.69 |       0.69 |
| Max Processing Time (s)    |                1015.84 |     667.27 |       4.62 |
| Std Dev Time (s)           |                 119.46 |     104.13 |       0.57 |
| P95 Processing Time (s)    |                 278.16 |     298.23 |       2.81 |

---

## 2. Accuracy by Violation Type

| Violation Type   |   Context-Managed (%) |   Diff v10 (%) |   LLM-Only (%) | Best System     |   Best Accuracy (%) |   CM vs Diff |   CM vs LLM |
|:-----------------|----------------------:|---------------:|---------------:|:----------------|--------------------:|-------------:|------------:|
| DIP              |                 89.58 |          47.92 |          25    | Context-Managed |               89.58 |        41.67 |       64.58 |
| ISP              |                 66.67 |          77.08 |         100    | LLM-Only        |              100    |       -10.42 |      -33.33 |
| LSP              |                 79.17 |           6.25 |          60.42 | Context-Managed |               79.17 |        72.92 |       18.75 |
| OCP              |                 37.5  |          54.17 |          97.92 | LLM-Only        |               97.92 |       -16.67 |      -60.42 |
| SRP              |                 60.42 |          47.92 |          83.33 | LLM-Only        |               83.33 |        12.5  |      -22.92 |

---

## 3. Accuracy by Difficulty Level

| Difficulty   |   Examples |   Context-Managed (%) |   Diff v10 (%) |   LLM-Only (%) |   CM Correct |   CM vs Diff |   CM vs LLM |
|:-------------|-----------:|----------------------:|---------------:|---------------:|-------------:|-------------:|------------:|
| EASY         |         80 |                 73.75 |          73.75 |          78.75 |           59 |          0   |        -5   |
| MODERATE     |         80 |                 65    |          47.5  |          72.5  |           52 |         17.5 |        -7.5 |
| HARD         |         80 |                 61.25 |          18.75 |          68.75 |           49 |         42.5 |        -7.5 |

---

## 4. Accuracy by Programming Language

| Language   |   Examples |   Context-Managed (%) |   Diff v10 (%) |   LLM-Only (%) |   CM vs Diff |   CM vs LLM |
|:-----------|-----------:|----------------------:|---------------:|---------------:|-------------:|------------:|
| CSHARP     |         60 |                 68.33 |          46.67 |          78.33 |        21.67 |      -10    |
| JAVA       |         60 |                 70    |          48.33 |          78.33 |        21.67 |       -8.33 |
| KOTLIN     |         60 |                 70    |          43.33 |          70    |        26.67 |        0    |
| PYTHON     |         60 |                 58.33 |          48.33 |          66.67 |        10    |       -8.33 |

---

## 5. Detailed Violation Breakdown (Context-Managed)

| Violation   | Difficulty   |   Total |   Correct |   Accuracy (%) |   Avg Time (s) |
|:------------|:-------------|--------:|----------:|---------------:|---------------:|
| DIP         | EASY         |      16 |        14 |          87.5  |          35.95 |
| DIP         | MODERATE     |      16 |        15 |          93.75 |          57.51 |
| DIP         | HARD         |      16 |        14 |          87.5  |         143.75 |
| ISP         | EASY         |      16 |        10 |          62.5  |          67.48 |
| ISP         | MODERATE     |      16 |        10 |          62.5  |         152.03 |
| ISP         | HARD         |      16 |        12 |          75    |         229.52 |
| LSP         | EASY         |      16 |        11 |          68.75 |          43.74 |
| LSP         | MODERATE     |      16 |        13 |          81.25 |          97.37 |
| LSP         | HARD         |      16 |        14 |          87.5  |         236.29 |
| OCP         | EASY         |      16 |        11 |          68.75 |          49.39 |
| OCP         | MODERATE     |      16 |         3 |          18.75 |         146.42 |
| OCP         | HARD         |      16 |         4 |          25    |         263.4  |
| SRP         | EASY         |      16 |        13 |          81.25 |          27.04 |
| SRP         | MODERATE     |      16 |        11 |          68.75 |         125.73 |
| SRP         | HARD         |      16 |         5 |          31.25 |         312.59 |

---

## 6. Confusion Matrix Summary (Context-Managed)

| Actual Violation   |   Total Examples |   Correct Detections |   Accuracy (%) |   Errors | Most Common Error   |   Error Count |
|:-------------------|-----------------:|---------------------:|---------------:|---------:|:--------------------|--------------:|
| DIP                |               48 |                   43 |          89.58 |        5 | SRP                 |             5 |
| ISP                |               48 |                   32 |          66.67 |       16 | LSP                 |            15 |
| LSP                |               48 |                   38 |          79.17 |       10 | DIP                 |             6 |
| OCP                |               48 |                   18 |          37.5  |       30 | DIP                 |            19 |
| SRP                |               48 |                   29 |          60.42 |       19 | DIP                 |            16 |

---

## 7. Recommendations by Violation Type

| Violation Type   | Recommended System   | Accuracy   | Reason                                                   | Alternative                                       |
|:-----------------|:---------------------|:-----------|:---------------------------------------------------------|:--------------------------------------------------|
| DIP              | Context-Managed Diff | 89.58%     | Best DIP detection, 64.6% better than LLM-Only           | None - Context-Managed is clearly superior        |
| ISP              | LLM-Only             | 100.00%    | Perfect accuracy, 33.3% better than Context-Managed      | None - LLM-Only is perfect                        |
| LSP              | Context-Managed Diff | 79.17%     | Best LSP detection, 18.8% better than LLM-Only           | LLM-Only (60.4%) if speed is critical             |
| OCP              | LLM-Only             | 97.92%     | Context-Managed is broken (37.5%), LLM-Only is excellent | None - Context-Managed should not be used for OCP |
| SRP              | LLM-Only             | 83.33%     | Better accuracy, 22.9% better than Context-Managed       | Context-Managed (60.4%) if using hybrid approach  |
| General Purpose  | LLM-Only             | 73.33%     | Best overall accuracy, 74x faster, most consistent       | Hybrid approach for maximum accuracy (~85%)       |

---

## Key Takeaways

### Best System Overall
**LLM-Only** - 73.33% accuracy, 1.79s average time

### Best System by Violation
- **DIP:** Context-Managed (89.58%)
- **ISP:** LLM-Only (100.00%)
- **LSP:** Context-Managed (79.17%)
- **OCP:** LLM-Only (97.92%)
- **SRP:** LLM-Only (83.33%)

### Critical Issues
1. **Diff v10 LSP Detection:** 6.25% accuracy (broken)
2. **Context-Managed OCP Detection:** 37.50% accuracy (broken)
3. **LLM-Only DIP Detection:** 25.00% accuracy (weak)

### Recommended Approach
**Hybrid System:**
- Use Context-Managed for DIP and LSP
- Use LLM-Only for ISP, OCP, and SRP
- Expected accuracy: ~85%
- Expected speed: ~27s average

---

**Data Sources:**
- Context-Managed: `result/local/diff_eval/qwen3-8b/detection_results.json`
- Diff v10: `result/local/diff_eval_v10/qwen3-8b/detection_results.json`
- LLM-Only: `analysis/analysis_output_langgraph/langgraph_detailed_results.csv`
