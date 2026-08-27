"""
Additional Deep Dive Analysis: Structural Analysis Effectiveness
Analyzing the impact and accuracy of structural pre-checks in Context-Managed Diff
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict, Counter

print("="*80)
print("STRUCTURAL ANALYSIS DEEP DIVE")
print("="*80)

# Load Context-Managed Diff data
with open(r'C:\Users\Jay\jcSOLID\result\local\diff_eval\qwen3-8b\detection_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract all results with structural checks
results_with_checks = []
for vtype, vdata in data['by_violation_type'].items():
    for result in vdata['results']:
        if result.get('all_checks') and len(result['all_checks']) > 0:
            result['ground_truth'] = vtype
            results_with_checks.append(result)

print(f"\nTotal examples with structural checks: {len(results_with_checks)}")

# ============================================================================
# 1. STRUCTURAL CHECK ACCURACY ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("1. STRUCTURAL CHECK ACCURACY BY VIOLATION TYPE")
print("="*80)

structural_stats = defaultdict(lambda: {
    'total': 0,
    'true_positive': 0,  # Correctly detected
    'true_negative': 0,  # Correctly said no violation
    'false_positive': 0, # Said violation when there wasn't
    'false_negative': 0  # Said no violation when there was
})

for result in results_with_checks:
    ground_truth = result['ground_truth']

    for check in result['all_checks']:
        if not isinstance(check, dict):
            continue

        check_vtype = check.get('violation_type', '')
        is_detected = check.get('is_detected', False)

        if check_vtype == ground_truth:
            # This is checking for the actual violation
            structural_stats[check_vtype]['total'] += 1
            if is_detected:
                structural_stats[check_vtype]['true_positive'] += 1
            else:
                structural_stats[check_vtype]['false_negative'] += 1
        else:
            # This is checking for a different violation (should be negative)
            if is_detected:
                structural_stats[check_vtype]['false_positive'] += 1
            else:
                structural_stats[check_vtype]['true_negative'] += 1

print("\nStructural Check Performance by Violation Type:")
print(f"{'Violation':<10} {'Total':<8} {'TP':<6} {'FN':<6} {'Recall':<10} {'FP':<6} {'TN':<6} {'Precision':<10}")
print("-"*80)

for vtype in sorted(structural_stats.keys()):
    stats = structural_stats[vtype]
    tp = stats['true_positive']
    fn = stats['false_negative']
    fp = stats['false_positive']
    tn = stats['true_negative']
    total = stats['total']

    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0

    print(f"{vtype:<10} {total:<8} {tp:<6} {fn:<6} {recall:<10.1%} {fp:<6} {tn:<6} {precision:<10.1%}")

# ============================================================================
# 2. IMPACT OF STRUCTURAL CHECKS ON FINAL ACCURACY
# ============================================================================
print("\n" + "="*80)
print("2. IMPACT OF STRUCTURAL CHECKS ON FINAL ACCURACY")
print("="*80)

# Analyze cases where structural check was wrong
structural_impact = {
    'correct_skip_correct_final': 0,  # Structural said no, final said no (correct)
    'correct_skip_wrong_final': 0,    # Structural said no, final said yes (structural was right)
    'wrong_skip_correct_final': 0,    # Structural said yes, final correct
    'wrong_skip_wrong_final': 0,      # Structural said yes, final wrong
    'fn_recovered': 0,                # Structural FN but final correct
    'fn_not_recovered': 0             # Structural FN and final wrong
}

for result in results_with_checks:
    ground_truth = result['ground_truth']
    final_detected = result['detected_violation_type']
    final_correct = result['detection_success']

    # Find structural check for ground truth
    structural_detected = None
    for check in result['all_checks']:
        if isinstance(check, dict) and check.get('violation_type') == ground_truth:
            structural_detected = check.get('is_detected', False)
            break

    if structural_detected is not None:
        if not structural_detected:
            # Structural check said no violation
            if final_correct:
                structural_impact['fn_recovered'] += 1
            else:
                structural_impact['fn_not_recovered'] += 1

print("\nStructural False Negative Recovery:")
print(f"  False negatives recovered by LLM: {structural_impact['fn_recovered']}")
print(f"  False negatives NOT recovered: {structural_impact['fn_not_recovered']}")
print(f"  Recovery rate: {structural_impact['fn_recovered']/(structural_impact['fn_recovered']+structural_impact['fn_not_recovered'])*100:.1f}%")

# ============================================================================
# 3. STRUCTURAL CHECK PATTERNS
# ============================================================================
print("\n" + "="*80)
print("3. STRUCTURAL CHECK PATTERNS")
print("="*80)

# Analyze which violations are most often skipped together
skip_patterns = defaultdict(int)

for result in results_with_checks:
    skipped = []
    for check in result['all_checks']:
        if isinstance(check, dict) and not check.get('is_detected', False):
            skipped.append(check.get('violation_type', ''))

    if len(skipped) > 1:
        pattern = tuple(sorted(skipped))
        skip_patterns[pattern] += 1

print("\nMost Common Skip Patterns (violations skipped together):")
for pattern, count in sorted(skip_patterns.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f"  {', '.join(pattern)}: {count} times")

# ============================================================================
# 4. DIFFICULTY LEVEL IMPACT ON STRUCTURAL CHECKS
# ============================================================================
print("\n" + "="*80)
print("4. STRUCTURAL CHECK ACCURACY BY DIFFICULTY")
print("="*80)

difficulty_stats = defaultdict(lambda: {'total': 0, 'fn': 0, 'tp': 0})

for result in results_with_checks:
    ground_truth = result['ground_truth']
    level = result.get('level', 'UNKNOWN')

    for check in result['all_checks']:
        if isinstance(check, dict) and check.get('violation_type') == ground_truth:
            difficulty_stats[level]['total'] += 1
            if check.get('is_detected', False):
                difficulty_stats[level]['tp'] += 1
            else:
                difficulty_stats[level]['fn'] += 1

print("\nStructural Check Recall by Difficulty:")
print(f"{'Level':<12} {'Total':<8} {'TP':<6} {'FN':<6} {'Recall':<10}")
print("-"*60)

for level in ['EASY', 'MODERATE', 'HARD']:
    stats = difficulty_stats[level]
    total = stats['total']
    tp = stats['tp']
    fn = stats['fn']
    recall = tp / total if total > 0 else 0
    print(f"{level:<12} {total:<8} {tp:<6} {fn:<6} {recall:<10.1%}")

# ============================================================================
# 5. LANGUAGE-SPECIFIC STRUCTURAL CHECK PERFORMANCE
# ============================================================================
print("\n" + "="*80)
print("5. STRUCTURAL CHECK ACCURACY BY LANGUAGE")
print("="*80)

language_stats = defaultdict(lambda: {'total': 0, 'fn': 0, 'tp': 0})

for result in results_with_checks:
    ground_truth = result['ground_truth']
    language = result.get('language', 'UNKNOWN')

    for check in result['all_checks']:
        if isinstance(check, dict) and check.get('violation_type') == ground_truth:
            language_stats[language]['total'] += 1
            if check.get('is_detected', False):
                language_stats[language]['tp'] += 1
            else:
                language_stats[language]['fn'] += 1

print("\nStructural Check Recall by Language:")
print(f"{'Language':<12} {'Total':<8} {'TP':<6} {'FN':<6} {'Recall':<10}")
print("-"*60)

for language in sorted(language_stats.keys()):
    stats = language_stats[language]
    total = stats['total']
    tp = stats['tp']
    fn = stats['fn']
    recall = tp / total if total > 0 else 0
    print(f"{language:<12} {total:<8} {tp:<6} {fn:<6} {recall:<10.1%}")

# ============================================================================
# 6. DETAILED FALSE NEGATIVE ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("6. DETAILED FALSE NEGATIVE ANALYSIS")
print("="*80)

false_negatives = []

for result in results_with_checks:
    ground_truth = result['ground_truth']

    for check in result['all_checks']:
        if isinstance(check, dict) and check.get('violation_type') == ground_truth:
            if not check.get('is_detected', False):
                false_negatives.append({
                    'example_id': result['example_id'],
                    'violation': ground_truth,
                    'level': result.get('level', 'UNKNOWN'),
                    'language': result.get('language', 'UNKNOWN'),
                    'final_correct': result['detection_success'],
                    'explanation': check.get('detailed_explanation', '')[:100]
                })

print(f"\nTotal False Negatives: {len(false_negatives)}")
print("\nFalse Negatives by Violation Type:")

fn_by_vtype = defaultdict(list)
for fn in false_negatives:
    fn_by_vtype[fn['violation']].append(fn)

for vtype in sorted(fn_by_vtype.keys()):
    fns = fn_by_vtype[vtype]
    recovered = sum(1 for fn in fns if fn['final_correct'])
    print(f"\n{vtype}: {len(fns)} false negatives ({recovered} recovered by LLM)")

    # Show examples
    for fn in fns[:3]:  # Show first 3
        status = "RECOVERED" if fn['final_correct'] else "NOT RECOVERED"
        print(f"  - {fn['example_id']} ({fn['level']}, {fn['language']}) [{status}]")
        print(f"    Reason: {fn['explanation']}")

# ============================================================================
# 7. EFFICIENCY ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("7. STRUCTURAL CHECK EFFICIENCY ANALYSIS")
print("="*80)

total_checks = 0
total_skips = 0
correct_skips = 0

for result in results_with_checks:
    ground_truth = result['ground_truth']

    for check in result['all_checks']:
        if isinstance(check, dict):
            total_checks += 1
            check_vtype = check.get('violation_type', '')
            is_detected = check.get('is_detected', False)

            if not is_detected:
                total_skips += 1
                # Correct skip if it's not the ground truth
                if check_vtype != ground_truth:
                    correct_skips += 1

print(f"\nTotal structural checks performed: {total_checks}")
print(f"Total skips (said no violation): {total_skips}")
print(f"Correct skips: {correct_skips}")
print(f"Incorrect skips (false negatives): {total_skips - correct_skips}")
print(f"\nSkip accuracy: {correct_skips/total_skips*100:.1f}%")
print(f"Efficiency gain: {total_skips/total_checks*100:.1f}% of checks skipped")

# ============================================================================
# 8. RECOMMENDATIONS
# ============================================================================
print("\n" + "="*80)
print("8. RECOMMENDATIONS FOR STRUCTURAL CHECK IMPROVEMENT")
print("="*80)

print("\nBased on the analysis:")
print("\n1. KEEP structural checks for:")
for vtype in sorted(structural_stats.keys()):
    stats = structural_stats[vtype]
    tp = stats['true_positive']
    fn = stats['false_negative']
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    if recall >= 0.90:  # 90% or better recall
        print(f"   - {vtype}: {recall:.1%} recall (excellent)")

print("\n2. IMPROVE structural checks for:")
for vtype in sorted(structural_stats.keys()):
    stats = structural_stats[vtype]
    tp = stats['true_positive']
    fn = stats['false_negative']
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    if 0.70 <= recall < 0.90:  # 70-90% recall
        print(f"   - {vtype}: {recall:.1%} recall (needs improvement)")

print("\n3. DISABLE or REDESIGN structural checks for:")
for vtype in sorted(structural_stats.keys()):
    stats = structural_stats[vtype]
    tp = stats['true_positive']
    fn = stats['false_negative']
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0

    if recall < 0.70:  # Below 70% recall
        print(f"   - {vtype}: {recall:.1%} recall (too many false negatives)")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
