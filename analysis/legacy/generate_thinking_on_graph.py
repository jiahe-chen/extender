#!/usr/bin/env python3
"""
SOLID Principles Benchmark Analysis - Thinking On vs Legacy Comparison
Analyzes API call success rate and runtime performance
"""

import json
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Set style for professional visualizations (matching analysis_solid_benchmark.py)
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['figure.dpi'] = 150

# Color palette - professional, matching analysis_solid_benchmark.py
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#4CAF50',
    'error': '#E74C3C',
    'neutral': '#7F8C8D'
}

# Mode colors
MODE_COLORS = {
    'thinking_on': '#E74C3C',  # Red for thinking_on
    'legacy': '#2E86AB'         # Blue for legacy
}


def load_results(file_path):
    """Load results from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def extract_metrics(data):
    """Extract API success rate and runtime from results."""
    all_results = []

    for violation_type, violation_data in data.get('by_violation_type', {}).items():
        results = violation_data.get('results', [])
        all_results.extend(results)

    if not all_results:
        return None, None, 0

    # Calculate API call success rate
    successful_calls = sum(1 for r in all_results if r.get('api_call_success', False))
    total_calls = len(all_results)
    success_rate = (successful_calls / total_calls) * 100 if total_calls > 0 else 0

    # Calculate average runtime (only for successful calls with processing time > 0)
    runtimes = [r.get('processing_time_seconds', 0) for r in all_results
                if r.get('api_call_success', False) and r.get('processing_time_seconds', 0) > 0]
    avg_runtime = np.mean(runtimes) if runtimes else 0

    return success_rate, avg_runtime, total_calls


def load_model_data(base_path, mode_name):
    """Load all model data from a directory."""
    models_data = {}

    for model_dir in sorted(base_path.iterdir()):
        if model_dir.is_dir():
            json_files = list(model_dir.glob('*.json'))
            if json_files:
                data = load_results(json_files[0])
                model_name = data.get('configuration', {}).get('model', model_dir.name)
                # Normalize model name to just base name (e.g., "qwen3:8b" -> "qwen3-8b")
                model_key = model_name.replace(':', '-').lower()

                success_rate, avg_runtime, total = extract_metrics(data)

                if total > 0:
                    models_data[model_key] = {
                        'name': model_name,
                        'success_rate': success_rate,
                        'avg_runtime': avg_runtime,
                        'total': total
                    }

    return models_data


def plot_success_rate_comparison(ax, model_labels, thinking_success, legacy_success, x, bar_width):
    """Plot API call success rate comparison."""
    bars_thinking = ax.bar(x - bar_width/2, thinking_success, bar_width,
                           label='thinking_on', color=MODE_COLORS['thinking_on'],
                           edgecolor='black', linewidth=0.8, alpha=0.9)
    bars_legacy = ax.bar(x + bar_width/2, legacy_success, bar_width,
                         label='legacy', color=MODE_COLORS['legacy'],
                         edgecolor='black', linewidth=0.8, alpha=0.9)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontweight='bold')
    ax.set_title('API Call Success Rate: thinking_on vs legacy', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=10)
    ax.set_ylim(0, 115)
    ax.legend(loc='upper right', framealpha=0.9)
    ax.axhline(y=100, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)

    # Add value labels on bars
    for bar in bars_thinking:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color=MODE_COLORS['thinking_on'])

    for bar in bars_legacy:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color=MODE_COLORS['legacy'])


def plot_runtime_comparison(ax, model_labels, thinking_runtime, legacy_runtime, x, bar_width):
    """Plot average runtime comparison."""
    bars_thinking = ax.bar(x - bar_width/2, thinking_runtime, bar_width,
                           label='thinking_on', color=MODE_COLORS['thinking_on'],
                           edgecolor='black', linewidth=0.8, alpha=0.9)
    bars_legacy = ax.bar(x + bar_width/2, legacy_runtime, bar_width,
                         label='legacy', color=MODE_COLORS['legacy'],
                         edgecolor='black', linewidth=0.8, alpha=0.9)

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Average Runtime (seconds)', fontweight='bold')
    ax.set_title('Average Processing Time: thinking_on vs legacy', fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(model_labels, fontsize=10)
    ax.legend(loc='upper right', framealpha=0.9)

    # Add value labels on bars
    for bar in bars_thinking:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color=MODE_COLORS['thinking_on'])

    for bar in bars_legacy:
        height = bar.get_height()
        ax.annotate(f'{height:.1f}s',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9, fontweight='bold',
                    color=MODE_COLORS['legacy'])


def main():
    # Define paths
    thinking_on_path = Path('/Users/he/jcSOLID/result/local/single_agent/thinking_on')
    legacy_path = Path('/Users/he/jcSOLID/result/local/single_agent/legacy')

    # Load data for both modes
    thinking_on_data = load_model_data(thinking_on_path, 'thinking_on')
    legacy_data = load_model_data(legacy_path, 'legacy')

    print("=" * 60)
    print("THINKING_ON vs LEGACY Comparison")
    print("=" * 60)

    # Find common models
    common_models = sorted(set(thinking_on_data.keys()) & set(legacy_data.keys()))

    if not common_models:
        print("No common models found between thinking_on and legacy!")
        print(f"Thinking_on models: {list(thinking_on_data.keys())}")
        print(f"Legacy models: {list(legacy_data.keys())}")
        return

    print(f"\nCommon models for comparison: {common_models}")

    # Prepare data for plotting
    model_labels = []
    thinking_success = []
    legacy_success = []
    thinking_runtime = []
    legacy_runtime = []

    for model_key in common_models:
        t_data = thinking_on_data[model_key]
        l_data = legacy_data[model_key]

        # Create clean display name
        display_name = t_data['name'].replace(':', '-')
        model_labels.append(display_name)

        thinking_success.append(t_data['success_rate'])
        legacy_success.append(l_data['success_rate'])
        thinking_runtime.append(t_data['avg_runtime'])
        legacy_runtime.append(l_data['avg_runtime'])

        print(f"\n{display_name}:")
        print(f"  thinking_on: {t_data['success_rate']:.1f}% success, {t_data['avg_runtime']:.1f}s avg runtime (n={t_data['total']})")
        print(f"  legacy:      {l_data['success_rate']:.1f}% success, {l_data['avg_runtime']:.1f}s avg runtime (n={l_data['total']})")

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    x = np.arange(len(model_labels))
    bar_width = 0.35

    # Plot success rate comparison
    plot_success_rate_comparison(ax1, model_labels, thinking_success, legacy_success, x, bar_width)

    # Plot runtime comparison
    plot_runtime_comparison(ax2, model_labels, thinking_runtime, legacy_runtime, x, bar_width)

    plt.tight_layout()

    # Save the figure
    output_path = '/Users/he/jcSOLID/analysis_output/thinking_on_vs_legacy_metrics.png'
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    print(f"\n{'=' * 60}")
    print(f"Graph saved to: {output_path}")
    plt.close()


if __name__ == '__main__':
    main()
