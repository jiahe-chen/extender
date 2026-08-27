#!/usr/bin/env python3
"""
Create a comprehensive summary dashboard with all key metrics.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_all_data():
    """Load all comparison data."""
    qwen3_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b/qwen3_8b_detailed_results.csv')
    two_agent_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_two_agent/two_agent_detailed_results.csv')
    langgraph_csv = Path('/Users/he/jcSOLID/analysis/analysis_output_langgraph/langgraph_detailed_results.csv')

    dfs = []
    if qwen3_csv.exists():
        dfs.append(pd.read_csv(qwen3_csv))
    if two_agent_csv.exists():
        dfs.append(pd.read_csv(two_agent_csv))
    if langgraph_csv.exists():
        dfs.append(pd.read_csv(langgraph_csv))

    return pd.concat(dfs, ignore_index=True)

def create_summary_dashboard():
    """Create a comprehensive summary dashboard."""
    df = load_all_data()

    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    agent_types = sorted(df['agent_type'].unique())
    violation_types = sorted(df['violation_type'].unique())
    level_order = ['EASY', 'MODERATE', 'HARD']

    colors = {'diff_eval': 'steelblue', 'langgraph': 'lightgreen', 'two_agent': 'coral'}

    # 1. Overall Accuracy Comparison (Top Left)
    ax1 = fig.add_subplot(gs[0, 0])
    agent_accuracy = df.groupby('agent_type')['detection_success'].mean().sort_values(ascending=False)
    bars = ax1.bar(range(len(agent_accuracy)), agent_accuracy.values,
                   color=[colors[agent] for agent in agent_accuracy.index])
    ax1.set_xticks(range(len(agent_accuracy)))
    ax1.set_xticklabels(agent_accuracy.index, rotation=0)
    ax1.set_ylabel('Accuracy', fontsize=10)
    ax1.set_title('Overall Accuracy', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, 1)
    ax1.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, agent_accuracy.values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.1%}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 2. Processing Time Comparison (Top Middle)
    ax2 = fig.add_subplot(gs[0, 1])
    agent_time = df.groupby('agent_type')['processing_time'].mean().sort_values()
    bars = ax2.bar(range(len(agent_time)), agent_time.values,
                   color=[colors[agent] for agent in agent_time.index])
    ax2.set_xticks(range(len(agent_time)))
    ax2.set_xticklabels(agent_time.index, rotation=0)
    ax2.set_ylabel('Time (seconds)', fontsize=10)
    ax2.set_title('Average Processing Time', fontsize=12, fontweight='bold')
    ax2.set_yscale('log')
    ax2.grid(axis='y', alpha=0.3)

    for bar, val in zip(bars, agent_time.values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() * 1.2,
                f'{val:.1f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 3. Accuracy by Violation Type (Top Right)
    ax3 = fig.add_subplot(gs[0, 2])
    violation_data = df.groupby(['agent_type', 'violation_type'])['detection_success'].mean().unstack()
    x = np.arange(len(violation_types))
    width = 0.25

    for i, agent in enumerate(agent_types):
        if agent in violation_data.index:
            offset = (i - 1) * width
            ax3.bar(x + offset, violation_data.loc[agent], width,
                   label=agent, color=colors[agent], alpha=0.8)

    ax3.set_xlabel('Violation Type', fontsize=10)
    ax3.set_ylabel('Accuracy', fontsize=10)
    ax3.set_title('Accuracy by Violation Type', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(violation_types)
    ax3.legend(fontsize=8)
    ax3.set_ylim(0, 1)
    ax3.grid(axis='y', alpha=0.3)

    # 4. Accuracy by Difficulty Level (Middle Left)
    ax4 = fig.add_subplot(gs[1, 0])
    level_data = df.groupby(['agent_type', 'level'])['detection_success'].mean().unstack()
    level_data = level_data[level_order]
    x = np.arange(len(level_order))

    for i, agent in enumerate(agent_types):
        if agent in level_data.index:
            offset = (i - 1) * width
            ax4.bar(x + offset, level_data.loc[agent], width,
                   label=agent, color=colors[agent], alpha=0.8)

    ax4.set_xlabel('Difficulty Level', fontsize=10)
    ax4.set_ylabel('Accuracy', fontsize=10)
    ax4.set_title('Accuracy by Difficulty', fontsize=12, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(level_order)
    ax4.legend(fontsize=8)
    ax4.set_ylim(0, 1)
    ax4.grid(axis='y', alpha=0.3)

    # 5. False Negative Rate by Violation (Middle Middle)
    ax5 = fig.add_subplot(gs[1, 1])
    fn_data = []
    for agent in agent_types:
        agent_df = df[df['agent_type'] == agent]
        for violation in violation_types:
            violation_df = agent_df[agent_df['actual_violation_type'] == violation]
            if len(violation_df) > 0:
                fn_rate = (1 - violation_df['detection_success'].mean()) * 100
                fn_data.append({'agent': agent, 'violation': violation, 'fn_rate': fn_rate})

    df_fn = pd.DataFrame(fn_data)
    pivot_fn = df_fn.pivot(index='violation', columns='agent', values='fn_rate')
    x = np.arange(len(violation_types))

    for i, agent in enumerate(agent_types):
        if agent in pivot_fn.columns:
            offset = (i - 1) * width
            ax5.bar(x + offset, pivot_fn[agent], width,
                   label=agent, color=colors[agent], alpha=0.8)

    ax5.set_xlabel('Violation Type', fontsize=10)
    ax5.set_ylabel('FN Rate (%)', fontsize=10)
    ax5.set_title('False Negative Rate', fontsize=12, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(violation_types)
    ax5.legend(fontsize=8)
    ax5.grid(axis='y', alpha=0.3)

    # 6. Performance Degradation by Difficulty (Middle Right)
    ax6 = fig.add_subplot(gs[1, 2])
    for agent in agent_types:
        agent_df = df[df['agent_type'] == agent]
        level_acc = []
        for level in level_order:
            level_df = agent_df[agent_df['level'] == level]
            if len(level_df) > 0:
                level_acc.append(level_df['detection_success'].mean() * 100)
            else:
                level_acc.append(0)

        ax6.plot(level_order, level_acc, marker='o', linewidth=2,
                label=agent, color=colors[agent], markersize=8)

    ax6.set_xlabel('Difficulty Level', fontsize=10)
    ax6.set_ylabel('Accuracy (%)', fontsize=10)
    ax6.set_title('Performance Degradation', fontsize=12, fontweight='bold')
    ax6.legend(fontsize=8)
    ax6.grid(alpha=0.3)
    ax6.set_ylim(0, 100)

    # 7. Strengths Radar Chart (Bottom Left)
    ax7 = fig.add_subplot(gs[2, 0], projection='polar')

    # Calculate best performance for each violation type
    best_performance = {}
    for violation in violation_types:
        best_acc = 0
        best_agent = None
        for agent in agent_types:
            agent_df = df[df['agent_type'] == agent]
            violation_df = agent_df[agent_df['violation_type'] == violation]
            if len(violation_df) > 0:
                acc = violation_df['detection_success'].mean()
                if acc > best_acc:
                    best_acc = acc
                    best_agent = agent
        best_performance[violation] = (best_agent, best_acc)

    # Create radar chart for diff_eval
    agent = 'diff_eval'
    agent_df = df[df['agent_type'] == agent]
    values = []
    for violation in violation_types:
        violation_df = agent_df[agent_df['violation_type'] == violation]
        if len(violation_df) > 0:
            values.append(violation_df['detection_success'].mean())
        else:
            values.append(0)

    angles = np.linspace(0, 2 * np.pi, len(violation_types), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]

    ax7.plot(angles, values, 'o-', linewidth=2, color=colors['diff_eval'], label='diff_eval')
    ax7.fill(angles, values, alpha=0.25, color=colors['diff_eval'])
    ax7.set_xticks(angles[:-1])
    ax7.set_xticklabels(violation_types, fontsize=9)
    ax7.set_ylim(0, 1)
    ax7.set_title('diff_eval Strengths', fontsize=12, fontweight='bold', pad=20)
    ax7.grid(True)

    # 8. Key Metrics Table (Bottom Middle)
    ax8 = fig.add_subplot(gs[2, 1])
    ax8.axis('off')

    # Create metrics table
    metrics_data = []
    for agent in agent_types:
        agent_df = df[df['agent_type'] == agent]
        metrics_data.append([
            agent,
            f"{agent_df['detection_success'].mean():.1%}",
            f"{agent_df['processing_time'].mean():.1f}s",
            f"{len(agent_df[agent_df['detection_success'] == False])}",
            f"{(1 - agent_df['detection_success'].mean()):.1%}"
        ])

    table = ax8.table(cellText=metrics_data,
                     colLabels=['Agent', 'Accuracy', 'Avg Time', 'FN Count', 'FN Rate'],
                     cellLoc='center',
                     loc='center',
                     bbox=[0, 0.2, 1, 0.6])

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)

    # Color code the cells
    for i in range(1, len(agent_types) + 1):
        table[(i, 0)].set_facecolor(colors[metrics_data[i-1][0]])
        table[(i, 0)].set_alpha(0.3)

    ax8.set_title('Key Metrics Summary', fontsize=12, fontweight='bold', pad=20)

    # 9. Recommendations (Bottom Right)
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')

    recommendations = [
        "RECOMMENDATIONS:",
        "",
        "✓ Use langgraph as default",
        "  (Best accuracy & speed)",
        "",
        "✓ Use diff_eval for ISP",
        "  (77.08% accuracy)",
        "",
        "✗ Fix diff_eval LSP detection",
        "  (Only 6.25% accuracy)",
        "",
        "✗ Optimize diff_eval speed",
        "  (88x slower than langgraph)",
        "",
        "⚠ Consider ensemble approach",
        "  (Combine strengths)"
    ]

    y_pos = 0.9
    for line in recommendations:
        if line.startswith("✓"):
            color = 'green'
            weight = 'bold'
        elif line.startswith("✗"):
            color = 'red'
            weight = 'bold'
        elif line.startswith("⚠"):
            color = 'orange'
            weight = 'bold'
        elif line.startswith("RECOMMENDATIONS"):
            color = 'black'
            weight = 'bold'
        else:
            color = 'black'
            weight = 'normal'

        ax9.text(0.1, y_pos, line, fontsize=10, color=color,
                weight=weight, verticalalignment='top', family='monospace')
        y_pos -= 0.06

    ax9.set_xlim(0, 1)
    ax9.set_ylim(0, 1)

    # Main title
    fig.suptitle('SOLID Violation Detection - Comprehensive Comparison Dashboard',
                fontsize=16, fontweight='bold', y=0.98)

    # Save
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b')
    output_file = output_dir / '00_SUMMARY_DASHBOARD.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved summary dashboard to: {output_file}")
    plt.close()

    # Create a second simplified comparison chart
    create_simplified_comparison(df, output_dir)

def create_simplified_comparison(df, output_dir):
    """Create a simplified comparison chart for quick reference."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    agent_types = sorted(df['agent_type'].unique())
    violation_types = sorted(df['violation_type'].unique())
    colors = {'diff_eval': 'steelblue', 'langgraph': 'lightgreen', 'two_agent': 'coral'}

    # 1. Overall Performance
    ax = axes[0, 0]
    agent_stats = df.groupby('agent_type').agg({
        'detection_success': 'mean',
        'processing_time': 'mean'
    }).sort_values('detection_success', ascending=False)

    x = np.arange(len(agent_stats))
    width = 0.35

    ax2 = ax.twinx()
    bars1 = ax.bar(x - width/2, agent_stats['detection_success'] * 100, width,
                   label='Accuracy (%)', color='skyblue', alpha=0.8)
    bars2 = ax2.bar(x + width/2, agent_stats['processing_time'], width,
                    label='Time (s)', color='salmon', alpha=0.8)

    ax.set_xlabel('Agent Type', fontsize=11, fontweight='bold')
    ax.set_ylabel('Accuracy (%)', fontsize=11, fontweight='bold', color='skyblue')
    ax2.set_ylabel('Processing Time (s)', fontsize=11, fontweight='bold', color='salmon')
    ax.set_title('Overall Performance Comparison', fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(agent_stats.index, fontsize=10)
    ax.tick_params(axis='y', labelcolor='skyblue')
    ax2.tick_params(axis='y', labelcolor='salmon')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar in bars1:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{height:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')

    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s', ha='center', va='bottom', fontsize=9, fontweight='bold')

    # 2. Best at Each Violation Type
    ax = axes[0, 1]
    best_agents = []
    best_scores = []

    for violation in violation_types:
        best_acc = 0
        best_agent = None
        for agent in agent_types:
            agent_df = df[df['agent_type'] == agent]
            violation_df = agent_df[agent_df['violation_type'] == violation]
            if len(violation_df) > 0:
                acc = violation_df['detection_success'].mean()
                if acc > best_acc:
                    best_acc = acc
                    best_agent = agent
        best_agents.append(best_agent)
        best_scores.append(best_acc * 100)

    bars = ax.barh(violation_types, best_scores,
                   color=[colors[agent] for agent in best_agents])
    ax.set_xlabel('Best Accuracy (%)', fontsize=11, fontweight='bold')
    ax.set_title('Best Performer by Violation Type', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 100)
    ax.grid(axis='x', alpha=0.3)

    # Add labels
    for i, (bar, agent, score) in enumerate(zip(bars, best_agents, best_scores)):
        ax.text(score + 2, i, f'{agent} ({score:.1f}%)',
               va='center', fontsize=9, fontweight='bold')

    # 3. Strengths and Weaknesses
    ax = axes[1, 0]
    ax.axis('off')

    strengths_weaknesses = {
        'diff_eval': {
            'strengths': ['✓ ISP: 77.08%', '✓ EASY: 73.75%', '✓ DIP: 47.92%'],
            'weaknesses': ['✗ LSP: 6.25%', '✗ Speed: 135.95s', '✗ HARD: 18.75%']
        },
        'langgraph': {
            'strengths': ['✓ OCP: 93.75%', '✓ Speed: 1.54s', '✓ Overall: 55.08%'],
            'weaknesses': ['✗ DIP: 30.00%', '✗ ISP: 47.92%']
        },
        'two_agent': {
            'strengths': ['✓ SRP: 89.17%', '✓ OCP: 59.58%'],
            'weaknesses': ['✗ DIP: 41.67%', '✗ ISP: 38.75%', '✗ LSP: 18.75%']
        }
    }

    y_pos = 0.95
    for agent, data in strengths_weaknesses.items():
        ax.text(0.05, y_pos, f'{agent.upper()}:', fontsize=11, fontweight='bold',
               color=colors[agent])
        y_pos -= 0.05

        ax.text(0.1, y_pos, 'Strengths:', fontsize=10, fontweight='bold', color='green')
        y_pos -= 0.04
        for strength in data['strengths']:
            ax.text(0.15, y_pos, strength, fontsize=9, color='green', family='monospace')
            y_pos -= 0.04

        ax.text(0.1, y_pos, 'Weaknesses:', fontsize=10, fontweight='bold', color='red')
        y_pos -= 0.04
        for weakness in data['weaknesses']:
            ax.text(0.15, y_pos, weakness, fontsize=9, color='red', family='monospace')
            y_pos -= 0.04

        y_pos -= 0.03

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title('Strengths & Weaknesses', fontsize=13, fontweight='bold')

    # 4. Final Recommendation
    ax = axes[1, 1]
    ax.axis('off')

    recommendation_text = """
FINAL RECOMMENDATION

🥇 PRIMARY CHOICE: langgraph
   • Best overall accuracy (55.08%)
   • Fastest processing (1.54s)
   • Good balance across all metrics
   • Recommended for production use

🥈 SPECIALIZED USE: diff_eval
   • Excellent for ISP detection (77.08%)
   • Good for EASY cases (73.75%)
   • NOT recommended for:
     - LSP detection (only 6.25%)
     - HARD cases (only 18.75%)
     - Time-sensitive applications

🥉 ALTERNATIVE: two_agent
   • Best for SRP detection (89.17%)
   • Moderate speed (8.75s)
   • Good for specific use cases

💡 BEST STRATEGY: Ensemble
   • Use diff_eval for ISP
   • Use langgraph for OCP
   • Use two_agent for SRP
   • Expected accuracy: 70%+
"""

    ax.text(0.05, 0.95, recommendation_text, fontsize=10,
           verticalalignment='top', family='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    plt.suptitle('Quick Reference Guide - SOLID Violation Detection',
                fontsize=16, fontweight='bold')
    plt.tight_layout()

    output_file = output_dir / '00_QUICK_REFERENCE.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved quick reference to: {output_file}")
    plt.close()

if __name__ == '__main__':
    print("Creating summary dashboard...")
    create_summary_dashboard()
    print("\nDashboard creation complete!")
