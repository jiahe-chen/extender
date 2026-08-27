"""
分析 detailed_results_v5_updated.json 文件
统计不同模型和违规类型的检测准确率 (violation_match: true 的占比)
只考虑 example 类型的数据
包含错误分析和混淆矩阵
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict

# 设置样式
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.size'] = 12  # 增大默认字号
plt.rcParams['axes.labelsize'] = 14  # 坐标轴标签字号
plt.rcParams['axes.titlesize'] = 16  # 标题字号
plt.rcParams['xtick.labelsize'] = 12  # x轴刻度字号
plt.rcParams['ytick.labelsize'] = 12  # y轴刻度字号
plt.rcParams['legend.fontsize'] = 12  # 图例字号

class LiteratureAnalyzer:
    def __init__(self, json_path):
        self.json_path = Path(json_path)
        self.data = None
        self.results_df = None
        self.raw_data = []  # 保存原始数据

    def load_data(self):
        """加载 JSON 数据"""
        print("="*80)
        print("Loading data...")
        print("="*80)

        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

        print(f"Successfully loaded data with {len(self.data)} top-level keys\n")

    def extract_examples(self):
        """提取所有 example 类型的数据"""
        print("Extracting example data...")

        examples = []

        # 遍历嵌套的字典结构
        for model_key, model_data in self.data.items():
            # 检查是否有 'example' 键
            if 'example' in model_data:
                example_data = model_data['example']

                # 获取模型信息并提取实际模型名称
                model_full = example_data.get('model', model_key)

                # 从完整模型名称中提取核心模型名称
                # 例如: "dip--codellama70b-temp0-latest--example" -> "codellama70b"
                if 'qwen2.5-coder32b' in model_full:
                    model_name = 'qwen2.5-coder32b'
                elif 'deepseek33b' in model_full:
                    model_name = 'deepseek33b'
                elif 'codellama70b' in model_full:
                    model_name = 'codellama70b'
                elif 'gpt-4o-mini' in model_full:
                    model_name = 'gpt-4o-mini'
                else:
                    model_name = model_full  # 保留原始名称作为后备

                # 遍历违规类型
                violation_results = example_data.get('violation_results', {})

                for violation_type, violation_data in violation_results.items():
                    items = violation_data.get('items', [])

                    for item in items:
                        # Handle None values safely
                        expected = item.get('expected_violation', '')
                        detected = item.get('detected_violation', '')

                        row = {
                            'model': model_name,
                            'model_key': model_key,
                            'violation_type': violation_type.upper(),
                            'expected_violation': expected.upper() if expected else '',
                            'detected_violation': detected.upper() if detected else '',
                            'violation_match': item.get('violation_match', False),
                            'status': item.get('status'),
                            'failure_reason': item.get('failure_reason'),
                            'language': item.get('language'),
                            'item_id': item.get('id'),
                            'response_length': item.get('response_length', 0),
                        }

                        examples.append(row)
                        self.raw_data.append(item)  # 保存原始数据

        self.results_df = pd.DataFrame(examples)
        print(f"Extracted {len(self.results_df)} example records\n")

        return self.results_df

    def calculate_overall_accuracy(self):
        """计算总体准确率"""
        print("="*80)
        print("OVERALL ACCURACY STATISTICS")
        print("="*80)

        total = len(self.results_df)
        correct = self.results_df['violation_match'].sum()
        accuracy = correct / total * 100 if total > 0 else 0

        print(f"\nTotal Examples: {total}")
        print(f"Correct Detections: {correct}")
        print(f"Overall Accuracy: {accuracy:.2f}%\n")

        return {'total': total, 'correct': correct, 'accuracy': accuracy}

    def calculate_by_model(self):
        """按模型统计准确率"""
        print("="*80)
        print("ACCURACY BY MODEL")
        print("="*80)

        model_stats = {}

        print(f"\n{'Model':<50} {'Total':<10} {'Correct':<10} {'Accuracy':<10}")
        print("-" * 80)

        for model in sorted(self.results_df['model'].unique()):
            model_df = self.results_df[self.results_df['model'] == model]
            total = len(model_df)
            correct = model_df['violation_match'].sum()
            accuracy = correct / total * 100 if total > 0 else 0

            model_stats[model] = {
                'total': total,
                'correct': correct,
                'accuracy': accuracy
            }

            print(f"{model:<50} {total:<10} {correct:<10} {accuracy:<10.2f}%")

        print("\n")
        return model_stats

    def calculate_by_violation(self):
        """按违规类型统计准确率"""
        print("="*80)
        print("ACCURACY BY VIOLATION TYPE")
        print("="*80)

        violation_stats = {}

        print(f"\n{'Violation':<15} {'Total':<10} {'Correct':<10} {'Accuracy':<10}")
        print("-" * 55)

        for violation in sorted(self.results_df['expected_violation'].unique()):
            viol_df = self.results_df[self.results_df['expected_violation'] == violation]
            total = len(viol_df)
            correct = viol_df['violation_match'].sum()
            accuracy = correct / total * 100 if total > 0 else 0

            violation_stats[violation] = {
                'total': total,
                'correct': correct,
                'accuracy': accuracy
            }

            print(f"{violation:<15} {total:<10} {correct:<10} {accuracy:<10.2f}%")

        print("\n")
        return violation_stats

    def analyze_errors(self):
        """错误分析"""
        print("="*80)
        print("ERROR ANALYSIS")
        print("="*80)

        # 获取所有错误的样本
        errors_df = self.results_df[~self.results_df['violation_match']]

        print(f"\nTotal Errors: {len(errors_df)} ({len(errors_df)/len(self.results_df)*100:.2f}%)")

        # 按失败原因统计
        print("\nError Distribution by Failure Reason:")
        print("-" * 60)
        failure_counts = errors_df['failure_reason'].value_counts()
        for reason, count in failure_counts.items():
            pct = count / len(errors_df) * 100
            print(f"  {reason}: {count} ({pct:.1f}%)")

        # 按模型统计错误
        print("\nError Count by Model:")
        print("-" * 60)
        model_errors = errors_df.groupby('model').size().sort_values(ascending=False)
        for model, count in model_errors.head(10).items():
            total = len(self.results_df[self.results_df['model'] == model])
            error_rate = count / total * 100
            print(f"  {model[:45]}: {count}/{total} ({error_rate:.1f}%)")

        # 按违规类型统计错误
        print("\nError Count by Violation Type:")
        print("-" * 60)
        violation_errors = errors_df.groupby('expected_violation').size().sort_values(ascending=False)
        for violation, count in violation_errors.items():
            total = len(self.results_df[self.results_df['expected_violation'] == violation])
            error_rate = count / total * 100
            print(f"  {violation}: {count}/{total} ({error_rate:.1f}%)")

        # 常见的错误预测
        print("\nMost Common Misclassifications (Expected -> Detected):")
        print("-" * 60)
        misclass = errors_df.groupby(['expected_violation', 'detected_violation']).size().sort_values(ascending=False)
        for (expected, detected), count in misclass.head(10).items():
            print(f"  {expected} -> {detected}: {count}")

        print("\n")

        return {
            'total_errors': len(errors_df),
            'failure_reasons': failure_counts.to_dict(),
            'model_errors': model_errors.to_dict(),
            'violation_errors': violation_errors.to_dict(),
            'misclassifications': misclass.to_dict()
        }

    def generate_confusion_matrices(self):
        """生成混淆矩阵"""
        print("="*80)
        print("CONFUSION MATRIX ANALYSIS")
        print("="*80)

        # 获取所有违规类型
        all_violations = sorted(set(self.results_df['expected_violation'].unique()) |
                               set(self.results_df['detected_violation'].unique()))
        all_violations = [v for v in all_violations if v and v != '']

        # 总体混淆矩阵
        print("\nOverall Confusion Matrix:")
        print("-" * 60)

        cm_overall = pd.crosstab(
            self.results_df['expected_violation'],
            self.results_df['detected_violation'],
            rownames=['Expected'],
            colnames=['Detected'],
            dropna=False
        )

        # 确保所有违规类型都在矩阵中
        for v in all_violations:
            if v not in cm_overall.index:
                cm_overall.loc[v] = 0
            if v not in cm_overall.columns:
                cm_overall[v] = 0

        cm_overall = cm_overall.reindex(index=all_violations, columns=all_violations, fill_value=0)

        print(cm_overall)
        print("\n")

        # 按模型的混淆矩阵（只显示前几个模型）
        confusion_matrices = {'overall': cm_overall}

        top_models = self.results_df['model'].value_counts().head(5).index
        for model in top_models:
            model_df = self.results_df[self.results_df['model'] == model]

            cm_model = pd.crosstab(
                model_df['expected_violation'],
                model_df['detected_violation'],
                rownames=['Expected'],
                colnames=['Detected'],
                dropna=False
            )

            # 确保所有违规类型都在矩阵中
            for v in all_violations:
                if v not in cm_model.index:
                    cm_model.loc[v] = 0
                if v not in cm_model.columns:
                    cm_model[v] = 0

            cm_model = cm_model.reindex(index=all_violations, columns=all_violations, fill_value=0)

            confusion_matrices[model] = cm_model

        return confusion_matrices

    def visualize_confusion_matrices(self, output_dir, confusion_matrices):
        """可视化混淆矩阵"""
        print("Generating confusion matrix visualizations...")

        output_path = Path(output_dir)

        # 1. 总体混淆矩阵
        fig1, ax1 = plt.subplots(figsize=(12, 10))
        cm = confusion_matrices['overall']

        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax1,
                   cbar_kws={'label': 'Count'}, square=True,
                   annot_kws={'fontsize': 14, 'fontweight': 'bold'})
        ax1.set_title('Overall Confusion Matrix', fontsize=18, fontweight='bold', pad=20)
        ax1.set_xlabel('Detected Violation', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Expected Violation', fontsize=16, fontweight='bold')
        ax1.tick_params(axis='both', labelsize=14)

        plt.tight_layout()
        fig1.savefig(output_path / '05_confusion_matrix_overall.png', dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved 05_confusion_matrix_overall.png")
        plt.close(fig1)

        # 2. 按模型的混淆矩阵（多子图）
        models = [k for k in confusion_matrices.keys() if k != 'overall']
        if models:
            n_models = len(models)
            n_cols = 2
            n_rows = (n_models + 1) // 2

            fig2, axes = plt.subplots(n_rows, n_cols, figsize=(18, 8*n_rows))
            if n_rows == 1:
                axes = axes.reshape(1, -1)

            for idx, model in enumerate(models):
                row = idx // n_cols
                col = idx % n_cols
                ax = axes[row, col]

                cm = confusion_matrices[model]
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                           cbar_kws={'label': 'Count'}, square=True,
                           annot_kws={'fontsize': 12, 'fontweight': 'bold'})

                ax.set_title(f'{model}', fontsize=14, fontweight='bold', pad=10)
                ax.set_xlabel('Detected', fontsize=12, fontweight='bold')
                ax.set_ylabel('Expected', fontsize=12, fontweight='bold')
                ax.tick_params(axis='both', labelsize=11)

            # 隐藏多余的子图
            for idx in range(n_models, n_rows * n_cols):
                row = idx // n_cols
                col = idx % n_cols
                axes[row, col].axis('off')

            plt.tight_layout()
            fig2.savefig(output_path / '06_confusion_matrices_by_model.png', dpi=300, bbox_inches='tight')
            print(f"  [OK] Saved 06_confusion_matrices_by_model.png")
            plt.close(fig2)

        print()

    def generate_visualizations(self, output_dir, model_stats, violation_stats):
        """生成可视化图表"""
        print("Generating visualizations...")

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 1. 按模型的准确率柱状图
        fig1, ax1 = plt.subplots(figsize=(14, 8))
        models = list(model_stats.keys())
        accuracies = [model_stats[m]['accuracy'] for m in models]

        bars = ax1.bar(range(len(models)), accuracies, color='steelblue', alpha=0.8)
        ax1.set_xlabel('Model', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Accuracy (%)', fontsize=16, fontweight='bold')
        ax1.set_title('Detection Accuracy by Model', fontsize=18, fontweight='bold', pad=20)
        ax1.set_xticks(range(len(models)))
        ax1.set_xticklabels(models, rotation=0, ha='center', fontsize=14)
        ax1.grid(axis='y', alpha=0.3)
        ax1.axhline(y=np.mean(accuracies), color='r', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(accuracies):.1f}%')
        ax1.legend(fontsize=14)

        # 添加数值标签
        for i, (bar, acc) in enumerate(zip(bars, accuracies)):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{acc:.1f}%',
                    ha='center', va='bottom', fontsize=13, fontweight='bold')

        plt.tight_layout()
        fig1.savefig(output_path / '01_accuracy_by_model.png', dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved 01_accuracy_by_model.png")
        plt.close(fig1)

        # 2. 按违规类型的准确率柱状图
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        violations = list(violation_stats.keys())
        accuracies = [violation_stats[v]['accuracy'] for v in violations]

        bars = ax2.bar(violations, accuracies, color='lightcoral', alpha=0.8)
        ax2.set_xlabel('Violation Type', fontsize=16, fontweight='bold')
        ax2.set_ylabel('Accuracy (%)', fontsize=16, fontweight='bold')
        ax2.set_title('Detection Accuracy by Violation Type', fontsize=18, fontweight='bold', pad=20)
        ax2.tick_params(axis='both', labelsize=14)
        ax2.grid(axis='y', alpha=0.3)
        ax2.axhline(y=np.mean(accuracies), color='r', linestyle='--', linewidth=2,
                   label=f'Mean: {np.mean(accuracies):.1f}%')
        ax2.legend(fontsize=14)

        # 添加数值标签
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{acc:.1f}%',
                    ha='center', va='bottom', fontsize=13, fontweight='bold')

        plt.tight_layout()
        fig2.savefig(output_path / '02_accuracy_by_violation.png', dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved 02_accuracy_by_violation.png")
        plt.close(fig2)

        # 3. 热力图：模型 x 违规类型
        fig3, ax3 = plt.subplots(figsize=(12, 10))

        # 准备热力图数据
        models = sorted(self.results_df['model'].unique())
        violations = sorted(self.results_df['expected_violation'].unique())

        heatmap_data = []
        for model in models:
            row = []
            for violation in violations:
                subset = self.results_df[
                    (self.results_df['model'] == model) &
                    (self.results_df['expected_violation'] == violation)
                ]
                if len(subset) > 0:
                    acc = subset['violation_match'].mean() * 100
                    row.append(acc)
                else:
                    row.append(np.nan)
            heatmap_data.append(row)

        # 绘制热力图
        im = ax3.imshow(heatmap_data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

        # 设置坐标轴
        ax3.set_xticks(range(len(violations)))
        ax3.set_yticks(range(len(models)))
        ax3.set_xticklabels(violations, fontsize=14, fontweight='bold')
        ax3.set_yticklabels(models, fontsize=14, fontweight='bold')

        # 添加数值标签
        for i in range(len(models)):
            for j in range(len(violations)):
                if not np.isnan(heatmap_data[i][j]):
                    text = ax3.text(j, i, f'{heatmap_data[i][j]:.0f}',
                                   ha="center", va="center", color="black",
                                   fontsize=13, fontweight='bold')

        ax3.set_title('Detection Accuracy Heatmap: Model x Violation Type',
                     fontsize=18, fontweight='bold', pad=20)
        ax3.set_xlabel('Expected Violation Type', fontsize=16, fontweight='bold')
        ax3.set_ylabel('Model', fontsize=16, fontweight='bold')

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax3)
        cbar.set_label('Accuracy (%)', rotation=270, labelpad=25, fontsize=14, fontweight='bold')
        cbar.ax.tick_params(labelsize=12)

        plt.tight_layout()
        fig3.savefig(output_path / '03_heatmap_model_violation.png', dpi=300, bbox_inches='tight')
        print(f"  [OK] Saved 03_heatmap_model_violation.png")
        plt.close(fig3)

        print()

    def generate_report(self, output_dir, overall, model_stats, violation_stats, error_analysis):
        """生成文本报告"""
        output_path = Path(output_dir)
        report_path = output_path / 'literature_analysis_report.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("LITERATURE DETAILED_RESULTS_V5 ANALYSIS REPORT\n")
            f.write("Detection Accuracy Analysis (violation_match: true)\n")
            f.write("="*80 + "\n\n")

            # 总体统计
            f.write("## OVERALL STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Examples: {overall['total']}\n")
            f.write(f"Correct Detections: {overall['correct']}\n")
            f.write(f"Overall Accuracy: {overall['accuracy']:.2f}%\n")
            f.write(f"Total Errors: {error_analysis['total_errors']}\n")
            f.write(f"Error Rate: {error_analysis['total_errors']/overall['total']*100:.2f}%\n\n")

            # 按模型统计
            f.write("## ACCURACY BY MODEL\n")
            f.write("-"*80 + "\n")
            sorted_models = sorted(model_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)
            for model, stats in sorted_models:
                f.write(f"\n{model}:\n")
                f.write(f"  Total: {stats['total']}\n")
                f.write(f"  Correct: {stats['correct']}\n")
                f.write(f"  Accuracy: {stats['accuracy']:.2f}%\n")

            # 按违规类型统计
            f.write("\n## ACCURACY BY VIOLATION TYPE\n")
            f.write("-"*80 + "\n")
            sorted_violations = sorted(violation_stats.items(), key=lambda x: x[1]['accuracy'], reverse=True)
            for violation, stats in sorted_violations:
                f.write(f"\n{violation}:\n")
                f.write(f"  Total: {stats['total']}\n")
                f.write(f"  Correct: {stats['correct']}\n")
                f.write(f"  Accuracy: {stats['accuracy']:.2f}%\n")

            # 错误分析
            f.write("\n## ERROR ANALYSIS\n")
            f.write("-"*80 + "\n")
            f.write(f"\nTotal Errors: {error_analysis['total_errors']}\n")
            f.write("\nFailure Reasons:\n")
            for reason, count in error_analysis['failure_reasons'].items():
                pct = count / error_analysis['total_errors'] * 100
                f.write(f"  {reason}: {count} ({pct:.1f}%)\n")

            f.write("\nTop 10 Misclassifications:\n")
            sorted_misclass = sorted(error_analysis['misclassifications'].items(),
                                    key=lambda x: x[1], reverse=True)[:10]
            for (expected, detected), count in sorted_misclass:
                f.write(f"  {expected} -> {detected}: {count}\n")

            # 最佳和最差表现
            f.write("\n## BEST AND WORST PERFORMERS\n")
            f.write("-"*80 + "\n")

            # 最佳模型
            best_model = max(model_stats.items(), key=lambda x: x[1]['accuracy'])
            f.write(f"\nBest Model: {best_model[0]}\n")
            f.write(f"  Accuracy: {best_model[1]['accuracy']:.2f}%\n")

            # 最差模型
            worst_model = min(model_stats.items(), key=lambda x: x[1]['accuracy'])
            f.write(f"\nWorst Model: {worst_model[0]}\n")
            f.write(f"  Accuracy: {worst_model[1]['accuracy']:.2f}%\n")

            # 最容易检测的违规类型
            best_violation = max(violation_stats.items(), key=lambda x: x[1]['accuracy'])
            f.write(f"\nEasiest Violation to Detect: {best_violation[0]}\n")
            f.write(f"  Accuracy: {best_violation[1]['accuracy']:.2f}%\n")

            # 最难检测的违规类型
            worst_violation = min(violation_stats.items(), key=lambda x: x[1]['accuracy'])
            f.write(f"\nHardest Violation to Detect: {worst_violation[0]}\n")
            f.write(f"  Accuracy: {worst_violation[1]['accuracy']:.2f}%\n")

            f.write("\n" + "="*80 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*80 + "\n")

        print(f"  [OK] Saved report to {report_path}\n")

    def save_detailed_csv(self, output_dir):
        """保存详细的 CSV 数据"""
        output_path = Path(output_dir)

        # 保存处理后的数据
        csv_path = output_path / 'literature_detailed_results.csv'
        self.results_df.to_csv(csv_path, index=False, encoding='utf-8')
        print(f"  [OK] Saved detailed CSV to {csv_path}")

        # 保存原始数据为 JSON
        raw_json_path = output_path / 'literature_raw_data.json'
        with open(raw_json_path, 'w', encoding='utf-8') as f:
            json.dump(self.raw_data, f, indent=2, ensure_ascii=False)
        print(f"  [OK] Saved raw data JSON to {raw_json_path}\n")

    def run_analysis(self, output_dir):
        """运行完整分析"""
        # 加载数据
        self.load_data()

        # 提取 example 数据
        self.extract_examples()

        # 计算各种统计
        overall = self.calculate_overall_accuracy()
        model_stats = self.calculate_by_model()
        violation_stats = self.calculate_by_violation()
        error_analysis = self.analyze_errors()

        # 生成混淆矩阵
        confusion_matrices = self.generate_confusion_matrices()

        # 生成可视化
        self.generate_visualizations(output_dir, model_stats, violation_stats)
        self.visualize_confusion_matrices(output_dir, confusion_matrices)

        # 生成报告
        self.generate_report(output_dir, overall, model_stats, violation_stats, error_analysis)

        # 保存详细数据
        self.save_detailed_csv(output_dir)

        print("="*80)
        print("Analysis Complete!")
        print(f"All results saved to: {output_dir}")
        print("="*80)


def main():
    # 设置路径
    json_path = r"C:\Users\Jay\jcSOLID\literature\detailed_results_v5_updated.json"
    output_dir = r"C:\Users\Jay\jcSOLID\analysis\literature_analysis"

    # 创建分析器并运行
    analyzer = LiteratureAnalyzer(json_path)
    analyzer.run_analysis(output_dir)


if __name__ == "__main__":
    main()
