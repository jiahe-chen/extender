#!/usr/bin/env python3
"""
Create side-by-side confusion matrix comparison for diff_eval, two_agent, and langgraph.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_qwen3_data():
    """Load qwen3-8b diff_eval data."""
    file_path = Path('/Users/he/jcSOLID/result/local/diff_eval/qwen3-8b/detection_results.json')

    with open(file_path, 'r') as f:
        data = json.load(f)

    results = []
    for violation_type, violation_data in data['by_violation_type'].items():
        for result in violation_data['results']:
            results.append({
                'agent_type': 'diff_eval',
                'model': 'qwen3-8b',
                'violation_type': result['ground_truth'],
                'detected_violation_type': result.get('detected_violation_type', ''),
                'actual_violation_type': result['ground_truth'],
                'detection_success': result['detection_success']
            })

    return pd.DataFrame(results)

def load_comparison_data():
    """Load two_agent and langgraph data."""
    two_agent_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_two_agent/two_agent_detailed_results.csv')
    langgraph_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_langgraph/langgraph_detailed_results.csv')

    dfs = []

    if two_agent_csv.exists():
        df = pd.read_csv(two_agent_csv)
        dfs.append(df[['agent_type', 'model', 'violation_type', 'detected_violation_type',
                       'actual_violation_type', 'detection_success']])

    if langgraph_csv.exists():
        df = pd.read_csv(langgraph_csv)
        dfs.append(df[['agent_type', 'model', 'violation_type', 'detected_violation_type',
                       'actual_violation_type', 'detection_success']])

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def create_confusion_matrix(df, violation_types):
    """Create confusion matrix for a given dataframe."""
    confusion = pd.DataFrame(0, index=violation_types, columns=violation_types + ['None/Other'])

    for _, row in df.iterrows():
        actual = row['actual_violation_type']
        detected = row['detected_violation_type']

        if actual in violation_types:
            if detected in violation_types:
                confusion.loc[actual, detected] += 1
            else:
                confusion.loc[actual, 'None/Other'] += 1

    return confusion

def create_comparison_plot():
    """Create side-by-side confusion matrix comparison."""
    # Load data
    print("Loading data...")
    df_qwen3 = load_qwen3_data()
    df_comparison = load_comparison_data()

    # Combine all data
    df_all = pd.concat([df_qwen3, df_comparison], ignore_index=True)

    # Get violation types
    violation_types = sorted(df_all['violation_type'].unique())

    # Get agent types
    agent_types = sorted(df_all['agent_type'].unique())

    print(f"Agent types: {agent_types}")
    print(f"Violation types: {violation_types}")

    # Create figure with subplots
    fig, axes = plt.subplots(1, len(agent_types), figsize=(20, 6))

    if len(agent_types) == 1:
        axes = [axes]

    # Create confusion matrix for each agent type
    for idx, agent in enumerate(agent_types):
        agent_df = df_all[df_all['agent_type'] == agent]
        confusion = create_confusion_matrix(agent_df, violation_types)

        # Plot heatmap
        sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues',
                   ax=axes[idx], cbar_kws={'label': 'Count'},
                   vmin=0, vmax=confusion.values.max())

        # Calculate accuracy
        accuracy = agent_df['detection_success'].mean()

        axes[idx].set_title(f'{agent}\nAccuracy: {accuracy:.2%}', fontsize=14, fontweight='bold')
        axes[idx].set_xlabel('Detected Violation Type', fontsize=11)
        axes[idx].set_ylabel('Actual Violation Type', fontsize=11)

        # Rotate labels
        axes[idx].set_xticklabels(axes[idx].get_xticklabels(), rotation=45, ha='right')
        axes[idx].set_yticklabels(axes[idx].get_yticklabels(), rotation=0)

    plt.suptitle('Confusion Matrix Comparison: diff_eval vs two_agent vs langgraph',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    # Save
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b')
    output_file = output_dir / '13_confusion_matrix_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\nSaved to: {output_file}")
    plt.close()

    # Create a second version with normalized confusion matrices (percentages)
    fig, axes = plt.subplots(1, len(agent_types), figsize=(20, 6))

    if len(agent_types) == 1:
        axes = [axes]

    for idx, agent in enumerate(agent_types):
        agent_df = df_all[df_all['agent_type'] == agent]
        confusion = create_confusion_matrix(agent_df, violation_types)

        # Normalize by row (actual violation type)
        confusion_normalized = confusion.div(confusion.sum(axis=1), axis=0) * 100

        # Plot heatmap
        sns.heatmap(confusion_normalized, annot=True, fmt='.1f', cmap='RdYlGn',
                   ax=axes[idx], cbar_kws={'label': 'Percentage (%)'},
                   vmin=0, vmax=100)

        # Calculate accuracy
        accuracy = agent_df['detection_success'].mean()

        axes[idx].set_title(f'{agent}\nAccuracy: {accuracy:.2%}', fontsize=14, fontweight='bold')
        axes[idx].set_xlabel('Detected Violation Type', fontsize=11)
        axes[idx].set_ylabel('Actual Violation Type', fontsize=11)

        # Rotate labels
        axes[idx].set_xticklabels(axes[idx].get_xticklabels(), rotation=45, ha='right')
        axes[idx].set_yticklabels(axes[idx].get_yticklabels(), rotation=0)

    plt.suptitle('Confusion Matrix Comparison (Normalized %): diff_eval vs two_agent vs langgraph',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    # Save
    output_file = output_dir / '14_confusion_matrix_comparison_normalized.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved to: {output_file}")
    plt.close()

    # Print summary statistics
    print("\n" + "=" * 80)
    print("CONFUSION MATRIX COMPARISON SUMMARY")
    print("=" * 80)

    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]
        confusion = create_confusion_matrix(agent_df, violation_types)

        print(f"\n{agent.upper()}:")
        print(f"  Total examples: {len(agent_df)}")
        print(f"  Overall accuracy: {agent_df['detection_success'].mean():.2%}")

        # Calculate per-violation accuracy
        print(f"  Per-violation accuracy:")
        for violation in violation_types:
            violation_df = agent_df[agent_df['actual_violation_type'] == violation]
            if len(violation_df) > 0:
                acc = violation_df['detection_success'].mean()
                correct = confusion.loc[violation, violation]
                total = confusion.loc[violation].sum()
                print(f"    {violation}: {acc:.2%} ({correct}/{total})")

        # Calculate misclassification rate
        total_predictions = confusion.sum().sum()
        correct_predictions = sum(confusion.loc[v, v] for v in violation_types)
        misclassified = total_predictions - correct_predictions
        print(f"  Misclassification rate: {misclassified/total_predictions:.2%} ({misclassified}/{total_predictions})")

if __name__ == '__main__':
    create_comparison_plot()
    print("\nComparison complete!")
