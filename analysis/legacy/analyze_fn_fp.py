#!/usr/bin/env python3
"""
Detailed False Negative (FN) and False Positive (FP) analysis for all three approaches.
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
                'example_id': result['example_id'],
                'violation_type': result['ground_truth'],
                'detected_violation_type': result.get('detected_violation_type', ''),
                'actual_violation_type': result['ground_truth'],
                'detection_success': result['detection_success'],
                'level': result['level'],
                'language': result['language']
            })

    return pd.DataFrame(results)

def load_comparison_data():
    """Load two_agent and langgraph data."""
    two_agent_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_two_agent/two_agent_detailed_results.csv')
    langgraph_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_langgraph/langgraph_detailed_results.csv')

    dfs = []

    if two_agent_csv.exists():
        df = pd.read_csv(two_agent_csv)
        dfs.append(df)

    if langgraph_csv.exists():
        df = pd.read_csv(langgraph_csv)
        dfs.append(df)

    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def analyze_fn_fp(df, agent_name):
    """Analyze False Negatives and False Positives."""
    violation_types = sorted(df['violation_type'].unique())

    fn_analysis = defaultdict(lambda: defaultdict(int))
    fp_analysis = defaultdict(lambda: defaultdict(int))

    for _, row in df.iterrows():
        actual = row['actual_violation_type']
        detected = row['detected_violation_type']

        if actual != detected:
            # False Negative: actual violation not detected (detected as something else or nothing)
            if detected == '' or detected not in violation_types:
                fn_analysis[actual]['Not Detected'] += 1
            else:
                fn_analysis[actual][f'Detected as {detected}'] += 1

            # False Positive: detected violation that wasn't there
            if detected != '' and detected in violation_types:
                fp_analysis[detected][f'Actually {actual}'] += 1

    return fn_analysis, fp_analysis

def create_fn_fp_visualizations(df_all, output_dir):
    """Create FN/FP visualizations."""
    output_dir = Path(output_dir)

    agent_types = sorted(df_all['agent_type'].unique())
    violation_types = sorted(df_all['violation_type'].unique())

    # 1. FN/FP Count by Agent and Violation Type
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))

    # False Negatives
    fn_data = []
    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]
        for violation in violation_types:
            violation_df = agent_df[agent_df['actual_violation_type'] == violation]
            fn_count = len(violation_df[violation_df['detection_success'] == False])
            fn_data.append({
                'agent': agent,
                'violation': violation,
                'count': fn_count
            })

    df_fn = pd.DataFrame(fn_data)
    pivot_fn = df_fn.pivot(index='violation', columns='agent', values='count')

    pivot_fn.plot(kind='bar', ax=axes[0], width=0.8)
    axes[0].set_title('False Negatives (FN) by Violation Type and Agent', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Actual Violation Type', fontsize=11)
    axes[0].set_ylabel('Number of False Negatives', fontsize=11)
    axes[0].legend(title='Agent Type')
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)

    # False Positives
    fp_data = []
    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]
        for violation in violation_types:
            # Count how many times this violation was incorrectly detected
            fp_count = len(agent_df[(agent_df['detected_violation_type'] == violation) &
                                   (agent_df['actual_violation_type'] != violation)])
            fp_data.append({
                'agent': agent,
                'violation': violation,
                'count': fp_count
            })

    df_fp = pd.DataFrame(fp_data)
    pivot_fp = df_fp.pivot(index='violation', columns='agent', values='count')

    pivot_fp.plot(kind='bar', ax=axes[1], width=0.8, color=['coral', 'lightgreen', 'skyblue'])
    axes[1].set_title('False Positives (FP) by Violation Type and Agent', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Detected Violation Type (Incorrect)', fontsize=11)
    axes[1].set_ylabel('Number of False Positives', fontsize=11)
    axes[1].legend(title='Agent Type')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)

    plt.tight_layout()
    plt.savefig(output_dir / '15_fn_fp_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 2. FN/FP Rate by Difficulty Level
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    level_order = ['EASY', 'MODERATE', 'HARD']

    # FN Rate by Level
    fn_rate_data = []
    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]
        for level in level_order:
            level_df = agent_df[agent_df['level'] == level]
            if len(level_df) > 0:
                fn_rate = (1 - level_df['detection_success'].mean()) * 100
                fn_rate_data.append({
                    'agent': agent,
                    'level': level,
                    'rate': fn_rate
                })

    df_fn_rate = pd.DataFrame(fn_rate_data)
    pivot_fn_rate = df_fn_rate.pivot(index='level', columns='agent', values='rate')
    pivot_fn_rate = pivot_fn_rate.reindex(level_order)

    pivot_fn_rate.plot(kind='bar', ax=axes[0], width=0.8)
    axes[0].set_title('False Negative Rate by Difficulty Level', fontsize=14, fontweight='bold')
    axes[0].set_xlabel('Difficulty Level', fontsize=11)
    axes[0].set_ylabel('FN Rate (%)', fontsize=11)
    axes[0].legend(title='Agent Type')
    axes[0].grid(axis='y', alpha=0.3)
    axes[0].set_xticklabels(axes[0].get_xticklabels(), rotation=0)

    # FP Rate by Level (FP as percentage of total predictions at that level)
    fp_rate_data = []
    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]
        for level in level_order:
            level_df = agent_df[agent_df['level'] == level]
            if len(level_df) > 0:
                # FP: detected something but it was wrong
                fp_count = len(level_df[(level_df['detected_violation_type'] != '') &
                                       (level_df['detection_success'] == False)])
                fp_rate = (fp_count / len(level_df)) * 100
                fp_rate_data.append({
                    'agent': agent,
                    'level': level,
                    'rate': fp_rate
                })

    df_fp_rate = pd.DataFrame(fp_rate_data)
    pivot_fp_rate = df_fp_rate.pivot(index='level', columns='agent', values='rate')
    pivot_fp_rate = pivot_fp_rate.reindex(level_order)

    pivot_fp_rate.plot(kind='bar', ax=axes[1], width=0.8, color=['coral', 'lightgreen', 'skyblue'])
    axes[1].set_title('False Positive Rate by Difficulty Level', fontsize=14, fontweight='bold')
    axes[1].set_xlabel('Difficulty Level', fontsize=11)
    axes[1].set_ylabel('FP Rate (%)', fontsize=11)
    axes[1].legend(title='Agent Type')
    axes[1].grid(axis='y', alpha=0.3)
    axes[1].set_xticklabels(axes[1].get_xticklabels(), rotation=0)

    plt.tight_layout()
    plt.savefig(output_dir / '16_fn_fp_by_difficulty.png', dpi=300, bbox_inches='tight')
    plt.close()

    # 3. Misclassification Matrix (where do FNs go?)
    for agent in agent_types:
        agent_df = df_all[df_all['agent_type'] == agent]

        # Create misclassification matrix
        misclass_matrix = pd.DataFrame(0, index=violation_types, columns=violation_types + ['Not Detected'])

        for _, row in agent_df.iterrows():
            actual = row['actual_violation_type']
            detected = row['detected_violation_type']

            if actual != detected and actual in violation_types:
                if detected in violation_types:
                    misclass_matrix.loc[actual, detected] += 1
                else:
                    misclass_matrix.loc[actual, 'Not Detected'] += 1

        plt.figure(figsize=(10, 8))
        sns.heatmap(misclass_matrix, annot=True, fmt='d', cmap='Reds',
                   cbar_kws={'label': 'Misclassification Count'})
        plt.title(f'Misclassification Matrix: {agent}\n(Where do False Negatives go?)',
                 fontsize=14, fontweight='bold')
        plt.xlabel('Incorrectly Detected As', fontsize=11)
        plt.ylabel('Actual Violation Type', fontsize=11)
        plt.tight_layout()
        plt.savefig(output_dir / f'17_misclassification_matrix_{agent}.png', dpi=300, bbox_inches='tight')
        plt.close()

def generate_fn_fp_report(df_all, output_file):
    """Generate detailed FN/FP report."""
    agent_types = sorted(df_all['agent_type'].unique())
    violation_types = sorted(df_all['violation_type'].unique())

    with open(output_file, 'w') as f:
        f.write("=" * 100 + "\n")
        f.write("FALSE NEGATIVE (FN) AND FALSE POSITIVE (FP) ANALYSIS\n")
        f.write("=" * 100 + "\n\n")

        for agent in agent_types:
            agent_df = df_all[df_all['agent_type'] == agent]

            f.write(f"\n{'=' * 100}\n")
            f.write(f"{agent.upper()} - DETAILED FN/FP ANALYSIS\n")
            f.write(f"{'=' * 100}\n\n")

            # Overall statistics
            total = len(agent_df)
            correct = agent_df['detection_success'].sum()
            incorrect = total - correct

            f.write(f"Overall Statistics:\n")
            f.write(f"  Total Examples: {total}\n")
            f.write(f"  Correct: {correct} ({correct/total:.2%})\n")
            f.write(f"  Incorrect: {incorrect} ({incorrect/total:.2%})\n\n")

            # FN Analysis by Violation Type
            f.write(f"FALSE NEGATIVES (FN) BY VIOLATION TYPE:\n")
            f.write(f"{'-' * 100}\n")

            for violation in violation_types:
                violation_df = agent_df[agent_df['actual_violation_type'] == violation]
                fn_df = violation_df[violation_df['detection_success'] == False]

                f.write(f"\n{violation}:\n")
                f.write(f"  Total Examples: {len(violation_df)}\n")
                f.write(f"  False Negatives: {len(fn_df)} ({len(fn_df)/len(violation_df):.2%})\n")

                if len(fn_df) > 0:
                    f.write(f"  Misclassified as:\n")

                    # Count what they were detected as
                    detected_as = fn_df['detected_violation_type'].value_counts()
                    for detected, count in detected_as.items():
                        if detected == '' or detected not in violation_types:
                            f.write(f"    Not Detected: {count}\n")
                        else:
                            f.write(f"    {detected}: {count}\n")

                    # Show examples by difficulty
                    f.write(f"  FN by Difficulty:\n")
                    for level in ['EASY', 'MODERATE', 'HARD']:
                        level_fn = fn_df[fn_df['level'] == level]
                        if len(level_fn) > 0:
                            f.write(f"    {level}: {len(level_fn)}\n")

            # FP Analysis by Violation Type
            f.write(f"\n\nFALSE POSITIVES (FP) BY VIOLATION TYPE:\n")
            f.write(f"{'-' * 100}\n")

            for violation in violation_types:
                # Count how many times this violation was incorrectly detected
                fp_df = agent_df[(agent_df['detected_violation_type'] == violation) &
                               (agent_df['actual_violation_type'] != violation)]

                if len(fp_df) > 0:
                    f.write(f"\n{violation} (incorrectly detected):\n")
                    f.write(f"  Total False Positives: {len(fp_df)}\n")
                    f.write(f"  Actually was:\n")

                    # Count what they actually were
                    actually_was = fp_df['actual_violation_type'].value_counts()
                    for actual, count in actually_was.items():
                        f.write(f"    {actual}: {count}\n")

            # Most Common Misclassifications
            f.write(f"\n\nMOST COMMON MISCLASSIFICATIONS:\n")
            f.write(f"{'-' * 100}\n")

            misclass_df = agent_df[agent_df['detection_success'] == False]
            misclass_pairs = misclass_df.groupby(['actual_violation_type', 'detected_violation_type']).size()
            misclass_pairs = misclass_pairs.sort_values(ascending=False).head(10)

            for (actual, detected), count in misclass_pairs.items():
                if detected == '' or detected not in violation_types:
                    f.write(f"  {actual} → Not Detected: {count} times\n")
                else:
                    f.write(f"  {actual} → {detected}: {count} times\n")

            # FN/FP by Difficulty Level
            f.write(f"\n\nFN/FP BY DIFFICULTY LEVEL:\n")
            f.write(f"{'-' * 100}\n")

            for level in ['EASY', 'MODERATE', 'HARD']:
                level_df = agent_df[agent_df['level'] == level]
                if len(level_df) > 0:
                    fn_count = len(level_df[level_df['detection_success'] == False])
                    fn_rate = fn_count / len(level_df)

                    f.write(f"\n{level}:\n")
                    f.write(f"  Total Examples: {len(level_df)}\n")
                    f.write(f"  False Negatives: {fn_count} ({fn_rate:.2%})\n")

        # Comparative Summary
        f.write(f"\n\n{'=' * 100}\n")
        f.write(f"COMPARATIVE SUMMARY\n")
        f.write(f"{'=' * 100}\n\n")

        # FN Rate Comparison
        f.write(f"FALSE NEGATIVE RATE BY AGENT:\n")
        f.write(f"{'-' * 100}\n")
        for agent in agent_types:
            agent_df = df_all[df_all['agent_type'] == agent]
            fn_rate = (1 - agent_df['detection_success'].mean())
            f.write(f"  {agent}: {fn_rate:.2%}\n")

        # FN by Violation Type Comparison
        f.write(f"\n\nFALSE NEGATIVES BY VIOLATION TYPE (COMPARISON):\n")
        f.write(f"{'-' * 100}\n")
        f.write(f"{'Violation':<12}")
        for agent in agent_types:
            f.write(f"{agent:<20}")
        f.write("\n")

        for violation in violation_types:
            f.write(f"{violation:<12}")
            for agent in agent_types:
                agent_df = df_all[df_all['agent_type'] == agent]
                violation_df = agent_df[agent_df['actual_violation_type'] == violation]
                fn_count = len(violation_df[violation_df['detection_success'] == False])
                total = len(violation_df)
                f.write(f"{fn_count}/{total} ({fn_count/total:.1%})".ljust(20))
            f.write("\n")

        f.write(f"\n{'=' * 100}\n")
        f.write(f"END OF FN/FP ANALYSIS\n")
        f.write(f"{'=' * 100}\n")

def main():
    # Load data
    print("Loading data...")
    df_qwen3 = load_qwen3_data()
    df_comparison = load_comparison_data()

    # Combine all data
    df_all = pd.concat([df_qwen3, df_comparison], ignore_index=True)

    print(f"Total examples: {len(df_all)}")
    print(f"Agent types: {df_all['agent_type'].unique()}")

    # Create output directory
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b')

    # Create visualizations
    print("\nCreating FN/FP visualizations...")
    create_fn_fp_visualizations(df_all, output_dir)

    # Generate report
    print("Generating FN/FP report...")
    report_file = output_dir / 'fn_fp_analysis_report.txt'
    generate_fn_fp_report(df_all, report_file)

    print(f"\nAll outputs saved to: {output_dir}")
    print("FN/FP analysis complete!")

if __name__ == '__main__':
    main()
