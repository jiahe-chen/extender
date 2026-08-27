#!/usr/bin/env python3
"""
Complete data analysis for diff_eval results following the two_agent analysis framework.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from collections import defaultdict

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_detection_results(file_path):
    """Load detection results from JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def extract_results_data(data, model_name):
    """Extract results into a flat list of dictionaries."""
    results = []

    for violation_type, violation_data in data['by_violation_type'].items():
        for result in violation_data['results']:
            results.append({
                'model': model_name,
                'violation_type': result['violation_type'],
                'example_id': result['example_id'],
                'level': result['level'],
                'language': result['language'],
                'detection_success': result['detection_success'],
                'detected_violation_type': result.get('detected_violation_type', ''),
                'actual_violation_type': result['violation_type'],
                'processing_time': result['processing_time_seconds'],
                'api_call_success': result['api_call_success']
            })

    return results

def calculate_accuracy_metrics(df):
    """Calculate accuracy metrics by model and violation type."""
    metrics = {}

    # Overall accuracy by model
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        metrics[model] = {
            'overall_accuracy': model_df['detection_success'].mean(),
            'total_examples': len(model_df),
            'correct_detections': model_df['detection_success'].sum()
        }

    # Accuracy by violation type
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        metrics[model]['by_violation'] = {}

        for violation in df['violation_type'].unique():
            violation_df = model_df[model_df['violation_type'] == violation]
            if len(violation_df) > 0:
                metrics[model]['by_violation'][violation] = {
                    'accuracy': violation_df['detection_success'].mean(),
                    'total': len(violation_df),
                    'correct': violation_df['detection_success'].sum()
                }

    # Accuracy by difficulty level
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        metrics[model]['by_level'] = {}

        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = model_df[model_df['level'] == level]
            if len(level_df) > 0:
                metrics[model]['by_level'][level] = {
                    'accuracy': level_df['detection_success'].mean(),
                    'total': len(level_df),
                    'correct': level_df['detection_success'].sum()
                }

    # Accuracy by language
    for model in df['model'].unique():
        model_df = df[df['model'] == model]
        metrics[model]['by_language'] = {}

        for language in df['language'].unique():
            lang_df = model_df[model_df['language'] == language]
            if len(lang_df) > 0:
                metrics[model]['by_language'][language] = {
                    'accuracy': lang_df['detection_success'].mean(),
                    'total': len(lang_df),
                    'correct': lang_df['detection_success'].sum()
                }

    return metrics

def create_visualizations(df, output_dir):
    """Create all visualization plots."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Accuracy by Model
    plt.figure(figsize=(10, 6))
    model_accuracy = df.groupby('model')['detection_success'].mean().sort_values(ascending=False)
    bars = plt.bar(range(len(model_accuracy)), model_accuracy.values)
    plt.xticks(range(len(model_accuracy)), model_accuracy.index, rotation=45, ha='right')
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Model (diff_eval)')
    plt.ylim(0, 1)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, model_accuracy.values)):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '01_diff_eval_accuracy_by_model.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Accuracy by Violation Type
    plt.figure(figsize=(12, 6))
    violation_accuracy = df.groupby('violation_type')['detection_success'].mean().sort_values(ascending=False)
    bars = plt.bar(range(len(violation_accuracy)), violation_accuracy.values)
    plt.xticks(range(len(violation_accuracy)), violation_accuracy.index, rotation=0)
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Violation Type (diff_eval)')
    plt.ylim(0, 1)

    # Add value labels
    for bar, val in zip(bars, violation_accuracy.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '02_diff_eval_accuracy_by_violation.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Heatmap: Model vs Violation Type
    plt.figure(figsize=(10, 8))
    pivot_data = df.pivot_table(
        values='detection_success',
        index='model',
        columns='violation_type',
        aggfunc='mean'
    )
    sns.heatmap(pivot_data, annot=True, fmt='.2%', cmap='RdYlGn', vmin=0, vmax=1,
                cbar_kws={'label': 'Accuracy'})
    plt.title('Detection Accuracy Heatmap: Model vs Violation Type (diff_eval)')
    plt.xlabel('Violation Type')
    plt.ylabel('Model')
    plt.tight_layout()
    plt.savefig(output_dir / '03_diff_eval_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Runtime Distribution by Model
    plt.figure(figsize=(12, 6))
    models = df['model'].unique()
    runtime_data = [df[df['model'] == model]['processing_time'].values for model in models]

    bp = plt.boxplot(runtime_data, labels=models, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')

    plt.ylabel('Processing Time (seconds)')
    plt.title('Processing Time Distribution by Model (diff_eval)')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '04_diff_eval_runtime_boxplot.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Accuracy vs Runtime Scatter
    plt.figure(figsize=(10, 6))
    model_stats = df.groupby('model').agg({
        'detection_success': 'mean',
        'processing_time': 'mean'
    }).reset_index()

    plt.scatter(model_stats['processing_time'], model_stats['detection_success'],
               s=200, alpha=0.6, c=range(len(model_stats)), cmap='viridis')

    for idx, row in model_stats.iterrows():
        plt.annotate(row['model'],
                    (row['processing_time'], row['detection_success']),
                    xytext=(5, 5), textcoords='offset points', fontsize=9)

    plt.xlabel('Average Processing Time (seconds)')
    plt.ylabel('Detection Accuracy')
    plt.title('Accuracy vs Processing Time by Model (diff_eval)')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '05_diff_eval_accuracy_vs_runtime.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 6. Confusion Matrix for each model
    for model in df['model'].unique():
        model_df = df[df['model'] == model]

        # Create confusion matrix
        violation_types = sorted(df['violation_type'].unique())
        confusion = pd.DataFrame(0, index=violation_types, columns=violation_types + ['None/Other'])

        for _, row in model_df.iterrows():
            actual = row['actual_violation_type']
            detected = row['detected_violation_type'] if row['detected_violation_type'] in violation_types else 'None/Other'
            confusion.loc[actual, detected] += 1

        # Plot
        plt.figure(figsize=(10, 8))
        sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues', cbar_kws={'label': 'Count'})
        plt.title(f'Confusion Matrix: {model} (diff_eval)')
        plt.xlabel('Detected Violation Type')
        plt.ylabel('Actual Violation Type')
        plt.tight_layout()
        plt.savefig(output_dir / f'06_diff_eval_confusion_matrix_{model.replace(":", "_")}.png',
                   dpi=300, bbox_inches='tight')
        plt.close()

    # 7. Accuracy by Difficulty Level
    plt.figure(figsize=(12, 6))
    level_order = ['EASY', 'MODERATE', 'HARD']
    level_data = df.groupby(['model', 'level'])['detection_success'].mean().unstack()
    level_data = level_data[level_order]  # Reorder columns

    level_data.plot(kind='bar', figsize=(12, 6))
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Difficulty Level (diff_eval)')
    plt.xlabel('Model')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Difficulty Level')
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '07_diff_eval_accuracy_by_level.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 8. Accuracy by Language
    plt.figure(figsize=(12, 6))
    lang_data = df.groupby(['model', 'language'])['detection_success'].mean().unstack()

    lang_data.plot(kind='bar', figsize=(12, 6))
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Programming Language (diff_eval)')
    plt.xlabel('Model')
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Language')
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '08_diff_eval_accuracy_by_language.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_summary_report(df, metrics, output_file):
    """Generate a comprehensive summary report."""
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("DIFF_EVAL DETECTION RESULTS - COMPREHENSIVE ANALYSIS\n")
        f.write("=" * 80 + "\n\n")

        # Overall Statistics
        f.write("OVERALL STATISTICS\n")
        f.write("-" * 80 + "\n")
        f.write(f"Total Examples: {len(df)}\n")
        f.write(f"Number of Models: {df['model'].nunique()}\n")
        f.write(f"Violation Types: {', '.join(sorted(df['violation_type'].unique()))}\n")
        f.write(f"Languages: {', '.join(sorted(df['language'].unique()))}\n")
        f.write(f"Difficulty Levels: {', '.join(sorted(df['level'].unique()))}\n\n")

        # Model Performance
        f.write("MODEL PERFORMANCE SUMMARY\n")
        f.write("-" * 80 + "\n")
        for model in sorted(metrics.keys()):
            m = metrics[model]
            f.write(f"\n{model}:\n")
            f.write(f"  Overall Accuracy: {m['overall_accuracy']:.2%}\n")
            f.write(f"  Correct Detections: {m['correct_detections']}/{m['total_examples']}\n")

            # Average processing time
            model_df = df[df['model'] == model]
            avg_time = model_df['processing_time'].mean()
            median_time = model_df['processing_time'].median()
            f.write(f"  Avg Processing Time: {avg_time:.2f}s (median: {median_time:.2f}s)\n")

        # Best and Worst Performing Models
        f.write("\n" + "=" * 80 + "\n")
        f.write("RANKING\n")
        f.write("-" * 80 + "\n")
        model_accuracy = df.groupby('model')['detection_success'].mean().sort_values(ascending=False)
        f.write("\nBest Performing Models:\n")
        for i, (model, acc) in enumerate(model_accuracy.head(3).items(), 1):
            f.write(f"  {i}. {model}: {acc:.2%}\n")

        f.write("\nLowest Performing Models:\n")
        for i, (model, acc) in enumerate(model_accuracy.tail(3).items(), 1):
            f.write(f"  {i}. {model}: {acc:.2%}\n")

        # Violation Type Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIOLATION TYPE ANALYSIS\n")
        f.write("-" * 80 + "\n")
        violation_accuracy = df.groupby('violation_type')['detection_success'].mean().sort_values(ascending=False)
        f.write("\nEasiest to Detect:\n")
        for violation, acc in violation_accuracy.head(3).items():
            f.write(f"  {violation}: {acc:.2%}\n")

        f.write("\nHardest to Detect:\n")
        for violation, acc in violation_accuracy.tail(3).items():
            f.write(f"  {violation}: {acc:.2%}\n")

        # Difficulty Level Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("DIFFICULTY LEVEL ANALYSIS\n")
        f.write("-" * 80 + "\n")
        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = df[df['level'] == level]
            acc = level_df['detection_success'].mean()
            f.write(f"\n{level}:\n")
            f.write(f"  Accuracy: {acc:.2%}\n")
            f.write(f"  Examples: {len(level_df)}\n")
            f.write(f"  Correct: {level_df['detection_success'].sum()}\n")

        # Language Analysis
        f.write("\n" + "=" * 80 + "\n")
        f.write("PROGRAMMING LANGUAGE ANALYSIS\n")
        f.write("-" * 80 + "\n")
        for language in sorted(df['language'].unique()):
            lang_df = df[df['language'] == language]
            acc = lang_df['detection_success'].mean()
            f.write(f"\n{language}:\n")
            f.write(f"  Accuracy: {acc:.2%}\n")
            f.write(f"  Examples: {len(lang_df)}\n")
            f.write(f"  Correct: {lang_df['detection_success'].sum()}\n")

        # Detailed Model Breakdown
        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED MODEL BREAKDOWN\n")
        f.write("-" * 80 + "\n")
        for model in sorted(metrics.keys()):
            f.write(f"\n{model}\n")
            f.write("-" * 40 + "\n")

            # By violation type
            f.write("  By Violation Type:\n")
            for violation, stats in sorted(metrics[model]['by_violation'].items()):
                f.write(f"    {violation}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})\n")

            # By difficulty level
            f.write("\n  By Difficulty Level:\n")
            for level, stats in sorted(metrics[model]['by_level'].items()):
                f.write(f"    {level}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})\n")

            # By language
            f.write("\n  By Language:\n")
            for language, stats in sorted(metrics[model]['by_language'].items()):
                f.write(f"    {language}: {stats['accuracy']:.2%} ({stats['correct']}/{stats['total']})\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")

def main():
    # Define paths
    base_dir = Path('/Users/he/jcSOLID/result/local/diff_eval')
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_diff_eval')

    # Load data from both models
    all_results = []

    for model_dir in base_dir.iterdir():
        if model_dir.is_dir():
            model_name = model_dir.name
            results_file = model_dir / 'detection_results.json'

            if results_file.exists():
                print(f"Loading data for {model_name}...")
                data = load_detection_results(results_file)
                results = extract_results_data(data, model_name)
                all_results.extend(results)

    # Create DataFrame
    df = pd.DataFrame(all_results)
    print(f"\nTotal records loaded: {len(df)}")
    print(f"Models: {df['model'].unique()}")

    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculate_accuracy_metrics(df)

    # Create visualizations
    print("Creating visualizations...")
    create_visualizations(df, output_dir)

    # Save detailed results to CSV
    print("Saving detailed results...")
    csv_file = output_dir / 'diff_eval_detailed_results.csv'
    df.to_csv(csv_file, index=False)
    print(f"Saved to {csv_file}")

    # Generate summary report
    print("Generating summary report...")
    report_file = output_dir / 'diff_eval_summary_report.txt'
    generate_summary_report(df, metrics, report_file)
    print(f"Saved to {report_file}")

    # Print quick summary
    print("\n" + "=" * 80)
    print("QUICK SUMMARY")
    print("=" * 80)
    for model in sorted(df['model'].unique()):
        model_df = df[df['model'] == model]
        acc = model_df['detection_success'].mean()
        avg_time = model_df['processing_time'].mean()
        print(f"{model}: {acc:.2%} accuracy, {avg_time:.2f}s avg time")

    print(f"\nAll outputs saved to: {output_dir}")
    print("Analysis complete!")

if __name__ == '__main__':
    main()
