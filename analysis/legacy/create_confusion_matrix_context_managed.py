#!/usr/bin/env python3
"""
Create detailed confusion matrix for Context-Managed Diff (qwen3-8b)
Analyzes detection patterns and misclassifications
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 10)

def load_context_managed_data():
    """Load Context-Managed Diff qwen3-8b data."""
    file_path = Path(r'C:\Users\Jay\jcSOLID\result\local\diff_eval\qwen3-8b\detection_results.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = []
    for violation_type, violation_data in data['by_violation_type'].items():
        for result in violation_data['results']:
            results.append({
                'actual_violation': violation_type,
                'detected_violation': result.get('detected_violation_type', 'None'),
                'detection_success': result['detection_success'],
                'level': result.get('level', 'UNKNOWN'),
                'language': result.get('language', 'UNKNOWN'),
                'example_id': result.get('example_id', 'UNKNOWN')
            })

    return pd.DataFrame(results)

def create_confusion_matrix(df, violation_types):
    """Create confusion matrix."""
    # Add 'None/Other' category for failed detections
    all_categories = violation_types + ['None/Other']
    confusion = pd.DataFrame(0, index=violation_types, columns=all_categories)

    for _, row in df.iterrows():
        actual = row['actual_violation']
        detected = row['detected_violation']

        if actual in violation_types:
            if detected in violation_types:
                confusion.loc[actual, detected] += 1
            else:
                confusion.loc[actual, 'None/Other'] += 1

    return confusion

def plot_confusion_matrix_counts(confusion, accuracy, output_path):
    """Plot confusion matrix with counts."""
    fig, ax = plt.subplots(figsize=(12, 10))

    # Create heatmap
    sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues',
                ax=ax, cbar_kws={'label': 'Count'},
                vmin=0, vmax=confusion.values.max(),
                linewidths=0.5, linecolor='gray')

    ax.set_title(f'Confusion Matrix: Context-Managed Diff (Qwen3-8B)\nOverall Accuracy: {accuracy:.2%}',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Detected Violation Type', fontsize=13, fontweight='bold')
    ax.set_ylabel('Actual Violation Type', fontsize=13, fontweight='bold')

    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def plot_confusion_matrix_normalized(confusion, accuracy, output_path):
    """Plot normalized confusion matrix (percentages)."""
    fig, ax = plt.subplots(figsize=(12, 10))

    # Normalize by row (actual violation type)
    confusion_normalized = confusion.div(confusion.sum(axis=1), axis=0) * 100

    # Create heatmap with custom colormap
    sns.heatmap(confusion_normalized, annot=True, fmt='.1f', cmap='RdYlGn',
                ax=ax, cbar_kws={'label': 'Percentage (%)'},
                vmin=0, vmax=100,
                linewidths=0.5, linecolor='gray')

    ax.set_title(f'Confusion Matrix (Normalized %): Context-Managed Diff (Qwen3-8B)\nOverall Accuracy: {accuracy:.2%}',
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Detected Violation Type', fontsize=13, fontweight='bold')
    ax.set_ylabel('Actual Violation Type', fontsize=13, fontweight='bold')

    # Rotate labels
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=11)
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=11)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def plot_per_violation_accuracy(df, violation_types, output_path):
    """Plot per-violation accuracy breakdown."""
    fig, ax = plt.subplots(figsize=(12, 7))

    accuracies = []
    correct_counts = []
    total_counts = []

    for violation in violation_types:
        violation_df = df[df['actual_violation'] == violation]
        acc = violation_df['detection_success'].mean() * 100
        correct = violation_df['detection_success'].sum()
        total = len(violation_df)

        accuracies.append(acc)
        correct_counts.append(correct)
        total_counts.append(total)

    # Create bars
    colors = ['#2ecc71' if acc >= 80 else '#f39c12' if acc >= 60 else '#e74c3c' for acc in accuracies]
    bars = ax.bar(violation_types, accuracies, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    # Add value labels
    for bar, acc, correct, total in zip(bars, accuracies, correct_counts, total_counts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{acc:.1f}%\n({correct}/{total})',
                ha='center', va='bottom', fontsize=11, fontweight='bold')

    ax.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
    ax.set_title('Per-Violation Detection Accuracy', fontsize=15, fontweight='bold')
    ax.set_ylim(0, 110)
    ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='80% threshold (good)')
    ax.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='60% threshold (moderate)')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def plot_misclassification_patterns(df, output_path):
    """Plot top misclassification patterns."""
    # Get misclassifications
    misclassified = df[df['detection_success'] == False].copy()

    # Count misclassification patterns
    pattern_counts = misclassified.groupby(['actual_violation', 'detected_violation']).size().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 8))

    # Create labels
    labels = [f"{actual} → {detected}" for (actual, detected), _ in pattern_counts.items()]
    counts = pattern_counts.values

    # Create horizontal bar chart
    bars = ax.barh(range(len(labels)), counts, color='#e74c3c', alpha=0.7, edgecolor='black', linewidth=1)

    # Add value labels
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width, bar.get_y() + bar.get_height()/2.,
                f' {count}',
                ha='left', va='center', fontsize=11, fontweight='bold')

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('Number of Occurrences', fontsize=13, fontweight='bold')
    ax.set_title('Top 10 Misclassification Patterns', fontsize=15, fontweight='bold')
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def plot_accuracy_by_difficulty(df, violation_types, output_path):
    """Plot accuracy by difficulty level for each violation."""
    fig, ax = plt.subplots(figsize=(14, 8))

    levels = ['EASY', 'MODERATE', 'HARD']
    x = np.arange(len(violation_types))
    width = 0.25

    for idx, level in enumerate(levels):
        accuracies = []
        for violation in violation_types:
            level_violation_df = df[(df['actual_violation'] == violation) & (df['level'] == level)]
            if len(level_violation_df) > 0:
                acc = level_violation_df['detection_success'].mean() * 100
            else:
                acc = 0
            accuracies.append(acc)

        offset = (idx - 1) * width
        bars = ax.bar(x + offset, accuracies, width, label=level, alpha=0.8)

        # Add value labels
        for bar, acc in zip(bars, accuracies):
            if acc > 0:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{acc:.0f}%',
                        ha='center', va='bottom', fontsize=9)

    ax.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
    ax.set_title('Accuracy by Difficulty Level and Violation Type', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(violation_types, fontsize=11)
    ax.legend(fontsize=11)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def plot_accuracy_by_language(df, violation_types, output_path):
    """Plot accuracy by programming language."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Normalize language names
    df['language_norm'] = df['language'].replace({'C#': 'CSHARP'})
    languages = sorted(df['language_norm'].unique())

    x = np.arange(len(violation_types))
    width = 0.15

    for idx, language in enumerate(languages):
        accuracies = []
        for violation in violation_types:
            lang_violation_df = df[(df['actual_violation'] == violation) & (df['language_norm'] == language)]
            if len(lang_violation_df) > 0:
                acc = lang_violation_df['detection_success'].mean() * 100
            else:
                acc = 0
            accuracies.append(acc)

        offset = (idx - 2) * width
        bars = ax.bar(x + offset, accuracies, width, label=language, alpha=0.8)

    ax.set_ylabel('Accuracy (%)', fontsize=13, fontweight='bold')
    ax.set_title('Accuracy by Programming Language and Violation Type', fontsize=15, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(violation_types, fontsize=11)
    ax.legend(fontsize=10, ncol=2)
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[OK] Saved: {output_path.name}")
    plt.close()

def print_detailed_statistics(df, confusion, violation_types):
    """Print detailed statistics."""
    print("\n" + "="*80)
    print("DETAILED CONFUSION MATRIX ANALYSIS")
    print("="*80)

    # Overall statistics
    total_examples = len(df)
    overall_accuracy = df['detection_success'].mean()
    total_correct = df['detection_success'].sum()

    print(f"\nOVERALL STATISTICS:")
    print(f"  Total examples: {total_examples}")
    print(f"  Overall accuracy: {overall_accuracy:.2%} ({total_correct}/{total_examples})")
    print(f"  Total errors: {total_examples - total_correct} ({(1-overall_accuracy):.2%})")

    # Per-violation statistics
    print(f"\nPER-VIOLATION STATISTICS:")
    print(f"{'Violation':<10} {'Total':<8} {'Correct':<8} {'Accuracy':<10} {'Precision':<10} {'Recall':<10}")
    print("-"*70)

    for violation in violation_types:
        # Recall (sensitivity): TP / (TP + FN)
        violation_df = df[df['actual_violation'] == violation]
        total = len(violation_df)
        correct = violation_df['detection_success'].sum()
        recall = correct / total if total > 0 else 0

        # Precision: TP / (TP + FP)
        detected_as_violation = df[df['detected_violation'] == violation]
        true_positives = len(detected_as_violation[detected_as_violation['actual_violation'] == violation])
        precision = true_positives / len(detected_as_violation) if len(detected_as_violation) > 0 else 0

        print(f"{violation:<10} {total:<8} {correct:<8} {recall:<10.2%} {precision:<10.2%} {recall:<10.2%}")

    # Confusion patterns
    print(f"\nTOP CONFUSION PATTERNS:")
    misclassified = df[df['detection_success'] == False]
    pattern_counts = misclassified.groupby(['actual_violation', 'detected_violation']).size().sort_values(ascending=False).head(10)

    for (actual, detected), count in pattern_counts.items():
        percentage = count / len(misclassified) * 100
        print(f"  {actual} → {detected}: {count} times ({percentage:.1f}% of all errors)")

    # Difficulty breakdown
    print(f"\nACCURACY BY DIFFICULTY:")
    for level in ['EASY', 'MODERATE', 'HARD']:
        level_df = df[df['level'] == level]
        if len(level_df) > 0:
            acc = level_df['detection_success'].mean()
            correct = level_df['detection_success'].sum()
            total = len(level_df)
            print(f"  {level:<10}: {acc:.2%} ({correct}/{total})")

    # Language breakdown
    print(f"\nACCURACY BY LANGUAGE:")
    df['language_norm'] = df['language'].replace({'C#': 'CSHARP'})
    for language in sorted(df['language_norm'].unique()):
        lang_df = df[df['language_norm'] == language]
        if len(lang_df) > 0:
            acc = lang_df['detection_success'].mean()
            correct = lang_df['detection_success'].sum()
            total = len(lang_df)
            print(f"  {language:<10}: {acc:.2%} ({correct}/{total})")

    # Most problematic examples
    print(f"\nMOST PROBLEMATIC COMBINATIONS:")
    for violation in violation_types:
        for level in ['HARD']:
            combo_df = df[(df['actual_violation'] == violation) & (df['level'] == level)]
            if len(combo_df) > 0:
                acc = combo_df['detection_success'].mean()
                if acc < 0.5:  # Less than 50% accuracy
                    correct = combo_df['detection_success'].sum()
                    total = len(combo_df)
                    print(f"  {violation} + {level}: {acc:.2%} ({correct}/{total}) - NEEDS ATTENTION")

def main():
    """Main function."""
    print("="*80)
    print("CONFUSION MATRIX ANALYSIS: Context-Managed Diff (Qwen3-8B)")
    print("="*80)

    # Create output directory
    output_dir = Path(r'C:\Users\Jay\jcSOLID\analysis\confusion_matrix_analysis')
    output_dir.mkdir(exist_ok=True)

    # Load data
    print("\nLoading data...")
    df = load_context_managed_data()

    # Get violation types
    violation_types = sorted(df['actual_violation'].unique())
    print(f"Violation types: {violation_types}")
    print(f"Total examples: {len(df)}")

    # Create confusion matrix
    print("\nCreating confusion matrix...")
    confusion = create_confusion_matrix(df, violation_types)

    # Calculate overall accuracy
    overall_accuracy = df['detection_success'].mean()

    # Generate visualizations
    print("\nGenerating visualizations...")

    plot_confusion_matrix_counts(
        confusion, overall_accuracy,
        output_dir / 'confusion_matrix_counts.png'
    )

    plot_confusion_matrix_normalized(
        confusion, overall_accuracy,
        output_dir / 'confusion_matrix_normalized.png'
    )

    plot_per_violation_accuracy(
        df, violation_types,
        output_dir / 'per_violation_accuracy.png'
    )

    plot_misclassification_patterns(
        df,
        output_dir / 'misclassification_patterns.png'
    )

    plot_accuracy_by_difficulty(
        df, violation_types,
        output_dir / 'accuracy_by_difficulty.png'
    )

    plot_accuracy_by_language(
        df, violation_types,
        output_dir / 'accuracy_by_language.png'
    )

    # Print detailed statistics
    print_detailed_statistics(df, confusion, violation_types)

    # Save confusion matrix to CSV
    csv_path = output_dir / 'confusion_matrix.csv'
    confusion.to_csv(csv_path)
    print(f"\n[OK] Saved confusion matrix to: {csv_path}")

    # Save normalized confusion matrix to CSV
    confusion_normalized = confusion.div(confusion.sum(axis=1), axis=0) * 100
    csv_normalized_path = output_dir / 'confusion_matrix_normalized.csv'
    confusion_normalized.to_csv(csv_normalized_path)
    print(f"[OK] Saved normalized confusion matrix to: {csv_normalized_path}")

    print("\n" + "="*80)
    print(f"All visualizations saved to: {output_dir}")
    print("="*80)
    print("\nGenerated files:")
    for file in sorted(output_dir.glob('*.png')):
        print(f"  - {file.name}")
    print("\nCSV files:")
    for file in sorted(output_dir.glob('*.csv')):
        print(f"  - {file.name}")

    print("\nAnalysis complete!")

if __name__ == '__main__':
    main()
