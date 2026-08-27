"""
SOLID Principles Benchmark Analysis - Langgraph vs Legacy Single-Agent Comparison
Compares langgraph single-agent with legacy single-agent performance
"""

import json
import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict

# Set style for professional visualizations
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.dpi'] = 150

# Color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#4CAF50',
    'error': '#E74C3C',
    'neutral': '#7F8C8D',
    'langgraph': '#3498DB',
    'legacy': '#9B59B6'
}

MODEL_COLORS = {
    'gemma3-4b': '#2E86AB',
    'qwen3-4b': '#A23B72',
    'llama3-2-3b': '#F18F01',
    'qwen3-8b': '#4CAF50',
    'deepseek-r1-8b': '#9B59B6',
    'llama3-1-8b': '#E74C3C'
}

VIOLATION_COLORS = {
    'SRP': '#3498DB',
    'OCP': '#2ECC71',
    'LSP': '#E74C3C',
    'ISP': '#9B59B6',
    'DIP': '#F39C12'
}


def load_results(base_path, subfolder):
    """Load results for specified subfolder"""
    results = {}
    agent_path = Path(base_path) / 'local' / 'single_agent' / subfolder

    if not agent_path.exists():
        print(f"Path not found: {agent_path}")
        return results

    for model_dir in agent_path.iterdir():
        if model_dir.is_dir():
            for result_name in ['detection_results.json', 'detection_results_thinking.json']:
                result_file = model_dir / result_name
                if result_file.exists():
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        model_name = model_dir.name
                        results[model_name] = data
                        print(f"Loaded [{subfolder}]: {model_name} ({data.get('total_examples', 0)} examples)")
                    break

    return results


def extract_metrics(results, agent_type):
    """Extract detailed metrics from results"""
    all_records = []

    for model_name, data in results.items():
        by_violation = data.get('by_violation_type', {})

        for violation_type, violation_data in by_violation.items():
            for example in violation_data.get('results', []):
                record = {
                    'agent_type': agent_type,
                    'model': model_name,
                    'violation_type': violation_type,
                    'example_id': example.get('example_id', ''),
                    'level': example.get('level', 'UNKNOWN'),
                    'language': example.get('language', 'UNKNOWN'),
                    'detection_success': example.get('detection_success', False),
                    'detected_violation_type': example.get('detected_violation_type'),
                    'actual_violation_type': violation_type,
                    'processing_time': example.get('processing_time_seconds', 0),
                    'api_call_success': example.get('api_call_success', True)
                }
                all_records.append(record)

    return pd.DataFrame(all_records)


def calculate_accuracy_metrics(df):
    """Calculate accuracy metrics"""
    model_accuracy = df.groupby('model').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    model_accuracy.columns = ['correct', 'total', 'accuracy']

    violation_accuracy = df.groupby('violation_type').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    violation_accuracy.columns = ['correct', 'total', 'accuracy']

    cross_accuracy = df.groupby(['model', 'violation_type']).agg({
        'detection_success': 'mean'
    }).round(4).unstack(fill_value=0)
    cross_accuracy.columns = cross_accuracy.columns.droplevel(0)

    return model_accuracy, violation_accuracy, cross_accuracy


def create_comparison_visualizations(langgraph_df, legacy_df, output_dir):
    """Create comparison visualizations between langgraph and legacy single-agent"""
    os.makedirs(output_dir, exist_ok=True)

    # Get common models
    langgraph_models = set(langgraph_df['model'].unique())
    legacy_models = set(legacy_df['model'].unique())
    common_models = sorted(langgraph_models & legacy_models)

    print(f"Langgraph models: {sorted(langgraph_models)}")
    print(f"Legacy models: {sorted(legacy_models)}")
    print(f"Common models for comparison: {common_models}")

    # 1. Side-by-side Accuracy Comparison (common models)
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(common_models))
        width = 0.35

        langgraph_acc = [langgraph_df[langgraph_df['model'] == m]['detection_success'].mean() * 100 for m in common_models]
        legacy_acc = [legacy_df[legacy_df['model'] == m]['detection_success'].mean() * 100 for m in common_models]

        bars1 = ax.bar(x - width/2, langgraph_acc, width, label='Langgraph', color=COLORS['langgraph'], alpha=0.8)
        bars2 = ax.bar(x + width/2, legacy_acc, width, label='Legacy', color=COLORS['legacy'], alpha=0.8)

        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Langgraph vs Legacy Single-Agent: Detection Accuracy Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(common_models, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 100)

        for bar, acc in zip(bars1, langgraph_acc):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
        for bar, acc in zip(bars2, legacy_acc):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/01_comparison_accuracy_by_model.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 2. Accuracy Difference (Langgraph - Legacy)
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        diff = [langgraph_acc[i] - legacy_acc[i] for i in range(len(common_models))]
        colors = [COLORS['success'] if d >= 0 else COLORS['error'] for d in diff]

        bars = ax.bar(common_models, diff, color=colors, edgecolor='white', linewidth=1.2)

        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_ylabel('Accuracy Difference (%)')
        ax.set_title('Langgraph vs Legacy Single-Agent: Accuracy Improvement\n(Positive = Langgraph Better)')
        plt.xticks(rotation=45, ha='right')

        for bar, d in zip(bars, diff):
            ypos = bar.get_height() + 0.5 if d >= 0 else bar.get_height() - 1.5
            ax.text(bar.get_x() + bar.get_width()/2, ypos,
                    f'{d:+.1f}%', ha='center', va='bottom' if d >= 0 else 'top', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/02_comparison_accuracy_difference.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 3. Accuracy by Violation Type Comparison
    fig, ax = plt.subplots(figsize=(12, 6))

    violations = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    x = np.arange(len(violations))
    width = 0.35

    langgraph_v_acc = [langgraph_df[langgraph_df['violation_type'] == v]['detection_success'].mean() * 100 for v in violations]
    legacy_v_acc = [legacy_df[legacy_df['violation_type'] == v]['detection_success'].mean() * 100 for v in violations]

    bars1 = ax.bar(x - width/2, langgraph_v_acc, width, label='Langgraph', color=COLORS['langgraph'], alpha=0.8)
    bars2 = ax.bar(x + width/2, legacy_v_acc, width, label='Legacy', color=COLORS['legacy'], alpha=0.8)

    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Langgraph vs Legacy Single-Agent: Accuracy by Violation Type')
    ax.set_xticks(x)
    ax.set_xticklabels(violations)
    ax.legend()
    ax.set_ylim(0, 100)

    for bar, acc in zip(bars1, langgraph_v_acc):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
    for bar, acc in zip(bars2, legacy_v_acc):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_comparison_accuracy_by_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Violation Type Accuracy Difference
    fig, ax = plt.subplots(figsize=(10, 6))

    v_diff = [langgraph_v_acc[i] - legacy_v_acc[i] for i in range(len(violations))]
    colors = [COLORS['success'] if d >= 0 else COLORS['error'] for d in v_diff]

    bars = ax.bar(violations, v_diff, color=colors, edgecolor='white', linewidth=1.2)

    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_ylabel('Accuracy Difference (%)')
    ax.set_title('Langgraph vs Legacy: Accuracy Improvement by Violation Type\n(Positive = Langgraph Better)')

    for bar, d in zip(bars, v_diff):
        ypos = bar.get_height() + 0.5 if d >= 0 else bar.get_height() - 1.5
        ax.text(bar.get_x() + bar.get_width()/2, ypos,
                f'{d:+.1f}%', ha='center', va='bottom' if d >= 0 else 'top', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_comparison_violation_difference.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Runtime Comparison
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(common_models))
        width = 0.35

        langgraph_rt = [langgraph_df[langgraph_df['model'] == m]['processing_time'].mean() for m in common_models]
        legacy_rt = [legacy_df[legacy_df['model'] == m]['processing_time'].mean() for m in common_models]

        bars1 = ax.bar(x - width/2, langgraph_rt, width, label='Langgraph', color=COLORS['langgraph'], alpha=0.8)
        bars2 = ax.bar(x + width/2, legacy_rt, width, label='Legacy', color=COLORS['legacy'], alpha=0.8)

        ax.set_ylabel('Mean Processing Time (seconds)')
        ax.set_title('Langgraph vs Legacy Single-Agent: Runtime Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(common_models, rotation=45, ha='right')
        ax.legend()

        for bar, rt in zip(bars1, langgraph_rt):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{rt:.2f}s', ha='center', va='bottom', fontsize=9)
        for bar, rt in zip(bars2, legacy_rt):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    f'{rt:.2f}s', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/05_comparison_runtime.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 6. Combined Accuracy vs Runtime Scatter
    fig, ax = plt.subplots(figsize=(12, 8))

    # Langgraph points
    for model in langgraph_df['model'].unique():
        model_data = langgraph_df[langgraph_df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()
        ax.scatter(runtime, acc, s=150, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   marker='o', edgecolor='white', linewidth=2, alpha=0.7)

    # Legacy points
    for model in legacy_df['model'].unique():
        model_data = legacy_df[legacy_df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()
        ax.scatter(runtime, acc, s=150, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   marker='s', edgecolor='black', linewidth=2, alpha=0.7)

    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Langgraph'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10, markeredgecolor='black', label='Legacy'),
    ]
    for model, color in MODEL_COLORS.items():
        if model in langgraph_df['model'].unique() or model in legacy_df['model'].unique():
            legend_elements.append(
                Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=model)
            )

    ax.legend(handles=legend_elements, loc='best', frameon=True)
    ax.set_xlabel('Mean Processing Time (seconds)')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Langgraph vs Legacy: Accuracy-Runtime Trade-off\n(Circle=Langgraph, Square=Legacy)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_comparison_accuracy_vs_runtime_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 7. Heatmap Comparison (side by side)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Langgraph heatmap
    langgraph_cross = langgraph_df.groupby(['model', 'violation_type'])['detection_success'].mean().unstack(fill_value=0) * 100
    sns.heatmap(langgraph_cross, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=axes[0], cbar_kws={'label': 'Accuracy (%)'})
    axes[0].set_title('Langgraph: Model x Violation Accuracy')
    axes[0].set_xlabel('Violation Type')
    axes[0].set_ylabel('Model')

    # Legacy heatmap
    legacy_cross = legacy_df.groupby(['model', 'violation_type'])['detection_success'].mean().unstack(fill_value=0) * 100
    sns.heatmap(legacy_cross, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=axes[1], cbar_kws={'label': 'Accuracy (%)'})
    axes[1].set_title('Legacy: Model x Violation Accuracy')
    axes[1].set_xlabel('Violation Type')
    axes[1].set_ylabel('Model')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/07_comparison_heatmaps.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 8. Overall Summary Bar Chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Accuracy subplot
    acc_cats = ['Overall', 'SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    langgraph_overall_acc = langgraph_df['detection_success'].mean() * 100
    legacy_overall_acc = legacy_df['detection_success'].mean() * 100

    langgraph_acc_vals = [langgraph_overall_acc] + langgraph_v_acc
    legacy_acc_vals = [legacy_overall_acc] + legacy_v_acc

    x_acc = np.arange(len(acc_cats))
    width = 0.35
    bars1 = ax1.bar(x_acc - width/2, langgraph_acc_vals, width, label='Langgraph', color=COLORS['langgraph'], alpha=0.8)
    bars2 = ax1.bar(x_acc + width/2, legacy_acc_vals, width, label='Legacy', color=COLORS['legacy'], alpha=0.8)

    ax1.set_ylabel('Accuracy (%)')
    ax1.set_title('Accuracy Comparison Summary')
    ax1.set_xticks(x_acc)
    ax1.set_xticklabels(acc_cats)
    ax1.legend()
    ax1.set_ylim(0, 100)

    # Runtime subplot
    rt_models = common_models if common_models else list(set(langgraph_df['model'].unique()) | set(legacy_df['model'].unique()))
    langgraph_rts = [langgraph_df[langgraph_df['model'] == m]['processing_time'].mean() if m in langgraph_df['model'].values else 0 for m in rt_models]
    legacy_rts = [legacy_df[legacy_df['model'] == m]['processing_time'].mean() if m in legacy_df['model'].values else 0 for m in rt_models]

    x_rt = np.arange(len(rt_models))
    bars3 = ax2.bar(x_rt - width/2, langgraph_rts, width, label='Langgraph', color=COLORS['langgraph'], alpha=0.8)
    bars4 = ax2.bar(x_rt + width/2, legacy_rts, width, label='Legacy', color=COLORS['legacy'], alpha=0.8)

    ax2.set_ylabel('Mean Processing Time (seconds)')
    ax2.set_title('Runtime Comparison Summary')
    ax2.set_xticks(x_rt)
    ax2.set_xticklabels(rt_models, rotation=45, ha='right')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(f'{output_dir}/08_comparison_summary.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Comparison visualizations saved to: {output_dir}")

    return langgraph_v_acc, legacy_v_acc


def generate_comparison_report(langgraph_df, legacy_df, output_dir):
    """Generate comparison report"""
    report = []
    report.append("=" * 80)
    report.append("SOLID BENCHMARK: LANGGRAPH vs LEGACY SINGLE-AGENT COMPARISON REPORT")
    report.append("=" * 80)
    report.append("")

    # Summary
    report.append("## OVERALL SUMMARY")
    report.append("-" * 40)

    langgraph_acc = langgraph_df['detection_success'].mean() * 100
    legacy_acc = legacy_df['detection_success'].mean() * 100
    langgraph_rt = langgraph_df['processing_time'].mean()
    legacy_rt = legacy_df['processing_time'].mean()

    report.append(f"Langgraph Single-Agent:")
    report.append(f"  - Total Examples: {len(langgraph_df)}")
    report.append(f"  - Models: {langgraph_df['model'].nunique()} ({', '.join(sorted(langgraph_df['model'].unique()))})")
    report.append(f"  - Overall Accuracy: {langgraph_acc:.2f}%")
    report.append(f"  - Mean Runtime: {langgraph_rt:.2f}s")
    report.append("")

    report.append(f"Legacy Single-Agent:")
    report.append(f"  - Total Examples: {len(legacy_df)}")
    report.append(f"  - Models: {legacy_df['model'].nunique()} ({', '.join(sorted(legacy_df['model'].unique()))})")
    report.append(f"  - Overall Accuracy: {legacy_acc:.2f}%")
    report.append(f"  - Mean Runtime: {legacy_rt:.2f}s")
    report.append("")

    report.append(f"DIFFERENCE (Langgraph - Legacy):")
    report.append(f"  - Accuracy: {langgraph_acc - legacy_acc:+.2f}%")
    report.append(f"  - Runtime: {langgraph_rt - legacy_rt:+.2f}s")
    report.append("")

    # Accuracy by Model Comparison
    report.append("## ACCURACY BY MODEL")
    report.append("-" * 40)

    common_models = sorted(set(langgraph_df['model'].unique()) & set(legacy_df['model'].unique()))
    all_models = sorted(set(langgraph_df['model'].unique()) | set(legacy_df['model'].unique()))

    report.append(f"{'Model':<20} {'Langgraph':>12} {'Legacy':>12} {'Diff':>10}")
    report.append("-" * 56)

    for model in all_models:
        lg_acc = langgraph_df[langgraph_df['model'] == model]['detection_success'].mean() * 100 if model in langgraph_df['model'].values else None
        le_acc = legacy_df[legacy_df['model'] == model]['detection_success'].mean() * 100 if model in legacy_df['model'].values else None

        lg_str = f"{lg_acc:.2f}%" if lg_acc is not None else "N/A"
        le_str = f"{le_acc:.2f}%" if le_acc is not None else "N/A"
        d_str = f"{lg_acc - le_acc:+.2f}%" if lg_acc is not None and le_acc is not None else "N/A"

        report.append(f"{model:<20} {lg_str:>12} {le_str:>12} {d_str:>10}")

    report.append("")

    # Accuracy by Violation Type
    report.append("## ACCURACY BY VIOLATION TYPE")
    report.append("-" * 40)

    violations = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    report.append(f"{'Violation':<10} {'Langgraph':>12} {'Legacy':>12} {'Diff':>10}")
    report.append("-" * 46)

    for v in violations:
        lg_acc = langgraph_df[langgraph_df['violation_type'] == v]['detection_success'].mean() * 100
        le_acc = legacy_df[legacy_df['violation_type'] == v]['detection_success'].mean() * 100
        diff = lg_acc - le_acc

        report.append(f"{v:<10} {lg_acc:>11.2f}% {le_acc:>11.2f}% {diff:>+9.2f}%")

    report.append("")

    # Runtime by Model Comparison
    report.append("## RUNTIME BY MODEL")
    report.append("-" * 40)

    report.append(f"{'Model':<20} {'Langgraph':>12} {'Legacy':>12} {'Diff':>10}")
    report.append("-" * 56)

    for model in all_models:
        lg_rt = langgraph_df[langgraph_df['model'] == model]['processing_time'].mean() if model in langgraph_df['model'].values else None
        le_rt = legacy_df[legacy_df['model'] == model]['processing_time'].mean() if model in legacy_df['model'].values else None

        lg_str = f"{lg_rt:.2f}s" if lg_rt is not None else "N/A"
        le_str = f"{le_rt:.2f}s" if le_rt is not None else "N/A"
        d_str = f"{lg_rt - le_rt:+.2f}s" if lg_rt is not None and le_rt is not None else "N/A"

        report.append(f"{model:<20} {lg_str:>12} {le_str:>12} {d_str:>10}")

    report.append("")

    # Key Findings
    report.append("## KEY FINDINGS")
    report.append("-" * 40)

    if langgraph_acc > legacy_acc:
        report.append(f"- Langgraph approach shows HIGHER accuracy ({langgraph_acc:.2f}% vs {legacy_acc:.2f}%)")
    elif langgraph_acc < legacy_acc:
        report.append(f"- Legacy approach shows HIGHER accuracy ({legacy_acc:.2f}% vs {langgraph_acc:.2f}%)")
    else:
        report.append(f"- Both approaches have SAME accuracy ({langgraph_acc:.2f}%)")

    if langgraph_rt > legacy_rt:
        report.append(f"- Langgraph approach is SLOWER ({langgraph_rt:.2f}s vs {legacy_rt:.2f}s)")
    elif langgraph_rt < legacy_rt:
        report.append(f"- Langgraph approach is FASTER ({langgraph_rt:.2f}s vs {legacy_rt:.2f}s)")
    else:
        report.append(f"- Both approaches have SAME runtime ({langgraph_rt:.2f}s)")

    # Best improvements
    if common_models:
        improvements = []
        for model in common_models:
            lg_acc = langgraph_df[langgraph_df['model'] == model]['detection_success'].mean() * 100
            le_acc = legacy_df[legacy_df['model'] == model]['detection_success'].mean() * 100
            improvements.append((model, lg_acc - le_acc))

        improvements.sort(key=lambda x: x[1], reverse=True)

        if improvements[0][1] > 0:
            report.append(f"- Best improvement with Langgraph: {improvements[0][0]} ({improvements[0][1]:+.2f}%)")
        if improvements[-1][1] < 0:
            report.append(f"- Worst regression with Langgraph: {improvements[-1][0]} ({improvements[-1][1]:+.2f}%)")

    # Violation type insights
    report.append("")
    report.append("## VIOLATION TYPE INSIGHTS")
    report.append("-" * 40)

    v_improvements = []
    for v in violations:
        lg_acc = langgraph_df[langgraph_df['violation_type'] == v]['detection_success'].mean() * 100
        le_acc = legacy_df[legacy_df['violation_type'] == v]['detection_success'].mean() * 100
        v_improvements.append((v, lg_acc - le_acc))

    v_improvements.sort(key=lambda x: x[1], reverse=True)

    report.append(f"- Best improvement: {v_improvements[0][0]} ({v_improvements[0][1]:+.2f}%)")
    report.append(f"- Worst regression: {v_improvements[-1][0]} ({v_improvements[-1][1]:+.2f}%)")

    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    # Save report
    report_text = "\n".join(report)
    report_path = f"{output_dir}/comparison_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {report_path}")

    return report_text


def main():
    # Paths
    base_path = Path('result')
    output_dir = 'analysis_output_langgraph_vs_legacy'

    print("=" * 60)
    print("SOLID Benchmark - Langgraph vs Legacy Single-Agent Comparison")
    print("=" * 60)
    print()

    # Load Langgraph Results
    print("Loading Langgraph Single-Agent Results...")
    langgraph_results = load_results(base_path, 'langgraph')

    # Load Legacy Results
    print("\nLoading Legacy Single-Agent Results...")
    legacy_results = load_results(base_path, 'legacy')

    if not langgraph_results:
        print("No langgraph results found!")
        return

    if not legacy_results:
        print("No legacy results found!")
        return

    # Extract metrics
    print("\nExtracting metrics...")
    langgraph_df = extract_metrics(langgraph_results, 'langgraph')
    legacy_df = extract_metrics(legacy_results, 'legacy')

    print(f"Langgraph records: {len(langgraph_df)}")
    print(f"Legacy records: {len(legacy_df)}")

    # Create visualizations
    print("\n" + "=" * 40)
    print("CREATING COMPARISON VISUALIZATIONS")
    print("=" * 40)

    create_comparison_visualizations(langgraph_df, legacy_df, output_dir)

    # Generate report
    print("\n" + "=" * 40)
    print("GENERATING COMPARISON REPORT")
    print("=" * 40)

    generate_comparison_report(langgraph_df, legacy_df, output_dir)

    # Save data to CSV
    langgraph_df.to_csv(f'{output_dir}/langgraph_detailed_results.csv', index=False)
    legacy_df.to_csv(f'{output_dir}/legacy_detailed_results.csv', index=False)
    combined_df = pd.concat([langgraph_df, legacy_df], ignore_index=True)
    combined_df.to_csv(f'{output_dir}/combined_results.csv', index=False)
    print(f"\nResults saved to: {output_dir}/")


if __name__ == '__main__':
    main()
