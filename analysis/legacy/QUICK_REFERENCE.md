# Quick Reference Card: Qwen3-8B SOLID Violation Detection

**Last Updated:** 2026-01-29

---

## 🎯 Which System Should I Use?

### Production Deployment

| Your Priority | Recommended System | Accuracy | Speed | Why? |
|---------------|-------------------|----------|-------|------|
| **Speed & Simplicity** | **LLM-Only** | 73.3% | 1.79s | 74x faster, highest overall accuracy |
| **Maximum Accuracy** | **Hybrid** | ~85% | ~27s | Best of both worlds |
| **DIP Detection** | **Context-Managed** | 89.6% | 132s | 64.6% better than LLM-Only |
| **LSP Detection** | **Context-Managed** | 79.2% | 132s | 18.8% better than LLM-Only |
| **ISP Detection** | **LLM-Only** | 100.0% | 1.79s | Perfect accuracy |
| **OCP Detection** | **LLM-Only** | 97.9% | 1.79s | Context-Managed is broken (37.5%) |
| **SRP Detection** | **LLM-Only** | 83.3% | 1.79s | 22.9% better than Context-Managed |

---

## 📊 Performance at a Glance

### Overall Comparison

```
Accuracy:
LLM-Only:           73.3% ████████████████████████████████████████████████████████████████████████
Context-Managed:    66.7% ████████████████████████████████████████████████████████████████
Diff v10:           46.7% ███████████████████████████████████████████

Speed (lower is better):
LLM-Only:            1.79s █
Context-Managed:   132.55s ██████████████████████████████████████████████████████████████████████████
Diff v10:          135.95s ███████████████████████████████████████████████████████████████████████████
```

### Accuracy by Violation Type

| Violation | Context-Managed | Diff v10 | LLM-Only | Winner |
|-----------|----------------|----------|----------|--------|
| **DIP** | **89.6%** ⭐ | 47.9% | 25.0% | Context-Managed |
| **ISP** | 66.7% | 77.1% | **100.0%** ⭐ | LLM-Only |
| **LSP** | **79.2%** ⭐ | 6.2% ❌ | 60.4% | Context-Managed |
| **OCP** | 37.5% ❌ | 54.2% | **97.9%** ⭐ | LLM-Only |
| **SRP** | 60.4% | 47.9% | **83.3%** ⭐ | LLM-Only |

---

## 🚨 Critical Issues

### 1. Diff v10 LSP Detection BROKEN
- **Accuracy:** 6.2% (93.8% error rate)
- **Status:** ❌ Do not use for LSP
- **Action:** Use Context-Managed or LLM-Only instead

### 2. Context-Managed OCP Detection FAILED
- **Accuracy:** 37.5% (62.5% error rate)
- **Status:** ❌ Do not use for OCP
- **Action:** Use LLM-Only (97.9% accuracy)

### 3. LLM-Only DIP Detection WEAK
- **Accuracy:** 25.0% (75.0% error rate)
- **Status:** ⚠️ Use Context-Managed instead
- **Action:** Use Context-Managed (89.6% accuracy)

---

## 💡 Quick Decision Tree

```
START: Need to detect SOLID violations
    ↓
    Q: What's your priority?
    ↓
    ├─→ Speed & Simplicity
    │   └─→ Use LLM-Only (73.3%, 1.79s)
    │
    ├─→ Maximum Accuracy
    │   └─→ Use Hybrid Approach (~85%, ~27s)
    │       ├─→ DIP or LSP? → Context-Managed
    │       └─→ ISP, OCP, SRP? → LLM-Only
    │
    └─→ Specific Violation Type
        ├─→ DIP? → Context-Managed (89.6%)
        ├─→ ISP? → LLM-Only (100.0%)
        ├─→ LSP? → Context-Managed (79.2%)
        ├─→ OCP? → LLM-Only (97.9%)
        └─→ SRP? → LLM-Only (83.3%)
```

---

## 📈 Performance by Difficulty

| System | EASY | MODERATE | HARD | Trend |
|--------|------|----------|------|-------|
| **LLM-Only** | 78.8% | 72.5% | 68.8% | Consistent ✓ |
| **Context-Managed** | 73.8% | 65.0% | 61.3% | Gradual decline |
| **Diff v10** | 73.8% | 47.5% | 18.8% | Catastrophic ❌ |

**Insight:** LLM-Only maintains consistent performance across all difficulty levels.

---

## 🌍 Performance by Language

| Language | Context-Managed | Diff v10 | LLM-Only | Best |
|----------|----------------|----------|----------|------|
| **Java** | 70.0% | 48.3% | **78.3%** | LLM-Only |
| **Kotlin** | **70.0%** | 43.3% | **70.0%** | Tie |
| **C#** | 68.3% | 46.7% | **78.3%** | LLM-Only |
| **Python** | 58.3% | 48.3% | **66.7%** | LLM-Only |

**Insight:** Python is the hardest language for all systems.

---

## 🔧 Common Error Patterns

### Context-Managed Errors

| Pattern | Count | % of Errors | Issue |
|---------|-------|-------------|-------|
| **OCP → DIP** | 19 | 23.8% | Over-focuses on dependencies |
| **SRP → DIP** | 16 | 20.0% | Cannot distinguish responsibility from dependency |
| **ISP → LSP** | 15 | 18.8% | Confuses interfaces with inheritance |

**Root Cause:** System is biased toward detecting dependencies (DIP).

### LLM-Only Errors

| Pattern | Count | % of Errors | Issue |
|---------|-------|-------------|-------|
| **DIP → SRP** | 26 | 40.6% | Cannot distinguish dependency from responsibility |
| **DIP → OCP** | 8 | 12.5% | Confuses dependencies with extensibility |

**Root Cause:** Weak at understanding dependency relationships.

---

## 🎯 Recommendations Summary

### Immediate Actions (Week 1)
1. ✅ **Deploy LLM-Only** as default system
2. ⚠️ **Fix Diff v10 LSP bug** (if still needed)
3. ⚠️ **Implement advisory mode** for structural checks

### Short-term (Month 1)
4. ⚠️ **Implement hybrid routing** (DIP/LSP → Context-Managed, others → LLM-Only)
5. ⚠️ **Fix LSP structural checks** (80.9% → 95%+ recall)
6. ⚠️ **Improve Python support** (58.33% → 70%+)

### Medium-term (Quarter 1)
7. 🔬 **Redesign OCP detection** (37.5% → 70%+)
8. 🔬 **Add confidence scores** (enable threshold tuning)
9. 🔬 **Reduce DIP false positives** (51.19% → 70%+ precision)

---

## 📚 Where to Learn More

### Quick Start (5-10 minutes)
- **This card** - Quick reference
- [summary_tables/SUMMARY_TABLES.md](./summary_tables/SUMMARY_TABLES.md) - Comparison tables

### Decision Making (10-15 minutes)
- [EXECUTIVE_SUMMARY.md](./EXECUTIVE_SUMMARY.md) - High-level overview
- [visualizations/](./visualizations/) - 10 charts

### Deep Understanding (30-60 minutes)
- [COMPREHENSIVE_ANALYSIS_REPORT.md](./COMPREHENSIVE_ANALYSIS_REPORT.md) - Complete analysis
- [CONFUSION_MATRIX_REPORT.md](./CONFUSION_MATRIX_REPORT.md) - Error patterns

### Technical Details (60+ minutes)
- [STRUCTURAL_ANALYSIS_REPORT.md](./STRUCTURAL_ANALYSIS_REPORT.md) - Structural checks
- [confusion_matrix_analysis/](./confusion_matrix_analysis/) - Detailed visualizations
- All Python scripts for reproducibility

---

## 🔢 Key Numbers to Remember

| Metric | Value | Meaning |
|--------|-------|---------|
| **73.3%** | LLM-Only accuracy | Best overall performance |
| **74x** | Speed advantage | LLM-Only vs Context-Managed |
| **89.6%** | Context-Managed DIP | Best DIP detection |
| **100.0%** | LLM-Only ISP | Perfect ISP detection |
| **37.5%** | Context-Managed OCP | Critical failure - do not use |
| **6.2%** | Diff v10 LSP | Critical failure - do not use |
| **~85%** | Hybrid accuracy | Expected with optimal routing |

---

## ⚡ Quick Commands

### Run All Analyses
```bash
cd analysis
python comprehensive_analysis.py
python structural_analysis_deep_dive.py
python generate_visualizations.py
python create_confusion_matrix_context_managed.py
python generate_summary_tables.py
```

### View Results
```bash
# View main report
cat EXECUTIVE_SUMMARY.md

# View tables
cat summary_tables/SUMMARY_TABLES.md

# View visualizations
ls visualizations/
ls confusion_matrix_analysis/
```

---

## 🎓 Glossary

| Term | Definition |
|------|------------|
| **Context-Managed** | New approach with structural analysis and context management |
| **Diff v10** | Previous diff-based evaluation approach |
| **LLM-Only** | Direct LLM analysis without diff context (LangGraph) |
| **Structural Check** | Pre-check that analyzes code structure before LLM |
| **False Negative** | Missed violation (said no violation when there was one) |
| **False Positive** | Incorrect detection (said violation when there wasn't one) |
| **Precision** | Accuracy of positive predictions (TP / (TP + FP)) |
| **Recall** | Ability to find all positives (TP / (TP + FN)) |
| **Hybrid Approach** | Route to best system per violation type |

---

## 📞 Quick Help

### I need to...

**...deploy a system now**
→ Use LLM-Only (73.3% accuracy, 1.79s speed)

**...get maximum accuracy**
→ Use Hybrid approach (~85% accuracy, ~27s speed)

**...detect DIP violations**
→ Use Context-Managed (89.6% accuracy)

**...detect ISP violations**
→ Use LLM-Only (100.0% accuracy)

**...detect LSP violations**
→ Use Context-Managed (79.2% accuracy)

**...detect OCP violations**
→ Use LLM-Only (97.9% accuracy) - Context-Managed is broken

**...detect SRP violations**
→ Use LLM-Only (83.3% accuracy)

**...understand why errors occur**
→ Read [CONFUSION_MATRIX_REPORT.md](./CONFUSION_MATRIX_REPORT.md)

**...improve the system**
→ Read [STRUCTURAL_ANALYSIS_REPORT.md](./STRUCTURAL_ANALYSIS_REPORT.md)

**...see all the data**
→ Check [summary_tables/](./summary_tables/) and [visualizations/](./visualizations/)

---

## 🎯 Bottom Line

### For Production
**Use LLM-Only** - Best overall performance (73.3% accuracy, 74x faster)

### For Maximum Accuracy
**Use Hybrid** - Route by violation type (~85% accuracy expected)

### Critical Issues
1. **Never use Diff v10 for LSP** (6.2% accuracy)
2. **Never use Context-Managed for OCP** (37.5% accuracy)
3. **Never use LLM-Only for DIP** (25.0% accuracy)

### Best Practices
- Use the right system for each violation type
- Monitor performance continuously
- Fix critical issues before production deployment

---

**Quick Reference Card Version:** 1.0
**Last Updated:** 2026-01-29
**Full Documentation:** [README.md](./README.md)
