#!/usr/bin/env python3
"""
Create a visual index/gallery of all generated charts with thumbnails and descriptions.
"""

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from pathlib import Path
import numpy as np

def create_visual_index():
    """Create a visual index of all charts."""
    output_dir = Path('/Users/he/jcSOLID/analysis/analysis_output_qwen3_8b')

    # Define all charts with descriptions
    charts = [
        {
            'file': '00_SUMMARY_DASHBOARD.png',
            'title': 'Summary Dashboard',
            'desc': 'Comprehensive 9-panel overview'
        },
        {
            'file': '00_QUICK_REFERENCE.png',
            'title': 'Quick Reference',
            'desc': 'Fast comparison guide'
        },
        {
            'file': '01_qwen3_overall_accuracy.png',
            'title': 'qwen3-8b Accuracy',
            'desc': 'Overall performance: 46.67%'
        },
        {
            'file': '02_qwen3_accuracy_by_violation.png',
            'title': 'By Violation Type',
            'desc': 'ISP best: 77.08%, LSP worst: 6.25%'
        },
        {
            'file': '03_qwen3_accuracy_by_level.png',
            'title': 'By Difficulty',
            'desc': 'EASY: 73.75%, HARD: 18.75%'
        },
        {
            'file': '04_qwen3_accuracy_by_language.png',
            'title': 'By Language',
            'desc': 'Performance across languages'
        },
        {
            'file': '05_qwen3_confusion_matrix.png',
            'title': 'Confusion Matrix',
            'desc': 'qwen3-8b error patterns'
        },
        {
            'file': '06_qwen3_processing_time_dist.png',
            'title': 'Processing Time',
            'desc': 'Avg: 135.95s, Median: 112s'
        },
        {
            'file': '07_comparison_overall_accuracy.png',
            'title': 'Overall Comparison',
            'desc': 'langgraph: 55%, two_agent: 50%, diff_eval: 47%'
        },
        {
            'file': '08_comparison_by_violation.png',
            'title': 'Violation Comparison',
            'desc': 'Performance by violation type'
        },
        {
            'file': '09_comparison_by_level.png',
            'title': 'Difficulty Comparison',
            'desc': 'Performance by difficulty level'
        },
        {
            'file': '10_comparison_processing_time.png',
            'title': 'Time Comparison',
            'desc': 'langgraph: 1.54s, diff_eval: 135.95s'
        },
        {
            'file': '11_comparison_accuracy_vs_time.png',
            'title': 'Accuracy vs Time',
            'desc': 'Efficiency scatter plot'
        },
        {
            'file': '12_comparison_heatmaps.png',
            'title': 'Performance Heatmaps',
            'desc': 'Violation × Difficulty heatmaps'
        },
        {
            'file': '13_confusion_matrix_comparison.png',
            'title': 'Confusion Matrices',
            'desc': 'Side-by-side comparison (counts)'
        },
        {
            'file': '14_confusion_matrix_comparison_normalized.png',
            'title': 'Normalized Confusion',
            'desc': 'Side-by-side comparison (%)'
        },
        {
            'file': '15_fn_fp_comparison.png',
            'title': 'FN/FP Analysis',
            'desc': 'False negatives and positives'
        },
        {
            'file': '16_fn_fp_by_difficulty.png',
            'title': 'FN/FP by Difficulty',
            'desc': 'Error rates by difficulty'
        },
        {
            'file': '17_misclassification_matrix_diff_eval.png',
            'title': 'diff_eval Errors',
            'desc': 'Where FNs go: LSP→ISP (34)'
        },
        {
            'file': '17_misclassification_matrix_langgraph.png',
            'title': 'langgraph Errors',
            'desc': 'Where FNs go: DIP→SRP (118)'
        },
        {
            'file': '17_misclassification_matrix_two_agent.png',
            'title': 'two_agent Errors',
            'desc': 'Where FNs go: LSP→DIP (93)'
        }
    ]

    # Create figure with grid layout
    n_charts = len(charts)
    n_cols = 4
    n_rows = (n_charts + n_cols - 1) // n_cols

    fig = plt.figure(figsize=(20, n_rows * 4))

    for idx, chart in enumerate(charts):
        ax = plt.subplot(n_rows, n_cols, idx + 1)

        chart_path = output_dir / chart['file']

        if chart_path.exists():
            try:
                img = mpimg.imread(chart_path)
                ax.imshow(img)
                ax.axis('off')

                # Add title and description
                title_text = f"{idx+1:02d}. {chart['title']}"
                ax.set_title(title_text, fontsize=10, fontweight='bold', pad=5)

                # Add description at bottom
                ax.text(0.5, -0.05, chart['desc'],
                       transform=ax.transAxes,
                       ha='center', va='top',
                       fontsize=8, style='italic',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
            except Exception as e:
                ax.text(0.5, 0.5, f"Error loading\n{chart['file']}",
                       ha='center', va='center')
                ax.axis('off')
        else:
            ax.text(0.5, 0.5, f"File not found:\n{chart['file']}",
                   ha='center', va='center')
            ax.axis('off')

    plt.suptitle('qwen3-8b Analysis - Visual Index (21 Charts)',
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    output_file = output_dir / 'VISUAL_INDEX.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved visual index to: {output_file}")
    plt.close()

    # Create a categorized index
    create_categorized_index(output_dir, charts)

def create_categorized_index(output_dir, charts):
    """Create a categorized visual index."""
    categories = {
        'Overview': [0, 1],  # Dashboard and Quick Reference
        'qwen3-8b Analysis': [2, 3, 4, 5, 6, 7],
        'Three-Way Comparison': [8, 9, 10, 11, 12, 13],
        'Error Analysis': [14, 15, 16, 17, 18, 19, 20]
    }

    fig = plt.figure(figsize=(20, 16))

    row_offset = 0
    for cat_name, indices in categories.items():
        n_charts = len(indices)
        n_cols = min(4, n_charts)
        n_rows = (n_charts + n_cols - 1) // n_cols

        for i, idx in enumerate(indices):
            chart = charts[idx]
            ax = plt.subplot(8, 4, row_offset * 4 + i + 1)

            chart_path = output_dir / chart['file']

            if chart_path.exists():
                try:
                    img = mpimg.imread(chart_path)
                    ax.imshow(img)
                    ax.axis('off')

                    title_text = f"{idx+1:02d}. {chart['title']}"
                    ax.set_title(title_text, fontsize=9, fontweight='bold', pad=3)

                    ax.text(0.5, -0.03, chart['desc'],
                           transform=ax.transAxes,
                           ha='center', va='top',
                           fontsize=7, style='italic',
                           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.2))
                except:
                    ax.text(0.5, 0.5, "Error", ha='center', va='center')
                    ax.axis('off')

        # Add category label
        if row_offset == 0:
            y_pos = 0.98
        elif row_offset == 2:
            y_pos = 0.73
        elif row_offset == 4:
            y_pos = 0.48
        else:
            y_pos = 0.23

        fig.text(0.02, y_pos, cat_name, fontsize=14, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))

        row_offset += n_rows

    plt.suptitle('qwen3-8b Analysis - Categorized Index',
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 1, 0.99])

    output_file = output_dir / 'CATEGORIZED_INDEX.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved categorized index to: {output_file}")
    plt.close()

if __name__ == '__main__':
    print("Creating visual indices...")
    create_visual_index()
    print("\nVisual index creation complete!")
