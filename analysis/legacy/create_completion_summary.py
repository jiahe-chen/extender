#!/usr/bin/env python3
"""
Create a final completion summary visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def create_completion_summary():
    """Create a visual completion summary."""

    fig = plt.figure(figsize=(20, 14))

    # Title
    fig.text(0.5, 0.97, '🎉 qwen3-8b 分析项目完成总结 🎉',
             ha='center', fontsize=24, fontweight='bold',
             bbox=dict(boxstyle='round,pad=1', facecolor='lightgreen', alpha=0.3))

    # Section 1: Project Overview (Top)
    ax1 = plt.subplot(4, 3, (1, 3))
    ax1.axis('off')

    overview_text = """
    📊 项目概览

    ✅ 任务状态: 已完成
    📅 完成日期: 2026-01-27
    ⏱️  总用时: ~2小时
    📦 交付成果: 32个文件 (5.6 MB)

    🎯 分析目标:
    • 全面评估 qwen3-8b (diff_eval) 的性能
    • 与 two_agent 和 langgraph 进行横向对比
    • 识别优势、劣势和改进方向
    • 提供可操作的改进建议
    """

    ax1.text(0.05, 0.95, overview_text, transform=ax1.transAxes,
            fontsize=11, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    # Section 2: Deliverables Breakdown (Middle Left)
    ax2 = plt.subplot(4, 3, 4)
    ax2.axis('off')

    deliverables = {
        '可视化图表': 23,
        'Markdown文档': 6,
        '文本报告': 2,
        'CSV数据': 1
    }

    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
    wedges, texts, autotexts = ax2.pie(deliverables.values(), labels=deliverables.keys(),
                                        autopct='%d', colors=colors,
                                        startangle=90, textprops={'fontsize': 10})

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(12)

    ax2.set_title('📦 交付成果分布', fontsize=13, fontweight='bold', pad=20)

    # Section 3: Analysis Coverage (Middle Center)
    ax3 = plt.subplot(4, 3, 5)
    ax3.axis('off')

    coverage_text = """
    📊 分析覆盖范围

    ✅ 总体准确率对比
    ✅ 按违规类型分析 (5种)
    ✅ 按难度级别分析 (3种)
    ✅ 按编程语言分析 (5种)
    ✅ 处理时间分析
    ✅ 混淆矩阵分析
    ✅ False Negative 分析
    ✅ False Positive 分析
    ✅ 误分类模式分析
    ✅ 性能下降趋势分析

    总计: 10个分析维度
    """

    ax3.text(0.05, 0.95, coverage_text, transform=ax3.transAxes,
            fontsize=9, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))

    # Section 4: Key Findings (Middle Right)
    ax4 = plt.subplot(4, 3, 6)
    ax4.axis('off')

    findings_text = """
    🎯 核心发现

    整体排名:
    🥇 langgraph:  55.08%
    🥈 two_agent:  49.58%
    🥉 diff_eval:  46.67%

    diff_eval 优势:
    ✅ ISP: 77.08% (第1)
    ✅ EASY: 73.75% (第1)
    ✅ DIP: 47.92% (第1)

    diff_eval 劣势:
    ❌ LSP: 6.25% (灾难)
    ❌ 速度: 135.95s (88倍慢)
    ❌ HARD: 18.75% (极差)
    """

    ax4.text(0.05, 0.95, findings_text, transform=ax4.transAxes,
            fontsize=9, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))

    # Section 5: Performance Comparison Bar Chart (Bottom Left)
    ax5 = plt.subplot(4, 3, 7)

    agents = ['langgraph', 'two_agent', 'diff_eval']
    accuracy = [55.08, 49.58, 46.67]
    colors_bar = ['lightgreen', 'coral', 'steelblue']

    bars = ax5.barh(agents, accuracy, color=colors_bar, alpha=0.7, edgecolor='black', linewidth=2)
    ax5.set_xlabel('准确率 (%)', fontsize=11, fontweight='bold')
    ax5.set_title('📊 准确率对比', fontsize=12, fontweight='bold')
    ax5.set_xlim(0, 100)
    ax5.grid(axis='x', alpha=0.3)

    for i, (bar, val) in enumerate(zip(bars, accuracy)):
        ax5.text(val + 1, i, f'{val:.2f}%', va='center', fontsize=10, fontweight='bold')

    # Section 6: Processing Time Comparison (Bottom Center)
    ax6 = plt.subplot(4, 3, 8)

    times = [1.54, 8.75, 135.95]

    bars = ax6.barh(agents, times, color=colors_bar, alpha=0.7, edgecolor='black', linewidth=2)
    ax6.set_xlabel('处理时间 (秒)', fontsize=11, fontweight='bold')
    ax6.set_title('⏱️  处理时间对比', fontsize=12, fontweight='bold')
    ax6.set_xscale('log')
    ax6.grid(axis='x', alpha=0.3)

    for i, (bar, val) in enumerate(zip(bars, times)):
        ax6.text(val * 1.2, i, f'{val:.2f}s', va='center', fontsize=10, fontweight='bold')

    # Section 7: Violation Type Performance (Bottom Right)
    ax7 = plt.subplot(4, 3, 9)

    violations = ['ISP', 'OCP', 'SRP', 'DIP', 'LSP']
    diff_eval_scores = [77.08, 54.17, 47.92, 47.92, 6.25]

    bars = ax7.bar(violations, diff_eval_scores, color='steelblue', alpha=0.7, edgecolor='black', linewidth=2)
    ax7.set_ylabel('准确率 (%)', fontsize=11, fontweight='bold')
    ax7.set_title('📈 diff_eval 按违规类型', fontsize=12, fontweight='bold')
    ax7.set_ylim(0, 100)
    ax7.grid(axis='y', alpha=0.3)

    # Color code bars
    for i, (bar, val) in enumerate(zip(bars, diff_eval_scores)):
        if val > 70:
            bar.set_color('green')
        elif val > 40:
            bar.set_color('orange')
        else:
            bar.set_color('red')

        ax7.text(i, val + 2, f'{val:.1f}%', ha='center', fontsize=9, fontweight='bold')

    # Section 8: File Structure (Bottom)
    ax8 = plt.subplot(4, 3, (10, 12))
    ax8.axis('off')

    structure_text = """
    📁 文件结构

    analysis_output_qwen3_8b/
    │
    ├── 🎯 核心文件 (必看)
    │   ├── 00_SUMMARY_DASHBOARD.png          综合仪表板 (633KB)
    │   ├── 00_QUICK_REFERENCE.png            快速参考指南 (626KB)
    │   ├── VISUAL_INDEX.png                  可视化索引 (843KB)
    │   ├── CATEGORIZED_INDEX.png             分类索引 (513KB)
    │   ├── COMPLETE_ANALYSIS_REPORT.md       完整中文报告 (16KB)
    │   ├── EXECUTIVE_SUMMARY.md              执行总结 (11KB)
    │   └── COMPLETION_REPORT.md              完成报告 (11KB)
    │
    ├── 📊 可视化图表 (23个)
    │   ├── 01-06_qwen3_*.png                 qwen3-8b 单独分析 (6个)
    │   ├── 07-12_comparison_*.png            三方对比分析 (6个)
    │   ├── 13-14_confusion_matrix_*.png      混淆矩阵对比 (2个)
    │   └── 15-17_fn_fp_*.png                 FN/FP 错误分析 (5个)
    │
    ├── 📄 文档报告 (6个)
    │   ├── README.md                         索引导航
    │   ├── KEY_FINDINGS.md                   关键发现
    │   ├── FN_FP_ANALYSIS_SUMMARY.md         FN/FP 分析总结
    │   ├── qwen3_8b_comprehensive_report.txt 文本报告
    │   └── fn_fp_analysis_report.txt         详细 FN/FP 报告
    │
    └── 📊 数据文件 (1个)
        └── qwen3_8b_detailed_results.csv     原始结果数据 (240条)

    总计: 32个文件, 5.6 MB
    """

    ax8.text(0.05, 0.95, structure_text, transform=ax8.transAxes,
            fontsize=8, verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))

    # Footer with recommendations
    footer_text = """
    💡 推荐使用: langgraph (最佳准确率和速度) | 🔧 紧急修复: LSP检测 (6.25%) 和处理速度 (135.95s) | 🌟 集成方案: 结合三种方法的优势
    """

    fig.text(0.5, 0.02, footer_text, ha='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.5))

    plt.tight_layout(rect=[0, 0.03, 1, 0.96])

    # Save
    output_file = '/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b/00_COMPLETION_SUMMARY.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved completion summary to: {output_file}")
    plt.close()

if __name__ == '__main__':
    print("Creating completion summary...")
    create_completion_summary()
    print("\nCompletion summary created successfully!")
