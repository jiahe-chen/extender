"""
Check the actual detection_success rate from diff_eval JSON
"""

import json

# Load diff_eval data
with open(r'c:\Users\Jay\jcSOLID\result\local\diff_eval\run_1\qwen3-8b\detection_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

total = 0
success = 0

print("="*80)
print("DIFF_EVAL Detection Success Analysis")
print("="*80)

# Count by violation type
by_violation = {}

for vtype, vdata in data['by_violation_type'].items():
    by_violation[vtype] = {'total': 0, 'success': 0}

    for result in vdata['results']:
        total += 1
        by_violation[vtype]['total'] += 1

        if result.get('detection_success', False):
            success += 1
            by_violation[vtype]['success'] += 1

print(f"\nOverall:")
print(f"  Total examples: {total}")
print(f"  Detection success count: {success}")
print(f"  Detection success rate: {success/total*100:.2f}%")

print(f"\nBy Violation Type:")
for vtype in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
    if vtype in by_violation:
        v = by_violation[vtype]
        rate = v['success'] / v['total'] * 100 if v['total'] > 0 else 0
        print(f"  {vtype}: {v['success']}/{v['total']} = {rate:.2f}%")

print("\n" + "="*80)
print("Comparison with Current Analysis")
print("="*80)

# Load current analysis results
import pandas as pd
df = pd.read_csv(r'c:\Users\Jay\jcSOLID\analysis\analysis_output_top2_strategies\detailed_results.csv')
diff_df = df[df['strategy'] == 'diff_eval']

print(f"\nCurrent Analysis Results:")
print(f"  Top-1 Accuracy: {diff_df['top1_correct'].mean() * 100:.2f}%")
print(f"  Top-2 Accuracy: {diff_df['top2_correct'].mean() * 100:.2f}%")

print(f"\nActual JSON detection_success Rate: {success/total*100:.2f}%")

print(f"\nDifference:")
print(f"  detection_success vs Top-2: {(success/total - diff_df['top2_correct'].mean()) * 100:.2f}%")

print("\n" + "="*80)
print("Interpretation")
print("="*80)
print("""
detection_success = {:.2f}% means:
  - The ground truth violation WAS detected (appears in all_checks with is_detected=true)
  - But it might not be in the TOP 2 positions

Top-2 Accuracy = {:.2f}% means:
  - The ground truth violation is in the FIRST TWO detected violations
  - This is more strict than detection_success

The difference ({:.2f}%) represents cases where:
  - The ground truth was detected (detection_success=true)
  - But it was ranked 3rd or later (not in top-2)
""".format(success/total*100, diff_df['top2_correct'].mean() * 100,
           (success/total - diff_df['top2_correct'].mean()) * 100))

print("="*80)
