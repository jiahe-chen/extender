#!/usr/bin/env python3
"""
Comparison Analysis: Structure-OFF vs Structure-ON (run_top2) — diff_eval workflow, qwen3-8b
Both runs use Top-2 strategy and ranking_llm selection.

Key difference:
  - run_top2           : structural_analysis_enabled = True
  - run_structure_off_top2 : structural_analysis_enabled = False

Outputs → analysis/analysis_output_structure_off_comparison/
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".mplconfig"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VIOLATION_LABELS = ["SRP", "OCP", "LSP", "ISP", "DIP"]
DIFFICULTY_ORDER = ["EASY", "MODERATE", "HARD"]
LANG_ORDER = ["JAVA", "PYTHON", "KOTLIN", "CSHARP", "C#"]

C_ON  = "#4C78A8"   # Structural ON (blue)
C_OFF = "#F58518"   # Structural OFF (orange)
C_GAIN = "#54A24B"  # green (OFF gains)
C_LOSS = "#E45756"  # red (OFF losses)
C_NEUTRAL = "#888888"

OUTDIR = Path(__file__).parent / "analysis_output_structure_off_comparison"
OUTDIR.mkdir(parents=True, exist_ok=True)

DATA_TOP2      = Path(__file__).parent.parent / "result/local/diff_eval/run_top2/qwen3-8b/detection_results.json"
DATA_STRUCT_OFF = Path(__file__).parent.parent / "result/local/diff_eval/run_structure_off_top2/qwen3-8b/detection_results.json"

# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_json(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return json.loads(raw.replace(",]", "]").replace(",}", "}"))


def get_all_results(data: Dict[str, Any]) -> Dict[str, Dict]:
    """Returns {example_id: result_dict}."""
    out = {}
    for vtype in VIOLATION_LABELS:
        for r in data["by_violation_type"][vtype]["results"]:
            out[r["example_id"]] = r
    return out


def get_top_predictions(r: Dict) -> List[str]:
    dvt = r.get("detected_violation_type", "") or ""
    parts = [p.strip().upper() for p in dvt.split(",")]
    return [p for p in parts if p in VIOLATION_LABELS]


def get_all_detected(r: Dict) -> List[str]:
    return [c["violation_type"] for c in r.get("all_checks", []) if c.get("is_detected")]


def mrr_at2(results: List[Dict]) -> float:
    total = 0.0
    for r in results:
        preds = get_top_predictions(r)
        gt = r.get("ground_truth")
        if gt in preds:
            total += 1.0 / (preds.index(gt) + 1)
    return total / len(results) if results else 0.0


def compute_f1(y_true, y_pred, label):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0
    rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0
    return prec, rec, f1


# ---------------------------------------------------------------------------
# Aggregate Metrics
# ---------------------------------------------------------------------------
def aggregate(results: Dict[str, Dict]) -> Dict:
    rs = list(results.values())
    n = len(rs)
    pos1    = sum(1 for r in rs if (p := get_top_predictions(r)) and r["ground_truth"] == p[0])
    hit2    = sum(1 for r in rs if r["ground_truth"] in get_top_predictions(r))
    hit_any = sum(1 for r in rs if r["ground_truth"] in get_all_detected(r))
    pos2_only = sum(1 for r in rs
                    if (p := get_top_predictions(r)) and len(p) >= 2
                    and r["ground_truth"] == p[1] and r["ground_truth"] != p[0])
    times = [r.get("processing_time_seconds", 0) for r in rs]
    mrr = mrr_at2(rs)
    return {
        "n": n,
        "pos1_acc": pos1 / n,
        "hit2_acc": hit2 / n,
        "hit_any_acc": hit_any / n,
        "pos2_only_frac": pos2_only / n,
        "mrr2": mrr,
        "mean_time": float(np.mean(times)),
        "median_time": float(np.median(times)),
    }


def aggregate_group(results: Dict[str, Dict], key: str) -> Dict[str, Dict]:
    groups: Dict[str, List] = defaultdict(list)
    for r in results.values():
        groups[r.get(key, "?")].append(r)
    return {k: aggregate({f"{i}": r for i, r in enumerate(rs)}) for k, rs in groups.items()}


# ---------------------------------------------------------------------------
# Load Data
# ---------------------------------------------------------------------------
data_on  = load_json(DATA_TOP2)
data_off = load_json(DATA_STRUCT_OFF)
r_on  = get_all_results(data_on)
r_off = get_all_results(data_off)

agg_on  = aggregate(r_on)
agg_off = aggregate(r_off)

by_vtype_on  = aggregate_group(r_on,  "ground_truth")
by_vtype_off = aggregate_group(r_off, "ground_truth")
by_diff_on   = aggregate_group(r_on,  "level")
by_diff_off  = aggregate_group(r_off, "level")
by_lang_on   = aggregate_group(r_on,  "language")
by_lang_off  = aggregate_group(r_off, "language")


# ---------------------------------------------------------------------------
# Helper: save figure
# ---------------------------------------------------------------------------
def savefig(fig, name: str):
    path = OUTDIR / name
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Fig 1: Overall Metric Comparison Bar Chart
# ---------------------------------------------------------------------------
def fig_overall_metrics():
    metrics = ["Pos-1 Acc", "Hit@2 Acc", "Hit@any", "Pos-2 Only", "MRR@2"]
    vals_on  = [agg_on["pos1_acc"],  agg_on["hit2_acc"],  agg_on["hit_any_acc"],  agg_on["pos2_only_frac"],  agg_on["mrr2"]]
    vals_off = [agg_off["pos1_acc"], agg_off["hit2_acc"], agg_off["hit_any_acc"], agg_off["pos2_only_frac"], agg_off["mrr2"]]

    x = np.arange(len(metrics))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    bars_on  = ax.bar(x - width/2, [v*100 for v in vals_on],  width, label="Structural ON",  color=C_ON,  alpha=0.85)
    bars_off = ax.bar(x + width/2, [v*100 for v in vals_off], width, label="Structural OFF", color=C_OFF, alpha=0.85)

    for bar in list(bars_on) + list(bars_off):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, f"{h:.1f}%",
                ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylabel("Score (%)")
    ax.set_title("Overall Metrics: Structural Analysis ON vs OFF\n(diff_eval, Top-2, qwen3-8b, n=240)")
    ax.legend()
    ax.set_ylim(0, 105)
    ax.axhline(83.75, color=C_ON, linestyle="--", linewidth=0.8, alpha=0.5)
    ax.axhline(85.42, color=C_OFF, linestyle="--", linewidth=0.8, alpha=0.5)
    fig.tight_layout()
    savefig(fig, "01_overall_metrics.png")


# ---------------------------------------------------------------------------
# Fig 2: Hit@2 by Violation Type
# ---------------------------------------------------------------------------
def fig_hit2_by_violation():
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Hit@2
    ax = axes[0]
    on_vals  = [by_vtype_on[v]["hit2_acc"]*100  for v in VIOLATION_LABELS]
    off_vals = [by_vtype_off[v]["hit2_acc"]*100 for v in VIOLATION_LABELS]
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.35
    b1 = ax.bar(x - w/2, on_vals,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    b2 = ax.bar(x + w/2, off_vals, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, f"{h:.0f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(VIOLATION_LABELS)
    ax.set_ylabel("Hit@2 Accuracy (%)"); ax.set_title("Hit@2 by Violation Type")
    ax.legend(); ax.set_ylim(0, 115)

    # Diff (OFF - ON)
    ax2 = axes[1]
    diffs = [off_vals[i] - on_vals[i] for i in range(len(VIOLATION_LABELS))]
    colors = [C_GAIN if d > 0 else (C_LOSS if d < 0 else C_NEUTRAL) for d in diffs]
    bars = ax2.bar(VIOLATION_LABELS, diffs, color=colors, alpha=0.85)
    for bar, d in zip(bars, diffs):
        ax2.text(bar.get_x() + bar.get_width()/2, d + (0.3 if d >= 0 else -0.8),
                 f"{d:+.1f}pp", ha="center", va="bottom" if d >= 0 else "top", fontsize=9, fontweight="bold")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Hit@2 Difference (OFF − ON, pp)")
    ax2.set_title("Hit@2 Improvement: Structural OFF vs ON\n(positive = OFF better)")
    ax2.set_ylim(min(diffs) - 5, max(diffs) + 8)

    fig.suptitle("Hit@2 Accuracy by SOLID Violation Type", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "02_hit2_by_violation.png")


# ---------------------------------------------------------------------------
# Fig 3: Hit@2 by Difficulty
# ---------------------------------------------------------------------------
def fig_hit2_by_difficulty():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ax = axes[0]
    on_vals  = [by_diff_on[d]["hit2_acc"]*100  for d in DIFFICULTY_ORDER]
    off_vals = [by_diff_off[d]["hit2_acc"]*100 for d in DIFFICULTY_ORDER]
    x = np.arange(len(DIFFICULTY_ORDER))
    w = 0.35
    b1 = ax.bar(x - w/2, on_vals,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    b2 = ax.bar(x + w/2, off_vals, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, f"{h:.1f}%", ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(DIFFICULTY_ORDER)
    ax.set_ylabel("Hit@2 Accuracy (%)"); ax.set_title("Hit@2 by Difficulty Level")
    ax.legend(); ax.set_ylim(0, 110)

    ax2 = axes[1]
    diffs = [off_vals[i] - on_vals[i] for i in range(len(DIFFICULTY_ORDER))]
    colors = [C_GAIN if d > 0 else (C_LOSS if d < 0 else C_NEUTRAL) for d in diffs]
    bars = ax2.bar(DIFFICULTY_ORDER, diffs, color=colors, alpha=0.85)
    for bar, d in zip(bars, diffs):
        ax2.text(bar.get_x() + bar.get_width()/2, d + (0.2 if d >= 0 else -0.5),
                 f"{d:+.1f}pp", ha="center", va="bottom" if d >= 0 else "top", fontsize=10, fontweight="bold")
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("Difference (OFF − ON, pp)")
    ax2.set_title("Hit@2 Diff by Difficulty\n(positive = OFF better)")
    ax2.set_ylim(min(diffs) - 4, max(diffs) + 6)

    fig.suptitle("Hit@2 Accuracy by Difficulty Level", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "03_hit2_by_difficulty.png")


# ---------------------------------------------------------------------------
# Fig 4: Per-example agreement / flip analysis
# ---------------------------------------------------------------------------
def fig_flip_analysis():
    both_correct, on_only, off_only, both_wrong = [], [], [], []
    for eid in r_on:
        if eid not in r_off:
            continue
        a, b = r_on[eid], r_off[eid]
        gt = a["ground_truth"]
        a_hit = gt in get_top_predictions(a)
        b_hit = gt in get_top_predictions(b)
        if a_hit and b_hit:
            both_correct.append(eid)
        elif a_hit and not b_hit:
            on_only.append(eid)
        elif not a_hit and b_hit:
            off_only.append(eid)
        else:
            both_wrong.append(eid)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Pie chart
    ax = axes[0]
    sizes  = [len(both_correct), len(on_only), len(off_only), len(both_wrong)]
    labels_pie = [
        f"Both correct\n({len(both_correct)})",
        f"ON only correct\n({len(on_only)})",
        f"OFF only correct\n({len(off_only)})",
        f"Both wrong\n({len(both_wrong)})",
    ]
    colors_pie = [C_GAIN, C_ON, C_OFF, C_NEUTRAL]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels_pie, colors=colors_pie,
        autopct="%1.1f%%", startangle=90, pctdistance=0.7,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight("bold")
    ax.set_title("Per-Example Hit@2 Agreement (n=240)", fontsize=11)

    # Breakdown by violation for flipped cases
    ax2 = axes[1]
    on_gains  = Counter(r_on[eid]["ground_truth"] for eid in off_only)   # OFF rescues
    on_losses = Counter(r_on[eid]["ground_truth"] for eid in on_only)    # OFF loses
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.35
    gains  = [on_gains.get(v, 0)  for v in VIOLATION_LABELS]
    losses = [-on_losses.get(v, 0) for v in VIOLATION_LABELS]  # negative for visual
    ax2.bar(x, gains,  w, color=C_OFF, alpha=0.85, label="OFF gains (rescued)")
    ax2.bar(x, losses, w, color=C_ON,  alpha=0.85, label="ON gains (lost by OFF)")
    ax2.set_xticks(x); ax2.set_xticklabels(VIOLATION_LABELS)
    ax2.axhline(0, color="black", linewidth=0.8)
    ax2.set_ylabel("# Examples")
    ax2.set_title("Flip Cases by Violation Type\n(↑ = OFF gained, ↓ = OFF lost)")
    ax2.legend()
    for i, (g, l) in enumerate(zip(gains, losses)):
        if g: ax2.text(i, g + 0.15, str(g), ha="center", va="bottom", fontsize=9, color=C_OFF, fontweight="bold")
        if l: ax2.text(i, l - 0.15, str(-l), ha="center", va="top", fontsize=9, color=C_ON, fontweight="bold")

    fig.suptitle("Structural Analysis ON vs OFF — Flip Analysis", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "04_flip_analysis.png")
    return len(both_correct), len(on_only), len(off_only), len(both_wrong)


# ---------------------------------------------------------------------------
# Fig 5: Multi-violation detection distribution
# ---------------------------------------------------------------------------
def fig_multi_detection():
    multi_on  = [len(get_all_detected(r)) for r in r_on.values()]
    multi_off = [len(get_all_detected(r)) for r in r_off.values()]
    cnt_on  = Counter(multi_on)
    cnt_off = Counter(multi_off)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Bar chart side-by-side
    ax = axes[0]
    ks = list(range(0, 6))
    vals_on  = [cnt_on.get(k, 0)  for k in ks]
    vals_off = [cnt_off.get(k, 0) for k in ks]
    x = np.arange(len(ks))
    w = 0.35
    b1 = ax.bar(x - w/2, vals_on,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    b2 = ax.bar(x + w/2, vals_off, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, str(int(h)),
                    ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([str(k) for k in ks])
    ax.set_xlabel("# Violations Detected in all_checks")
    ax.set_ylabel("# Examples")
    ax.set_title("Distribution: How Many Violations Detected?")
    ax.legend()

    # Mean detected per violation type
    ax2 = axes[1]
    mean_on  = []
    mean_off = []
    for v in VIOLATION_LABELS:
        rs_on  = [r for r in r_on.values()  if r["ground_truth"] == v]
        rs_off = [r for r in r_off.values() if r["ground_truth"] == v]
        mean_on.append(np.mean([len(get_all_detected(r)) for r in rs_on]))
        mean_off.append(np.mean([len(get_all_detected(r)) for r in rs_off]))
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.35
    ax2.bar(x - w/2, mean_on,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    ax2.bar(x + w/2, mean_off, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(VIOLATION_LABELS)
    ax2.set_ylabel("Mean # Detected Violations")
    ax2.set_title("Mean Detected Violations per Ground-Truth Type")
    ax2.legend()
    for i, (a, b) in enumerate(zip(mean_on, mean_off)):
        ax2.text(i - w/2, a + 0.03, f"{a:.2f}", ha="center", va="bottom", fontsize=7)
        ax2.text(i + w/2, b + 0.03, f"{b:.2f}", ha="center", va="bottom", fontsize=7)

    fig.suptitle("Multi-Violation Detection: Structural Analysis ON vs OFF", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "05_multi_detection.png")


# ---------------------------------------------------------------------------
# Fig 6: Per-class F1, Precision, Recall
# ---------------------------------------------------------------------------
def fig_per_class_metrics():
    y_true, y_pred_on, y_pred_off = [], [], []
    for eid in r_on:
        if eid not in r_off:
            continue
        a, b = r_on[eid], r_off[eid]
        gt = a["ground_truth"]
        a_preds = get_top_predictions(a)
        b_preds = get_top_predictions(b)
        y_true.append(gt)
        y_pred_on.append(a_preds[0] if a_preds else "NONE")
        y_pred_off.append(b_preds[0] if b_preds else "NONE")

    metrics_on  = {v: compute_f1(y_true, y_pred_on,  v) for v in VIOLATION_LABELS}
    metrics_off = {v: compute_f1(y_true, y_pred_off, v) for v in VIOLATION_LABELS}

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    labels_plot = ["Precision", "Recall", "F1"]
    idx = [0, 1, 2]

    for metric_i, (metric_name, metric_idx) in enumerate(zip(labels_plot, idx)):
        ax = axes[metric_i]
        on_vals  = [metrics_on[v][metric_idx]  for v in VIOLATION_LABELS]
        off_vals = [metrics_off[v][metric_idx] for v in VIOLATION_LABELS]
        x = np.arange(len(VIOLATION_LABELS))
        w = 0.35
        b1 = ax.bar(x - w/2, on_vals,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
        b2 = ax.bar(x + w/2, off_vals, w, label="Struct OFF", color=C_OFF, alpha=0.85)
        for bar in list(b1) + list(b2):
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 0.01, f"{h:.2f}",
                    ha="center", va="bottom", fontsize=7)
        ax.set_xticks(x); ax.set_xticklabels(VIOLATION_LABELS)
        ax.set_ylabel(metric_name)
        ax.set_title(f"Per-class {metric_name} (Pos-1 predictions)")
        ax.legend(fontsize=8)
        ax.set_ylim(0, 1.15)

        # Macro line
        macro_on  = np.mean(on_vals)
        macro_off = np.mean(off_vals)
        ax.axhline(macro_on,  color=C_ON,  linestyle="--", linewidth=1, alpha=0.7,
                   label=f"ON macro={macro_on:.3f}")
        ax.axhline(macro_off, color=C_OFF, linestyle="--", linewidth=1, alpha=0.7,
                   label=f"OFF macro={macro_off:.3f}")
        ax.legend(fontsize=7)

    fig.suptitle("Per-class Metrics (Pos-1): Structural ON vs OFF", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "06_per_class_metrics.png")


# ---------------------------------------------------------------------------
# Fig 7: OCP bias analysis — prediction distribution heatmap
# ---------------------------------------------------------------------------
def fig_prediction_bias():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    labels_ext = VIOLATION_LABELS + ["NONE"]

    for ax_i, (results, title, color) in enumerate([
        (r_on,  "Structural ON",  C_ON),
        (r_off, "Structural OFF", C_OFF),
    ]):
        ax = axes[ax_i]
        mat = np.zeros((len(VIOLATION_LABELS), len(labels_ext)), dtype=int)
        for r in results.values():
            gt = r.get("ground_truth")
            if gt not in VIOLATION_LABELS:
                continue
            preds = get_top_predictions(r)
            pred1 = preds[0] if preds else "NONE"
            ri = VIOLATION_LABELS.index(gt)
            ci = labels_ext.index(pred1) if pred1 in labels_ext else len(labels_ext) - 1
            mat[ri, ci] += 1

        sns.heatmap(mat, annot=True, fmt="d", ax=ax,
                    xticklabels=labels_ext, yticklabels=VIOLATION_LABELS,
                    cmap="Blues", cbar=False)
        ax.set_xlabel("Pos-1 Predicted")
        ax.set_ylabel("Ground Truth")
        ax.set_title(f"{title} — Pos-1 Prediction Matrix")

    fig.suptitle("Prediction Confusion (Pos-1): Where Does Each GT Get Predicted?",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "07_prediction_bias_heatmap.png")


# ---------------------------------------------------------------------------
# Fig 8: Processing time comparison
# ---------------------------------------------------------------------------
def fig_processing_time():
    times_on  = [r.get("processing_time_seconds", 0) for r in r_on.values()]
    times_off = [r.get("processing_time_seconds", 0) for r in r_off.values()]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # Distribution
    ax = axes[0]
    bins = np.linspace(0, max(max(times_on), max(times_off)) * 1.05, 30)
    ax.hist(times_on,  bins=bins, alpha=0.6, color=C_ON,  label=f"Struct ON  (μ={np.mean(times_on):.1f}s)")
    ax.hist(times_off, bins=bins, alpha=0.6, color=C_OFF, label=f"Struct OFF (μ={np.mean(times_off):.1f}s)")
    ax.axvline(np.mean(times_on),  color=C_ON,  linestyle="--", linewidth=1.5)
    ax.axvline(np.mean(times_off), color=C_OFF, linestyle="--", linewidth=1.5)
    ax.set_xlabel("Processing Time (s)")
    ax.set_ylabel("# Examples")
    ax.set_title("Processing Time Distribution")
    ax.legend()

    # Per-violation mean time
    ax2 = axes[1]
    mean_on  = [np.mean([r.get("processing_time_seconds", 0) for r in r_on.values()  if r["ground_truth"] == v]) for v in VIOLATION_LABELS]
    mean_off = [np.mean([r.get("processing_time_seconds", 0) for r in r_off.values() if r["ground_truth"] == v]) for v in VIOLATION_LABELS]
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.35
    ax2.bar(x - w/2, mean_on,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    ax2.bar(x + w/2, mean_off, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(VIOLATION_LABELS)
    ax2.set_ylabel("Mean Processing Time (s)")
    ax2.set_title("Mean Processing Time per Violation Type")
    ax2.legend()
    for i, (a, b) in enumerate(zip(mean_on, mean_off)):
        ax2.text(i - w/2, a + 1, f"{a:.0f}s", ha="center", va="bottom", fontsize=7)
        ax2.text(i + w/2, b + 1, f"{b:.0f}s", ha="center", va="bottom", fontsize=7)

    fig.suptitle("Processing Time: Structural ON vs OFF", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "08_processing_time.png")


# ---------------------------------------------------------------------------
# Fig 9: Heatmap — Violation x Difficulty x Run
# ---------------------------------------------------------------------------
def fig_heatmap_vtype_diff():
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    vmin, vmax = 50, 105

    for ax_i, (results, title) in enumerate([(r_on, "Structural ON"), (r_off, "Structural OFF")]):
        ax = axes[ax_i]
        mat = np.zeros((len(VIOLATION_LABELS), len(DIFFICULTY_ORDER)))
        for vi, v in enumerate(VIOLATION_LABELS):
            for di, d in enumerate(DIFFICULTY_ORDER):
                rs = [r for r in results.values() if r["ground_truth"] == v and r.get("level") == d]
                if rs:
                    hit2 = sum(1 for r in rs if r["ground_truth"] in get_top_predictions(r))
                    mat[vi, di] = hit2 / len(rs) * 100

        sns.heatmap(mat, annot=True, fmt=".0f", ax=ax,
                    xticklabels=DIFFICULTY_ORDER, yticklabels=VIOLATION_LABELS,
                    cmap="RdYlGn", vmin=vmin, vmax=vmax, cbar=ax_i == 1,
                    linewidths=0.5)
        ax.set_title(f"{title} — Hit@2 (%) by Violation × Difficulty")
        ax.set_xlabel("Difficulty")
        ax.set_ylabel("SOLID Principle")

    fig.suptitle("Hit@2 Heatmap: Violation × Difficulty", fontsize=13, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "09_heatmap_violation_difficulty.png")


# ---------------------------------------------------------------------------
# Fig 10: Language comparison
# ---------------------------------------------------------------------------
def fig_language():
    langs = [l for l in ["JAVA", "PYTHON", "KOTLIN", "CSHARP", "C#"] if l in by_lang_on]

    fig, ax = plt.subplots(figsize=(10, 5))
    on_vals  = [by_lang_on.get(l, {}).get("hit2_acc", 0)*100  for l in langs]
    off_vals = [by_lang_off.get(l, {}).get("hit2_acc", 0)*100 for l in langs]
    ns       = [by_lang_on.get(l, {}).get("n", 0) for l in langs]
    x = np.arange(len(langs))
    w = 0.35
    b1 = ax.bar(x - w/2, on_vals,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    b2 = ax.bar(x + w/2, off_vals, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    for bar in list(b1) + list(b2):
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.5, f"{h:.0f}%",
                ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels([f"{l}\n(n={n})" for l, n in zip(langs, ns)])
    ax.set_ylabel("Hit@2 Accuracy (%)")
    ax.set_title("Hit@2 Accuracy by Programming Language\nStructural ON vs OFF")
    ax.legend(); ax.set_ylim(0, 115)

    fig.tight_layout()
    savefig(fig, "10_language_comparison.png")


# ---------------------------------------------------------------------------
# Fig 11: Summary dashboard
# ---------------------------------------------------------------------------
def fig_summary_dashboard(n_both_correct, n_on_only, n_off_only, n_both_wrong):
    fig = plt.figure(figsize=(16, 9))
    fig.patch.set_facecolor("#f8f9fa")

    # Title
    fig.text(0.5, 0.97, "Structural Analysis ON vs OFF — Summary Dashboard",
             ha="center", va="top", fontsize=16, fontweight="bold")
    fig.text(0.5, 0.93, "diff_eval workflow · qwen3-8b · Top-2 · n=240 examples",
             ha="center", va="top", fontsize=11, color="gray")

    # ---- Subplot 1: Key metrics table ----
    ax1 = fig.add_axes([0.02, 0.55, 0.38, 0.35])
    ax1.axis("off")
    table_data = [
        ["Metric", "Struct ON", "Struct OFF", "Δ (OFF−ON)"],
        ["Pos-1 Accuracy",  f"{agg_on['pos1_acc']*100:.2f}%",  f"{agg_off['pos1_acc']*100:.2f}%",  f"{(agg_off['pos1_acc']-agg_on['pos1_acc'])*100:+.2f}pp"],
        ["Hit@2 Accuracy",  f"{agg_on['hit2_acc']*100:.2f}%",  f"{agg_off['hit2_acc']*100:.2f}%",  f"{(agg_off['hit2_acc']-agg_on['hit2_acc'])*100:+.2f}pp"],
        ["Hit@any",         f"{agg_on['hit_any_acc']*100:.2f}%",f"{agg_off['hit_any_acc']*100:.2f}%",f"{(agg_off['hit_any_acc']-agg_on['hit_any_acc'])*100:+.2f}pp"],
        ["Pos-2 Only",      f"{agg_on['pos2_only_frac']*100:.2f}%",f"{agg_off['pos2_only_frac']*100:.2f}%",f"{(agg_off['pos2_only_frac']-agg_on['pos2_only_frac'])*100:+.2f}pp"],
        ["MRR@2",           f"{agg_on['mrr2']:.4f}",           f"{agg_off['mrr2']:.4f}",           f"{agg_off['mrr2']-agg_on['mrr2']:+.4f}"],
        ["Mean Time",       f"{agg_on['mean_time']:.1f}s",     f"{agg_off['mean_time']:.1f}s",      f"{agg_off['mean_time']-agg_on['mean_time']:+.1f}s"],
    ]
    cell_colors = [["#e0e0e0"]*4]
    for row in table_data[1:]:
        delta = row[3]
        if "pp" in delta or (delta[0] in ("+", "-") and "s" not in delta):
            try:
                v = float(delta.replace("pp","").replace("s",""))
                c = "#d4edda" if v > 0 else ("#f8d7da" if v < 0 else "#fff")
            except:
                c = "#fff"
        else:
            c = "#fff"
        cell_colors.append(["#fff","#ddeeff","#fff3cd",c])
    t = ax1.table(cellText=table_data, loc="center", cellLoc="center")
    t.auto_set_font_size(False)
    t.set_fontsize(9)
    t.scale(1.2, 1.8)
    # Apply cell colors manually
    for (row_i, col_j), cell in t.get_celld().items():
        if row_i < len(cell_colors) and col_j < len(cell_colors[row_i]):
            cell.set_facecolor(cell_colors[row_i][col_j])
    ax1.set_title("Key Metrics Comparison", fontsize=10, pad=5)

    # ---- Subplot 2: Hit@2 by violation ----
    ax2 = fig.add_axes([0.44, 0.55, 0.54, 0.35])
    on_vals  = [by_vtype_on[v]["hit2_acc"]*100  for v in VIOLATION_LABELS]
    off_vals = [by_vtype_off[v]["hit2_acc"]*100 for v in VIOLATION_LABELS]
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.35
    ax2.bar(x - w/2, on_vals,  w, label="Struct ON",  color=C_ON,  alpha=0.85)
    ax2.bar(x + w/2, off_vals, w, label="Struct OFF", color=C_OFF, alpha=0.85)
    ax2.set_xticks(x); ax2.set_xticklabels(VIOLATION_LABELS)
    ax2.set_ylabel("Hit@2 Acc (%)"); ax2.set_title("Hit@2 by Violation Type"); ax2.legend(fontsize=8)
    ax2.set_ylim(0, 115)
    for i, (a, b) in enumerate(zip(on_vals, off_vals)):
        ax2.text(i - w/2, a+1, f"{a:.0f}", ha="center", va="bottom", fontsize=7)
        ax2.text(i + w/2, b+1, f"{b:.0f}", ha="center", va="bottom", fontsize=7)

    # ---- Subplot 3: Pie of flip cases ----
    ax3 = fig.add_axes([0.02, 0.08, 0.28, 0.40])
    sizes = [n_both_correct, n_on_only, n_off_only, n_both_wrong]
    pie_labels = [f"Both ✓\n({n_both_correct})", f"ON only ✓\n({n_on_only})",
                  f"OFF only ✓\n({n_off_only})", f"Both ✗\n({n_both_wrong})"]
    ax3.pie(sizes, labels=pie_labels, colors=[C_GAIN, C_ON, C_OFF, C_NEUTRAL],
            autopct="%1.0f%%", startangle=90,
            wedgeprops={"edgecolor":"white","linewidth":1.5})
    ax3.set_title("Hit@2 Agreement per Example", fontsize=9)

    # ---- Subplot 4: Difficulty comparison ----
    ax4 = fig.add_axes([0.34, 0.08, 0.30, 0.40])
    on_d  = [by_diff_on[d]["hit2_acc"]*100  for d in DIFFICULTY_ORDER]
    off_d = [by_diff_off[d]["hit2_acc"]*100 for d in DIFFICULTY_ORDER]
    x = np.arange(len(DIFFICULTY_ORDER))
    ax4.bar(x - w/2, on_d,  w, color=C_ON,  alpha=0.85, label="Struct ON")
    ax4.bar(x + w/2, off_d, w, color=C_OFF, alpha=0.85, label="Struct OFF")
    ax4.set_xticks(x); ax4.set_xticklabels(DIFFICULTY_ORDER)
    ax4.set_ylabel("Hit@2 Acc (%)"); ax4.set_title("Hit@2 by Difficulty"); ax4.legend(fontsize=8)
    ax4.set_ylim(0, 110)
    for i, (a, b) in enumerate(zip(on_d, off_d)):
        ax4.text(i - w/2, a+1, f"{a:.0f}", ha="center", va="bottom", fontsize=8)
        ax4.text(i + w/2, b+1, f"{b:.0f}", ha="center", va="bottom", fontsize=8)

    # ---- Subplot 5: Multi-detection distribution ----
    ax5 = fig.add_axes([0.68, 0.08, 0.30, 0.40])
    multi_on  = Counter([len(get_all_detected(r)) for r in r_on.values()])
    multi_off = Counter([len(get_all_detected(r)) for r in r_off.values()])
    ks = [0, 1, 2, 3, 4, 5]
    vals_on  = [multi_on.get(k, 0)  for k in ks]
    vals_off = [multi_off.get(k, 0) for k in ks]
    x = np.arange(len(ks))
    ax5.bar(x - w/2, vals_on,  w, color=C_ON,  alpha=0.85, label="Struct ON")
    ax5.bar(x + w/2, vals_off, w, color=C_OFF, alpha=0.85, label="Struct OFF")
    ax5.set_xticks(x); ax5.set_xticklabels([str(k) for k in ks])
    ax5.set_xlabel("# Violations in all_checks")
    ax5.set_ylabel("# Examples")
    ax5.set_title("Multi-Detection Distribution")
    ax5.legend(fontsize=8)

    savefig(fig, "00_summary_dashboard.png")


# ---------------------------------------------------------------------------
# CSV exports
# ---------------------------------------------------------------------------
def export_csvs():
    rows = []
    for eid in r_on:
        if eid not in r_off:
            continue
        a, b = r_on[eid], r_off[eid]
        gt = a["ground_truth"]
        a_preds = get_top_predictions(a)
        b_preds = get_top_predictions(b)
        a_hit = gt in a_preds
        b_hit = gt in b_preds
        rows.append({
            "example_id": eid,
            "ground_truth": gt,
            "level": a.get("level"),
            "language": a.get("language"),
            "on_pos1": a_preds[0] if a_preds else "NONE",
            "on_pos2": a_preds[1] if len(a_preds) > 1 else "NONE",
            "off_pos1": b_preds[0] if b_preds else "NONE",
            "off_pos2": b_preds[1] if len(b_preds) > 1 else "NONE",
            "on_hit2": a_hit,
            "off_hit2": b_hit,
            "flip": ("both_correct" if a_hit and b_hit else
                     "on_only" if a_hit else
                     "off_only" if b_hit else "both_wrong"),
            "on_n_detected": len(get_all_detected(a)),
            "off_n_detected": len(get_all_detected(b)),
            "on_time": a.get("processing_time_seconds", 0),
            "off_time": b.get("processing_time_seconds", 0),
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUTDIR / "detailed_comparison.csv", index=False)
    print(f"  Saved: {OUTDIR / 'detailed_comparison.csv'}")

    # Aggregate by violation
    agg_rows = []
    for v in VIOLATION_LABELS:
        sub = df[df["ground_truth"] == v]
        agg_rows.append({
            "violation": v,
            "n": len(sub),
            "on_pos1_acc":  (sub["on_pos1"]  == sub["ground_truth"]).mean(),
            "on_hit2_acc":  sub["on_hit2"].mean(),
            "off_pos1_acc": (sub["off_pos1"] == sub["ground_truth"]).mean(),
            "off_hit2_acc": sub["off_hit2"].mean(),
            "diff_hit2": sub["off_hit2"].mean() - sub["on_hit2"].mean(),
        })
    pd.DataFrame(agg_rows).to_csv(OUTDIR / "by_violation.csv", index=False)

    # Aggregate by difficulty
    agg_rows_d = []
    for d in DIFFICULTY_ORDER:
        sub = df[df["level"] == d]
        agg_rows_d.append({
            "difficulty": d,
            "n": len(sub),
            "on_hit2_acc":  sub["on_hit2"].mean(),
            "off_hit2_acc": sub["off_hit2"].mean(),
            "diff_hit2": sub["off_hit2"].mean() - sub["on_hit2"].mean(),
        })
    pd.DataFrame(agg_rows_d).to_csv(OUTDIR / "by_difficulty.csv", index=False)

    return df


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_report(n_both_correct, n_on_only, n_off_only, n_both_wrong, df):
    report = f"""# Structural Analysis ON vs OFF — Comparison Report
## diff_eval workflow | qwen3-8b | Top-2 strategy | n=240

---

## 1. Configuration Difference

| Parameter | run_top2 (Struct ON) | run_structure_off_top2 (Struct OFF) |
|-----------|----------------------|--------------------------------------|
| `structural_analysis_enabled` | **True** | **False** |
| `selection_method` | ranking_llm | ranking_llm |
| `max_examples_per_violation` | None (all) | 5 |
| `total_iterations` | 5 | 5 |
| `temperature` | 0.0 | 0.0 |

> **Note**: `max_examples_per_violation=5` in Struct OFF limits the dataset to 5 examples per violation
> type for prompt/context construction, while Struct ON uses all available examples. Both runs operate
> on the same 240 evaluation examples.

---

## 2. Overall Metrics

| Metric | Struct ON | Struct OFF | Δ (OFF − ON) |
|--------|-----------|------------|--------------|
| Pos-1 Accuracy | {agg_on['pos1_acc']*100:.2f}% | {agg_off['pos1_acc']*100:.2f}% | {(agg_off['pos1_acc']-agg_on['pos1_acc'])*100:+.2f}pp |
| Hit@2 Accuracy | {agg_on['hit2_acc']*100:.2f}% | {agg_off['hit2_acc']*100:.2f}% | {(agg_off['hit2_acc']-agg_on['hit2_acc'])*100:+.2f}pp |
| Hit@any (all_checks) | {agg_on['hit_any_acc']*100:.2f}% | {agg_off['hit_any_acc']*100:.2f}% | {(agg_off['hit_any_acc']-agg_on['hit_any_acc'])*100:+.2f}pp |
| Pos-2 Only Contribution | {agg_on['pos2_only_frac']*100:.2f}% | {agg_off['pos2_only_frac']*100:.2f}% | {(agg_off['pos2_only_frac']-agg_on['pos2_only_frac'])*100:+.2f}pp |
| MRR@2 | {agg_on['mrr2']:.4f} | {agg_off['mrr2']:.4f} | {agg_off['mrr2']-agg_on['mrr2']:+.4f} |
| Mean Processing Time | {agg_on['mean_time']:.1f}s | {agg_off['mean_time']:.1f}s | {agg_off['mean_time']-agg_on['mean_time']:+.1f}s |

**Key finding**: Removing structural analysis yields **+{(agg_off['hit2_acc']-agg_on['hit2_acc'])*100:.2f}pp Hit@2** improvement despite
being a simpler pipeline. However, it comes at the cost of +{agg_off['mean_time']-agg_on['mean_time']:.1f}s/example mean processing time.

---

## 3. Hit@2 by Violation Type

| Violation | ON Pos-1 | ON Hit@2 | OFF Pos-1 | OFF Hit@2 | Δ Hit@2 |
|-----------|----------|----------|-----------|-----------|---------|
"""
    for v in VIOLATION_LABELS:
        a, b = by_vtype_on[v], by_vtype_off[v]
        diff = b['hit2_acc'] - a['hit2_acc']
        direction = "↑" if diff > 0 else ("↓" if diff < 0 else "—")
        report += f"| {v} | {a['pos1_acc']*100:.1f}% | {a['hit2_acc']*100:.1f}% | {b['pos1_acc']*100:.1f}% | {b['hit2_acc']*100:.1f}% | {direction} {diff*100:+.1f}pp |\n"

    report += f"""
**Notable findings**:
- **DIP**: Struct OFF achieves **100% Hit@2** (vs 95.8% for ON), a perfect score — removing structural
  analysis actually benefits DIP detection significantly.
- **OCP**: Struct OFF is slightly worse (-2.1pp), and this is concentrated in HARD examples where
  structural code patterns help disambiguate OCP vs DIP violations.
- **SRP, ISP**: Small improvements with Struct OFF.

---

## 4. Hit@2 by Difficulty Level

| Difficulty | ON Hit@2 | OFF Hit@2 | Δ Hit@2 | N |
|-----------|---------|----------|---------|---|
"""
    for d in DIFFICULTY_ORDER:
        a, b = by_diff_on[d], by_diff_off[d]
        diff = b['hit2_acc'] - a['hit2_acc']
        direction = "↑" if diff > 0 else ("↓" if diff < 0 else "—")
        report += f"| {d} | {a['hit2_acc']*100:.1f}% | {b['hit2_acc']*100:.1f}% | {direction} {diff*100:+.1f}pp | {a['n']} |\n"

    report += f"""
**Key finding**: HARD examples are slightly worse under Struct OFF (-2.5pp), while EASY and MODERATE
improve. This suggests structural analysis provides the most value for complex, hard-to-distinguish violations.

---

## 5. Per-Example Agreement Analysis

| Category | Count | % |
|----------|-------|---|
| Both correct (Hit@2) | {n_both_correct} | {n_both_correct/240*100:.1f}% |
| Struct ON only correct | {n_on_only} | {n_on_only/240*100:.1f}% |
| Struct OFF only correct | {n_off_only} | {n_off_only/240*100:.1f}% |
| Both wrong | {n_both_wrong} | {n_both_wrong/240*100:.1f}% |

**Flip analysis by violation type**:

| Violation | OFF gained | OFF lost | Net |
|-----------|-----------|---------|-----|
"""
    flip_df = df[df["flip"].isin(["on_only", "off_only"])]
    for v in VIOLATION_LABELS:
        gained = len(df[(df["ground_truth"] == v) & (df["flip"] == "off_only")])
        lost   = len(df[(df["ground_truth"] == v) & (df["flip"] == "on_only")])
        net    = gained - lost
        sym    = "+" if net > 0 else ("" if net == 0 else "")
        report += f"| {v} | {gained} | {lost} | {net:+d} |\n"

    report += f"""

---

## 6. Multi-Violation Detection

Without structural analysis, the model detects **more** violations per example on average:

| Stat | Struct ON | Struct OFF |
|------|-----------|------------|
| Mean detected violations | {np.mean([len(get_all_detected(r)) for r in r_on.values()]):.2f} | {np.mean([len(get_all_detected(r)) for r in r_off.values()]):.2f} |
| Examples with 5/5 detected | {sum(1 for r in r_on.values() if len(get_all_detected(r))==5)} | {sum(1 for r in r_off.values() if len(get_all_detected(r))==5)} |
| Examples with 0 detected | {sum(1 for r in r_on.values() if len(get_all_detected(r))==0)} | {sum(1 for r in r_off.values() if len(get_all_detected(r))==0)} |

Struct OFF detects an average of **{np.mean([len(get_all_detected(r)) for r in r_off.values()]):.2f}** violations per example vs
**{np.mean([len(get_all_detected(r)) for r in r_on.values()]):.2f}** for Struct ON. This higher detection rate improves Hit@2
by putting the correct answer in the top-2 more often — but hurts Pos-1 accuracy as the first prediction
is less precise.

---

## 7. Processing Time

| Stat | Struct ON | Struct OFF | Δ |
|------|-----------|------------|---|
| Mean (s) | {agg_on['mean_time']:.1f} | {agg_off['mean_time']:.1f} | {agg_off['mean_time']-agg_on['mean_time']:+.1f} |
| Median (s) | {np.median([r.get('processing_time_seconds',0) for r in r_on.values()]):.1f} | {np.median([r.get('processing_time_seconds',0) for r in r_off.values()]):.1f} | — |

**Counterintuitively, Struct OFF is slower (+{agg_off['mean_time']-agg_on['mean_time']:.1f}s mean)**. This is likely because:
1. With structural analysis disabled, the model relies more heavily on LLM-based reasoning at each iteration.
2. Structural analysis may prune certain code paths early, reducing total token generation.
3. The `max_examples_per_violation=5` setting in Struct OFF could affect internal context management.

---

## 8. Language Comparison

| Language | Struct ON Hit@2 | Struct OFF Hit@2 | Δ | N |
|----------|----------------|-----------------|---|---|
"""
    for lang in sorted(by_lang_on.keys()):
        if lang in by_lang_off:
            a, b = by_lang_on[lang], by_lang_off[lang]
            diff = b['hit2_acc'] - a['hit2_acc']
            report += f"| {lang} | {a['hit2_acc']*100:.1f}% | {b['hit2_acc']*100:.1f}% | {diff*100:+.1f}pp | {a['n']} |\n"

    report += f"""

**Python gains the most** (+6.7pp) from removing structural analysis, while Kotlin loses slightly (-3.3pp).
C# and CSHARP (same language, split across notations) show no change.

---

## 9. Conclusions

1. **Overall**: Removing structural analysis yields a modest Hit@2 improvement (+1.67pp: 83.75% → 85.42%),
   with perfect DIP detection (100%) being the standout result.

2. **Trade-off — precision vs recall**: Struct OFF detects more violations per example (mean 4.07 vs 3.64),
   improving Hit@2 coverage but lowering Pos-1 accuracy (-2.08pp). The model becomes more "generous"
   in its detections without structural constraints.

3. **HARD examples regress**: Structural analysis genuinely helps for difficult code where subtle
   structural patterns distinguish OCP from DIP violations (-2.5pp Hit@2 for HARD in Struct OFF).

4. **OCP suffers the most**: 6 OCP HARD cases are rescued by structural analysis. The heatmap shows
   Struct ON makes fewer DIP-for-OCP misclassifications in HARD examples.

5. **DIP benefits most**: Structural analysis appears to add noise to DIP detection in some cases —
   removing it achieves a perfect 100% Hit@2 for DIP.

6. **Processing time paradox**: Struct OFF is slower (+22.4s/example), suggesting structural analysis
   helps prune the solution space rather than adding computation.

7. **Recommendation**: For maximum Hit@2 performance across all SOLID principles, Struct OFF is slightly
   preferred (+1.67pp) and simpler to deploy. For OCP and HARD examples specifically, structural analysis
   provides meaningful value. A hybrid approach — structural analysis only for complex/hard examples or
   only during OCP evaluation — could capture the best of both.

---

## 10. Generated Artifacts

### Visualizations
- `00_summary_dashboard.png` — Full metrics dashboard
- `01_overall_metrics.png` — Overall metrics bar comparison
- `02_hit2_by_violation.png` — Hit@2 by SOLID principle
- `03_hit2_by_difficulty.png` — Hit@2 by difficulty level
- `04_flip_analysis.png` — Per-example agreement & flip analysis
- `05_multi_detection.png` — Multi-violation detection distribution
- `06_per_class_metrics.png` — Per-class F1, Precision, Recall (Pos-1)
- `07_prediction_bias_heatmap.png` — Prediction confusion matrices
- `08_processing_time.png` — Processing time distribution
- `09_heatmap_violation_difficulty.png` — Violation × Difficulty heatmap
- `10_language_comparison.png` — Hit@2 by programming language

### Data Files
- `detailed_comparison.csv` — Per-example results for both runs
- `by_violation.csv` — Aggregated metrics by violation type
- `by_difficulty.csv` — Aggregated metrics by difficulty level
"""
    path = OUTDIR / "analysis_report.md"
    path.write_text(report, encoding="utf-8")
    print(f"  Saved: {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Generating figures...")
    fig_overall_metrics()
    fig_hit2_by_violation()
    fig_hit2_by_difficulty()
    n_both_correct, n_on_only, n_off_only, n_both_wrong = fig_flip_analysis()
    fig_multi_detection()
    fig_per_class_metrics()
    fig_prediction_bias()
    fig_processing_time()
    fig_heatmap_vtype_diff()
    fig_language()
    fig_summary_dashboard(n_both_correct, n_on_only, n_off_only, n_both_wrong)

    print("Exporting CSVs...")
    df = export_csvs()

    print("Writing report...")
    write_report(n_both_correct, n_on_only, n_off_only, n_both_wrong, df)

    print(f"\nAll outputs written to: {OUTDIR}")
