"""
Comprehensive Analysis: Context-Managed Diff vs Diff vs LLM-Only
Analyzing Qwen3-8B performance across three different approaches
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

# Load data
def load_diff_eval_data(file_path):
    """Load diff_eval format data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for vtype, vdata in data['by_violation_type'].items():
        for result in vdata['results']:
            result['ground_truth'] = vtype
            results.append(result)

    return pd.DataFrame(results)

def load_langgraph_data(csv_path):
    """Load langgraph CSV data"""
    df = pd.read_csv(csv_path)
    return df[df['model'] == 'qwen3-8b']

# Load all three datasets
print("Loading datasets...")
context_managed_diff = load_diff_eval_data(
    r'C:\Users\Jay\jcSOLID\result\local\diff_eval\qwen3-8b\detection_results.json'
)
diff = load_diff_eval_data(
    r'C:\Users\Jay\jcSOLID\result\local\diff_eval_v10\qwen3-8b\detection_results.json'
)
llm_only = load_langgraph_data(
    r'C:\Users\Jay\jcSOLID\analysis\analysis_output_langgraph\langgraph_detailed_results.csv'
)

# Rename columns for consistency
context_managed_diff = context_managed_diff.rename(columns={
    'processing_time_seconds': 'processing_time'
})
diff = diff.rename(columns={
    'processing_time_seconds': 'processing_time'
})

print("\n" + "="*80)
print("COMPREHENSIVE ANALYSIS: QWEN3-8B PERFORMANCE COMPARISON")
print("="*80)

# ============================================================================
# 1. OVERALL PERFORMANCE METRICS
# ============================================================================
print("\n1. OVERALL PERFORMANCE METRICS")
print("-"*80)

metrics = {
    'System': ['Context-Managed Diff', 'Diff', 'LLM-Only'],
    'Total Examples': [
        len(context_managed_diff),
        len(diff),
        len(llm_only)
    ],
    'Overall Accuracy': [
        context_managed_diff['detection_success'].mean(),
        diff['detection_success'].mean(),
        llm_only['detection_success'].mean()
    ],
    'Avg Time (s)': [
        context_managed_diff['processing_time'].mean(),
        diff['processing_time'].mean(),
        llm_only['processing_time'].mean()
    ],
    'Median Time (s)': [
        context_managed_diff['processing_time'].median(),
        diff['processing_time'].median(),
        llm_only['processing_time'].median()
    ],
    'Max Time (s)': [
        context_managed_diff['processing_time'].max(),
        diff['processing_time'].max(),
        llm_only['processing_time'].max()
    ]
}

metrics_df = pd.DataFrame(metrics)
print(metrics_df.to_string(index=False))

# Calculate improvements
print("\nRelative Performance:")
print(f"  Context-Managed vs Diff:")
print(f"    Accuracy: {(metrics['Overall Accuracy'][0]/metrics['Overall Accuracy'][1]-1)*100:+.1f}%")
print(f"    Speed: {(1-metrics['Avg Time (s)'][0]/metrics['Avg Time (s)'][1])*100:+.1f}%")
print(f"  Context-Managed vs LLM-Only:")
print(f"    Accuracy: {(metrics['Overall Accuracy'][0]/metrics['Overall Accuracy'][2]-1)*100:+.1f}%")
print(f"    Speed: {(1-metrics['Avg Time (s)'][0]/metrics['Avg Time (s)'][2])*100:+.1f}%")

# ============================================================================
# 2. ACCURACY BY VIOLATION TYPE
# ============================================================================
print("\n\n2. ACCURACY BY VIOLATION TYPE")
print("-"*80)

violation_types = sorted(context_managed_diff['ground_truth'].unique())
vtype_results = []

for vtype in violation_types:
    cm_acc = context_managed_diff[context_managed_diff['ground_truth']==vtype]['detection_success'].mean()
    d_acc = diff[diff['ground_truth']==vtype]['detection_success'].mean()
    lo_acc = llm_only[llm_only['violation_type']==vtype]['detection_success'].mean()

    vtype_results.append({
        'Violation': vtype,
        'Context-Managed': f"{cm_acc:.1%}",
        'Diff': f"{d_acc:.1%}",
        'LLM-Only': f"{lo_acc:.1%}",
        'CM vs Diff': f"{(cm_acc-d_acc)*100:+.1f}%",
        'CM vs LLM': f"{(cm_acc-lo_acc)*100:+.1f}%"
    })

vtype_df = pd.DataFrame(vtype_results)
print(vtype_df.to_string(index=False))

# ============================================================================
# 3. ACCURACY BY DIFFICULTY LEVEL
# ============================================================================
print("\n\n3. ACCURACY BY DIFFICULTY LEVEL")
print("-"*80)

level_results = []
for level in ['EASY', 'MODERATE', 'HARD']:
    cm_acc = context_managed_diff[context_managed_diff['level']==level]['detection_success'].mean()
    d_acc = diff[diff['level']==level]['detection_success'].mean()
    lo_acc = llm_only[llm_only['level']==level]['detection_success'].mean()

    level_results.append({
        'Level': level,
        'Context-Managed': f"{cm_acc:.1%}",
        'Diff': f"{d_acc:.1%}",
        'LLM-Only': f"{lo_acc:.1%}",
        'CM vs Diff': f"{(cm_acc-d_acc)*100:+.1f}%",
        'CM vs LLM': f"{(cm_acc-lo_acc)*100:+.1f}%"
    })

level_df = pd.DataFrame(level_results)
print(level_df.to_string(index=False))

# ============================================================================
# 4. ACCURACY BY LANGUAGE
# ============================================================================
print("\n\n4. ACCURACY BY LANGUAGE")
print("-"*80)

# Normalize language names
context_managed_diff['language_norm'] = context_managed_diff['language'].replace({'C#': 'CSHARP'})
diff['language_norm'] = diff['language'].replace({'C#': 'CSHARP'})
llm_only['language_norm'] = llm_only['language'].replace({'C#': 'CSHARP'})

lang_results = []
for lang in sorted(context_managed_diff['language_norm'].unique()):
    cm_acc = context_managed_diff[context_managed_diff['language_norm']==lang]['detection_success'].mean()
    d_acc = diff[diff['language_norm']==lang]['detection_success'].mean()
    lo_acc = llm_only[llm_only['language_norm']==lang]['detection_success'].mean()
    count = len(context_managed_diff[context_managed_diff['language_norm']==lang])

    lang_results.append({
        'Language': lang,
        'Count': count,
        'Context-Managed': f"{cm_acc:.1%}",
        'Diff': f"{d_acc:.1%}",
        'LLM-Only': f"{lo_acc:.1%}",
        'CM vs Diff': f"{(cm_acc-d_acc)*100:+.1f}%"
    })

lang_df = pd.DataFrame(lang_results)
print(lang_df.to_string(index=False))

# ============================================================================
# 5. PROCESSING TIME ANALYSIS
# ============================================================================
print("\n\n5. PROCESSING TIME ANALYSIS")
print("-"*80)

time_stats = []
for name, df in [('Context-Managed', context_managed_diff),
                  ('Diff', diff),
                  ('LLM-Only', llm_only)]:
    time_stats.append({
        'System': name,
        'Mean': f"{df['processing_time'].mean():.2f}s",
        'Median': f"{df['processing_time'].median():.2f}s",
        'Std Dev': f"{df['processing_time'].std():.2f}s",
        'Min': f"{df['processing_time'].min():.2f}s",
        'Max': f"{df['processing_time'].max():.2f}s",
        'P95': f"{df['processing_time'].quantile(0.95):.2f}s"
    })

time_df = pd.DataFrame(time_stats)
print(time_df.to_string(index=False))

# Time by difficulty
print("\nProcessing Time by Difficulty:")
for level in ['EASY', 'MODERATE', 'HARD']:
    cm_time = context_managed_diff[context_managed_diff['level']==level]['processing_time'].mean()
    d_time = diff[diff['level']==level]['processing_time'].mean()
    lo_time = llm_only[llm_only['level']==level]['processing_time'].mean()
    print(f"  {level:8s}: CM={cm_time:5.2f}s, Diff={d_time:5.2f}s, LLM={lo_time:5.2f}s")

# ============================================================================
# 6. ERROR ANALYSIS
# ============================================================================
print("\n\n6. ERROR ANALYSIS")
print("-"*80)

def analyze_errors(df, name):
    """Analyze error patterns"""
    errors = df[df['detection_success'] == False]

    print(f"\n{name}:")
    print(f"  Total Errors: {len(errors)} / {len(df)} ({len(errors)/len(df)*100:.1f}%)")

    # Determine the ground truth column name
    gt_col = 'ground_truth' if 'ground_truth' in df.columns else 'violation_type'

    # Errors by violation type
    print(f"  Errors by Violation Type:")
    for vtype in sorted(df[gt_col].unique()):
        vtype_total = len(df[df[gt_col]==vtype])
        vtype_errors = len(errors[errors[gt_col]==vtype])
        print(f"    {vtype}: {vtype_errors}/{vtype_total} ({vtype_errors/vtype_total*100:.1f}%)")

    # Errors by difficulty
    print(f"  Errors by Difficulty:")
    for level in ['EASY', 'MODERATE', 'HARD']:
        level_total = len(df[df['level']==level])
        level_errors = len(errors[errors['level']==level])
        print(f"    {level}: {level_errors}/{level_total} ({level_errors/level_total*100:.1f}%)")

    # Most common misclassifications
    if 'detected_violation_type' in df.columns:
        print(f"  Top Misclassifications:")
        misclass = errors.groupby([gt_col, 'detected_violation_type']).size().sort_values(ascending=False).head(5)
        for (gt, detected), count in misclass.items():
            print(f"    {gt} → {detected}: {count} times")

analyze_errors(context_managed_diff, "Context-Managed Diff")
analyze_errors(diff, "Diff")
analyze_errors(llm_only, "LLM-Only")

# ============================================================================
# 7. STRUCTURAL ANALYSIS (all_checks)
# ============================================================================
print("\n\n7. STRUCTURAL ANALYSIS (Context-Managed Diff Only)")
print("-"*80)

# Check if all_checks exists
if 'all_checks' in context_managed_diff.columns:
    total_with_checks = context_managed_diff['all_checks'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False).sum()
    print(f"Examples with structural checks: {total_with_checks} / {len(context_managed_diff)}")

    # Analyze structural check effectiveness
    structural_skips = []
    false_positives = []

    for idx, row in context_managed_diff.iterrows():
        if isinstance(row['all_checks'], list) and len(row['all_checks']) > 0:
            ground_truth = row['ground_truth']

            # Count how many violations were checked
            try:
                checked_violations = [check.get('violation_type', '') for check in row['all_checks'] if isinstance(check, dict)]
            except:
                continue

            # Check if ground truth was correctly identified as not detected in structural check
            for check in row['all_checks']:
                if not isinstance(check, dict):
                    continue

                vtype = check.get('violation_type', '')
                is_detected = check.get('is_detected', False)

                if vtype == ground_truth:
                    if not is_detected:
                        # Structural check said no violation, but there is one (false negative)
                        false_positives.append({
                            'example_id': row['example_id'],
                            'violation': ground_truth,
                            'level': row['level']
                        })
                else:
                    if not is_detected:
                        # Correctly skipped a non-relevant violation
                        structural_skips.append(vtype)

    print(f"\nStructural Check Statistics:")
    print(f"  Total structural skips: {len(structural_skips)}")
    print(f"  Average skips per example: {len(structural_skips)/total_with_checks:.1f}")
    print(f"  False negatives (missed violations): {len(false_positives)}")

    if structural_skips:
        from collections import Counter
        skip_counts = Counter(structural_skips)
        print(f"\n  Most frequently skipped violations:")
        for vtype, count in skip_counts.most_common():
            print(f"    {vtype}: {count} times")

    if false_positives:
        print(f"\n  False negatives by violation type:")
        fn_by_type = pd.DataFrame(false_positives).groupby('violation').size()
        for vtype, count in fn_by_type.items():
            print(f"    {vtype}: {count}")

# ============================================================================
# 8. KEY FINDINGS AND RECOMMENDATIONS
# ============================================================================
print("\n\n8. KEY FINDINGS AND RECOMMENDATIONS")
print("="*80)

cm_acc = context_managed_diff['detection_success'].mean()
d_acc = diff['detection_success'].mean()
lo_acc = llm_only['detection_success'].mean()

cm_time = context_managed_diff['processing_time'].mean()
d_time = diff['processing_time'].mean()
lo_time = llm_only['processing_time'].mean()

print("\nA. Performance Summary:")
print(f"   1. Context-Managed Diff: {cm_acc:.1%} accuracy, {cm_time:.2f}s avg time")
print(f"   2. Diff: {d_acc:.1%} accuracy, {d_time:.2f}s avg time")
print(f"   3. LLM-Only: {lo_acc:.1%} accuracy, {lo_time:.2f}s avg time")

print("\nB. Best System by Metric:")
best_acc = max(cm_acc, d_acc, lo_acc)
best_time = min(cm_time, d_time, lo_time)

if cm_acc == best_acc:
    print(f"   Accuracy: Context-Managed Diff ({cm_acc:.1%})")
elif d_acc == best_acc:
    print(f"   Accuracy: Diff ({d_acc:.1%})")
else:
    print(f"   Accuracy: LLM-Only ({lo_acc:.1%})")

if cm_time == best_time:
    print(f"   Speed: Context-Managed Diff ({cm_time:.2f}s)")
elif d_time == best_time:
    print(f"   Speed: Diff ({d_time:.2f}s)")
else:
    print(f"   Speed: LLM-Only ({lo_time:.2f}s)")

print("\nC. Strengths and Weaknesses:")
print("   Context-Managed Diff:")
for vtype in violation_types:
    cm_v = context_managed_diff[context_managed_diff['ground_truth']==vtype]['detection_success'].mean()
    d_v = diff[diff['ground_truth']==vtype]['detection_success'].mean()
    if cm_v > d_v + 0.1:
        print(f"     + Strong at {vtype}: {cm_v:.1%} vs {d_v:.1%}")
    elif cm_v < d_v - 0.1:
        print(f"     - Weak at {vtype}: {cm_v:.1%} vs {d_v:.1%}")

print("\nD. Recommendations:")
if cm_acc > d_acc and cm_time < d_time * 1.5:
    print("   → Use Context-Managed Diff: Better accuracy with acceptable speed")
elif d_acc > cm_acc * 1.1:
    print("   → Use Diff: Significantly better accuracy")
elif cm_time < d_time * 0.5:
    print("   → Use Context-Managed Diff: Much faster with similar accuracy")
else:
    print("   → Consider hybrid approach based on violation type")

print("\n" + "="*80)
print("Analysis complete!")
print("="*80)
