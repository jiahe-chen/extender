"""
Visualization Script: Generate charts and graphs for the analysis
Creates visual representations of the comparison data
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

# Create output directory
output_dir = Path(r'C:\Users\Jay\jcSOLID\analysis\visualizations')
output_dir.mkdir(exist_ok=True)

print("Loading data...")

# Load data
def load_diff_eval_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    results = []
    for vtype, vdata in data['by_violation_type'].items():
        for result in vdata['results']:
            result['ground_truth'] = vtype
            results.append(result)
    return pd.DataFrame(results)

def load_langgraph_data(csv_path):
    df = pd.read_csv(csv_path)
    return df[df['model'] == 'qwen3-8b']

context_managed = load_diff_eval_data(
    r'C:\Users\Jay\jcSOLID\result\local\diff_eval\qwen3-8b\detection_results.json'
)
diff = load_diff_eval_data(
    r'C:\Users\Jay\jcSOLID\result\local\diff_eval_v10\qwen3-8b\detection_results.json'
)
llm_only = load_langgraph_data(
    r'C:\Users\Jay\jcSOLID\analysis\analysis_output_langgraph\langgraph_detailed_results.csv'
)

# Rename columns
context_managed = context_managed.rename(columns={'processing_time_seconds': 'processing_time'})
diff = diff.rename(columns={'processing_time_seconds': 'processing_time'})

print("Generating visualizations...")

# ============================================================================
# 1. Overall Accuracy Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

systems = ['Context-Managed\nDiff', 'Diff v10', 'LLM-Only']
accuracies = [
    context_managed['detection_success'].mean() * 100,
    diff['detection_success'].mean() * 100,
    llm_only['detection_success'].mean() * 100
]
colors = ['#3498db', '#e74c3c', '#2ecc71']

bars = ax.bar(systems, accuracies, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels on bars
for bar, acc in zip(bars, accuracies):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{acc:.1f}%',
            ha='center', va='bottom', fontsize=14, fontweight='bold')

ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax.set_title('Overall Accuracy Comparison: Qwen3-8B', fontsize=14, fontweight='bold')
ax.set_ylim(0, 100)
ax.axhline(y=70, color='gray', linestyle='--', alpha=0.5, label='70% threshold')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / '1_overall_accuracy.png', dpi=300, bbox_inches='tight')
print("Saved: 1_overall_accuracy.png")
plt.close()

# ============================================================================
# 2. Accuracy by Violation Type
# ============================================================================
fig, ax = plt.subplots(figsize=(12, 7))

violation_types = ['DIP', 'ISP', 'LSP', 'OCP', 'SRP']
x = np.arange(len(violation_types))
width = 0.25

cm_accs = [context_managed[context_managed['ground_truth']==v]['detection_success'].mean() * 100
           for v in violation_types]
diff_accs = [diff[diff['ground_truth']==v]['detection_success'].mean() * 100
             for v in violation_types]
llm_accs = [llm_only[llm_only['violation_type']==v]['detection_success'].mean() * 100
            for v in violation_types]

bars1 = ax.bar(x - width, cm_accs, width, label='Context-Managed', color='#3498db', alpha=0.8)
bars2 = ax.bar(x, diff_accs, width, label='Diff v10', color='#e74c3c', alpha=0.8)
bars3 = ax.bar(x + width, llm_accs, width, label='LLM-Only', color='#2ecc71', alpha=0.8)

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.0f}%',
                ha='center', va='bottom', fontsize=9)

ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax.set_title('Accuracy by Violation Type', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(violation_types, fontsize=11)
ax.legend(fontsize=10)
ax.set_ylim(0, 110)
ax.axhline(y=70, color='gray', linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig(output_dir / '2_accuracy_by_violation.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 2_accuracy_by_violation.png")
plt.close()

# ============================================================================
# 3. Accuracy by Difficulty Level
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

levels = ['EASY', 'MODERATE', 'HARD']
x = np.arange(len(levels))
width = 0.25

cm_accs = [context_managed[context_managed['level']==l]['detection_success'].mean() * 100
           for l in levels]
diff_accs = [diff[diff['level']==l]['detection_success'].mean() * 100
             for l in levels]
llm_accs = [llm_only[llm_only['level']==l]['detection_success'].mean() * 100
            for l in levels]

bars1 = ax.bar(x - width, cm_accs, width, label='Context-Managed', color='#3498db', alpha=0.8)
bars2 = ax.bar(x, diff_accs, width, label='Diff v10', color='#e74c3c', alpha=0.8)
bars3 = ax.bar(x + width, llm_accs, width, label='LLM-Only', color='#2ecc71', alpha=0.8)

# Add value labels
for bars in [bars1, bars2, bars3]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%',
                ha='center', va='bottom', fontsize=10)

ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax.set_title('Accuracy by Difficulty Level', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(levels, fontsize=11)
ax.legend(fontsize=10)
ax.set_ylim(0, 100)

plt.tight_layout()
plt.savefig(output_dir / '3_accuracy_by_difficulty.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 3_accuracy_by_difficulty.png")
plt.close()

# ============================================================================
# 4. Processing Time Comparison
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

systems = ['Context-Managed\nDiff', 'Diff v10', 'LLM-Only']
times = [
    context_managed['processing_time'].mean(),
    diff['processing_time'].mean(),
    llm_only['processing_time'].mean()
]
colors = ['#3498db', '#e74c3c', '#2ecc71']

bars = ax.bar(systems, times, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels
for bar, time in zip(bars, times):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{time:.1f}s',
            ha='center', va='bottom', fontsize=12, fontweight='bold')

ax.set_ylabel('Average Processing Time (seconds)', fontsize=12, fontweight='bold')
ax.set_title('Processing Time Comparison', fontsize=14, fontweight='bold')
ax.set_yscale('log')  # Log scale to show the huge difference

plt.tight_layout()
plt.savefig(output_dir / '4_processing_time.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 4_processing_time.png")
plt.close()

# ============================================================================
# 5. Accuracy vs Speed Trade-off
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 8))

systems_data = [
    ('Context-Managed', context_managed['detection_success'].mean() * 100,
     context_managed['processing_time'].mean(), '#3498db'),
    ('Diff v10', diff['detection_success'].mean() * 100,
     diff['processing_time'].mean(), '#e74c3c'),
    ('LLM-Only', llm_only['detection_success'].mean() * 100,
     llm_only['processing_time'].mean(), '#2ecc71')
]

for name, acc, time, color in systems_data:
    ax.scatter(time, acc, s=500, alpha=0.7, color=color, edgecolors='black', linewidth=2)
    ax.annotate(name, (time, acc), fontsize=12, fontweight='bold',
                ha='center', va='center')

ax.set_xlabel('Average Processing Time (seconds, log scale)', fontsize=12, fontweight='bold')
ax.set_ylabel('Accuracy (%)', fontsize=12, fontweight='bold')
ax.set_title('Accuracy vs Speed Trade-off', fontsize=14, fontweight='bold')
ax.set_xscale('log')
ax.grid(True, alpha=0.3)

# Add quadrant lines
ax.axhline(y=70, color='gray', linestyle='--', alpha=0.5, label='70% accuracy')
ax.axvline(x=10, color='gray', linestyle='--', alpha=0.5, label='10s threshold')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / '5_accuracy_vs_speed.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 5_accuracy_vs_speed.png")
plt.close()

# ============================================================================
# 6. Heatmap: Accuracy by Violation and System
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

# Prepare data
violation_types = ['DIP', 'ISP', 'LSP', 'OCP', 'SRP']
systems = ['Context-Managed', 'Diff v10', 'LLM-Only']

data = []
for system_name, df in [('Context-Managed', context_managed),
                         ('Diff v10', diff),
                         ('LLM-Only', llm_only)]:
    row = []
    for vtype in violation_types:
        if system_name == 'LLM-Only':
            acc = df[df['violation_type']==vtype]['detection_success'].mean() * 100
        else:
            acc = df[df['ground_truth']==vtype]['detection_success'].mean() * 100
        row.append(acc)
    data.append(row)

# Create heatmap
im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

# Set ticks
ax.set_xticks(np.arange(len(violation_types)))
ax.set_yticks(np.arange(len(systems)))
ax.set_xticklabels(violation_types, fontsize=11)
ax.set_yticklabels(systems, fontsize=11)

# Add text annotations
for i in range(len(systems)):
    for j in range(len(violation_types)):
        text = ax.text(j, i, f'{data[i][j]:.1f}%',
                      ha="center", va="center", color="black", fontsize=10, fontweight='bold')

ax.set_title('Accuracy Heatmap by Violation Type and System', fontsize=14, fontweight='bold')
fig.colorbar(im, ax=ax, label='Accuracy (%)')

plt.tight_layout()
plt.savefig(output_dir / '6_accuracy_heatmap.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 6_accuracy_heatmap.png")
plt.close()

# ============================================================================
# 7. Error Distribution by Violation Type
# ============================================================================
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

for idx, (name, df, ax) in enumerate([
    ('Context-Managed', context_managed, axes[0]),
    ('Diff v10', diff, axes[1]),
    ('LLM-Only', llm_only, axes[2])
]):
    violation_col = 'ground_truth' if name != 'LLM-Only' else 'violation_type'

    error_counts = []
    for vtype in violation_types:
        total = len(df[df[violation_col]==vtype])
        errors = len(df[(df[violation_col]==vtype) & (df['detection_success']==False)])
        error_counts.append(errors)

    bars = ax.bar(violation_types, error_counts, color='#e74c3c', alpha=0.7)

    # Add value labels
    for bar, count in zip(bars, error_counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{count}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.set_title(name, fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Errors', fontsize=10)
    ax.set_ylim(0, max(error_counts) * 1.2)

plt.suptitle('Error Distribution by Violation Type', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(output_dir / '7_error_distribution.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 7_error_distribution.png")
plt.close()

# ============================================================================
# 8. Structural Analysis: Skip Patterns
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

# Count structural skips
skip_counts = {'ISP': 180, 'LSP': 160, 'DIP': 62, 'OCP': 28, 'SRP': 21}
violations = list(skip_counts.keys())
counts = list(skip_counts.values())

bars = ax.barh(violations, counts, color='#9b59b6', alpha=0.7)

# Add value labels
for bar, count in zip(bars, counts):
    width = bar.get_width()
    ax.text(width, bar.get_y() + bar.get_height()/2.,
            f'{count} ({count/sum(counts)*100:.1f}%)',
            ha='left', va='center', fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_xlabel('Number of Skips', fontsize=12, fontweight='bold')
ax.set_title('Structural Analysis: Violations Skipped (Context-Managed)',
             fontsize=14, fontweight='bold')
ax.set_xlim(0, max(counts) * 1.3)

plt.tight_layout()
plt.savefig(output_dir / '8_structural_skips.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 8_structural_skips.png")
plt.close()

# ============================================================================
# 9. Structural Check Recall by Violation
# ============================================================================
fig, ax = plt.subplots(figsize=(10, 6))

recalls = {'ISP': 100.0, 'OCP': 100.0, 'DIP': 97.9, 'SRP': 93.8, 'LSP': 80.9}
violations = list(recalls.keys())
recall_values = list(recalls.values())
colors = ['#2ecc71' if r >= 95 else '#f39c12' if r >= 85 else '#e74c3c' for r in recall_values]

bars = ax.bar(violations, recall_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

# Add value labels
for bar, recall in zip(bars, recall_values):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{recall:.1f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_ylabel('Recall (%)', fontsize=12, fontweight='bold')
ax.set_title('Structural Check Recall by Violation Type', fontsize=14, fontweight='bold')
ax.set_ylim(0, 110)
ax.axhline(y=95, color='green', linestyle='--', alpha=0.5, label='95% threshold (excellent)')
ax.axhline(y=85, color='orange', linestyle='--', alpha=0.5, label='85% threshold (good)')
ax.legend()

plt.tight_layout()
plt.savefig(output_dir / '9_structural_recall.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 9_structural_recall.png")
plt.close()

# ============================================================================
# 10. Summary Dashboard
# ============================================================================
fig = plt.figure(figsize=(16, 10))
gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

# Overall accuracy
ax1 = fig.add_subplot(gs[0, :])
systems = ['Context-Managed', 'Diff v10', 'LLM-Only']
accuracies = [66.7, 46.7, 73.3]
colors = ['#3498db', '#e74c3c', '#2ecc71']
bars = ax1.bar(systems, accuracies, color=colors, alpha=0.8)
for bar, acc in zip(bars, accuracies):
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
            f'{acc:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
ax1.set_ylabel('Accuracy (%)', fontweight='bold')
ax1.set_title('Overall Accuracy', fontsize=13, fontweight='bold')
ax1.set_ylim(0, 100)

# Processing time
ax2 = fig.add_subplot(gs[1, 0])
times = [132.55, 135.95, 1.79]
bars = ax2.bar(systems, times, color=colors, alpha=0.8)
ax2.set_ylabel('Time (s)', fontweight='bold')
ax2.set_title('Avg Processing Time', fontsize=11, fontweight='bold')
ax2.set_yscale('log')
ax2.tick_params(axis='x', rotation=45)

# Best violation for each system
ax3 = fig.add_subplot(gs[1, 1])
best_violations = ['DIP\n89.6%', 'ISP\n77.1%', 'ISP\n100%']
ax3.bar(systems, [89.6, 77.1, 100], color=colors, alpha=0.8)
ax3.set_ylabel('Accuracy (%)', fontweight='bold')
ax3.set_title('Best Violation Type', fontsize=11, fontweight='bold')
ax3.tick_params(axis='x', rotation=45)

# Worst violation for each system
ax4 = fig.add_subplot(gs[1, 2])
worst_violations = ['OCP\n37.5%', 'LSP\n6.2%', 'DIP\n25.0%']
ax4.bar(systems, [37.5, 6.2, 25.0], color=colors, alpha=0.8)
ax4.set_ylabel('Accuracy (%)', fontweight='bold')
ax4.set_title('Worst Violation Type', fontsize=11, fontweight='bold')
ax4.tick_params(axis='x', rotation=45)

# Accuracy by difficulty
ax5 = fig.add_subplot(gs[2, :])
levels = ['EASY', 'MODERATE', 'HARD']
x = np.arange(len(levels))
width = 0.25
cm_accs = [73.8, 65.0, 61.3]
diff_accs = [73.8, 47.5, 18.8]
llm_accs = [78.8, 72.5, 68.8]
ax5.bar(x - width, cm_accs, width, label='Context-Managed', color='#3498db', alpha=0.8)
ax5.bar(x, diff_accs, width, label='Diff v10', color='#e74c3c', alpha=0.8)
ax5.bar(x + width, llm_accs, width, label='LLM-Only', color='#2ecc71', alpha=0.8)
ax5.set_xticks(x)
ax5.set_xticklabels(levels)
ax5.set_ylabel('Accuracy (%)', fontweight='bold')
ax5.set_title('Accuracy by Difficulty Level', fontsize=13, fontweight='bold')
ax5.legend()

plt.suptitle('Qwen3-8B SOLID Violation Detection: Summary Dashboard',
             fontsize=16, fontweight='bold', y=0.98)
plt.savefig(output_dir / '10_summary_dashboard.png', dpi=300, bbox_inches='tight')
print("[OK] Saved: 10_summary_dashboard.png")
plt.close()

print(f"\n{'='*80}")
print("All visualizations saved to:", output_dir)
print(f"{'='*80}")
print("\nGenerated files:")
for i in range(1, 11):
    print(f"  {i}. {list(output_dir.glob(f'{i}_*.png'))[0].name}")
