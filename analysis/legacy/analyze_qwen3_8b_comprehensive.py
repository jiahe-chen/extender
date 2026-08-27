#!/usr/bin/env python3
"""
Comprehensive analysis for qwen3-8b diff_eval results with comparisons to two_agent and langgraph.
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

def extract_qwen3_results(data):
    """Extract qwen3-8b results into a flat list of dictionaries."""
    results = []

    for violation_type, violation_data in data['by_violation_type'].items():
        for result in violation_data['results']:
            results.append({
                'agent_type': 'diff_eval',
                'model': 'qwen3-8b',
                'violation_type': result['ground_truth'],
                'example_id': result['example_id'],
                'level': result['level'],
                'language': result['language'],
                'detection_success': result['detection_success'],
                'detected_violation_type': result.get('detected_violation_type', ''),
                'actual_violation_type': result['ground_truth'],
                'processing_time': result['processing_time_seconds'],
                'api_call_success': result['api_call_success']
            })

    return results

def load_comparison_data():
    """Load two_agent and langgraph data for comparison."""
    # Load two_agent data
    two_agent_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_two_agent/two_agent_detailed_results.csv')
    langgraph_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_langgraph/langgraph_detailed_results.csv')

    dfs = []

    if two_agent_csv.exists():
        df_two_agent = pd.read_csv(two_agent_csv)
        dfs.append(df_two_agent)

    if langgraph_csv.exists():
        df_langgraph = pd.read_csv(langgraph_csv)
        dfs.append(df_langgraph)

    return dfs

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

def create_qwen3_visualizations(df, output_dir):
    """Create visualizations for qwen3-8b results."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Overall Accuracy
    plt.figure(figsize=(8, 6))
    acc = df['detection_success'].mean()
    plt.bar(['qwen3-8b'], [acc], color='steelblue')
    plt.ylabel('Accuracy')
    plt.title('qwen3-8b Detection Accuracy (diff_eval)')
    plt.ylim(0, 1)
    plt.text(0, acc + 0.02, f'{acc:.2%}', ha='center', va='bottom', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / '01_qwen3_overall_accuracy.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Accuracy by Violation Type
    plt.figure(figsize=(12, 6))
    violation_accuracy = df.groupby('violation_type')['detection_success'].mean().sort_values(ascending=False)
    bars = plt.bar(range(len(violation_accuracy)), violation_accuracy.values, color='steelblue')
    plt.xticks(range(len(violation_accuracy)), violation_accuracy.index, rotation=0)
    plt.ylabel('Accuracy')
    plt.title('qwen3-8b Detection Accuracy by Violation Type')
    plt.ylim(0, 1)

    for bar, val in zip(bars, violation_accuracy.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '02_qwen3_accuracy_by_violation.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Accuracy by Difficulty Level
    plt.figure(figsize=(10, 6))
    level_order = ['EASY', 'MODERATE', 'HARD']
    level_accuracy = df.groupby('level')['detection_success'].mean()
    level_accuracy = level_accuracy.reindex(level_order)

    bars = plt.bar(range(len(level_accuracy)), level_accuracy.values, color=['green', 'orange', 'red'])
    plt.xticks(range(len(level_accuracy)), level_order)
    plt.ylabel('Accuracy')
    plt.title('qwen3-8b Detection Accuracy by Difficulty Level')
    plt.ylim(0, 1)

    for bar, val in zip(bars, level_accuracy.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_dir / '03_qwen3_accuracy_by_level.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Accuracy by Language
    plt.figure(figsize=(10, 6))
    lang_accuracy = df.groupby('language')['detection_success'].mean().sort_values(ascending=False)
    bars = plt.bar(range(len(lang_accuracy)), lang_accuracy.values, color='steelblue')
    plt.xticks(range(len(lang_accuracy)), lang_accuracy.index, rotation=45, ha='right')
    plt.ylabel('Accuracy')
    plt.title('qwen3-8b Detection Accuracy by Programming Language')
    plt.ylim(0, 1)

    for bar, val in zip(bars, lang_accuracy.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / '04_qwen3_accuracy_by_language.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Confusion Matrix
    plt.figure(figsize=(10, 8))
    violation_types = sorted(df['violation_type'].unique())
    confusion = pd.DataFrame(0, index=violation_types, columns=violation_types + ['None/Other'])

    for _, row in df.iterrows():
        actual = row['actual_violation_type']
        detected = row['detected_violation_type'] if row['detected_violation_type'] in violation_types else 'None/Other'
        confusion.loc[actual, detected] += 1

    sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues', cbar_kws={'label': 'Count'})
    plt.title('qwen3-8b Confusion Matrix')
    plt.xlabel('Detected Violation Type')
    plt.ylabel('Actual Violation Type')
    plt.tight_layout()
    plt.savefig(output_dir / '05_qwen3_confusion_matrix.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 6. Processing Time Distribution
    plt.figure(figsize=(10, 6))
    plt.hist(df['processing_time'], bins=30, color='steelblue', edgecolor='black', alpha=0.7)
    plt.xlabel('Processing Time (seconds)')
    plt.ylabel('Frequency')
    plt.title('qwen3-8b Processing Time Distribution')
    plt.axvline(df['processing_time'].mean(), color='red', linestyle='--',
                label=f'Mean: {df["processing_time"].mean():.2f}s')
    plt.axvline(df['processing_time'].median(), color='green', linestyle='--',
                label=f'Median: {df["processing_time"].median():.2f}s')
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / '06_qwen3_processing_time_dist.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_comparison_visualizations(df_qwen3, df_comparison, output_dir):
    """Create comparison visualizations between qwen3-8b and other approaches."""
    output_dir = Path(output_dir)

    # Combine all data
    df_all = pd.concat([df_qwen3, df_comparison], ignore_index=True)

    # 1. Overall Accuracy Comparison
    plt.figure(figsize=(12, 6))
    agent_accuracy = df_all.groupby('agent_type')['detection_success'].mean().sort_values(ascending=False)
    bars = plt.bar(range(len(agent_accuracy)), agent_accuracy.values,
                   color=['steelblue', 'coral', 'lightgreen'][:len(agent_accuracy)])
    plt.xticks(range(len(agent_accuracy)), agent_accuracy.index, rotation=0)
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy Comparison: diff_eval vs two_agent vs langgraph')
    plt.ylim(0, 1)

    for bar, val in zip(bars, agent_accuracy.values):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{val:.2%}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / '07_comparison_overall_accuracy.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. Accuracy by Violation Type - Comparison
    plt.figure(figsize=(14, 7))
    violation_comparison = df_all.groupby(['agent_type', 'violation_type'])['detection_success'].mean().unstack()
    violation_comparison.plot(kind='bar', figsize=(14, 7), width=0.8)
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Violation Type: Comparison')
    plt.xlabel('Agent Type')
    plt.xticks(rotation=0)
    plt.legend(title='Violation Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '08_comparison_by_violation.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Accuracy by Difficulty Level - Comparison
    plt.figure(figsize=(12, 6))
    level_order = ['EASY', 'MODERATE', 'HARD']
    level_comparison = df_all.groupby(['agent_type', 'level'])['detection_success'].mean().unstack()
    level_comparison = level_comparison[level_order]

    level_comparison.plot(kind='bar', figsize=(12, 6), color=['green', 'orange', 'red'])
    plt.ylabel('Accuracy')
    plt.title('Detection Accuracy by Difficulty Level: Comparison')
    plt.xlabel('Agent Type')
    plt.xticks(rotation=0)
    plt.legend(title='Difficulty Level')
    plt.ylim(0, 1)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '09_comparison_by_level.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 4. Processing Time Comparison
    plt.figure(figsize=(12, 6))
    agent_types = df_all['agent_type'].unique()
    time_data = [df_all[df_all['agent_type'] == agent]['processing_time'].values for agent in agent_types]

    bp = plt.boxplot(time_data, labels=agent_types, patch_artist=True)
    colors = ['steelblue', 'coral', 'lightgreen']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)

    plt.ylabel('Processing Time (seconds)')
    plt.title('Processing Time Distribution: Comparison')
    plt.xticks(rotation=0)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '10_comparison_processing_time.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 5. Accuracy vs Processing Time Scatter
    plt.figure(figsize=(12, 7))
    agent_stats = df_all.groupby('agent_type').agg({
        'detection_success': 'mean',
        'processing_time': 'mean'
    }).reset_index()

    colors_map = {'diff_eval': 'steelblue', 'two_agent': 'coral', 'langgraph': 'lightgreen'}
    for idx, row in agent_stats.iterrows():
        color = colors_map.get(row['agent_type'], 'gray')
        plt.scatter(row['processing_time'], row['detection_success'],
                   s=300, alpha=0.6, c=color, edgecolors='black', linewidth=2)
        plt.annotate(row['agent_type'],
                    (row['processing_time'], row['detection_success']),
                    xytext=(10, 10), textcoords='offset points', fontsize=11, fontweight='bold')

    plt.xlabel('Average Processing Time (seconds)')
    plt.ylabel('Detection Accuracy')
    plt.title('Accuracy vs Processing Time: Comparison')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / '11_comparison_accuracy_vs_time.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 6. Heatmap Comparison - Violation Type Performance
    fig, axes = plt.subplots(1, len(agent_types), figsize=(18, 6))
    if len(agent_types) == 1:
        axes = [axes]

    for idx, agent in enumerate(agent_types):
        agent_df = df_all[df_all['agent_type'] == agent]
        pivot_data = agent_df.pivot_table(
            values='detection_success',
            index='violation_type',
            columns='level',
            aggfunc='mean'
        )

        if len(level_order) == len(pivot_data.columns):
            pivot_data = pivot_data[level_order]

        sns.heatmap(pivot_data, annot=True, fmt='.2%', cmap='RdYlGn',
                   vmin=0, vmax=1, ax=axes[idx], cbar_kws={'label': 'Accuracy'})
        axes[idx].set_title(f'{agent} Performance')
        axes[idx].set_xlabel('Difficulty Level')
        axes[idx].set_ylabel('Violation Type')

    plt.tight_layout()
    plt.savefig(output_dir / '12_comparison_heatmaps.png', dpi=300, bbox_inches='tight')
    plt.close()

def generate_comprehensive_report(df_qwen3, df_comparison, metrics, output_file):
    """Generate a comprehensive summary report with comparisons."""
    with open(output_file, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("QWEN3-8B COMPREHENSIVE ANALYSIS WITH COMPARISONS\n")
        f.write("=" * 100 + "\n\n")

        # qwen3-8b Statistics
        f.write("QWEN3-8B (diff_eval) STATISTICS\n")
        f.write("-" * 100 + "\n")
        f.write(f"Total Examples: {len(df_qwen3)}\n")
        f.write(f"Overall Accuracy: {df_qwen3['detection_success'].mean():.2%}\n")
        f.write(f"Correct Detections: {df_qwen3['detection_success'].sum()}/{len(df_qwen3)}\n")
        f.write(f"Average Processing Time: {df_qwen3['processing_time'].mean():.2f}s\n")
        f.write(f"Median Processing Time: {df_qwen3['processing_time'].median():.2f}s\n")
        f.write(f"Violation Types: {', '.join(sorted(df_qwen3['violation_type'].unique()))}\n")
        f.write(f"Languages: {', '.join(sorted(df_qwen3['language'].unique()))}\n\n")

        # Performance by Violation Type
        f.write("PERFORMANCE BY VIOLATION TYPE\n")
        f.write("-" * 100 + "\n")
        for violation in sorted(df_qwen3['violation_type'].unique()):
            violation_df = df_qwen3[df_qwen3['violation_type'] == violation]
            acc = violation_df['detection_success'].mean()
            f.write(f"{violation}: {acc:.2%} ({violation_df['detection_success'].sum()}/{len(violation_df)})\n")
        f.write("\n")

        # Performance by Difficulty Level
        f.write("PERFORMANCE BY DIFFICULTY LEVEL\n")
        f.write("-" * 100 + "\n")
        for level in ['EASY', 'MODERATE', 'HARD']:
            level_df = df_qwen3[df_qwen3['level'] == level]
            if len(level_df) > 0:
                acc = level_df['detection_success'].mean()
                f.write(f"{level}: {acc:.2%} ({level_df['detection_success'].sum()}/{len(level_df)})\n")
        f.write("\n")

        # Performance by Language
        f.write("PERFORMANCE BY PROGRAMMING LANGUAGE\n")
        f.write("-" * 100 + "\n")
        for language in sorted(df_qwen3['language'].unique()):
            lang_df = df_qwen3[df_qwen3['language'] == language]
            acc = lang_df['detection_success'].mean()
            f.write(f"{language}: {acc:.2%} ({lang_df['detection_success'].sum()}/{len(lang_df)})\n")
        f.write("\n")

        # Comparison with other approaches
        if df_comparison is not None and len(df_comparison) > 0:
            f.write("=" * 100 + "\n")
            f.write("COMPARISON WITH OTHER APPROACHES\n")
            f.write("=" * 100 + "\n\n")

            df_all = pd.concat([df_qwen3, df_comparison], ignore_index=True)

            # Overall comparison
            f.write("OVERALL ACCURACY COMPARISON\n")
            f.write("-" * 100 + "\n")
            agent_stats = df_all.groupby('agent_type').agg({
                'detection_success': 'mean',
                'processing_time': 'mean'
            }).sort_values('detection_success', ascending=False)

            for agent, row in agent_stats.iterrows():
                f.write(f"{agent}: {row['detection_success']:.2%} accuracy, "
                       f"{row['processing_time']:.2f}s avg time\n")
            f.write("\n")

            # Violation type comparison
            f.write("ACCURACY BY VIOLATION TYPE - COMPARISON\n")
            f.write("-" * 100 + "\n")
            violation_comparison = df_all.groupby(['agent_type', 'violation_type'])['detection_success'].mean().unstack()
            f.write(violation_comparison.to_string(float_format=lambda x: f'{x:.2%}'))
            f.write("\n\n")

            # Difficulty level comparison
            f.write("ACCURACY BY DIFFICULTY LEVEL - COMPARISON\n")
            f.write("-" * 100 + "\n")
            level_comparison = df_all.groupby(['agent_type', 'level'])['detection_success'].mean().unstack()
            level_order = ['EASY', 'MODERATE', 'HARD']
            if all(level in level_comparison.columns for level in level_order):
                level_comparison = level_comparison[level_order]
            f.write(level_comparison.to_string(float_format=lambda x: f'{x:.2%}'))
            f.write("\n\n")

            # Key insights
            f.write("KEY INSIGHTS\n")
            f.write("-" * 100 + "\n")

            # Best performing approach
            best_agent = agent_stats.index[0]
            best_acc = agent_stats.iloc[0]['detection_success']
            f.write(f"1. Best Overall Performance: {best_agent} ({best_acc:.2%})\n")

            # qwen3-8b ranking
            qwen3_rank = list(agent_stats.index).index('diff_eval') + 1
            qwen3_acc = agent_stats.loc['diff_eval', 'detection_success']
            f.write(f"2. qwen3-8b (diff_eval) Ranking: #{qwen3_rank} with {qwen3_acc:.2%} accuracy\n")

            # Processing time comparison
            fastest_agent = agent_stats['processing_time'].idxmin()
            fastest_time = agent_stats.loc[fastest_agent, 'processing_time']
            f.write(f"3. Fastest Approach: {fastest_agent} ({fastest_time:.2f}s avg)\n")

            # Accuracy difference
            if qwen3_rank > 1:
                acc_diff = best_acc - qwen3_acc
                f.write(f"4. Accuracy Gap: qwen3-8b is {acc_diff:.2%} behind the best approach\n")
            else:
                f.write(f"4. qwen3-8b achieves the best accuracy!\n")

            f.write("\n")

        f.write("=" * 100 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 100 + "\n")

def main():
    # Define paths
    qwen3_file = Path('/Users/he/jcSOLID/result/local/diff_eval/qwen3-8b/detection_results.json')
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b')

    # Load qwen3-8b data
    print("Loading qwen3-8b data...")
    data = load_detection_results(qwen3_file)
    qwen3_results = extract_qwen3_results(data)
    df_qwen3 = pd.DataFrame(qwen3_results)

    print(f"Loaded {len(df_qwen3)} qwen3-8b examples")

    # Load comparison data
    print("\nLoading comparison data...")
    comparison_dfs = load_comparison_data()

    if comparison_dfs:
        df_comparison = pd.concat(comparison_dfs, ignore_index=True)
        print(f"Loaded {len(df_comparison)} comparison examples from {df_comparison['agent_type'].nunique()} approaches")
    else:
        df_comparison = pd.DataFrame()
        print("No comparison data found")

    # Calculate metrics
    print("\nCalculating metrics...")
    metrics = calculate_accuracy_metrics(df_qwen3)

    # Create qwen3-8b visualizations
    print("Creating qwen3-8b visualizations...")
    create_qwen3_visualizations(df_qwen3, output_dir)

    # Create comparison visualizations
    if len(df_comparison) > 0:
        print("Creating comparison visualizations...")
        create_comparison_visualizations(df_qwen3, df_comparison, output_dir)

    # Save detailed results
    print("Saving detailed results...")
    csv_file = output_dir / 'qwen3_8b_detailed_results.csv'
    df_qwen3.to_csv(csv_file, index=False)
    print(f"Saved to {csv_file}")

    # Generate comprehensive report
    print("Generating comprehensive report...")
    report_file = output_dir / 'qwen3_8b_comprehensive_report.txt'
    generate_comprehensive_report(df_qwen3, df_comparison, metrics, report_file)
    print(f"Saved to {report_file}")

    # Print quick summary
    print("\n" + "=" * 100)
    print("QUICK SUMMARY")
    print("=" * 100)
    print(f"qwen3-8b (diff_eval):")
    print(f"  Accuracy: {df_qwen3['detection_success'].mean():.2%}")
    print(f"  Avg Time: {df_qwen3['processing_time'].mean():.2f}s")
    print(f"  Examples: {len(df_qwen3)}")

    if len(df_comparison) > 0:
        print("\nComparison:")
        df_all = pd.concat([df_qwen3, df_comparison], ignore_index=True)
        for agent in sorted(df_all['agent_type'].unique()):
            agent_df = df_all[df_all['agent_type'] == agent]
            print(f"  {agent}: {agent_df['detection_success'].mean():.2%} accuracy, "
                  f"{agent_df['processing_time'].mean():.2f}s avg time")

    print(f"\nAll outputs saved to: {output_dir}")
    print("Analysis complete!")

if __name__ == '__main__':
    main()
