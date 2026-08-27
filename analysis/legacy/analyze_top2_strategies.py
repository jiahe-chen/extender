"""
Comprehensive analysis of top_2 strategies: single_agent, two_agent, and diff_eval
Analyzes performance metrics, MRR, difficulty levels, and generates confusion matrices
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)

class Top2StrategyAnalyzer:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.strategies = ['single_agent', 'two_agent', 'diff_eval']
        self.data = {}
        self.results_df = None

    def load_data(self):
        """Load detection results from all three strategies"""
        print("Loading data from all strategies...")

        for strategy in self.strategies:
            file_path = self.base_path / f"result/local/{strategy}/run_1/qwen3-8b/detection_results.json"
            print(f"  Loading {strategy}...")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Try to parse the JSON
                    data = json.loads(content)
                    self.data[strategy] = data
                    print(f"    [OK] Loaded {strategy}")
            except json.JSONDecodeError as e:
                print(f"    [ERROR] JSON decode error in {strategy}: {e}")
                # Try to fix common JSON issues
                try:
                    # Remove trailing commas or fix other issues
                    content = content.replace(',]', ']').replace(',}', '}')
                    data = json.loads(content)
                    self.data[strategy] = data
                    print(f"    [OK] Loaded {strategy} after fixing")
                except:
                    print(f"    [ERROR] Could not load {strategy}")
                    self.data[strategy] = None
            except Exception as e:
                print(f"    [ERROR] Error loading {strategy}: {e}")
                self.data[strategy] = None

        print(f"\nSuccessfully loaded {len([d for d in self.data.values() if d is not None])} strategies\n")

    def extract_results(self):
        """Extract results into a structured DataFrame"""
        print("Extracting results into DataFrame...")

        all_results = []

        for strategy, data in self.data.items():
            if data is None:
                continue

            # Get results from the nested structure: by_violation_type -> violation -> results
            by_violation = data.get('by_violation_type', {})

            for violation_type, violation_data in by_violation.items():
                results = violation_data.get('results', [])

                for result in results:
                    # For diff_eval, the actual violation is in 'ground_truth', not 'violation_type'
                    # For single_agent and two_agent, the actual violation is the violation_type (the key in by_violation_type)
                    if strategy == 'diff_eval':
                        actual_violation = result.get('ground_truth', violation_type)
                    else:
                        actual_violation = violation_type

                    row = {
                        'strategy': strategy,
                        'example_id': result.get('example_id'),
                        'violation_type': violation_type,  # The category this example belongs to
                        'level': result.get('level'),
                        'language': result.get('language'),
                        'actual_violation': actual_violation,
                        'processing_time': result.get('processing_time_seconds', 0),
                    }

                    # For diff_eval, also store the built-in detection_success field
                    if strategy == 'diff_eval':
                        row['detection_success'] = result.get('detection_success', False)

                    # Parse model_response to extract top_2 predictions
                    # For diff_eval, use all_checks to get ranked violations
                    if strategy == 'diff_eval':
                        all_checks = result.get('all_checks', [])
                        # Filter detected violations and sort by order (they should already be in order)
                        detected_violations = [check for check in all_checks if check.get('is_detected', False)]

                        predictions = []
                        for check in detected_violations[:2]:  # Take top 2
                            predictions.append({
                                'violation_type': check.get('violation_type'),
                                'explanation': check.get('detailed_explanation', '')
                            })
                    else:
                        # For single_agent and two_agent, parse model_response
                        model_response = result.get('model_response', '')
                        predictions = []

                        try:
                            # Try to parse the model_response as JSON
                            if model_response:
                                response_json = json.loads(model_response)
                                violations = response_json.get('violations', [])

                                for v in violations[:2]:  # Take top 2
                                    predictions.append({
                                        'violation_type': v.get('violation_type'),
                                        'explanation': v.get('explanation')
                                    })
                        except:
                            # If parsing fails, try to extract from detected_violation_type string
                            detected = result.get('detected_violation_type', '')
                            if detected:
                                # Split by comma and take first two
                                detected_list = [v.strip() for v in detected.split(',')]
                                for v in detected_list[:2]:
                                    predictions.append({
                                        'violation_type': v,
                                        'explanation': ''
                                    })

                    # Extract top_2 predictions
                    if len(predictions) >= 1:
                        row['prediction_1'] = predictions[0].get('violation_type')
                    else:
                        row['prediction_1'] = None

                    if len(predictions) >= 2:
                        row['prediction_2'] = predictions[1].get('violation_type')
                    else:
                        row['prediction_2'] = None

                    # Calculate metrics
                    row['top1_correct'] = row['prediction_1'] == row['actual_violation']
                    row['top2_correct'] = (row['prediction_1'] == row['actual_violation'] or
                                          row['prediction_2'] == row['actual_violation'])

                    # Calculate MRR (Mean Reciprocal Rank)
                    if row['prediction_1'] == row['actual_violation']:
                        row['reciprocal_rank'] = 1.0
                    elif row['prediction_2'] == row['actual_violation']:
                        row['reciprocal_rank'] = 0.5
                    else:
                        row['reciprocal_rank'] = 0.0

                    # Track which position the correct answer is in
                    if row['prediction_1'] == row['actual_violation']:
                        row['correct_position'] = 1
                    elif row['prediction_2'] == row['actual_violation']:
                        row['correct_position'] = 2
                    else:
                        row['correct_position'] = 0  # Not in top 2

                    all_results.append(row)

        self.results_df = pd.DataFrame(all_results)
        print(f"  [OK] Extracted {len(self.results_df)} results\n")

        return self.results_df

    def calculate_overall_metrics(self):
        """Calculate overall performance metrics for each strategy"""
        print("="*80)
        print("OVERALL PERFORMANCE METRICS")
        print("="*80)

        metrics = {}

        for strategy in self.strategies:
            strategy_df = self.results_df[self.results_df['strategy'] == strategy]

            if len(strategy_df) == 0:
                continue

            metrics[strategy] = {
                'total_examples': len(strategy_df),
                'top1_accuracy': strategy_df['top1_correct'].mean() * 100,
                'top2_accuracy': strategy_df['top2_correct'].mean() * 100,
                'mrr': strategy_df['reciprocal_rank'].mean(),
                'mean_processing_time': strategy_df['processing_time'].mean(),
                'median_processing_time': strategy_df['processing_time'].median(),
            }

            # For diff_eval, also calculate detection success rate
            if strategy == 'diff_eval' and 'detection_success' in strategy_df.columns:
                metrics[strategy]['detection_rate'] = strategy_df['detection_success'].mean() * 100

            print(f"\n{strategy.upper()}:")
            print(f"  Total Examples: {metrics[strategy]['total_examples']}")

            # For diff_eval, show detection rate first
            if strategy == 'diff_eval' and 'detection_rate' in metrics[strategy]:
                print(f"  Overall Detection Rate: {metrics[strategy]['detection_rate']:.2f}% (ground truth detected at any position)")

            print(f"  Top-1 Accuracy: {metrics[strategy]['top1_accuracy']:.2f}%")
            print(f"  Top-2 Accuracy: {metrics[strategy]['top2_accuracy']:.2f}%")

            # For diff_eval, show the gap
            if strategy == 'diff_eval' and 'detection_rate' in metrics[strategy]:
                gap = metrics[strategy]['detection_rate'] - metrics[strategy]['top2_accuracy']
                print(f"  Detection Gap: {gap:.2f}% (detected but ranked 3rd or later)")

            print(f"  MRR (Mean Reciprocal Rank): {metrics[strategy]['mrr']:.4f}")
            print(f"  Mean Processing Time: {metrics[strategy]['mean_processing_time']:.2f}s")
            print(f"  Median Processing Time: {metrics[strategy]['median_processing_time']:.2f}s")

        print("\n" + "="*80 + "\n")
        return metrics

    def analyze_by_difficulty(self):
        """Analyze performance by difficulty level"""
        print("="*80)
        print("PERFORMANCE BY DIFFICULTY LEVEL")
        print("="*80)

        difficulty_results = {}

        for strategy in self.strategies:
            strategy_df = self.results_df[self.results_df['strategy'] == strategy]

            if len(strategy_df) == 0:
                continue

            print(f"\n{strategy.upper()}:")
            print(f"{'Level':<12} {'Count':<8} {'Top-1 Acc':<12} {'Top-2 Acc':<12} {'MRR':<10} {'Avg Time':<10}")
            print("-" * 70)

            difficulty_results[strategy] = {}

            for level in ['EASY', 'MODERATE', 'HARD']:
                level_df = strategy_df[strategy_df['level'] == level]

                if len(level_df) > 0:
                    difficulty_results[strategy][level] = {
                        'count': len(level_df),
                        'top1_acc': level_df['top1_correct'].mean() * 100,
                        'top2_acc': level_df['top2_correct'].mean() * 100,
                        'mrr': level_df['reciprocal_rank'].mean(),
                        'avg_time': level_df['processing_time'].mean(),
                    }

                    print(f"{level:<12} {difficulty_results[strategy][level]['count']:<8} "
                          f"{difficulty_results[strategy][level]['top1_acc']:<12.2f} "
                          f"{difficulty_results[strategy][level]['top2_acc']:<12.2f} "
                          f"{difficulty_results[strategy][level]['mrr']:<10.4f} "
                          f"{difficulty_results[strategy][level]['avg_time']:<10.2f}")

        print("\n" + "="*80 + "\n")
        return difficulty_results

    def analyze_by_violation_type(self):
        """Analyze performance by violation type"""
        print("="*80)
        print("PERFORMANCE BY VIOLATION TYPE")
        print("="*80)

        violation_results = {}

        for strategy in self.strategies:
            strategy_df = self.results_df[self.results_df['strategy'] == strategy]

            if len(strategy_df) == 0:
                continue

            print(f"\n{strategy.upper()}:")
            print(f"{'Violation':<12} {'Count':<8} {'Top-1 Acc':<12} {'Top-2 Acc':<12} {'MRR':<10}")
            print("-" * 60)

            violation_results[strategy] = {}

            for violation in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
                viol_df = strategy_df[strategy_df['violation_type'] == violation]

                if len(viol_df) > 0:
                    violation_results[strategy][violation] = {
                        'count': len(viol_df),
                        'top1_acc': viol_df['top1_correct'].mean() * 100,
                        'top2_acc': viol_df['top2_correct'].mean() * 100,
                        'mrr': viol_df['reciprocal_rank'].mean(),
                    }

                    print(f"{violation:<12} {violation_results[strategy][violation]['count']:<8} "
                          f"{violation_results[strategy][violation]['top1_acc']:<12.2f} "
                          f"{violation_results[strategy][violation]['top2_acc']:<12.2f} "
                          f"{violation_results[strategy][violation]['mrr']:<10.4f}")

        print("\n" + "="*80 + "\n")
        return violation_results

    def generate_confusion_matrices(self):
        """Generate confusion matrices for each strategy"""
        print("Generating confusion matrices...")

        violation_types = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']

        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        for idx, strategy in enumerate(self.strategies):
            strategy_df = self.results_df[self.results_df['strategy'] == strategy]

            if len(strategy_df) == 0:
                continue

            # Create confusion matrix
            cm = pd.crosstab(
                strategy_df['actual_violation'],
                strategy_df['prediction_1'],
                rownames=['Actual'],
                colnames=['Predicted'],
                dropna=False
            )

            # Ensure all violation types are present
            for vtype in violation_types:
                if vtype not in cm.index:
                    cm.loc[vtype] = 0
                if vtype not in cm.columns:
                    cm[vtype] = 0

            cm = cm.reindex(index=violation_types, columns=violation_types, fill_value=0)

            # Plot
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                       cbar_kws={'label': 'Count'})
            axes[idx].set_title(f'{strategy.replace("_", " ").title()}\nConfusion Matrix (Top-1)')
            axes[idx].set_xlabel('Predicted Violation')
            axes[idx].set_ylabel('Actual Violation')

        plt.tight_layout()
        return fig

    def plot_comparison_charts(self, overall_metrics, difficulty_results, violation_results):
        """Generate comparison charts"""
        print("Generating comparison charts...")

        # 1. Overall Accuracy Comparison
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        strategies = list(overall_metrics.keys())
        top1_accs = [overall_metrics[s]['top1_accuracy'] for s in strategies]
        top2_accs = [overall_metrics[s]['top2_accuracy'] for s in strategies]

        x = np.arange(len(strategies))
        width = 0.35

        ax1.bar(x - width/2, top1_accs, width, label='Top-1 Accuracy', color='steelblue')
        ax1.bar(x + width/2, top2_accs, width, label='Top-2 Accuracy', color='lightcoral')

        ax1.set_xlabel('Strategy')
        ax1.set_ylabel('Accuracy (%)')
        ax1.set_title('Overall Accuracy Comparison: Top-1 vs Top-2')
        ax1.set_xticks(x)
        ax1.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # 2. MRR Comparison
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        mrrs = [overall_metrics[s]['mrr'] for s in strategies]

        ax2.bar(strategies, mrrs, color='mediumseagreen')
        ax2.set_xlabel('Strategy')
        ax2.set_ylabel('MRR (Mean Reciprocal Rank)')
        ax2.set_title('Mean Reciprocal Rank Comparison')
        ax2.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
        ax2.grid(axis='y', alpha=0.3)

        # 3. Performance by Difficulty
        fig3, axes3 = plt.subplots(1, 2, figsize=(16, 6))

        # Top-1 by difficulty
        for strategy in strategies:
            if strategy in difficulty_results:
                levels = list(difficulty_results[strategy].keys())
                accs = [difficulty_results[strategy][l]['top1_acc'] for l in levels]
                axes3[0].plot(levels, accs, marker='o', label=strategy.replace('_', ' ').title(), linewidth=2)

        axes3[0].set_xlabel('Difficulty Level')
        axes3[0].set_ylabel('Top-1 Accuracy (%)')
        axes3[0].set_title('Top-1 Accuracy by Difficulty Level')
        axes3[0].legend()
        axes3[0].grid(alpha=0.3)

        # Top-2 by difficulty
        for strategy in strategies:
            if strategy in difficulty_results:
                levels = list(difficulty_results[strategy].keys())
                accs = [difficulty_results[strategy][l]['top2_acc'] for l in levels]
                axes3[1].plot(levels, accs, marker='o', label=strategy.replace('_', ' ').title(), linewidth=2)

        axes3[1].set_xlabel('Difficulty Level')
        axes3[1].set_ylabel('Top-2 Accuracy (%)')
        axes3[1].set_title('Top-2 Accuracy by Difficulty Level')
        axes3[1].legend()
        axes3[1].grid(alpha=0.3)

        plt.tight_layout()

        # 4. Performance by Violation Type
        fig4, axes4 = plt.subplots(1, 2, figsize=(16, 6))

        violation_types = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
        x = np.arange(len(violation_types))
        width = 0.25

        # Top-1 by violation
        for i, strategy in enumerate(strategies):
            if strategy in violation_results:
                accs = [violation_results[strategy].get(v, {}).get('top1_acc', 0) for v in violation_types]
                axes4[0].bar(x + i*width, accs, width, label=strategy.replace('_', ' ').title())

        axes4[0].set_xlabel('Violation Type')
        axes4[0].set_ylabel('Top-1 Accuracy (%)')
        axes4[0].set_title('Top-1 Accuracy by Violation Type')
        axes4[0].set_xticks(x + width)
        axes4[0].set_xticklabels(violation_types)
        axes4[0].legend()
        axes4[0].grid(axis='y', alpha=0.3)

        # Top-2 by violation
        for i, strategy in enumerate(strategies):
            if strategy in violation_results:
                accs = [violation_results[strategy].get(v, {}).get('top2_acc', 0) for v in violation_types]
                axes4[1].bar(x + i*width, accs, width, label=strategy.replace('_', ' ').title())

        axes4[1].set_xlabel('Violation Type')
        axes4[1].set_ylabel('Top-2 Accuracy (%)')
        axes4[1].set_title('Top-2 Accuracy by Violation Type')
        axes4[1].set_xticks(x + width)
        axes4[1].set_xticklabels(violation_types)
        axes4[1].legend()
        axes4[1].grid(axis='y', alpha=0.3)

        plt.tight_layout()

        # 5. Processing Time Comparison
        fig5, ax5 = plt.subplots(figsize=(10, 6))
        mean_times = [overall_metrics[s]['mean_processing_time'] for s in strategies]

        ax5.bar(strategies, mean_times, color='coral')
        ax5.set_xlabel('Strategy')
        ax5.set_ylabel('Mean Processing Time (s)')
        ax5.set_title('Processing Time Comparison')
        ax5.set_xticklabels([s.replace('_', ' ').title() for s in strategies])
        ax5.grid(axis='y', alpha=0.3)

        return fig1, fig2, fig3, fig4, fig5

    def save_results(self, output_dir):
        """Save all results and visualizations"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        print(f"Saving results to {output_path}...")

        # Save DataFrame
        csv_path = output_path / 'detailed_results.csv'
        self.results_df.to_csv(csv_path, index=False)
        print(f"  [OK] Saved detailed results to {csv_path}")

        # Calculate metrics
        overall_metrics = self.calculate_overall_metrics()
        difficulty_results = self.analyze_by_difficulty()
        violation_results = self.analyze_by_violation_type()

        # Generate and save confusion matrices
        cm_fig = self.generate_confusion_matrices()
        cm_fig.savefig(output_path / '01_confusion_matrices.png', dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved confusion matrices")
        plt.close(cm_fig)

        # Generate and save comparison charts
        figs = self.plot_comparison_charts(overall_metrics, difficulty_results, violation_results)
        fig_names = [
            '02_accuracy_comparison.png',
            '03_mrr_comparison.png',
            '04_difficulty_analysis.png',
            '05_violation_type_analysis.png',
            '06_processing_time.png'
        ]

        for fig, name in zip(figs, fig_names):
            fig.savefig(output_path / name, dpi=300, bbox_inches='tight')
            print(f"  [OK] Saved {name}")
            plt.close(fig)

        # Generate summary report
        self.generate_summary_report(output_path, overall_metrics, difficulty_results, violation_results)

        print(f"\n[OK] All results saved to {output_path}\n")

    def generate_summary_report(self, output_path, overall_metrics, difficulty_results, violation_results):
        """Generate a text summary report"""
        report_path = output_path / 'analysis_report.txt'

        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("TOP-2 STRATEGY COMPARISON REPORT\n")
            f.write("Strategies: single_agent, two_agent, diff_eval\n")
            f.write("Model: qwen3-8b\n")
            f.write("="*80 + "\n\n")

            # Overall metrics
            f.write("## OVERALL PERFORMANCE\n")
            f.write("-"*80 + "\n")
            for strategy, metrics in overall_metrics.items():
                f.write(f"\n{strategy.upper()}:\n")
                f.write(f"  Total Examples: {metrics['total_examples']}\n")
                f.write(f"  Top-1 Accuracy: {metrics['top1_accuracy']:.2f}%\n")
                f.write(f"  Top-2 Accuracy: {metrics['top2_accuracy']:.2f}%\n")
                f.write(f"  Accuracy Gain (Top-2 vs Top-1): {metrics['top2_accuracy'] - metrics['top1_accuracy']:.2f}%\n")
                f.write(f"  MRR: {metrics['mrr']:.4f}\n")
                f.write(f"  Mean Processing Time: {metrics['mean_processing_time']:.2f}s\n")

            # Comparison
            f.write("\n\n## STRATEGY COMPARISON\n")
            f.write("-"*80 + "\n")
            strategies = list(overall_metrics.keys())
            if len(strategies) >= 2:
                best_top1 = max(strategies, key=lambda s: overall_metrics[s]['top1_accuracy'])
                best_top2 = max(strategies, key=lambda s: overall_metrics[s]['top2_accuracy'])
                best_mrr = max(strategies, key=lambda s: overall_metrics[s]['mrr'])
                fastest = min(strategies, key=lambda s: overall_metrics[s]['mean_processing_time'])

                f.write(f"Best Top-1 Accuracy: {best_top1} ({overall_metrics[best_top1]['top1_accuracy']:.2f}%)\n")
                f.write(f"Best Top-2 Accuracy: {best_top2} ({overall_metrics[best_top2]['top2_accuracy']:.2f}%)\n")
                f.write(f"Best MRR: {best_mrr} ({overall_metrics[best_mrr]['mrr']:.4f})\n")
                f.write(f"Fastest: {fastest} ({overall_metrics[fastest]['mean_processing_time']:.2f}s)\n")

            # Difficulty analysis
            f.write("\n\n## PERFORMANCE BY DIFFICULTY\n")
            f.write("-"*80 + "\n")
            for strategy in strategies:
                if strategy in difficulty_results:
                    f.write(f"\n{strategy.upper()}:\n")
                    for level in ['EASY', 'MODERATE', 'HARD']:
                        if level in difficulty_results[strategy]:
                            dr = difficulty_results[strategy][level]
                            f.write(f"  {level}: Top-1={dr['top1_acc']:.2f}%, Top-2={dr['top2_acc']:.2f}%, MRR={dr['mrr']:.4f}\n")

            # Violation type analysis
            f.write("\n\n## PERFORMANCE BY VIOLATION TYPE\n")
            f.write("-"*80 + "\n")
            for strategy in strategies:
                if strategy in violation_results:
                    f.write(f"\n{strategy.upper()}:\n")
                    for violation in ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']:
                        if violation in violation_results[strategy]:
                            vr = violation_results[strategy][violation]
                            f.write(f"  {violation}: Top-1={vr['top1_acc']:.2f}%, Top-2={vr['top2_acc']:.2f}%, MRR={vr['mrr']:.4f}\n")

            f.write("\n" + "="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")

        print(f"  [OK] Saved summary report to {report_path}")


def main():
    # Initialize analyzer
    base_path = Path(r"c:\Users\Jay\jcSOLID")
    analyzer = Top2StrategyAnalyzer(base_path)

    # Load data
    analyzer.load_data()

    # Extract results
    analyzer.extract_results()

    # Save all results
    output_dir = base_path / "analysis" / "analysis_output_top2_strategies"
    analyzer.save_results(output_dir)

    print("Analysis complete!")


if __name__ == "__main__":
    main()
