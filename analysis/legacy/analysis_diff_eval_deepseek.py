"""
SOLID Principles Benchmark Analysis - Diff Eval (deepseek-r1-8b)
Analyzes diff_eval workflow results for deepseek-r1-8b model
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
    'neutral': '#7F8C8D'
}

VIOLATION_COLORS = {
    'SRP': '#3498DB',
    'OCP': '#2ECC71',
    'LSP': '#E74C3C',
    'ISP': '#9B59B6',
    'DIP': '#F39C12'
}

LANGUAGE_COLORS = {
    'JAVA': '#E76F00',
    'PYTHON': '#3776AB',
    'KOTLIN': '#7F52FF',
    'CSHARP': '#68217A'
}

LEVEL_COLORS = {
    'EASY': '#4CAF50',
    'MODERATE': '#FF9800',
    'HARD': '#F44336'
}


def load_detection_results(file_path):
    """Load detection results from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"Loaded results from: {file_path}")
    print(f"Configuration: {data.get('configuration', {})}")
    print(f"Total examples: {data.get('total_examples', 0)}")

    return data


def extract_metrics(data):
    """Extract detailed metrics from results"""
    all_records = []

    by_violation = data.get('by_violation_type', {})

    for violation_type, violation_data in by_violation.items():
        for example in violation_data.get('results', []):
            record = {
                'violation_type': violation_type,
                'example_id': example.get('example_id', ''),
                'level': example.get('level', 'UNKNOWN'),
                'language': example.get('language', 'UNKNOWN'),
                'detection_success': example.get('detection_success', False),
                'detected_violation_type': example.get('detected_violation_type'),
                'ground_truth': example.get('ground_truth', violation_type),
                'processing_time': example.get('processing_time_seconds', 0),
                'api_call_success': example.get('api_call_success', True),
                'status': example.get('status', 'unknown'),
                'workflow': example.get('workflow', ''),
                'total_iterations': example.get('total_iterations', 0),
                'is_detected': example.get('is_detected', False),
                'signal': example.get('signal', ''),
                'explanation': example.get('explanation', '')
            }
            all_records.append(record)

    df = pd.DataFrame(all_records)
    print(f"\nExtracted {len(df)} records")
    return df


def calculate_accuracy_metrics(df):
    """Calculate accuracy metrics"""
    # Overall accuracy
    overall_accuracy = df['detection_success'].mean()

    # Accuracy by violation type
    violation_accuracy = df.groupby('violation_type').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    violation_accuracy.columns = ['correct', 'total', 'accuracy']

    # Accuracy by level
    level_accuracy = df.groupby('level').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    level_accuracy.columns = ['correct', 'total', 'accuracy']

    # Accuracy by language
    language_accuracy = df.groupby('language').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    language_accuracy.columns = ['correct', 'total', 'accuracy']

    # Cross-tabulation: violation x level
    cross_violation_level = df.groupby(['violation_type', 'level']).agg({
        'detection_success': 'mean'
    }).round(4).unstack(fill_value=0)
    cross_violation_level.columns = cross_violation_level.columns.droplevel(0)

    # Cross-tabulation: violation x language
    cross_violation_language = df.groupby(['violation_type', 'language']).agg({
        'detection_success': 'mean'
    }).round(4).unstack(fill_value=0)
    cross_violation_language.columns = cross_violation_language.columns.droplevel(0)

    return {
        'overall': overall_accuracy,
        'by_violation': violation_accuracy,
        'by_level': level_accuracy,
        'by_language': language_accuracy,
        'cross_violation_level': cross_violation_level,
        'cross_violation_language': cross_violation_language
    }


def calculate_runtime_metrics(df):
    """Calculate runtime metrics"""
    runtime_stats = {
        'overall': df['processing_time'].describe(),
        'by_violation': df.groupby('violation_type')['processing_time'].describe(),
        'by_level': df.groupby('level')['processing_time'].describe(),
        'by_language': df.groupby('language')['processing_time'].describe()
    }
    return runtime_stats


def analyze_misclassifications(df):
    """Analyze misclassification patterns"""
    # Filter examples where detection was attempted
    detected = df[df['detected_violation_type'].notna()].copy()

    if len(detected) == 0:
        return pd.DataFrame(), pd.DataFrame(), pd.Series(dtype=int)

    # Confusion matrix
    confusion_data = detected.groupby(['ground_truth', 'detected_violation_type']).size().unstack(fill_value=0)

    # Misclassification patterns
    misclassified = detected[detected['ground_truth'] != detected['detected_violation_type']]
    misclass_patterns = misclassified.groupby(['ground_truth', 'detected_violation_type']).size().reset_index(name='count')
    misclass_patterns = misclass_patterns.sort_values('count', ascending=False)

    # False negatives (no detection)
    false_negatives = df[df['detected_violation_type'].isna()].copy()
    fn_by_type = false_negatives.groupby('violation_type').size()

    return confusion_data, misclass_patterns, fn_by_type


def create_visualizations(df, metrics, runtime_stats, confusion_data, misclass_patterns, fn_by_type, output_dir):
    """Create comprehensive visualizations"""
    os.makedirs(output_dir, exist_ok=True)

    # 1. Overall Accuracy by Violation Type
    fig, ax = plt.subplots(figsize=(10, 6))
    violations = metrics['by_violation'].index.tolist()
    accuracies = metrics['by_violation']['accuracy'].values * 100
    colors = [VIOLATION_COLORS.get(v, COLORS['neutral']) for v in violations]

    bars = ax.bar(range(len(violations)), accuracies, color=colors, edgecolor='white', linewidth=1.2)
    ax.set_xticks(range(len(violations)))
    ax.set_xticklabels(violations)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Diff Eval (deepseek-r1-8b): Detection Accuracy by SOLID Principle')
    ax.set_ylim(0, 100)

    for bar, acc, total in zip(bars, accuracies, metrics['by_violation']['total'].values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%\n(n={int(total)})', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.axhline(y=metrics['overall']*100, color='red', linestyle='--', alpha=0.7, label=f'Overall: {metrics["overall"]*100:.1f}%')
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/01_accuracy_by_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Accuracy by Difficulty Level
    fig, ax = plt.subplots(figsize=(10, 6))
    levels = metrics['by_level'].index.tolist()
    accuracies = metrics['by_level']['accuracy'].values * 100
    colors = [LEVEL_COLORS.get(l, COLORS['neutral']) for l in levels]

    bars = ax.bar(range(len(levels)), accuracies, color=colors, edgecolor='white', linewidth=1.2)
    ax.set_xticks(range(len(levels)))
    ax.set_xticklabels(levels)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Diff Eval (deepseek-r1-8b): Detection Accuracy by Difficulty Level')
    ax.set_ylim(0, 100)

    for bar, acc, total in zip(bars, accuracies, metrics['by_level']['total'].values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%\n(n={int(total)})', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/02_accuracy_by_level.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Accuracy by Language
    fig, ax = plt.subplots(figsize=(10, 6))
    languages = metrics['by_language'].index.tolist()
    accuracies = metrics['by_language']['accuracy'].values * 100
    colors = [LANGUAGE_COLORS.get(l, COLORS['neutral']) for l in languages]

    bars = ax.bar(range(len(languages)), accuracies, color=colors, edgecolor='white', linewidth=1.2)
    ax.set_xticks(range(len(languages)))
    ax.set_xticklabels(languages)
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Diff Eval (deepseek-r1-8b): Detection Accuracy by Programming Language')
    ax.set_ylim(0, 100)

    for bar, acc, total in zip(bars, accuracies, metrics['by_language']['total'].values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%\n(n={int(total)})', ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(f'{output_dir}/03_accuracy_by_language.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 4. Heatmap: Violation Type x Difficulty Level
    fig, ax = plt.subplots(figsize=(10, 8))
    heatmap_data = metrics['cross_violation_level'] * 100

    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=ax,
                cbar_kws={'label': 'Accuracy (%)'})
    ax.set_title('Diff Eval (deepseek-r1-8b): Accuracy Heatmap (Violation x Level)')
    ax.set_xlabel('Difficulty Level')
    ax.set_ylabel('Violation Type')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/04_heatmap_violation_level.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 5. Heatmap: Violation Type x Language
    fig, ax = plt.subplots(figsize=(10, 8))
    heatmap_data = metrics['cross_violation_language'] * 100

    sns.heatmap(heatmap_data, annot=True, fmt='.1f', cmap='RdYlGn',
                center=50, vmin=0, vmax=100, ax=ax,
                cbar_kws={'label': 'Accuracy (%)'})
    ax.set_title('Diff Eval (deepseek-r1-8b): Accuracy Heatmap (Violation x Language)')
    ax.set_xlabel('Programming Language')
    ax.set_ylabel('Violation Type')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/05_heatmap_violation_language.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 6. Runtime Distribution by Violation Type
    fig, ax = plt.subplots(figsize=(12, 6))
    violation_order = df.groupby('violation_type')['processing_time'].median().sort_values().index.tolist()

    bp = ax.boxplot([df[df['violation_type'] == v]['processing_time'].values for v in violation_order],
                    labels=violation_order, patch_artist=True)

    for patch, violation in zip(bp['boxes'], violation_order):
        patch.set_facecolor(VIOLATION_COLORS.get(violation, COLORS['neutral']))
        patch.set_alpha(0.7)

    ax.set_ylabel('Processing Time (seconds)')
    ax.set_xlabel('Violation Type')
    ax.set_title('Diff Eval (deepseek-r1-8b): Processing Time Distribution by Violation Type')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/06_runtime_boxplot_violation.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 7. Runtime Distribution by Level
    fig, ax = plt.subplots(figsize=(10, 6))
    level_order = ['EASY', 'MODERATE', 'HARD']
    level_order = [l for l in level_order if l in df['level'].unique()]

    bp = ax.boxplot([df[df['level'] == l]['processing_time'].values for l in level_order],
                    labels=level_order, patch_artist=True)

    for patch, level in zip(bp['boxes'], level_order):
        patch.set_facecolor(LEVEL_COLORS.get(level, COLORS['neutral']))
        patch.set_alpha(0.7)

    ax.set_ylabel('Processing Time (seconds)')
    ax.set_xlabel('Difficulty Level')
    ax.set_title('Diff Eval (deepseek-r1-8b): Processing Time Distribution by Difficulty Level')
    plt.tight_layout()
    plt.savefig(f'{output_dir}/07_runtime_boxplot_level.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 8. Confusion Matrix (if data available)
    if not confusion_data.empty:
        fig, ax = plt.subplots(figsize=(10, 8))
        confusion_norm = confusion_data.div(confusion_data.sum(axis=1), axis=0) * 100

        sns.heatmap(confusion_norm, annot=True, fmt='.1f', cmap='Blues',
                    ax=ax, cbar_kws={'label': 'Percentage (%)'})
        ax.set_title('Diff Eval (deepseek-r1-8b): Confusion Matrix (Row-normalized)')
        ax.set_xlabel('Detected Violation Type')
        ax.set_ylabel('Actual Violation Type')
        plt.tight_layout()
        plt.savefig(f'{output_dir}/08_confusion_matrix.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 9. False Negative Analysis
    if len(fn_by_type) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        violations = fn_by_type.index.tolist()
        counts = fn_by_type.values
        colors = [VIOLATION_COLORS.get(v, COLORS['neutral']) for v in violations]

        bars = ax.bar(range(len(violations)), counts, color=colors, edgecolor='white', linewidth=1.2, alpha=0.7)
        ax.set_xticks(range(len(violations)))
        ax.set_xticklabels(violations)
        ax.set_ylabel('Count')
        ax.set_title('Diff Eval (deepseek-r1-8b): False Negatives by Violation Type')

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f'{int(count)}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()
        plt.savefig(f'{output_dir}/09_false_negatives.png', dpi=150, bbox_inches='tight')
        plt.close()

    # 10. Accuracy vs Runtime Scatter
    fig, ax = plt.subplots(figsize=(10, 8))

    for violation in df['violation_type'].unique():
        violation_data = df[df['violation_type'] == violation]
        acc = violation_data['detection_success'].mean() * 100
        runtime = violation_data['processing_time'].mean()

        ax.scatter(runtime, acc, s=200, c=VIOLATION_COLORS.get(violation, COLORS['neutral']),
                   label=violation, edgecolor='white', linewidth=2, alpha=0.8)

    ax.set_xlabel('Mean Processing Time (seconds)')
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Diff Eval (deepseek-r1-8b): Accuracy vs Processing Time Trade-off')
    ax.legend(loc='best', frameon=True)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)

    plt.tight_layout()
    plt.savefig(f'{output_dir}/10_accuracy_vs_runtime.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"Visualizations saved to: {output_dir}")


def generate_report(df, metrics, runtime_stats, confusion_data, misclass_patterns, fn_by_type, output_dir):
    """Generate comprehensive analysis report"""
    report = []
    report.append("=" * 80)
    report.append("SOLID BENCHMARK: DIFF EVAL (deepseek-r1-8b) ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    # Overall Summary
    report.append("## OVERALL SUMMARY")
    report.append("-" * 40)
    report.append(f"Total Examples: {len(df)}")
    report.append(f"Overall Accuracy: {metrics['overall']*100:.2f}%")
    report.append(f"Correct Detections: {df['detection_success'].sum()}")
    report.append(f"Incorrect Detections: {(~df['detection_success']).sum()}")
    report.append(f"Mean Processing Time: {df['processing_time'].mean():.2f}s")
    report.append(f"Median Processing Time: {df['processing_time'].median():.2f}s")
    report.append(f"Total Processing Time: {df['processing_time'].sum():.2f}s")
    report.append("")

    # Accuracy by Violation Type
    report.append("## ACCURACY BY VIOLATION TYPE")
    report.append("-" * 40)
    report.append(f"{'Violation':<10} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    report.append("-" * 40)

    for violation in metrics['by_violation'].index:
        correct = int(metrics['by_violation'].loc[violation, 'correct'])
        total = int(metrics['by_violation'].loc[violation, 'total'])
        accuracy = metrics['by_violation'].loc[violation, 'accuracy'] * 100
        report.append(f"{violation:<10} {correct:>8} {total:>8} {accuracy:>9.2f}%")

    report.append("")

    # Accuracy by Difficulty Level
    report.append("## ACCURACY BY DIFFICULTY LEVEL")
    report.append("-" * 40)
    report.append(f"{'Level':<12} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    report.append("-" * 40)

    for level in metrics['by_level'].index:
        correct = int(metrics['by_level'].loc[level, 'correct'])
        total = int(metrics['by_level'].loc[level, 'total'])
        accuracy = metrics['by_level'].loc[level, 'accuracy'] * 100
        report.append(f"{level:<12} {correct:>8} {total:>8} {accuracy:>9.2f}%")

    report.append("")

    # Accuracy by Language
    report.append("## ACCURACY BY PROGRAMMING LANGUAGE")
    report.append("-" * 40)
    report.append(f"{'Language':<12} {'Correct':>8} {'Total':>8} {'Accuracy':>10}")
    report.append("-" * 40)

    for language in metrics['by_language'].index:
        correct = int(metrics['by_language'].loc[language, 'correct'])
        total = int(metrics['by_language'].loc[language, 'total'])
        accuracy = metrics['by_language'].loc[language, 'accuracy'] * 100
        report.append(f"{language:<12} {correct:>8} {total:>8} {accuracy:>9.2f}%")

    report.append("")

    # Runtime Statistics
    report.append("## RUNTIME STATISTICS")
    report.append("-" * 40)
    report.append(f"Overall:")
    report.append(f"  Mean:   {runtime_stats['overall']['mean']:.2f}s")
    report.append(f"  Median: {runtime_stats['overall']['50%']:.2f}s")
    report.append(f"  Std:    {runtime_stats['overall']['std']:.2f}s")
    report.append(f"  Min:    {runtime_stats['overall']['min']:.2f}s")
    report.append(f"  Max:    {runtime_stats['overall']['max']:.2f}s")
    report.append("")

    report.append("By Violation Type:")
    for violation in runtime_stats['by_violation'].index:
        mean_time = runtime_stats['by_violation'].loc[violation, 'mean']
        report.append(f"  {violation}: {mean_time:.2f}s")
    report.append("")

    # Misclassification Analysis
    if not misclass_patterns.empty:
        report.append("## MISCLASSIFICATION PATTERNS")
        report.append("-" * 40)
        report.append(f"{'Actual':<10} {'Detected':<10} {'Count':>8}")
        report.append("-" * 40)

        for _, row in misclass_patterns.head(10).iterrows():
            report.append(f"{row['ground_truth']:<10} {row['detected_violation_type']:<10} {int(row['count']):>8}")

        report.append("")

    # False Negatives
    if len(fn_by_type) > 0:
        report.append("## FALSE NEGATIVES (No Detection)")
        report.append("-" * 40)
        report.append(f"{'Violation':<10} {'Count':>8}")
        report.append("-" * 40)

        for violation, count in fn_by_type.items():
            report.append(f"{violation:<10} {int(count):>8}")

        report.append(f"{'Total':<10} {int(fn_by_type.sum()):>8}")
        report.append("")

    # Key Findings
    report.append("## KEY FINDINGS")
    report.append("-" * 40)

    # Best and worst performing violations
    best_violation = metrics['by_violation']['accuracy'].idxmax()
    worst_violation = metrics['by_violation']['accuracy'].idxmin()
    report.append(f"- Best performing violation: {best_violation} ({metrics['by_violation'].loc[best_violation, 'accuracy']*100:.2f}%)")
    report.append(f"- Worst performing violation: {worst_violation} ({metrics['by_violation'].loc[worst_violation, 'accuracy']*100:.2f}%)")

    # Best and worst performing levels
    best_level = metrics['by_level']['accuracy'].idxmax()
    worst_level = metrics['by_level']['accuracy'].idxmin()
    report.append(f"- Best performing level: {best_level} ({metrics['by_level'].loc[best_level, 'accuracy']*100:.2f}%)")
    report.append(f"- Worst performing level: {worst_level} ({metrics['by_level'].loc[worst_level, 'accuracy']*100:.2f}%)")

    # Best and worst performing languages
    best_language = metrics['by_language']['accuracy'].idxmax()
    worst_language = metrics['by_language']['accuracy'].idxmin()
    report.append(f"- Best performing language: {best_language} ({metrics['by_language'].loc[best_language, 'accuracy']*100:.2f}%)")
    report.append(f"- Worst performing language: {worst_language} ({metrics['by_language'].loc[worst_language, 'accuracy']*100:.2f}%)")

    report.append("")
    report.append("=" * 80)
    report.append("END OF REPORT")
    report.append("=" * 80)

    # Save report
    report_text = "\n".join(report)
    report_path = f"{output_dir}/analysis_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print("\n" + report_text)
    print(f"\nReport saved to: {report_path}")

    return report_text


def main():
    # Paths
    input_file = Path('result/local/diff_eval/deepseek-r1-8b/detection_results.json')
    output_dir = 'analysis/analysis_output_diff_eval_deepseek'

    print("=" * 60)
    print("SOLID Principles Benchmark - Diff Eval Analysis")
    print("Model: deepseek-r1-8b")
    print("=" * 60)
    print()

    # Load results
    print("Loading detection results...")
    data = load_detection_results(input_file)

    # Extract metrics
    print("\nExtracting metrics...")
    df = extract_metrics(data)

    # Calculate metrics
    print("\nCalculating accuracy metrics...")
    metrics = calculate_accuracy_metrics(df)

    print("\nCalculating runtime metrics...")
    runtime_stats = calculate_runtime_metrics(df)

    print("\nAnalyzing misclassifications...")
    confusion_data, misclass_patterns, fn_by_type = analyze_misclassifications(df)

    # Create visualizations
    print("\nCreating visualizations...")
    create_visualizations(df, metrics, runtime_stats, confusion_data, misclass_patterns, fn_by_type, output_dir)

    # Generate report
    print("\nGenerating analysis report...")
    generate_report(df, metrics, runtime_stats, confusion_data, misclass_patterns, fn_by_type, output_dir)

    # Save detailed results to CSV
    csv_path = f'{output_dir}/detailed_results.csv'
    df.to_csv(csv_path, index=False)
    print(f"\nDetailed results saved to: {csv_path}")

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
