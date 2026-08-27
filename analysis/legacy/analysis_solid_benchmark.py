"""
SOLID Principles Benchmark Analysis
Analyzes detection accuracy and runtime performance for single-agent models
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

# Color palette - professional, no emoji colors
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#4CAF50',
    'error': '#E74C3C',
    'neutral': '#7F8C8D'
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


def load_single_agent_results(base_path):
    """Load all single agent results"""
    results = {}
    single_agent_path = Path(base_path) / 'local' / 'single_agent'

    if not single_agent_path.exists():
        print(f"Path not found: {single_agent_path}")
        return results

    for model_dir in single_agent_path.iterdir():
        if model_dir.is_dir():
            result_file = model_dir / 'detection_results.json'
            if result_file.exists():
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    model_name = model_dir.name
                    results[model_name] = data
                    print(f"Loaded: {model_name} ({data.get('total_examples', 0)} examples)")

    return results


def load_coze_results(base_path):
    """Load coze auto detection results for comparison"""
    results = {}
    coze_path = Path(base_path) / 'coze_auto_detection'

    if not coze_path.exists():
        return results

    for result_file in coze_path.glob('*.json'):
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            model_name = result_file.stem.replace('auto_detection_', '')
            results[model_name] = data
            print(f"Loaded Coze: {model_name}")

    return results


def extract_metrics(results):
    """Extract detailed metrics from results"""
    all_records = []

    for model_name, data in results.items():
        by_violation = data.get('by_violation_type', {})

        for violation_type, violation_data in by_violation.items():
            for example in violation_data.get('results', []):
                record = {
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
    """Calculate accuracy metrics by model and violation type"""
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
    # Runtime by model
    model_runtime = df.groupby('model').agg({
        'processing_time': ['mean', 'std', 'min', 'max', 'median']
    }).round(3)
    model_runtime.columns = ['mean', 'std', 'min', 'max', 'median']

    # Runtime by violation type
    violation_runtime = df.groupby('violation_type').agg({
        'processing_time': ['mean', 'std', 'median']
    }).round(3)
    violation_runtime.columns = ['mean', 'std', 'median']

    return model_runtime, violation_runtime


def analyze_misclassifications(df):
    """Analyze misclassification patterns"""
    # Filter only detected cases (where a violation was detected)
    detected = df[df['detected_violation_type'].notna()].copy()

    # Create confusion matrix data
    confusion_data = detected.groupby(['actual_violation_type', 'detected_violation_type']).size().unstack(fill_value=0)

    # Misclassification types
    misclassified = detected[detected['actual_violation_type'] != detected['detected_violation_type']]

    misclass_patterns = misclassified.groupby(['actual_violation_type', 'detected_violation_type']).size().reset_index(name='count')
    misclass_patterns = misclass_patterns.sort_values('count', ascending=False)

    # False negatives (not detected at all)
    false_negatives = df[df['detected_violation_type'].isna()].copy()
    fn_by_type = false_negatives.groupby('violation_type').size()

    return confusion_data, misclass_patterns, fn_by_type


def create_visualizations(df, model_accuracy, violation_accuracy, cross_accuracy,
                          model_runtime, violation_runtime, confusion_data,
                          misclass_patterns, fn_by_type, output_dir):
    """Create all visualizations"""
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
    ax.set_title('SOLID Violation Detection Accuracy by Model')
    ax.set_ylim(0, 100)

    # Add value labels
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, label='Random baseline')
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_accuracy_by_model.png', dpi=150, bbox_inches='tight')
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
    ax.set_title('Detection Accuracy by SOLID Principle Violation Type')
    ax.set_ylim(0, 100)

    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_accuracy_by_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Heatmap: Model x Violation Type Accuracy
    fig, ax = plt.subplots(figsize=(12, 8))
    heatmap_data = cross_accuracy * 100

    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=ax,
                cbar_kws={'label': 'Accuracy (%)'})
    ax.set_title('Detection Accuracy: Model vs Violation Type')
    ax.set_xlabel('Violation Type')
    ax.set_ylabel('Model')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_heatmap_accuracy.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Runtime by Model (Box Plot)
    fig, ax = plt.subplots(figsize=(12, 6))
    model_order = df.groupby('model')['processing_time'].median().sort_values().index.tolist()

    bp = ax.boxplot([df[df['model'] == m]['processing_time'].values for m in model_order],
                    labels=model_order, patch_artist=True)

    for patch, model in zip(bp['boxes'], model_order):
        patch.set_facecolor(MODEL_COLORS.get(model, COLORS['neutral']))
        patch.set_alpha(0.7)

    ax.set_ylabel('Processing Time (seconds)')
    ax.set_xlabel('Model')
    ax.set_title('Processing Time Distribution by Model')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_runtime_boxplot.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Mean Runtime Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    models = model_runtime.index.tolist()
    means = model_runtime['mean'].values
    stds = model_runtime['std'].values
    colors = [MODEL_COLORS.get(m, COLORS['neutral']) for m in models]

    bars = ax.bar(range(len(models)), means, yerr=stds, color=colors,
                  edgecolor='white', linewidth=1.2, capsize=5, alpha=0.8)
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.set_ylabel('Mean Processing Time (seconds)')
    ax.set_title('Average Processing Time by Model (with std)')

    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{mean:.2f}s', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_runtime_by_model.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 6. Confusion Matrix
    if not confusion_data.empty:
        fig, ax = plt.subplots(figsize=(10, 8))

        # Normalize by row (actual violation type)
        confusion_norm = confusion_data.div(confusion_data.sum(axis=1), axis=0) * 100

        sns.heatmap(confusion_norm, annot=True, fmt='.1f', cmap='Blues',
                    ax=ax, cbar_kws={'label': 'Percentage (%)'})
        ax.set_title('Confusion Matrix: Actual vs Detected Violation Type\n(Row-normalized)')
        ax.set_xlabel('Detected Violation Type')
        ax.set_ylabel('Actual Violation Type')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/06_confusion_matrix.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 7. Misclassification Patterns (Top 10)
    if len(misclass_patterns) > 0:
        fig, ax = plt.subplots(figsize=(12, 6))
        top_misclass = misclass_patterns.head(10)

        labels = [f"{row['actual_violation_type']} -> {row['detected_violation_type']}"
                  for _, row in top_misclass.iterrows()]
        counts = top_misclass['count'].values

        bars = ax.barh(range(len(labels)), counts, color=COLORS['error'], alpha=0.7)
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)
        ax.set_xlabel('Count')
        ax.set_title('Top Misclassification Patterns (Actual -> Detected)')
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                    str(count), ha='left', va='center', fontsize=10)

        plt.tight_layout()
        plt.savefig(f'{output_dir}/07_misclassification_patterns.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 8. False Negatives by Violation Type
    if len(fn_by_type) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        violations = fn_by_type.index.tolist()
        counts = fn_by_type.values
        colors = [VIOLATION_COLORS.get(v, COLORS['neutral']) for v in violations]

        bars = ax.bar(range(len(violations)), counts, color=colors, alpha=0.7)
        ax.set_xticks(range(len(violations)))
        ax.set_xticklabels(violations)
        ax.set_ylabel('Count')
        ax.set_title('False Negatives (Undetected Violations) by Type')

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    str(count), ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/08_false_negatives.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 9. Accuracy vs Runtime Scatter
    fig, ax = plt.subplots(figsize=(10, 8))

    for model in df['model'].unique():
        model_data = df[df['model'] == model]
        acc = model_data['detection_success'].mean() * 100
        runtime = model_data['processing_time'].mean()

        ax.scatter(runtime, acc, s=200, c=MODEL_COLORS.get(model, COLORS['neutral']),
                   label=model, edgecolor='white', linewidth=2, alpha=0.8)

    ax.set_xlabel('Mean Processing Time (seconds)')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Accuracy vs Processing Time Trade-off')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/09_accuracy_vs_runtime.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 10. Accuracy by Difficulty Level (if available)
    if 'level' in df.columns:
        level_accuracy = df.groupby(['model', 'level'])['detection_success'].mean().unstack(fill_value=0) * 100

        if not level_accuracy.empty and len(level_accuracy.columns) > 1:
            fig, ax = plt.subplots(figsize=(12, 6))
            level_accuracy.plot(kind='bar', ax=ax, width=0.8)
            ax.set_ylabel('Accuracy (%)')
            ax.set_xlabel('Model')
            ax.set_title('Detection Accuracy by Model and Difficulty Level')
            ax.legend(title='Difficulty Level')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(f'{output_dir}/10_accuracy_by_level.png', dpi=150, bbox_inches='tight')
            plt.close()

    print(f"\nAll visualizations saved to: {output_dir}")


def generate_report(df, model_accuracy, violation_accuracy, cross_accuracy,
                    model_runtime, confusion_data, misclass_patterns, fn_by_type,
                    coze_df=None, output_dir='.'):
    """Generate text report"""

    report = []
    report.append("=" * 80)
    report.append("SOLID PRINCIPLES BENCHMARK ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    # Summary Statistics
    report.append("## SUMMARY STATISTICS")
    report.append("-" * 40)
    report.append(f"Total Examples: {len(df)}")
    report.append(f"Models Evaluated: {df['model'].nunique()}")
    report.append(f"Violation Types: {df['violation_type'].nunique()}")
    report.append(f"Overall Accuracy: {df['detection_success'].mean()*100:.2f}%")
    report.append(f"Mean Processing Time: {df['processing_time'].mean():.2f}s")
    report.append("")

    # Accuracy by Model
    report.append("## ACCURACY BY MODEL")
    report.append("-" * 40)
    for model in model_accuracy.index:
        acc = model_accuracy.loc[model, 'accuracy'] * 100
        correct = int(model_accuracy.loc[model, 'correct'])
        total = int(model_accuracy.loc[model, 'total'])
        report.append(f"  {model}: {acc:.2f}% ({correct}/{total})")
    report.append("")

    # Best and Worst Performing Models
    best_model = model_accuracy['accuracy'].idxmax()
    worst_model = model_accuracy['accuracy'].idxmin()
    report.append(f"Best Model: {best_model} ({model_accuracy.loc[best_model, 'accuracy']*100:.2f}%)")
    report.append(f"Worst Model: {worst_model} ({model_accuracy.loc[worst_model, 'accuracy']*100:.2f}%)")
    report.append("")

    # Accuracy by Violation Type
    report.append("## ACCURACY BY VIOLATION TYPE")
    report.append("-" * 40)
    for vtype in violation_accuracy.index:
        acc = violation_accuracy.loc[vtype, 'accuracy'] * 100
        correct = int(violation_accuracy.loc[vtype, 'correct'])
        total = int(violation_accuracy.loc[vtype, 'total'])
        report.append(f"  {vtype}: {acc:.2f}% ({correct}/{total})")
    report.append("")

    # Easiest and Hardest to Detect
    easiest = violation_accuracy['accuracy'].idxmax()
    hardest = violation_accuracy['accuracy'].idxmin()
    report.append(f"Easiest to Detect: {easiest} ({violation_accuracy.loc[easiest, 'accuracy']*100:.2f}%)")
    report.append(f"Hardest to Detect: {hardest} ({violation_accuracy.loc[hardest, 'accuracy']*100:.2f}%)")
    report.append("")

    # Runtime Analysis
    report.append("## RUNTIME ANALYSIS")
    report.append("-" * 40)
    runtime_stats = df.groupby('model')['processing_time'].agg(['mean', 'median', 'std'])
    for model in runtime_stats.index:
        mean_t = runtime_stats.loc[model, 'mean']
        med_t = runtime_stats.loc[model, 'median']
        std_t = runtime_stats.loc[model, 'std']
        report.append(f"  {model}: mean={mean_t:.2f}s, median={med_t:.2f}s, std={std_t:.2f}s")
    report.append("")

    # Misclassification Analysis
    report.append("## MISCLASSIFICATION ANALYSIS")
    report.append("-" * 40)

    total_detected = len(df[df['detected_violation_type'].notna()])
    total_misclassified = len(df[(df['detected_violation_type'].notna()) &
                                  (df['actual_violation_type'] != df['detected_violation_type'])])
    total_false_neg = len(df[df['detected_violation_type'].isna()])

    report.append(f"Total Detected: {total_detected}")
    report.append(f"Correctly Classified: {total_detected - total_misclassified}")
    report.append(f"Misclassified: {total_misclassified}")
    report.append(f"False Negatives (Undetected): {total_false_neg}")
    report.append("")

    if len(misclass_patterns) > 0:
        report.append("Top Misclassification Patterns:")
        for _, row in misclass_patterns.head(5).iterrows():
            report.append(f"  {row['actual_violation_type']} -> {row['detected_violation_type']}: {row['count']} cases")
    report.append("")

    # False Negatives by Type
    if len(fn_by_type) > 0:
        report.append("False Negatives by Violation Type:")
        for vtype, count in fn_by_type.items():
            report.append(f"  {vtype}: {count} cases")
    report.append("")

    # Comparison with Coze (if available)
    if coze_df is not None and len(coze_df) > 0:
        report.append("## COMPARISON WITH COZE AUTO DETECTION")
        report.append("-" * 40)
        coze_accuracy = coze_df.groupby('model')['detection_success'].mean() * 100
        local_mean = df['detection_success'].mean() * 100

        for model, acc in coze_accuracy.items():
            report.append(f"  Coze ({model}): {acc:.2f}%")
        report.append(f"  Local Single-Agent Average: {local_mean:.2f}%")
        report.append("")

    # Cross-table Summary
    report.append("## MODEL x VIOLATION TYPE ACCURACY (%)")
    report.append("-" * 40)
    cross_pct = (cross_accuracy * 100).round(1)
    report.append(cross_pct.to_string())
    report.append("")

    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    # Save report
    report_text = "\n".join(report)
    report_path = f"{output_dir}/analysis_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {report_path}")

    return report_text


def main():
    # Paths
    base_path = Path('result')
    output_dir = 'analysis_output'

    print("=" * 60)
    print("SOLID Principles Benchmark Analysis")
    print("=" * 60)
    print()

    # Load data
    print("Loading Single Agent Results...")
    single_agent_results = load_single_agent_results(base_path)

    print("\nLoading Coze Auto Detection Results...")
    coze_results = load_coze_results(base_path)

    if not single_agent_results:
        print("No single agent results found!")
        return

    # Extract metrics
    print("\nExtracting metrics...")
    df = extract_metrics(single_agent_results)
    print(f"Total records: {len(df)}")

    # Extract Coze metrics for comparison
    coze_df = None
    if coze_results:
        coze_df = extract_metrics(coze_results)
        print(f"Coze records: {len(coze_df)}")

    # Calculate metrics
    print("\nCalculating accuracy metrics...")
    model_accuracy, violation_accuracy, cross_accuracy = calculate_accuracy_metrics(df)

    print("\nCalculating runtime metrics...")
    model_runtime, violation_runtime = calculate_runtime_metrics(df)

    print("\nAnalyzing misclassifications...")
    confusion_data, misclass_patterns, fn_by_type = analyze_misclassifications(df)

    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(df, model_accuracy, violation_accuracy, cross_accuracy,
                          model_runtime, violation_runtime, confusion_data,
                          misclass_patterns, fn_by_type, output_dir)

    # Generate report
    print("\nGenerating report...")
    generate_report(df, model_accuracy, violation_accuracy, cross_accuracy,
                    model_runtime, confusion_data, misclass_patterns, fn_by_type,
                    coze_df, output_dir)

    # Save data to CSV for further analysis
    df.to_csv(f'{output_dir}/detailed_results.csv', index=False)
    print(f"\nDetailed results saved to: {output_dir}/detailed_results.csv")


if __name__ == '__main__':
    main()
