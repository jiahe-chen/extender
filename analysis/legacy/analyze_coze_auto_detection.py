#!/usr/bin/env python3
"""
Coze Auto Detection Data Analysis
==================================

Analyzes the SOLID violation detection results from Coze API.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import Counter

# Configure matplotlib for better display
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10
plt.style.use('seaborn-v0_8-whitegrid')

def load_data(file_path: str) -> dict:
    """Load JSON data from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_results(data: dict) -> pd.DataFrame:
    """Extract results into a DataFrame"""
    records = []
    for violation_type, violation_data in data.get('by_violation_type', {}).items():
        for result in violation_data.get('results', []):
            records.append({
                'example_id': result.get('example_id'),
                'expected_violation': violation_type,
                'detected_violation': result.get('detected_violation_type'),
                'detection_success': result.get('detection_success', False),
                'level': result.get('level'),
                'language': result.get('language'),
                'chrf_score': result.get('refactor_chrf_score'),
                'api_success': result.get('api_call_success', False),
                'has_refactored_code': result.get('refactored_code') is not None,
            })
    return pd.DataFrame(records)

def analyze_model(name: str, df: pd.DataFrame):
    """Analyze results for a single model"""
    print(f"\n{'='*60}")
    print(f"MODEL: {name}")
    print(f"{'='*60}")

    # Overall stats
    total = len(df)
    successful = df['detection_success'].sum()
    accuracy = successful / total * 100 if total > 0 else 0

    print(f"\n## Overall Statistics")
    print(f"Total examples: {total}")
    print(f"Successful detections: {successful}")
    print(f"Overall Accuracy: {accuracy:.2f}%")

    # By violation type
    print(f"\n## Accuracy by Violation Type")
    by_type = df.groupby('expected_violation').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    by_type.columns = ['Correct', 'Total', 'Accuracy']
    by_type['Accuracy'] = (by_type['Accuracy'] * 100).round(2)
    print(by_type.to_string())

    # By difficulty level
    print(f"\n## Accuracy by Difficulty Level")
    by_level = df.groupby('level').agg({
        'detection_success': ['sum', 'count', 'mean']
    }).round(4)
    by_level.columns = ['Correct', 'Total', 'Accuracy']
    by_level['Accuracy'] = (by_level['Accuracy'] * 100).round(2)
    print(by_level.to_string())

    # ChrF scores (refactoring quality)
    valid_chrf = df[df['chrf_score'].notna()]['chrf_score']
    if len(valid_chrf) > 0:
        print(f"\n## Refactoring Quality (ChrF Scores)")
        print(f"Mean ChrF Score: {valid_chrf.mean():.2f}")
        print(f"Median ChrF Score: {valid_chrf.median():.2f}")
        print(f"Min ChrF Score: {valid_chrf.min():.2f}")
        print(f"Max ChrF Score: {valid_chrf.max():.2f}")
        print(f"Std Dev: {valid_chrf.std():.2f}")

    # Misclassifications
    print(f"\n## Misclassification Analysis")
    misclassified = df[~df['detection_success']]
    if len(misclassified) > 0:
        print(f"Total misclassified: {len(misclassified)}")

        # What was detected instead
        detected_types = misclassified['detected_violation'].value_counts()
        print(f"\nDetected types for misclassified examples:")
        for vtype, count in detected_types.items():
            print(f"  {vtype}: {count}")

    return {
        'name': name,
        'total': total,
        'accuracy': accuracy,
        'by_type': by_type,
        'by_level': by_level,
        'chrf_mean': valid_chrf.mean() if len(valid_chrf) > 0 else None,
    }

def create_visualizations(results: dict, output_dir: Path):
    """Create visualization charts"""
    output_dir.mkdir(exist_ok=True, parents=True)

    models = list(results.keys())

    # 1. Overall Accuracy Comparison
    fig, ax = plt.subplots(figsize=(10, 6))
    accuracies = [results[m]['accuracy'] for m in models]
    bars = ax.bar(models, accuracies, color=['#2ecc71', '#3498db'])
    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Overall Detection Accuracy by Model')
    ax.set_ylim(0, 100)
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f'{acc:.1f}%', ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'overall_accuracy.png', dpi=150)
    plt.close()

    # 2. Accuracy by Violation Type (grouped bar chart)
    fig, ax = plt.subplots(figsize=(12, 6))
    violation_types = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
    x = np.arange(len(violation_types))
    width = 0.35

    for i, model in enumerate(models):
        accs = []
        for vtype in violation_types:
            try:
                accs.append(results[model]['by_type'].loc[vtype, 'Accuracy'])
            except KeyError:
                accs.append(0)
        offset = width * (i - len(models)/2 + 0.5)
        bars = ax.bar(x + offset, accs, width, label=model)

    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Detection Accuracy by Violation Type')
    ax.set_xticks(x)
    ax.set_xticklabels(violation_types)
    ax.legend()
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_by_violation_type.png', dpi=150)
    plt.close()

    # 3. Accuracy by Difficulty Level
    fig, ax = plt.subplots(figsize=(10, 6))
    levels = ['EASY', 'MODERATE', 'HARD']
    x = np.arange(len(levels))
    width = 0.35

    for i, model in enumerate(models):
        accs = []
        for level in levels:
            try:
                accs.append(results[model]['by_level'].loc[level, 'Accuracy'])
            except KeyError:
                accs.append(0)
        offset = width * (i - len(models)/2 + 0.5)
        bars = ax.bar(x + offset, accs, width, label=model)

    ax.set_ylabel('Accuracy (%)')
    ax.set_title('Detection Accuracy by Difficulty Level')
    ax.set_xticks(x)
    ax.set_xticklabels(levels)
    ax.legend()
    ax.set_ylim(0, 100)
    plt.tight_layout()
    plt.savefig(output_dir / 'accuracy_by_difficulty.png', dpi=150)
    plt.close()

    # 4. ChrF Score Distribution
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for i, (model, df) in enumerate([(m, results[m].get('df')) for m in models]):
        if df is not None:
            valid_chrf = df[df['chrf_score'].notna()]['chrf_score']
            if len(valid_chrf) > 0:
                axes[i].hist(valid_chrf, bins=20, edgecolor='black', alpha=0.7)
                axes[i].axvline(valid_chrf.mean(), color='red', linestyle='--', label=f'Mean: {valid_chrf.mean():.1f}')
                axes[i].set_xlabel('ChrF Score')
                axes[i].set_ylabel('Count')
                axes[i].set_title(f'{model} - ChrF Score Distribution')
                axes[i].legend()
    plt.tight_layout()
    plt.savefig(output_dir / 'chrf_distribution.png', dpi=150)
    plt.close()

    print(f"\nVisualizations saved to: {output_dir}")

def generate_summary_table(results: dict) -> pd.DataFrame:
    """Generate a summary comparison table"""
    rows = []
    for model, data in results.items():
        row = {
            'Model': model,
            'Total Examples': data['total'],
            'Overall Accuracy (%)': round(data['accuracy'], 2),
        }

        # Add by-type accuracies
        for vtype in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
            try:
                row[f'{vtype} Acc (%)'] = data['by_type'].loc[vtype, 'Accuracy']
            except KeyError:
                row[f'{vtype} Acc (%)'] = 'N/A'

        # Add ChrF
        if data['chrf_mean'] is not None:
            row['Mean ChrF'] = round(data['chrf_mean'], 2)
        else:
            row['Mean ChrF'] = 'N/A'

        rows.append(row)

    return pd.DataFrame(rows)

def main():
    # Data files
    data_dir = Path('result/coze_auto_detection')
    files = {
        'DeepSeek V3': data_dir / 'auto_detection_deepseek_V3.json',
        'Doubao 1.5 Pro': data_dir / 'auto_detection_doubao_1.5_pro.json',
    }

    # Load and analyze each model
    results = {}
    for model_name, file_path in files.items():
        if file_path.exists():
            data = load_data(file_path)
            df = extract_results(data)
            analysis = analyze_model(model_name, df)
            analysis['df'] = df  # Store for visualizations
            results[model_name] = analysis
        else:
            print(f"Warning: File not found: {file_path}")

    # Create comparison summary
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")

    summary = generate_summary_table(results)
    print("\n" + summary.to_string(index=False))

    # Create visualizations
    output_dir = Path('result/coze_auto_detection/analysis')
    create_visualizations(results, output_dir)

    # Save summary to CSV
    summary.to_csv(output_dir / 'summary.csv', index=False)
    print(f"\nSummary saved to: {output_dir / 'summary.csv'}")

if __name__ == '__main__':
    main()
