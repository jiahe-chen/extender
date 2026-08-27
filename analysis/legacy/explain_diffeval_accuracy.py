"""
详细解释 DIFF_EVAL 准确率计算和为什么准确率较低
"""

import json
import pandas as pd
from collections import Counter

# 加载数据
print("="*80)
print("DIFF_EVAL 准确率详细分析")
print("="*80)

# 1. 从 CSV 读取结果
df = pd.read_csv(r'c:\Users\Jay\jcSOLID\analysis\analysis_output_top2_strategies\detailed_results.csv')
diff_df = df[df['strategy'] == 'diff_eval'].copy()

print(f"\n总样本数: {len(diff_df)}")
print(f"Top-1 正确数: {diff_df['top1_correct'].sum()}")
print(f"Top-1 准确率: {diff_df['top1_correct'].mean() * 100:.2f}%")
print(f"Top-2 正确数: {diff_df['top2_correct'].sum()}")
print(f"Top-2 准确率: {diff_df['top2_correct'].mean() * 100:.2f}%")

# 2. 分析预测分布
print("\n" + "="*80)
print("预测分布分析")
print("="*80)

print("\n第一个预测 (prediction_1) 的分布:")
pred1_counts = diff_df['prediction_1'].value_counts()
print(pred1_counts)

print("\n第二个预测 (prediction_2) 的分布:")
pred2_counts = diff_df['prediction_2'].value_counts()
print(pred2_counts)

# 3. 按实际违规类型分析
print("\n" + "="*80)
print("按实际违规类型的准确率")
print("="*80)

for violation in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
    viol_df = diff_df[diff_df['actual_violation'] == violation]
    if len(viol_df) > 0:
        top1_acc = viol_df['top1_correct'].mean() * 100
        top2_acc = viol_df['top2_correct'].mean() * 100

        print(f"\n{violation}:")
        print(f"  样本数: {len(viol_df)}")
        print(f"  Top-1 准确率: {top1_acc:.2f}%")
        print(f"  Top-2 准确率: {top2_acc:.2f}%")

        # 显示常见的错误预测
        wrong_df = viol_df[~viol_df['top1_correct']]
        if len(wrong_df) > 0:
            wrong_preds = wrong_df['prediction_1'].value_counts().head(3)
            print(f"  常见错误预测: {dict(wrong_preds)}")

# 4. 详细案例分析
print("\n" + "="*80)
print("具体案例分析")
print("="*80)

# 加载原始 JSON 数据
with open(r'c:\Users\Jay\jcSOLID\result\local\diff_eval\run_1\qwen3-8b\detection_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 分析几个典型案例
print("\n案例1: SRP_1 (Top-1 错误)")
srp_results = data['by_violation_type']['SRP']['results']
example1 = srp_results[0]
print(f"  Example ID: {example1['example_id']}")
print(f"  Ground Truth (实际): {example1['ground_truth']}")
print(f"  检测结果:")
for check in example1['all_checks']:
    status = "[YES]" if check['is_detected'] else "[NO]"
    print(f"    {check['violation_type']}: {status}")

detected = [c['violation_type'] for c in example1['all_checks'] if c['is_detected']]
print(f"  Top-2 预测: {detected[:2]}")
print(f"  结果: prediction_1={detected[0] if detected else None}, 实际={example1['ground_truth']}")
print(f"  Top-1 正确: {detected[0] == example1['ground_truth'] if detected else False}")

print("\n案例2: SRP_2 (Top-1 正确)")
example2 = srp_results[1]
print(f"  Example ID: {example2['example_id']}")
print(f"  Ground Truth (实际): {example2['ground_truth']}")
print(f"  检测结果:")
for check in example2['all_checks']:
    status = "[YES]" if check['is_detected'] else "[NO]"
    print(f"    {check['violation_type']}: {status}")

detected = [c['violation_type'] for c in example2['all_checks'] if c['is_detected']]
print(f"  Top-2 预测: {detected[:2]}")
print(f"  结果: prediction_1={detected[0] if detected else None}, 实际={example2['ground_truth']}")
print(f"  Top-1 正确: {detected[0] == example2['ground_truth'] if detected else False}")

# 5. 分析为什么准确率低
print("\n" + "="*80)
print("准确率低的原因分析")
print("="*80)

# 统计有多少个样本没有检测到任何违规
no_detection = diff_df[diff_df['prediction_1'].isna()]
print(f"\n1. 没有检测到任何违规的样本数: {len(no_detection)} ({len(no_detection)/len(diff_df)*100:.1f}%)")

# 统计有多少个样本检测到了错误的违规
wrong_first = diff_df[~diff_df['top1_correct'] & diff_df['prediction_1'].notna()]
print(f"2. 第一个预测错误的样本数: {len(wrong_first)} ({len(wrong_first)/len(diff_df)*100:.1f}%)")

# 统计第二个预测救回来的样本
saved_by_second = diff_df[~diff_df['top1_correct'] & diff_df['top2_correct']]
print(f"3. 被第二个预测救回的样本数: {len(saved_by_second)} ({len(saved_by_second)/len(diff_df)*100:.1f}%)")

# 统计完全错误的样本
completely_wrong = diff_df[~diff_df['top2_correct']]
print(f"4. Top-2 都错误的样本数: {len(completely_wrong)} ({len(completely_wrong)/len(diff_df)*100:.1f}%)")

# 6. 与其他策略对比
print("\n" + "="*80)
print("与其他策略对比")
print("="*80)

for strategy in ['single_agent', 'two_agent', 'diff_eval']:
    strat_df = df[df['strategy'] == strategy]
    print(f"\n{strategy.upper()}:")
    print(f"  Top-1 准确率: {strat_df['top1_correct'].mean() * 100:.2f}%")
    print(f"  Top-2 准确率: {strat_df['top2_correct'].mean() * 100:.2f}%")
    print(f"  Top-2 提升: +{(strat_df['top2_correct'].mean() - strat_df['top1_correct'].mean()) * 100:.2f}%")

# 7. 总结
print("\n" + "="*80)
print("总结")
print("="*80)

print("""
DIFF_EVAL 准确率较低的主要原因:

1. **系统性检查所有5个原则**: DIFF_EVAL 会检查所有 SOLID 原则，而不是直接预测最可能的违规
   - 这导致它可能检测到多个违规（包括错误的）
   - 第一个检测到的不一定是正确的

2. **检测顺序问题**: all_checks 数组按 SRP, OCP, LSP, ISP, DIP 顺序检查
   - 如果实际违规是 DIP，但 SRP 也被误检测，SRP 会排在第一位
   - 这解释了为什么 DIP 的 Top-1 准确率是 0%

3. **过度检测**: DIFF_EVAL 倾向于检测到多个违规（假阳性）
   - 这在某些情况下是好的（Top-2 准确率提升）
   - 但降低了 Top-1 的准确率

4. **处理时间长**: 150.65秒 vs 3.14秒 (single_agent)
   - 需要进行5次完整的检查
   - 包括结构化代码分析

优势:
- Top-2 准确率在某些违规类型上很高（OCP: 97.9%）
- 提供详细的解释和推理过程
- 适合研究和分析，不适合生产环境
""")

print("\n" + "="*80)
