#!/usr/bin/env python3
"""
Enhanced analysis comparing diff_eval and langgraph workflows.
Includes:
1. Difficulty vs Runtime relationship
2. Comprehensive comparison between diff_eval and langgraph
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data():
    """Load both diff_eval and langgraph data."""
    diff_eval_path = Path('/Users/he/jcSOLID/analysis/analysis_output_diff_eval/diff_eval_detailed_results.csv')
    langgraph_path = Path('/Users/he/jcSOLID/analysis/analysis_output_langgraph/langgraph_detailed_results.csv')

    df_diff = pd.read_csv(diff_eval_path)
    df_diff['workflow'] = 'diff_eval'

    df_lang = pd.read_csv(langgraph_path)
    df_lang['workflow'] = 'langgraph'
    # Rename agent_type column to match
    if 'agent_type' in df_lang.columns:
        df_lang = df_lang.drop('agent_type', axis=1)

    return df_diff, df_lang

def create_difficulty_runtime_plots(df_diff, df_lang, output_dir):
    """Create difficulty vs runtime relationship plots."""
    output_dir = Path(output_dir)

    # 1. Difficulty vs Runtime for diff_eval
    plt.figure(figsize=(12, 6))

    level_order = ['EASY', 'MODERATE', 'HARD']

    # Box plot
    plt.subplot(1, 2, 1)
    data_to_plot = [df_diff[df_diff['level'] == level]['processing_time'].values
                    for level in level_order]
    bp = plt.boxplot(data_to_plot, labels=level_order, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    plt.ylabel('Processing Time (seconds)')
    plt.title('Diff_Eval: Processing Time by Difficulty Level')
    plt.grid(axis='y', alpha=0.3)

    # Violin plot
    plt.subplot(1, 2, 2)
    df_diff_sorted = df_diff.copy()
    df_diff_sorted['level'] = pd.Categorical(df_diff_sorted['level'],
                                              categories=level_order,
                                              ordered=True)
    sns.violinplot(data=df_diff_sorted, x='level', y='processing_time',
                   order=level_order, palette='Set2')
    plt.ylabel('Processing Time (seconds)')
    plt.xlabel('Difficulty Level')
    plt.title('Diff_Eval: Runtime Distribution by Difficulty')
    plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / '09_diff_eval_difficulty_vs_runtime.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Difficulty vs Runtime for langgraph
    plt.figure(figsize=(12, 6))

    # Box plot
    plt.subplot(1, 2, 1)
    data_to_plot = [df_lang[df_lang['level'] == level]['processing_time'].values
                    for level in level_order]
    bp = plt.boxplot(data_to_plot, labels=level_order, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightgreen')
    plt.ylabel('Processing Time (seconds)')
    plt.title('Langgraph: Processing Time by Difficulty Level')
    plt.grid(axis='y', alpha=0.3)

    # Violin plot
    plt.subplot(1, 2, 2)
    df_lang_sorted = df_lang.copy()
    df_lang_sorted['level'] = pd.Categorical(df_lang_sorted['level'],
                                              categories=level_order,
                                              ordered=True)
    sns.violinplot(data=df_lang_sorted, x='level', y='processing_time',
                   order=level_order, palette='Set3')
    plt.ylabel('Processing Time (seconds)')
    plt.xlabel('Difficulty Level')
    plt.title('Langgraph: Runtime Distribution by Difficulty')
    plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / '09_langgraph_difficulty_vs_runtime.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Side-by-side comparison
    plt.figure(figsize=(14, 6))

    # Combine data
    df_combined = pd.concat([df_diff, df_lang])
    df_combined['level'] = pd.Categorical(df_combined['level'],
                                          categories=level_order,
                                          ordered=True)

    sns.boxplot(data=df_combined, x='level', y='processing_time',
                hue='workflow', order=level_order)
    plt.ylabel('Processing Time (seconds)')
    plt.xlabel('Difficulty Level')
    plt.title('Processing Time Comparison: Diff_Eval vs Langgraph by Difficulty')
    plt.legend(title='Workflow')
    plt.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / '10_combined_difficulty_vs_runtime.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Statistical summary table
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.axis('tight')
    ax.axis('off')

    summary_data = []
    for workflow in ['diff_eval', 'langgraph']:
        df_work = df_combined[df_combined['workflow'] == workflow]
        for level in level_order:
            df_level = df_work[df_work['level'] == level]
            summary_data.append([
                workflow,
                level,
                f"{df_level['processing_time'].mean():.2f}",
                f"{df_level['processing_time'].median():.2f}",
                f"{df_level['processing_time'].std():.2f}",
                f"{df_level['processing_time'].min():.2f}",
                f"{df_level['processing_time'].max():.2f}"
            ])

    table = ax.table(cellText=summary_data,
                     colLabels=['Workflow', 'Level', 'Mean', 'Median', 'Std Dev', 'Min', 'Max'],
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.15, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Color header
    for i in range(7):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    plt.title('Processing Time Statistics by Difficulty Level',
              fontsize=14, fontweight='bold', pad=20)
    plt.savefig(output_dir / '11_runtime_statistics_table.png',
                dpi=300, bbox_inches='tight')
    plt.close()

def create_comparison_visualizations(df_diff, df_lang, output_dir):
    """Create comprehensive comparison visualizations."""
    output_dir = Path(output_dir)

    # 1. Overall Accuracy Comparison
    plt.figure(figsize=(12, 6))

    comparison_data = []
    for workflow, df in [('diff_eval', df_diff), ('langgraph', df_lang)]:
        for model in df['model'].unique():
            model_df = df[df['model'] == model]
            comparison_data.append({
                'workflow': workflow,
                'model': model,
                'accuracy': model_df['detection_success'].mean()
            })

    df_comp = pd.DataFrame(comparison_data)

    # Group by model
    models = df_comp['model'].unique()
    x = np.arange(len(models))
    width = 0.35

    diff_vals = [df_comp[(df_comp['workflow'] == 'diff_eval') &
                         (df_comp['model'] == m)]['accuracy'].values[0]
                 if len(df_comp[(df_comp['workflow'] == 'diff_eval') &
                               (df_comp['model'] == m)]) > 0 else 0
                 for m in models]
    lang_vals = [df_comp[(df_comp['workflow'] == 'langgraph') &
                         (df_comp['model'] == m)]['accuracy'].values[0]
                 if len(df_comp[(df_comp['workflow'] == 'langgraph') &
                               (df_comp['model'] == m)]) > 0 else 0
                 for m in models]

    plt.bar(x - width/2, diff_vals, width, label='diff_eval', alpha=0.8)
    plt.bar(x + width/2, lang_vals, width, label='langgraph', alpha=0.8)

    plt.xlabel('Model')
    plt.ylabel('Accuracy')
    plt.title('Overall Accuracy Comparison: Diff_Eval vs Langgraph')
    plt.xticks(x, models, rotation=45, ha='right')
    plt.legend()
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, (d, l) in enumerate(zip(diff_vals, lang_vals)):
        if d > 0:
            plt.text(i - width/2, d + 0.02, f'{d:.1%}',
                    ha='center', va='bottom', fontsize=8)
        if l > 0:
            plt.text(i + width/2, l + 0.02, f'{l:.1%}',
                    ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_dir / '12_accuracy_comparison_by_model.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Violation Type Comparison
    plt.figure(figsize=(14, 6))

    violation_comp = []
    for workflow, df in [('diff_eval', df_diff), ('langgraph', df_lang)]:
        for violation in df['violation_type'].unique():
            viol_df = df[df['violation_type'] == violation]
            violation_comp.append({
                'workflow': workflow,
                'violation': violation,
                'accuracy': viol_df['detection_success'].mean()
            })

    df_viol = pd.DataFrame(violation_comp)

    violations = sorted(df_viol['violation'].unique())
    x = np.arange(len(violations))
    width = 0.35

    diff_vals = [df_viol[(df_viol['workflow'] == 'diff_eval') &
                         (df_viol['violation'] == v)]['accuracy'].values[0]
                 if len(df_viol[(df_viol['workflow'] == 'diff_eval') &
                               (df_viol['violation'] == v)]) > 0 else 0
                 for v in violations]
    lang_vals = [df_viol[(df_viol['workflow'] == 'langgraph') &
                         (df_viol['violation'] == v)]['accuracy'].values[0]
                 if len(df_viol[(df_viol['workflow'] == 'langgraph') &
                               (df_viol['violation'] == v)]) > 0 else 0
                 for v in violations]

    plt.bar(x - width/2, diff_vals, width, label='diff_eval', alpha=0.8, color='coral')
    plt.bar(x + width/2, lang_vals, width, label='langgraph', alpha=0.8, color='skyblue')

    plt.xlabel('Violation Type')
    plt.ylabel('Accuracy')
    plt.title('Accuracy by Violation Type: Diff_Eval vs Langgraph')
    plt.xticks(x, violations)
    plt.legend()
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, (d, l) in enumerate(zip(diff_vals, lang_vals)):
        plt.text(i - width/2, d + 0.02, f'{d:.1%}',
                ha='center', va='bottom', fontsize=9)
        plt.text(i + width/2, l + 0.02, f'{l:.1%}',
                ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '13_accuracy_comparison_by_violation.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Processing Time Comparison
    plt.figure(figsize=(12, 6))

    df_combined = pd.concat([df_diff, df_lang])

    sns.boxplot(data=df_combined, x='workflow', y='processing_time',
                palette=['coral', 'skyblue'])
    plt.ylabel('Processing Time (seconds)')
    plt.xlabel('Workflow')
    plt.title('Processing Time Distribution: Diff_Eval vs Langgraph')
    plt.grid(axis='y', alpha=0.3)

    # Add mean markers
    for i, workflow in enumerate(['diff_eval', 'langgraph']):
        mean_val = df_combined[df_combined['workflow'] == workflow]['processing_time'].mean()
        plt.plot(i, mean_val, 'D', color='red', markersize=10,
                label=f'Mean: {mean_val:.2f}s' if i == 0 else f'{mean_val:.2f}s')

    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / '14_runtime_comparison.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Difficulty Level Comparison
    plt.figure(figsize=(14, 6))

    level_comp = []
    for workflow, df in [('diff_eval', df_diff), ('langgraph', df_lang)]:
        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = df[df['level'] == level]
            level_comp.append({
                'workflow': workflow,
                'level': level,
                'accuracy': level_df['detection_success'].mean()
            })

    df_level = pd.DataFrame(level_comp)

    levels = ['EASY', 'MODERATE', 'HARD']
    x = np.arange(len(levels))
    width = 0.35

    diff_vals = [df_level[(df_level['workflow'] == 'diff_eval') &
                          (df_level['level'] == l)]['accuracy'].values[0]
                 for l in levels]
    lang_vals = [df_level[(df_level['workflow'] == 'langgraph') &
                          (df_level['level'] == l)]['accuracy'].values[0]
                 for l in levels]

    plt.bar(x - width/2, diff_vals, width, label='diff_eval', alpha=0.8, color='coral')
    plt.bar(x + width/2, lang_vals, width, label='langgraph', alpha=0.8, color='skyblue')

    plt.xlabel('Difficulty Level')
    plt.ylabel('Accuracy')
    plt.title('Accuracy by Difficulty Level: Diff_Eval vs Langgraph')
    plt.xticks(x, levels)
    plt.legend()
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)

    # Add value labels
    for i, (d, l) in enumerate(zip(diff_vals, lang_vals)):
        plt.text(i - width/2, d + 0.02, f'{d:.1%}',
                ha='center', va='bottom', fontsize=9)
        plt.text(i + width/2, l + 0.02, f'{l:.1%}',
                ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '15_accuracy_comparison_by_level.png',
                dpi=300, bbox_inches='tight')
    plt.close()

def generate_comparison_report(df_diff, df_lang, output_file):
    """Generate comprehensive comparison report."""
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE COMPARISON: DIFF_EVAL vs LANGGRAPH\n")
        f.write("=" * 80 + "\n\n")

        # Overall Statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Diff_Eval:\n")
        f.write(f"  Total Examples: {len(df_diff)}\n")
        f.write(f"  Overall Accuracy: {df_diff['detection_success'].mean():.2%}\n")
        f.write(f"  Avg Processing Time: {df_diff['processing_time'].mean():.2f}s\n")
        f.write(f"  Median Processing Time: {df_diff['processing_time'].median():.2f}s\n\n")

        f.write(f"Langgraph:\n")
        f.write(f"  Total Examples: {len(df_lang)}\n")
        f.write(f"  Overall Accuracy: {df_lang['detection_success'].mean():.2%}\n")
        f.write(f"  Avg Processing Time: {df_lang['processing_time'].mean():.2f}s\n")
        f.write(f"  Median Processing Time: {df_lang['processing_time'].median():.2f}s\n\n")

        # Performance Gap
        acc_gap = df_lang['detection_success'].mean() - df_diff['detection_success'].mean()
        time_gap = df_diff['processing_time'].mean() - df_lang['processing_time'].mean()

        f.write("PERFORMANCE GAP\n")
        f.write("-" * 80 + "\n")
        f.write(f"Accuracy Difference: {acc_gap:+.2%} ")
        f.write(f"({'Langgraph better' if acc_gap > 0 else 'Diff_Eval better'})\n")
        f.write(f"Speed Difference: {time_gap:+.2f}s ")
        f.write(f"({'Langgraph faster' if time_gap > 0 else 'Diff_Eval faster'})\n\n")

        # Model Comparison
        f.write("MODEL-BY-MODEL COMPARISON\n")
        f.write("-" * 80 + "\n")

        # Find common models
        diff_models = set(df_diff['model'].unique())
        lang_models = set(df_lang['model'].unique())
        common_models = diff_models & lang_models

        for model in sorted(common_models):
            diff_acc = df_diff[df_diff['model'] == model]['detection_success'].mean()
            lang_acc = df_lang[df_lang['model'] == model]['detection_success'].mean()
            diff_time = df_diff[df_diff['model'] == model]['processing_time'].mean()
            lang_time = df_lang[df_lang['model'] == model]['processing_time'].mean()

            f.write(f"\n{model}:\n")
            f.write(f"  Diff_Eval: {diff_acc:.2%} accuracy, {diff_time:.2f}s avg time\n")
            f.write(f"  Langgraph: {lang_acc:.2%} accuracy, {lang_time:.2f}s avg time\n")
            f.write(f"  Gap: {lang_acc - diff_acc:+.2%} accuracy, {diff_time - lang_time:+.2f}s time\n")

        # Violation Type Comparison
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIOLATION TYPE COMPARISON\n")
        f.write("-" * 80 + "\n")

        violations = sorted(set(df_diff['violation_type'].unique()) |
                          set(df_lang['violation_type'].unique()))

        for violation in violations:
            diff_viol = df_diff[df_diff['violation_type'] == violation]
            lang_viol = df_lang[df_lang['violation_type'] == violation]

            if len(diff_viol) > 0 and len(lang_viol) > 0:
                diff_acc = diff_viol['detection_success'].mean()
                lang_acc = lang_viol['detection_success'].mean()

                f.write(f"\n{violation}:\n")
                f.write(f"  Diff_Eval: {diff_acc:.2%}\n")
                f.write(f"  Langgraph: {lang_acc:.2%}\n")
                f.write(f"  Gap: {lang_acc - diff_acc:+.2%}\n")

        # Difficulty Level Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("DIFFICULTY LEVEL ANALYSIS\n")
        f.write("-" * 80 + "\n")

        for level in ['EASY', 'MODERATE', 'HARD']:
            diff_level = df_diff[df_diff['level'] == level]
            lang_level = df_lang[df_lang['level'] == level]

            diff_acc = diff_level['detection_success'].mean()
            lang_acc = lang_level['detection_success'].mean()
            diff_time = diff_level['processing_time'].mean()
            lang_time = lang_level['processing_time'].mean()

            f.write(f"\n{level}:\n")
            f.write(f"  Diff_Eval: {diff_acc:.2%} accuracy, {diff_time:.2f}s avg time\n")
            f.write(f"  Langgraph: {lang_acc:.2%} accuracy, {lang_time:.2f}s avg time\n")
            f.write(f"  Gap: {lang_acc - diff_acc:+.2%} accuracy, {diff_time - lang_time:+.2f}s time\n")

        # Runtime vs Difficulty Correlation
        f.write("\n" + "=" * 80 + "\n")
        f.write("RUNTIME vs DIFFICULTY CORRELATION\n")
        f.write("-" * 80 + "\n")

        f.write("\nDiff_Eval - Processing Time by Difficulty:\n")
        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = df_diff[df_diff['level'] == level]
            f.write(f"  {level}: Mean={level_df['processing_time'].mean():.2f}s, ")
            f.write(f"Median={level_df['processing_time'].median():.2f}s, ")
            f.write(f"Std={level_df['processing_time'].std():.2f}s\n")

        f.write("\nLanggraph - Processing Time by Difficulty:\n")
        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = df_lang[df_lang['level'] == level]
            f.write(f"  {level}: Mean={level_df['processing_time'].mean():.2f}s, ")
            f.write(f"Median={level_df['processing_time'].median():.2f}s, ")
            f.write(f"Std={level_df['processing_time'].std():.2f}s\n")

        # Key Insights
        f.write("\n" + "=" * 80 + "\n")
        f.write("KEY INSIGHTS\n")
        f.write("-" * 80 + "\n\n")

        f.write("1. ACCURACY:\n")
        if acc_gap > 0.1:
            f.write(f"   - Langgraph significantly outperforms diff_eval (+{acc_gap:.2%})\n")
        elif acc_gap < -0.1:
            f.write(f"   - Diff_eval significantly outperforms langgraph (+{-acc_gap:.2%})\n")
        else:
            f.write(f"   - Both workflows show similar accuracy (±{abs(acc_gap):.2%})\n")

        f.write("\n2. PROCESSING SPEED:\n")
        if time_gap > 10:
            f.write(f"   - Langgraph is much faster ({time_gap:.2f}s faster on average)\n")
        elif time_gap < -10:
            f.write(f"   - Diff_eval is much faster ({-time_gap:.2f}s faster on average)\n")
        else:
            f.write(f"   - Both workflows have similar speed (±{abs(time_gap):.2f}s)\n")

        f.write("\n3. DIFFICULTY IMPACT:\n")
        diff_easy_hard = (df_diff[df_diff['level'] == 'EASY']['processing_time'].mean() -
                         df_diff[df_diff['level'] == 'HARD']['processing_time'].mean())
        lang_easy_hard = (df_lang[df_lang['level'] == 'EASY']['processing_time'].mean() -
                         df_lang[df_lang['level'] == 'HARD']['processing_time'].mean())

        f.write(f"   - Diff_eval: HARD takes {-diff_easy_hard:.2f}s more than EASY\n")
        f.write(f"   - Langgraph: HARD takes {-lang_easy_hard:.2f}s more than EASY\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF COMPARISON REPORT\n")
        f.write("=" * 80 + "\n")

def main():
    print("Loading data...")
    df_diff, df_lang = load_data()

    print(f"Diff_Eval: {len(df_diff)} records")
    print(f"Langgraph: {len(df_lang)} records")

    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_diff_eval')

    print("\nCreating difficulty vs runtime visualizations...")
    create_difficulty_runtime_plots(df_diff, df_lang, output_dir)

    print("Creating comparison visualizations...")
    create_comparison_visualizations(df_diff, df_lang, output_dir)

    print("Generating comparison report...")
    report_file = output_dir / 'comparison_diff_eval_vs_langgraph.txt'
    generate_comparison_report(df_diff, df_lang, report_file)

    print(f"\nAll outputs saved to: {output_dir}")
    print("\nGenerated files:")
    print("  - 09_diff_eval_difficulty_vs_runtime.png")
    print("  - 09_langgraph_difficulty_vs_runtime.png")
    print("  - 10_combined_difficulty_vs_runtime.png")
    print("  - 11_runtime_statistics_table.png")
    print("  - 12_accuracy_comparison_by_model.png")
    print("  - 13_accuracy_comparison_by_violation.png")
    print("  - 14_runtime_comparison.png")
    print("  - 15_accuracy_comparison_by_level.png")
    print("  - comparison_diff_eval_vs_langgraph.txt")
    print("\nAnalysis complete!")

if __name__ == '__main__':
    main()
