"""
SOLID Principles Benchmark Analysis - Two Agent + Comparison
Analyzes two-agent results and compares with single-agent performance
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
    'single_agent': '#3498DB',
    'two_agent': '#E74C3C'
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


def load_results(base_path, agent_type='single_agent', subfolder='legacy'):
    """Load results for specified agent type"""
    results = {}

    if agent_type == 'single_agent':
        agent_path = Path(base_path) / 'local' / 'single_agent' / subfolder
    else:
        agent_path = Path(base_path) / 'local' / 'two_agent'

    if not agent_path.exists():
        print(f"Path not found: {agent_path}")
        return results

    for model_dir in agent_path.iterdir():
        if model_dir.is_dir():
            # Try different result file names
            for result_name in ['detection_results.json', 'detection_results_thinking.json']:
                result_file = model_dir / result_name
                if result_file.exists():
                    with open(result_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        model_name = model_dir.name
                        results[model_name] = data
                        print(f"Loaded [{agent_type}]: {model_name} ({data.get('total_examples', 0)} examples)")
                    break

    return results


def extract_metrics(results, agent_type='single_agent'):
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
    # Overall accuracy by model
    model_accuracy = df.groupby('model').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    model_accuracy.columns = ['correct', 'total', 'accuracy']

    # Accuracy by violation type
    violation_accuracy = df.groupby('violation_type').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    violation_accuracy.columns = ['correct', 'total', 'accuracy']

    # Accuracy by model and violation type
    cross_accuracy = df.groupby(['model', 'violation_type']).agg({
        'detection_success': 'mean'
    }).round(4).unstack(fill_value=0)
    cross_accuracy.columns = cross_accuracy.columns.droplevel(0)

    return model_accuracy, violation_accuracy, cross_accuracy


def calculate_runtime_metrics(df):
    """Calculate runtime metrics"""
    model_runtime = df.groupby('model').agg({
        'processing_time': ['mean', 'std', 'min', 'max', 'median']
    }).round(3)
    model_runtime.columns = ['mean', 'std', 'min', 'max', 'median']
    return model_runtime


def analyze_misclassifications(df):
    """Analyze misclassification patterns"""
    detected = df[df['detected_violation_type'].notna()].copy()

    if len(detected) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.Series(dtype=int)

    confusion_data = detected.groupby(['actual_violation_type', 'detected_violation_type']).size().unstack(fill_value=0)

    misclassified = detected[detected['actual_violation_type'] != detected['detected_violation_type']]
    misclass_patterns = misclassified.groupby(['actual_violation_type', 'detected_violation_type']).size().reset_index(name='count')
    misclass_patterns = misclass_patterns.sort_values('count', ascending=False)

    false_negatives = df[df['detected_violation_type'].isna()].copy()
    fn_by_type = false_negatives.groupby('violation_type').size()

    return confusion_data, misclass_patterns, fn_by_type


def create_two_agent_visualizations(df, model_accuracy, violation_accuracy, cross_accuracy,
                                     model_runtime, confusion_data, misclass_patterns,
                                     fn_by_type, output_dir):
    """Create visualizations for two-agent results"""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Overall Accuracy by Model
    fig, ax = plt.subplots(figsize=(10, 6))
    models = model_accuracy.index.tolist()
    accuracies = model_accuracy['accuracy'].values * 100
    colors = [MODEL_COLORS.get(m, COLORS['neutral']) for m in models]

    bars = ax.bar(range(len(models)), accuracies, color=colors, edgecolor='white', linewidth=1.2)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Two-Agent: SOLID Violation Detection Accuracy by Model')
    ax.set_ylim(0, 100)

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Random baseline')
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_two_agent_accuracy_by_model.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Accuracy by Violation Type
    fig, ax = plt.subplots(figsize=(10, 6))
    violations = violation_accuracy.index.tolist()
    accuracies = violation_accuracy['accuracy'].values * 100
    colors = [VIOLATION_COLORS.get(v, COLORS['neutral']) for v in violations]

    bars = ax.bar(range(len(violations)), accuracies, color=colors, edgecolor='white', linewidth=1.2)
    ax.set_xticks(range(len(violations)))
    ax.set_xticklabels(violations)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Two-Agent: Detection Accuracy by SOLID Principle')
    ax.set_ylim(0, 100)

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_two_agent_accuracy_by_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Heatmap: Model x Violation Type
    fig, ax = plt.subplots(figsize=(12, 8))
    heatmap_data = cross_accuracy * 100

    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=ax,
                cbar_kws={'label': 'Accuracy (%)'})
    ax.set_title('Two-Agent: Detection Accuracy Heatmap')
    ax.set_xlabel('Violation Type')
    ax.set_ylabel('Model')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_two_agent_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Runtime Box Plot
    fig, ax = plt.subplots(figsize=(12, 6))
    model_order = df.groupby('model')['processing_time'].median().sort_values().index.tolist()

    bp = ax.boxplot([df[df['model'] == m]['processing_time'].values for m in model_order],
                    labels=model_order, patch_artist=True)

    for patch, model in zip(bp['boxes'], model_order):
        patch.set_facecolor(MODEL_COLORS.get(model, COLORS['neutral']))
        patch.set_alpha(0.7)

    ax.set_ylabel('Processing Time (seconds)')
    ax.set_xlabel('Model')
    ax.set_title('Two-Agent: Processing Time Distribution')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_two_agent_runtime_boxplot.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Accuracy vs Runtime
    fig, ax = plt.subplots(figsize=(10, 8))

    for model in df['model'].unique():
        model_data = df[df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()

        ax.scatter(runtime, acc, s=200, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   label=model, edgecolor='white', linewidth=2, alpha=0.8)

    ax.set_xlabel('Mean Processing Time (seconds)')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Two-Agent: Accuracy vs Processing Time Trade-off')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_two_agent_accuracy_vs_runtime.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 6. Confusion Matrix (if data available)
    if not confusion_data.empty:
        fig, ax = plt.subplots(figsize=(10, 8))
        confusion_norm = confusion_data.div(confusion_data.sum(axis=1), axis=0) * 100

        sns.heatmap(confusion_norm, annot=True, fmt='.1f', cmap='Blues',
                    ax=ax, cbar_kws={'label': 'Percentage (%)'})
        ax.set_title('Two-Agent: Confusion Matrix (Row-normalized)')
        ax.set_xlabel('Detected Violation Type')
        ax.set_ylabel('Actual Violation Type')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/06_two_agent_confusion_matrix.png', dpi=150, bbox_inches='tight')
        plt.close()

    print(f"Two-agent visualizations saved to: {output_dir}")


def create_comparison_visualizations(single_df, two_df, output_dir):
    """Create comparison visualizations between single-agent and two-agent"""
    os.makedirs(output_dir, exist_ok=True)

    # Get common models
    single_models = set(single_df['model'].unique())
    two_models = set(two_df['model'].unique())
    common_models = sorted(single_models & two_models)

    print(f"Single-agent models: {sorted(single_models)}")
    print(f"Two-agent models: {sorted(two_models)}")
    print(f"Common models for comparison: {common_models}")

    # 1. Side-by-side Accuracy Comparison (common models)
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(common_models))
        width = 0.35

        single_acc = [single_df[single_df['model'] == m]['detection_success'].mean() * 100 for m in common_models]
        two_acc = [two_df[two_df['model'] == m]['detection_success'].mean() * 100 for m in common_models]

        bars1 = ax.bar(x - width/2, single_acc, width, label='Single-Agent', color=COLORS['single_agent'], alpha=0.8)
        bars2 = ax.bar(x + width/2, two_acc, width, label='Two-Agent', color=COLORS['two_agent'], alpha=0.8)

        ax.set_ylabel('Accuracy (%)')
        ax.set_title('Single-Agent vs Two-Agent: Detection Accuracy Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(common_models, rotation=45, ha='right')
        ax.legend()
        ax.set_ylim(0, 100)

        # Add value labels
        for bar, acc in zip(bars1, single_acc):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
        for bar, acc in zip(bars2, two_acc):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/01_comparison_accuracy_by_model.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 2. Accuracy Difference (Two-Agent - Single-Agent)
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        diff = [two_acc[i] - single_acc[i] for i in range(len(common_models))]
        colors = [COLORS['success'] if d >= 0 else COLORS['error'] for d in diff]

        bars = ax.bar(common_models, diff, color=colors, edgecolor='white', linewidth=1.2)

        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_ylabel('Accuracy Difference (%)')
        ax.set_title('Two-Agent vs Single-Agent: Accuracy Improvement\n(Positive = Two-Agent Better)')
        ax.set_xticklabels(common_models, rotation=45, ha='right')

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

    single_v_acc = [single_df[single_df['violation_type'] == v]['detection_success'].mean() * 100 for v in violations]
    two_v_acc = [two_df[two_df['violation_type'] == v]['detection_success'].mean() * 100 for v in violations]

    bars1 = ax.bar(x - width/2, single_v_acc, width, label='Single-Agent', color=COLORS['single_agent'], alpha=0.8)
    bars2 = ax.bar(x + width/2, two_v_acc, width, label='Two-Agent', color=COLORS['two_agent'], alpha=0.8)

    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Single-Agent vs Two-Agent: Accuracy by Violation Type')
    ax.set_xticks(x)
    ax.set_xticklabels(violations)
    ax.legend()
    ax.set_ylim(0, 100)

    for bar, acc in zip(bars1, single_v_acc):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)
    for bar, acc in zip(bars2, two_v_acc):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_comparison_accuracy_by_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Runtime Comparison
    if common_models:
        fig, ax = plt.subplots(figsize=(12, 6))

        x = np.arange(len(common_models))
        width = 0.35

        single_rt = [single_df[single_df['model'] == m]['processing_time'].mean() for m in common_models]
        two_rt = [two_df[two_df['model'] == m]['processing_time'].mean() for m in common_models]

        bars1 = ax.bar(x - width/2, single_rt, width, label='Single-Agent', color=COLORS['single_agent'], alpha=0.8)
        bars2 = ax.bar(x + width/2, two_rt, width, label='Two-Agent', color=COLORS['two_agent'], alpha=0.8)

        ax.set_ylabel('Mean Processing Time (seconds)')
        ax.set_title('Single-Agent vs Two-Agent: Runtime Comparison')
        ax.set_xticks(x)
        ax.set_xticklabels(common_models, rotation=45, ha='right')
        ax.legend()

        for bar, rt in zip(bars1, single_rt):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{rt:.1f}s', ha='center', va='bottom', fontsize=9)
        for bar, rt in zip(bars2, two_rt):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{rt:.1f}s', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/04_comparison_runtime.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 5. Combined Accuracy vs Runtime Scatter
    fig, ax = plt.subplots(figsize=(12, 8))

    # Single-agent points
    for model in single_df['model'].unique():
        model_data = single_df[single_df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()
        ax.scatter(runtime, acc, s=150, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   marker='o', edgecolor='white', linewidth=2, alpha=0.7)

    # Two-agent points
    for model in two_df['model'].unique():
        model_data = two_df[two_df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()
        ax.scatter(runtime, acc, s=150, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   marker='s', edgecolor='black', linewidth=2, alpha=0.7)

    # Create custom legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Single-Agent'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10, markeredgecolor='black', label='Two-Agent'),
    ]
    # Add model colors
    for model, color in MODEL_COLORS.items():
        if model in single_df['model'].unique() or model in two_df['model'].unique():
            legend_elements.append(
                Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=model)
            )

    ax.legend(handles=legend_elements, loc='best', frameon=True)
    ax.set_xlabel('Mean Processing Time (seconds)')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Single-Agent vs Two-Agent: Accuracy-Runtime Trade-off\n(Circle=Single, Square=Two)')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_comparison_accuracy_vs_runtime_scatter.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 6. Heatmap Comparison (side by side)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Single-agent heatmap
    single_cross = single_df.groupby(['model', 'violation_type'])['detection_success'].mean().unstack(fill_value=0) * 100
    sns.heatmap(single_cross, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=axes[0], cbar_kws={'label': 'Accuracy (%)'})
    axes[0].set_title('Single-Agent: Model x Violation Accuracy')
    axes[0].set_xlabel('Violation Type')
    axes[0].set_ylabel('Model')

    # Two-agent heatmap
    two_cross = two_df.groupby(['model', 'violation_type'])['detection_success'].mean().unstack(fill_value=0) * 100
    sns.heatmap(two_cross, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=axes[1], cbar_kws={'label': 'Accuracy (%)'})
    axes[1].set_title('Two-Agent: Model x Violation Accuracy')
    axes[1].set_xlabel('Violation Type')
    axes[1].set_ylabel('Model')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_comparison_heatmaps.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 7. Overall Summary Bar Chart
    fig, ax = plt.subplots(figsize=(10, 6))

    categories = ['Overall\nAccuracy', 'Mean\nRuntime (s)', 'SRP', 'OCP', 'LSP', 'ISP', 'DIP']

    single_overall_acc = single_df['detection_success'].mean() * 100
    two_overall_acc = two_df['detection_success'].mean() * 100
    single_overall_rt = single_df['processing_time'].mean()
    two_overall_rt = two_df['processing_time'].mean()

    single_vals = [single_overall_acc, single_overall_rt] + single_v_acc
    two_vals = [two_overall_acc, two_overall_rt] + two_v_acc

    x = np.arange(len(categories))
    width = 0.35

    # Normalize runtime for visualization (scale to similar range as accuracy)
    max_rt = max(single_overall_rt, two_overall_rt)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # Accuracy subplot
    acc_cats = ['Overall', 'SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    single_acc_vals = [single_overall_acc] + single_v_acc
    two_acc_vals = [two_overall_acc] + two_v_acc

    x_acc = np.arange(len(acc_cats))
    bars1 = ax1.bar(x_acc - width/2, single_acc_vals, width, label='Single-Agent', color=COLORS['single_agent'], alpha=0.8)
    bars2 = ax1.bar(x_acc + width/2, two_acc_vals, width, label='Two-Agent', color=COLORS['two_agent'], alpha=0.8)

    ax1.set_ylabel('Accuracy (%)')
    ax1.set_title('Accuracy Comparison Summary')
    ax1.set_xticks(x_acc)
    ax1.set_xticklabels(acc_cats)
    ax1.legend()
    ax1.set_ylim(0, 100)

    # Runtime subplot
    rt_models = common_models if common_models else list(set(single_df['model'].unique()) | set(two_df['model'].unique()))
    single_rts = [single_df[single_df['model'] == m]['processing_time'].mean() if m in single_df['model'].values else 0 for m in rt_models]
    two_rts = [two_df[two_df['model'] == m]['processing_time'].mean() if m in two_df['model'].values else 0 for m in rt_models]

    x_rt = np.arange(len(rt_models))
    bars3 = ax2.bar(x_rt - width/2, single_rts, width, label='Single-Agent', color=COLORS['single_agent'], alpha=0.8)
    bars4 = ax2.bar(x_rt + width/2, two_rts, width, label='Two-Agent', color=COLORS['two_agent'], alpha=0.8)

    ax2.set_ylabel('Mean Processing Time (seconds)')
    ax2.set_title('Runtime Comparison Summary')
    ax2.set_xticks(x_rt)
    ax2.set_xticklabels(rt_models, rotation=45, ha='right')
    ax2.legend()

    plt.tight_layout()
    plt.savefig(f'{output_dir}/07_comparison_summary.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Comparison visualizations saved to: {output_dir}")


def generate_comparison_report(single_df, two_df, output_dir):
    """Generate comparison report"""
    report = []
    report.append("=" * 80)
    report.append("SOLID BENCHMARK: SINGLE-AGENT vs TWO-AGENT COMPARISON REPORT")
    report.append("=" * 80)
    report.append("")

    # Summary
    report.append("## OVERALL SUMMARY")
    report.append("-" * 40)

    single_acc = single_df['detection_success'].mean() * 100
    two_acc = two_df['detection_success'].mean() * 100
    single_rt = single_df['processing_time'].mean()
    two_rt = two_df['processing_time'].mean()

    report.append(f"Single-Agent:")
    report.append(f"  - Total Examples: {len(single_df)}")
    report.append(f"  - Models: {single_df['model'].nunique()} ({', '.join(sorted(single_df['model'].unique()))})")
    report.append(f"  - Overall Accuracy: {single_acc:.2f}%")
    report.append(f"  - Mean Runtime: {single_rt:.2f}s")
    report.append("")

    report.append(f"Two-Agent:")
    report.append(f"  - Total Examples: {len(two_df)}")
    report.append(f"  - Models: {two_df['model'].nunique()} ({', '.join(sorted(two_df['model'].unique()))})")
    report.append(f"  - Overall Accuracy: {two_acc:.2f}%")
    report.append(f"  - Mean Runtime: {two_rt:.2f}s")
    report.append("")

    report.append(f"DIFFERENCE (Two-Agent - Single-Agent):")
    report.append(f"  - Accuracy: {two_acc - single_acc:+.2f}%")
    report.append(f"  - Runtime: {two_rt - single_rt:+.2f}s")
    report.append("")

    # Accuracy by Model Comparison
    report.append("## ACCURACY BY MODEL")
    report.append("-" * 40)

    common_models = sorted(set(single_df['model'].unique()) & set(two_df['model'].unique()))
    all_models = sorted(set(single_df['model'].unique()) | set(two_df['model'].unique()))

    report.append(f"{'Model':<20} {'Single-Agent':>12} {'Two-Agent':>12} {'Diff':>10}")
    report.append("-" * 56)

    for model in all_models:
        s_acc = single_df[single_df['model'] == model]['detection_success'].mean() * 100 if model in single_df['model'].values else None
        t_acc = two_df[two_df['model'] == model]['detection_success'].mean() * 100 if model in two_df['model'].values else None

        s_str = f"{s_acc:.2f}%" if s_acc is not None else "N/A"
        t_str = f"{t_acc:.2f}%" if t_acc is not None else "N/A"
        d_str = f"{t_acc - s_acc:+.2f}%" if s_acc is not None and t_acc is not None else "N/A"

        report.append(f"{model:<20} {s_str:>12} {t_str:>12} {d_str:>10}")

    report.append("")

    # Accuracy by Violation Type
    report.append("## ACCURACY BY VIOLATION TYPE")
    report.append("-" * 40)

    violations = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    report.append(f"{'Violation':<10} {'Single-Agent':>12} {'Two-Agent':>12} {'Diff':>10}")
    report.append("-" * 46)

    for v in violations:
        s_acc = single_df[single_df['violation_type'] == v]['detection_success'].mean() * 100
        t_acc = two_df[two_df['violation_type'] == v]['detection_success'].mean() * 100
        diff = t_acc - s_acc

        report.append(f"{v:<10} {s_acc:>11.2f}% {t_acc:>11.2f}% {diff:>+9.2f}%")

    report.append("")

    # Runtime by Model Comparison
    report.append("## RUNTIME BY MODEL")
    report.append("-" * 40)

    report.append(f"{'Model':<20} {'Single-Agent':>12} {'Two-Agent':>12} {'Diff':>10}")
    report.append("-" * 56)

    for model in all_models:
        s_rt = single_df[single_df['model'] == model]['processing_time'].mean() if model in single_df['model'].values else None
        t_rt = two_df[two_df['model'] == model]['processing_time'].mean() if model in two_df['model'].values else None

        s_str = f"{s_rt:.2f}s" if s_rt is not None else "N/A"
        t_str = f"{t_rt:.2f}s" if t_rt is not None else "N/A"
        d_str = f"{t_rt - s_rt:+.2f}s" if s_rt is not None and t_rt is not None else "N/A"

        report.append(f"{model:<20} {s_str:>12} {t_str:>12} {d_str:>10}")

    report.append("")

    # Key Findings
    report.append("## KEY FINDINGS")
    report.append("-" * 40)

    if two_acc > single_acc:
        report.append(f"- Two-Agent approach shows HIGHER accuracy ({two_acc:.2f}% vs {single_acc:.2f}%)")
    else:
        report.append(f"- Single-Agent approach shows HIGHER accuracy ({single_acc:.2f}% vs {two_acc:.2f}%)")

    if two_rt > single_rt:
        report.append(f"- Two-Agent approach is SLOWER ({two_rt:.2f}s vs {single_rt:.2f}s)")
    else:
        report.append(f"- Two-Agent approach is FASTER ({two_rt:.2f}s vs {single_rt:.2f}s)")

    # Best improvements
    if common_models:
        improvements = []
        for model in common_models:
            s_acc = single_df[single_df['model'] == model]['detection_success'].mean() * 100
            t_acc = two_df[two_df['model'] == model]['detection_success'].mean() * 100
            improvements.append((model, t_acc - s_acc))

        improvements.sort(key=lambda x: x[1], reverse=True)

        if improvements[0][1] > 0:
            report.append(f"- Best improvement with Two-Agent: {improvements[0][0]} ({improvements[0][1]:+.2f}%)")
        if improvements[-1][1] < 0:
            report.append(f"- Worst regression with Two-Agent: {improvements[-1][0]} ({improvements[-1][1]:+.2f}%)")

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
    two_agent_output = 'analysis_output_two_agent'
    comparison_output = 'analysis_output_comparison'

    print("=" * 60)
    print("SOLID Principles Benchmark - Two Agent & Comparison Analysis")
    print("=" * 60)
    print()

    # Load Single-Agent Results
    print("Loading Single-Agent Results...")
    single_results = load_results(base_path, 'single_agent', 'legacy')

    # Load Two-Agent Results
    print("\nLoading Two-Agent Results...")
    two_results = load_results(base_path, 'two_agent')

    if not two_results:
        print("No two-agent results found!")
        return

    # Extract metrics
    print("\nExtracting metrics...")
    single_df = extract_metrics(single_results, 'single_agent')
    two_df = extract_metrics(two_results, 'two_agent')

    print(f"Single-Agent records: {len(single_df)}")
    print(f"Two-Agent records: {len(two_df)}")

    # Two-Agent Analysis
    print("\n" + "=" * 40)
    print("TWO-AGENT ANALYSIS")
    print("=" * 40)

    model_accuracy, violation_accuracy, cross_accuracy = calculate_accuracy_metrics(two_df)
    model_runtime = calculate_runtime_metrics(two_df)
    confusion_data, misclass_patterns, fn_by_type = analyze_misclassifications(two_df)

    print("\nCreating two-agent visualizations...")
    create_two_agent_visualizations(two_df, model_accuracy, violation_accuracy, cross_accuracy,
                                     model_runtime, confusion_data, misclass_patterns,
                                     fn_by_type, two_agent_output)

    # Comparison Analysis
    if len(single_df) > 0:
        print("\n" + "=" * 40)
        print("COMPARISON ANALYSIS")
        print("=" * 40)

        print("\nCreating comparison visualizations...")
        create_comparison_visualizations(single_df, two_df, comparison_output)

        print("\nGenerating comparison report...")
        generate_comparison_report(single_df, two_df, comparison_output)

    # Save data to CSV
    two_df.to_csv(f'{two_agent_output}/two_agent_detailed_results.csv', index=False)
    print(f"\nTwo-agent results saved to: {two_agent_output}/two_agent_detailed_results.csv")

    if len(single_df) > 0:
        combined_df = pd.concat([single_df, two_df], ignore_index=True)
        combined_df.to_csv(f'{comparison_output}/combined_results.csv', index=False)
        print(f"Combined results saved to: {comparison_output}/combined_results.csv")


if __name__ == '__main__':
    main()
