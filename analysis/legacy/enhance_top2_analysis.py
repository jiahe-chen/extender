"""
Enhanced analysis for top_2 strategies with additional metrics:
- Ranking distribution (where correct answers appear)
- Top-2 benefit analysis
- Detailed comparison insights
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

def load_results():
    """Load the detailed results CSV"""
    csv_path = Path(r"c:\Users\Jay\jcSOLID\analysis\analysis_output_top2_strategies\detailed_results.csv")
    return pd.read_csv(csv_path)

def analyze_ranking_distribution(df, output_dir):
    """Analyze where correct answers appear in the rankings"""
    print("="*80)
    print("RANKING DISTRIBUTION ANALYSIS")
    print("="*80)

    strategies = df['strategy'].unique()

    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Overall ranking distribution
    ax1 = axes[0, 0]
    ranking_data = []
    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        pos_counts = strategy_df['correct_position'].value_counts().sort_index()

        # Calculate percentages
        total = len(strategy_df)
        pos_0 = pos_counts.get(0, 0) / total * 100  # Not in top 2
        pos_1 = pos_counts.get(1, 0) / total * 100  # Position 1
        pos_2 = pos_counts.get(2, 0) / total * 100  # Position 2

        ranking_data.append({
            'strategy': strategy,
            'Position 1': pos_1,
            'Position 2': pos_2,
            'Not in Top-2': pos_0
        })

        print(f"\n{strategy.upper()}:")
        print(f"  Position 1 (Top-1 correct): {pos_1:.2f}%")
        print(f"  Position 2 (Top-2 correct, not Top-1): {pos_2:.2f}%")
        print(f"  Not in Top-2: {pos_0:.2f}%")
        print(f"  Top-2 Benefit (Position 2 contribution): {pos_2:.2f}%")

    # Plot stacked bar chart
    ranking_df = pd.DataFrame(ranking_data)
    x = np.arange(len(strategies))
    width = 0.6

    p1 = ax1.bar(x, ranking_df['Position 1'], width, label='Position 1 (Correct)', color='#2ecc71')
    p2 = ax1.bar(x, ranking_df['Position 2'], width, bottom=ranking_df['Position 1'],
                 label='Position 2 (Correct)', color='#3498db')
    p3 = ax1.bar(x, ranking_df['Not in Top-2'], width,
                 bottom=ranking_df['Position 1'] + ranking_df['Position 2'],
                 label='Not in Top-2', color='#e74c3c')

    ax1.set_ylabel('Percentage (%)')
    ax1.set_title('Ranking Distribution: Where Correct Answers Appear')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Add percentage labels
    for i, strategy in enumerate(strategies):
        y_offset = 0
        for val, label in [(ranking_df.iloc[i]['Position 1'], 'Pos 1'),
                           (ranking_df.iloc[i]['Position 2'], 'Pos 2'),
                           (ranking_df.iloc[i]['Not in Top-2'], 'Miss')]:
            if val > 5:  # Only show label if segment is large enough
                ax1.text(i, y_offset + val/2, f'{val:.1f}%',
                        ha='center', va='center', fontweight='bold', fontsize=9)
            y_offset += val

    # 2. Ranking distribution by difficulty
    ax2 = axes[0, 1]
    difficulty_levels = ['EASY', 'MODERATE', 'HARD']

    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        pos2_benefits = []

        for level in difficulty_levels:
            level_df = strategy_df[strategy_df['level'] == level]
            if len(level_df) > 0:
                pos2_pct = (level_df['correct_position'] == 2).sum() / len(level_df) * 100
                pos2_benefits.append(pos2_pct)
            else:
                pos2_benefits.append(0)

        ax2.plot(difficulty_levels, pos2_benefits, marker='o', linewidth=2,
                label=strategy.replace('_', ' ').title())

    ax2.set_xlabel('Difficulty Level')
    ax2.set_ylabel('Position 2 Benefit (%)')
    ax2.set_title('Top-2 Benefit by Difficulty Level\n(% of cases where correct answer is at Position 2)')
    ax2.legend()
    ax2.grid(alpha=0.3)

    # 3. Ranking distribution by violation type
    ax3 = axes[1, 0]
    violation_types = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']

    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        pos2_benefits = []

        for vtype in violation_types:
            vtype_df = strategy_df[strategy_df['violation_type'] == vtype]
            if len(vtype_df) > 0:
                pos2_pct = (vtype_df['correct_position'] == 2).sum() / len(vtype_df) * 100
                pos2_benefits.append(pos2_pct)
            else:
                pos2_benefits.append(0)

        ax3.plot(violation_types, pos2_benefits, marker='o', linewidth=2,
                label=strategy.replace('_', ' ').title())

    ax3.set_xlabel('Violation Type')
    ax3.set_ylabel('Position 2 Benefit (%)')
    ax3.set_title('Top-2 Benefit by Violation Type\n(% of cases where correct answer is at Position 2)')
    ax3.legend()
    ax3.grid(alpha=0.3)

    # 4. MRR comparison with breakdown
    ax4 = axes[1, 1]

    mrr_data = []
    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        mrr_total = strategy_df['reciprocal_rank'].mean()
        mrr_from_pos1 = (strategy_df['correct_position'] == 1).sum() / len(strategy_df)
        mrr_from_pos2 = (strategy_df['correct_position'] == 2).sum() / len(strategy_df) * 0.5

        mrr_data.append({
            'strategy': strategy,
            'From Position 1': mrr_from_pos1,
            'From Position 2': mrr_from_pos2
        })

    mrr_df = pd.DataFrame(mrr_data)
    x = np.arange(len(strategies))
    width = 0.6

    p1 = ax4.bar(x, mrr_df['From Position 1'], width, label='Contribution from Position 1', color='#2ecc71')
    p2 = ax4.bar(x, mrr_df['From Position 2'], width, bottom=mrr_df['From Position 1'],
                 label='Contribution from Position 2', color='#3498db')

    ax4.set_ylabel('MRR Contribution')
    ax4.set_title('MRR Breakdown by Position')
    ax4.set_xticks(x)
    ax4.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)

    # Add total MRR labels
    for i, strategy in enumerate(strategies):
        total_mrr = mrr_df.iloc[i]['From Position 1'] + mrr_df.iloc[i]['From Position 2']
        ax4.text(i, total_mrr + 0.02, f'MRR: {total_mrr:.3f}',
                ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    fig.savefig(output_dir / '07_ranking_distribution_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\n[OK] Saved ranking distribution analysis")
    plt.close(fig)

    print("\n" + "="*80 + "\n")
    return ranking_df

def analyze_top2_benefit(df, output_dir):
    """Analyze the benefit of using top-2 predictions"""
    print("="*80)
    print("TOP-2 STRATEGY BENEFIT ANALYSIS")
    print("="*80)

    strategies = df['strategy'].unique()

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # 1. Accuracy improvement from Top-1 to Top-2
    ax1 = axes[0, 0]

    improvement_data = []
    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        top1_acc = strategy_df['top1_correct'].mean() * 100
        top2_acc = strategy_df['top2_correct'].mean() * 100
        improvement = top2_acc - top1_acc

        improvement_data.append({
            'strategy': strategy,
            'Top-1': top1_acc,
            'Top-2': top2_acc,
            'Improvement': improvement
        })

        print(f"\n{strategy.upper()}:")
        print(f"  Top-1 Accuracy: {top1_acc:.2f}%")
        print(f"  Top-2 Accuracy: {top2_acc:.2f}%")
        print(f"  Absolute Improvement: +{improvement:.2f}%")
        print(f"  Relative Improvement: +{(improvement/top1_acc*100):.2f}%")

    improvement_df = pd.DataFrame(improvement_data)
    x = np.arange(len(strategies))
    width = 0.35

    ax1.bar(x - width/2, improvement_df['Top-1'], width, label='Top-1 Accuracy', color='steelblue')
    ax1.bar(x + width/2, improvement_df['Top-2'], width, label='Top-2 Accuracy', color='lightcoral')

    # Add improvement arrows
    for i, row in improvement_df.iterrows():
        ax1.annotate('', xy=(i + width/2, row['Top-2']), xytext=(i - width/2, row['Top-1']),
                    arrowprops=dict(arrowstyle='->', lw=2, color='green'))
        ax1.text(i, (row['Top-1'] + row['Top-2'])/2, f'+{row["Improvement"]:.1f}%',
                ha='center', va='center', fontweight='bold', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax1.set_ylabel('Accuracy (%)')
    ax1.set_title('Accuracy Improvement: Top-1 vs Top-2')
    ax1.set_xticks(x)
    ax1.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # 2. Improvement by difficulty
    ax2 = axes[0, 1]
    difficulty_levels = ['EASY', 'MODERATE', 'HARD']

    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        improvements = []

        for level in difficulty_levels:
            level_df = strategy_df[strategy_df['level'] == level]
            if len(level_df) > 0:
                top1 = level_df['top1_correct'].mean() * 100
                top2 = level_df['top2_correct'].mean() * 100
                improvements.append(top2 - top1)
            else:
                improvements.append(0)

        ax2.plot(difficulty_levels, improvements, marker='o', linewidth=2,
                label=strategy.replace('_', ' ').title())

    ax2.set_xlabel('Difficulty Level')
    ax2.set_ylabel('Accuracy Improvement (%)')
    ax2.set_title('Top-2 Accuracy Improvement by Difficulty')
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    # 3. Improvement by violation type
    ax3 = axes[1, 0]
    violation_types = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']

    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        improvements = []

        for vtype in violation_types:
            vtype_df = strategy_df[strategy_df['violation_type'] == vtype]
            if len(vtype_df) > 0:
                top1 = vtype_df['top1_correct'].mean() * 100
                top2 = vtype_df['top2_correct'].mean() * 100
                improvements.append(top2 - top1)
            else:
                improvements.append(0)

        ax3.plot(violation_types, improvements, marker='o', linewidth=2,
                label=strategy.replace('_', ' ').title())

    ax3.set_xlabel('Violation Type')
    ax3.set_ylabel('Accuracy Improvement (%)')
    ax3.set_title('Top-2 Accuracy Improvement by Violation Type')
    ax3.legend()
    ax3.grid(alpha=0.3)
    ax3.axhline(y=0, color='black', linestyle='--', alpha=0.3)

    # 4. Heatmap of Top-2 benefit
    ax4 = axes[1, 1]

    # Create heatmap data
    heatmap_data = []
    for strategy in strategies:
        strategy_df = df[df['strategy'] == strategy]
        row = []
        for level in difficulty_levels:
            level_df = strategy_df[strategy_df['level'] == level]
            if len(level_df) > 0:
                top1 = level_df['top1_correct'].mean() * 100
                top2 = level_df['top2_correct'].mean() * 100
                row.append(top2 - top1)
            else:
                row.append(0)
        heatmap_data.append(row)

    heatmap_df = pd.DataFrame(heatmap_data,
                              index=[s.replace('_', ' ').title() for s in strategies],
                              columns=difficulty_levels)

    sns.heatmap(heatmap_df, annot=True, fmt='.1f', cmap='RdYlGn', center=20,
                cbar_kws={'label': 'Improvement (%)'}, ax=ax4)
    ax4.set_title('Top-2 Benefit Heatmap\n(Accuracy Improvement by Strategy and Difficulty)')
    ax4.set_xlabel('Difficulty Level')
    ax4.set_ylabel('Strategy')

    plt.tight_layout()
    fig.savefig(output_dir / '08_top2_benefit_analysis.png', dpi=300, bbox_inches='tight')
    print(f"\n[OK] Saved top-2 benefit analysis")
    plt.close(fig)

    print("\n" + "="*80 + "\n")
    return improvement_df

def generate_enhanced_report(df, ranking_df, improvement_df, output_dir):
    """Generate enhanced text report with additional insights"""
    report_path = output_dir / 'enhanced_analysis_report.txt'

    with open(report_path, 'w') as f:
        f.write("="*80 + "\n")
        f.write("ENHANCED TOP-2 STRATEGY ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")

        # Key insights
        f.write("## KEY INSIGHTS\n")
        f.write("-"*80 + "\n\n")

        strategies = df['strategy'].unique()

        # Best strategy for each metric
        best_top1 = improvement_df.loc[improvement_df['Top-1'].idxmax(), 'strategy']
        best_top2 = improvement_df.loc[improvement_df['Top-2'].idxmax(), 'strategy']
        best_improvement = improvement_df.loc[improvement_df['Improvement'].idxmax(), 'strategy']

        f.write(f"1. BEST PERFORMERS:\n")
        f.write(f"   - Best Top-1 Accuracy: {best_top1.replace('_', ' ').title()}\n")
        f.write(f"   - Best Top-2 Accuracy: {best_top2.replace('_', ' ').title()}\n")
        f.write(f"   - Largest Top-2 Benefit: {best_improvement.replace('_', ' ').title()}\n\n")

        # Ranking distribution insights
        f.write(f"2. RANKING DISTRIBUTION:\n")
        for i, row in ranking_df.iterrows():
            strategy = row['strategy']
            f.write(f"   {strategy.upper()}:\n")
            f.write(f"     - {row['Position 1']:.1f}% correct at Position 1\n")
            f.write(f"     - {row['Position 2']:.1f}% correct at Position 2 (Top-2 benefit)\n")
            f.write(f"     - {row['Not in Top-2']:.1f}% not in Top-2\n")
        f.write("\n")

        # Difficulty analysis
        f.write(f"3. DIFFICULTY LEVEL INSIGHTS:\n")
        for strategy in strategies:
            strategy_df = df[df['strategy'] == strategy]
            f.write(f"   {strategy.upper()}:\n")

            for level in ['EASY', 'MODERATE', 'HARD']:
                level_df = strategy_df[strategy_df['level'] == level]
                if len(level_df) > 0:
                    top1 = level_df['top1_correct'].mean() * 100
                    top2 = level_df['top2_correct'].mean() * 100
                    improvement = top2 - top1
                    f.write(f"     {level}: Top-1={top1:.1f}%, Top-2={top2:.1f}%, Gain=+{improvement:.1f}%\n")
            f.write("\n")

        # Violation type insights
        f.write(f"4. VIOLATION TYPE INSIGHTS:\n")
        for strategy in strategies:
            strategy_df = df[df['strategy'] == strategy]
            f.write(f"   {strategy.upper()}:\n")

            # Find best and worst performing violation types
            vtype_performance = []
            for vtype in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
                vtype_df = strategy_df[strategy_df['violation_type'] == vtype]
                if len(vtype_df) > 0:
                    top2_acc = vtype_df['top2_correct'].mean() * 100
                    vtype_performance.append((vtype, top2_acc))

            if vtype_performance:
                vtype_performance.sort(key=lambda x: x[1], reverse=True)
                best_vtype, best_acc = vtype_performance[0]
                worst_vtype, worst_acc = vtype_performance[-1]

                f.write(f"     Best: {best_vtype} ({best_acc:.1f}% Top-2 accuracy)\n")
                f.write(f"     Worst: {worst_vtype} ({worst_acc:.1f}% Top-2 accuracy)\n")
            f.write("\n")

        # Processing time analysis
        f.write(f"5. EFFICIENCY ANALYSIS:\n")
        for strategy in strategies:
            strategy_df = df[df['strategy'] == strategy]
            mean_time = strategy_df['processing_time'].mean()
            top2_acc = strategy_df['top2_correct'].mean() * 100
            efficiency = top2_acc / mean_time  # Accuracy per second

            f.write(f"   {strategy.upper()}:\n")
            f.write(f"     Mean Time: {mean_time:.2f}s\n")
            f.write(f"     Top-2 Accuracy: {top2_acc:.2f}%\n")
            f.write(f"     Efficiency (Acc/Time): {efficiency:.2f}%/s\n\n")

        # Recommendations
        f.write(f"6. RECOMMENDATIONS:\n")

        # Find most efficient strategy
        efficiency_scores = []
        for strategy in strategies:
            strategy_df = df[df['strategy'] == strategy]
            mean_time = strategy_df['processing_time'].mean()
            top2_acc = strategy_df['top2_correct'].mean() * 100
            efficiency = top2_acc / mean_time
            efficiency_scores.append((strategy, efficiency, top2_acc, mean_time))

        efficiency_scores.sort(key=lambda x: x[1], reverse=True)
        most_efficient = efficiency_scores[0]

        f.write(f"   - For SPEED: Use {most_efficient[0].replace('_', ' ').title()} ")
        f.write(f"({most_efficient[1]:.2f}%/s efficiency)\n")

        # Find most accurate
        accuracy_scores = [(s, df[df['strategy']==s]['top2_correct'].mean()*100) for s in strategies]
        accuracy_scores.sort(key=lambda x: x[1], reverse=True)
        most_accurate = accuracy_scores[0]

        f.write(f"   - For ACCURACY: Use {most_accurate[0].replace('_', ' ').title()} ")
        f.write(f"({most_accurate[1]:.2f}% Top-2 accuracy)\n")

        # Find best balance
        f.write(f"   - For BALANCE: Consider trade-offs between speed and accuracy\n")

        f.write("\n" + "="*80 + "\n")
        f.write("END OF ENHANCED REPORT\n")
        f.write("="*80 + "\n")

    print(f"[OK] Saved enhanced analysis report to {report_path}")

def main():
    print("Loading results...")
    df = load_results()

    output_dir = Path(r"c:\Users\Jay\jcSOLID\analysis\analysis_output_top2_strategies")

    # Run enhanced analyses
    ranking_df = analyze_ranking_distribution(df, output_dir)
    improvement_df = analyze_top2_benefit(df, output_dir)

    # Generate enhanced report
    generate_enhanced_report(df, ranking_df, improvement_df, output_dir)

    print("\n" + "="*80)
    print("ENHANCED ANALYSIS COMPLETE!")
    print("="*80)
    print(f"\nAll results saved to: {output_dir}")
    print("\nGenerated files:")
    print("  - 07_ranking_distribution_analysis.png")
    print("  - 08_top2_benefit_analysis.png")
    print("  - enhanced_analysis_report.txt")

if __name__ == "__main__":
    main()
