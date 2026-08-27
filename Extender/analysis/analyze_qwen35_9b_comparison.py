#!/usr/bin/env python3
"""
Analysis: qwen3.5-9b (local) vs qwen3.5 (cloud) — Top-2 strategy by default.

Configs compared (all Top-2):
  1. Diff Eval      — result/local/diff_eval/run_top2_new_model/qwen3-5-9b/
  2. Single Agent   — result/local/single_agent/run_top2_new_model/qwen3-5-9b/
  3. Two Agent      — result/local/two_agent/run_top2_new_model/qwen3-5-9b/
  4. Single Agent (Cloud) — result/local/single_agent/run_run_cloud_bench_top2/qwen3-5/

Outputs → analysis/analysis_output_qwen35_9b/
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
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
PRED_NONE = "NONE"
DIFFICULTY_ORDER = ["EASY", "MODERATE", "HARD"]

BASE = Path(__file__).parent.parent

CONFIGS = [
    {
        "key": "diff_eval",
        "label": "Diff Eval\n(9B)",
        "label_short": "Diff Eval (9B)",
        "path": BASE / "result/local/diff_eval/run_top2_new_model/qwen3-5-9b/detection_results.json",
        "workflow_type": "diff_eval",
        "color": "#E45756",
    },
    {
        "key": "single_agent",
        "label": "Single Agent\n(9B)",
        "label_short": "Single Agent (9B)",
        "path": BASE / "result/local/single_agent/run_top2_new_model/qwen3-5-9b/detection_results.json",
        "workflow_type": "agent",
        "color": "#4C78A8",
    },
    {
        "key": "two_agent",
        "label": "Two Agent\n(9B)",
        "label_short": "Two Agent (9B)",
        "path": BASE / "result/local/two_agent/run_top2_new_model/qwen3-5-9b/detection_results.json",
        "workflow_type": "agent",
        "color": "#54A24B",
    },
    {
        "key": "single_agent_cloud",
        "label": "Single Agent\n(Cloud)",
        "label_short": "Single Agent (Cloud)",
        "path": BASE / "result/local/single_agent/run_run_cloud_bench_top2/qwen3-5/detection_results.json",
        "workflow_type": "agent",
        "color": "#F58518",
    },
]

OUTDIR = Path(__file__).parent / "analysis_output_qwen35_9b"
OUTDIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_json_load(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        raw2 = raw.replace(",]", "]").replace(",}", "}")
        return json.loads(raw2)


def normalize_label(label: Optional[str]) -> Optional[str]:
    if label is None:
        return None
    s = str(label).strip().upper()
    if not s or s == "NONE":
        return None
    if s in VIOLATION_LABELS:
        return s
    for v in VIOLATION_LABELS:
        if v in s:
            return v
    return None


def parse_detected_list(raw: Any) -> List[str]:
    if not raw:
        return []
    parts = [p.strip() for p in str(raw).split(",")]
    out: List[str] = []
    for p in parts:
        n = normalize_label(p)
        if n and n not in out:
            out.append(n)
    return out


def parse_predictions_agent(result: Dict[str, Any], top_k: int = 2) -> List[str]:
    """Parse top-k predictions for single_agent / two_agent."""
    model_response = result.get("model_response") or ""
    predictions: List[str] = []
    if model_response:
        try:
            resp = json.loads(model_response)
            violations = resp.get("violations", [])
            if isinstance(violations, list):
                for v in violations:
                    n = normalize_label(v.get("violation_type") if isinstance(v, dict) else v)
                    if n and n not in predictions:
                        predictions.append(n)
        except Exception:
            pass
    if not predictions:
        predictions = parse_detected_list(result.get("detected_violation_type") or "")
    return predictions[:top_k]


def parse_predictions_diff_eval(result: Dict[str, Any], top_k: int = 2) -> List[str]:
    """Parse top-k predictions for diff_eval."""
    preds = parse_detected_list(result.get("violation_type"))
    if not preds:
        preds = parse_detected_list(result.get("detected_violation_type"))
    if preds:
        return preds[:top_k]
    detected: List[str] = []
    for chk in result.get("all_checks", []) or []:
        if not isinstance(chk, dict):
            continue
        if not chk.get("is_detected", False):
            continue
        n = normalize_label(chk.get("violation_type"))
        if n and n not in detected:
            detected.append(n)
    return detected[:top_k]


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def extract_rows(cfg: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
    key = cfg["key"]
    workflow_type = cfg["workflow_type"]
    rows: List[Dict[str, Any]] = []
    by_violation = data.get("by_violation_type", {}) or {}

    for bucket_vt, bucket in by_violation.items():
        for result in bucket.get("results", []) or []:
            if workflow_type == "diff_eval":
                actual = normalize_label(result.get("ground_truth")) or normalize_label(bucket_vt)
                preds = parse_predictions_diff_eval(result, top_k=2)
            else:
                actual = normalize_label(bucket_vt)
                preds = parse_predictions_agent(result, top_k=2)

            pred1 = preds[0] if len(preds) > 0 else None
            pred2 = preds[1] if len(preds) > 1 else None

            rr = 0.0
            correct_pos = 0
            if actual is not None:
                if pred1 == actual:
                    rr, correct_pos = 1.0, 1
                elif pred2 == actual:
                    rr, correct_pos = 0.5, 2

            row: Dict[str, Any] = {
                "config": key,
                "label": cfg["label_short"],
                "example_id": result.get("example_id"),
                "level": result.get("level", "UNKNOWN"),
                "language": result.get("language", "UNKNOWN"),
                "actual": actual,
                "pred1": pred1,
                "pred2": pred2,
                "top1_correct": bool(actual is not None and pred1 == actual),
                "top2_correct": bool(actual is not None and (pred1 == actual or pred2 == actual)),
                "reciprocal_rank": rr,
                "correct_position": correct_pos,
                "processing_time_s": float(result.get("processing_time_seconds") or 0.0),
            }

            if workflow_type == "diff_eval":
                all_checks = result.get("all_checks", []) or []
                detected_count = sum(1 for c in all_checks if isinstance(c, dict) and c.get("is_detected", False))
                row["detected_count"] = detected_count
                gt = row["actual"]
                row["gt_detected_anywhere"] = bool(any(
                    isinstance(c, dict) and c.get("is_detected", False) and normalize_label(c.get("violation_type")) == gt
                    for c in all_checks
                )) if gt is not None else False
                row["all_detected_types"] = ",".join(
                    normalize_label(c.get("violation_type")) or ""
                    for c in all_checks
                    if isinstance(c, dict) and c.get("is_detected", False)
                )
            else:
                row["detected_count"] = None
                row["gt_detected_anywhere"] = None
                row["all_detected_types"] = None

            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Metrics helpers
# ---------------------------------------------------------------------------

def confusion_matrix_df(df: pd.DataFrame, actual_col: str, pred_col: str, labels: List[str]) -> pd.DataFrame:
    a = df[actual_col].fillna(PRED_NONE)
    p = df[pred_col].fillna(PRED_NONE)
    cm = pd.crosstab(a, p, rownames=["Actual"], colnames=["Predicted"], dropna=False)
    for lab in labels:
        if lab not in cm.index:
            cm.loc[lab] = 0
        if lab not in cm.columns:
            cm[lab] = 0
    return cm.reindex(index=labels, columns=labels, fill_value=0)


def per_class_metrics(df: pd.DataFrame, pred_col: str = "pred1") -> pd.DataFrame:
    actual = df["actual"].fillna(PRED_NONE).astype(str)
    pred = df[pred_col].fillna(PRED_NONE).astype(str)
    rows = []
    for lab in VIOLATION_LABELS:
        tp = int(((actual == lab) & (pred == lab)).sum())
        fp = int(((actual != lab) & (pred == lab)).sum())
        fn = int(((actual == lab) & (pred != lab)).sum())
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        rows.append({"class": lab, "precision": prec, "recall": rec, "f1": f1, "tp": tp, "fp": fp, "fn": fn})
    return pd.DataFrame(rows)


def compute_summary(df: pd.DataFrame) -> Dict[str, float]:
    n = len(df)
    top1 = df["top1_correct"].mean()
    hit2 = df["top2_correct"].mean()
    mrr = df["reciprocal_rank"].mean()
    pos2_share = (df["correct_position"] == 2).mean()

    # Set-F1@2
    f1s = []
    for _, r in df.iterrows():
        gt = r["actual"]
        pred_set = [p for p in [r.get("pred1"), r.get("pred2")] if p is not None]
        if gt is None or not pred_set:
            f1s.append(0.0)
            continue
        hit = 1.0 if gt in pred_set else 0.0
        precision = hit / len(set(pred_set))
        recall = hit
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    set_f1 = float(np.mean(f1s)) if f1s else 0.0

    pcm = per_class_metrics(df, "pred1")
    macro_f1 = float(pcm["f1"].mean())

    # resolved pred (top-2 hit resolved to correct label)
    resolved_pred = df.apply(lambda r: r["actual"] if r["top2_correct"] else r["pred1"], axis=1)
    df2 = df.copy()
    df2["resolved"] = resolved_pred
    pcm_res = per_class_metrics(df2, "resolved")
    macro_f1_resolved = float(pcm_res["f1"].mean())

    mean_time = df["processing_time_s"].mean()

    return {
        "n": n,
        "top1_acc": top1,
        "hit2_acc": hit2,
        "mrr": mrr,
        "pos2_share": pos2_share,
        "set_f1_at2": set_f1,
        "macro_f1_top1": macro_f1,
        "macro_f1_resolved": macro_f1_resolved,
        "mean_time_s": mean_time,
    }


def _add_value_labels(ax, bars, fmt="{:.1f}%", scale=100, fontsize=8, offset=0.01):
    for bar in bars:
        h = bar.get_height()
        if h > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                    fmt.format(h * scale), ha="center", va="bottom", fontsize=fontsize)


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_01_overall_comparison(df: pd.DataFrame, outdir: Path):
    """Overall Hit@2 and Top-1 accuracy comparison across all 4 configs."""
    keys = [c["key"] for c in CONFIGS]
    labels = [c["label"] for c in CONFIGS]
    colors = [c["color"] for c in CONFIGS]
    x = np.arange(len(keys))
    w = 0.3

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # Left: Top-1 Accuracy
    ax = axes[0]
    top1_vals = [df[df["config"] == k]["top1_correct"].mean() for k in keys]
    bars = ax.bar(x, top1_vals, w * 1.8, color=colors, alpha=0.85, edgecolor="white")
    ax.axhline(0.25, linestyle="--", color="#888", linewidth=1.2, label="Random Baseline (25%)")
    _add_value_labels(ax, bars)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Accuracy")
    ax.set_title("Top-1 Accuracy (Pos-1 Correct)")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # Right: Hit@2
    ax = axes[1]
    hit2_vals = [df[df["config"] == k]["top2_correct"].mean() for k in keys]
    pos2_vals = [(df[df["config"] == k]["correct_position"] == 2).mean() for k in keys]
    pos1_vals = [h - p for h, p in zip(hit2_vals, pos2_vals)]

    for i, (k, color) in enumerate(zip(keys, colors)):
        b = ax.bar(x[i], hit2_vals[i], w * 1.8, color=color, alpha=0.5, edgecolor="white", label="_nolegend_")
        ax.bar(x[i], pos1_vals[i], w * 1.8, color=color, alpha=0.85, edgecolor="white")
        ax.bar(x[i], pos2_vals[i], w * 1.8, bottom=pos1_vals[i], color=color, alpha=0.4,
               hatch="///", edgecolor="white")

    # Totals
    for i, val in enumerate(hit2_vals):
        ax.text(x[i], val + 0.01, f"{val*100:.1f}%", ha="center", va="bottom", fontsize=8)

    ax.axhline(0.40, linestyle="--", color="#888", linewidth=1.2, label="Random Baseline (40%)")
    solid_patch = mpatches.Patch(color="#888", alpha=0.85, label="Pos-1 contribution")
    hatch_patch = mpatches.Patch(facecolor="#888", alpha=0.4, hatch="///", label="Pos-2 contribution")
    ax.legend(handles=[solid_patch, hatch_patch,
                        mpatches.Patch(color="#888", linestyle="--", label="Random (40%)")],
              fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("Accuracy")
    ax.set_title("Hit@2 Accuracy (with Pos-2 Contribution)")
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Overall Performance Comparison — qwen3.5-9b (Local) vs Cloud — Top-2 Strategy",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "01_overall_accuracy_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 01_overall_accuracy_comparison.png")


def plot_02_metrics_dashboard(df: pd.DataFrame, outdir: Path):
    """MRR, Macro-F1, Set-F1@2 for all configs."""
    keys = [c["key"] for c in CONFIGS]
    labels = [c["label"] for c in CONFIGS]
    colors = [c["color"] for c in CONFIGS]
    x = np.arange(len(keys))
    w = 0.22

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    metrics = {
        "MRR@2": "reciprocal_rank",
        "Macro-F1 (Top-1)": None,
        "Set-F1@2": None,
    }

    # MRR
    ax = axes[0]
    mrr_vals = [df[df["config"] == k]["reciprocal_rank"].mean() for k in keys]
    bars = ax.bar(x, mrr_vals, w * 2, color=colors, alpha=0.85, edgecolor="white")
    _add_value_labels(ax, bars, fmt="{:.3f}", scale=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("MRR@2"); ax.set_ylim(0, 1.05); ax.grid(axis="y", alpha=0.3)

    # Macro-F1
    ax = axes[1]
    mf1_vals = [per_class_metrics(df[df["config"] == k], "pred1")["f1"].mean() for k in keys]
    bars = ax.bar(x, mf1_vals, w * 2, color=colors, alpha=0.85, edgecolor="white")
    _add_value_labels(ax, bars, fmt="{:.3f}", scale=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("Macro-F1 (Top-1 Pred)"); ax.set_ylim(0, 1.05); ax.grid(axis="y", alpha=0.3)

    # Set-F1@2
    ax = axes[2]
    sf1_vals = []
    for k in keys:
        sub = df[df["config"] == k]
        f1s = []
        for _, r in sub.iterrows():
            gt = r["actual"]
            pred_set = [p for p in [r.get("pred1"), r.get("pred2")] if p is not None]
            if gt is None or not pred_set:
                f1s.append(0.0)
                continue
            hit = 1.0 if gt in pred_set else 0.0
            prec = hit / len(set(pred_set))
            f1 = (2 * prec * hit / (prec + hit)) if (prec + hit) > 0 else 0.0
            f1s.append(f1)
        sf1_vals.append(float(np.mean(f1s)) if f1s else 0.0)
    bars = ax.bar(x, sf1_vals, w * 2, color=colors, alpha=0.85, edgecolor="white")
    _add_value_labels(ax, bars, fmt="{:.3f}", scale=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9)
    ax.set_title("Set-F1@2"); ax.set_ylim(0, 1.05); ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Metrics Dashboard — Top-2 Strategy", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "02_metrics_dashboard.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 02_metrics_dashboard.png")


def plot_03_by_difficulty(df: pd.DataFrame, outdir: Path):
    """Hit@2 and Top-1 accuracy by difficulty level for all configs."""
    keys = [c["key"] for c in CONFIGS]
    labels_short = [c["label_short"] for c in CONFIGS]
    colors = [c["color"] for c in CONFIGS]

    x = np.arange(len(DIFFICULTY_ORDER))
    w = 0.18
    offsets = np.linspace(-(len(keys)-1)/2 * w, (len(keys)-1)/2 * w, len(keys))

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    for metric, col, title in [
        ("top1_correct", "Top-1 Accuracy", "Top-1 Accuracy by Difficulty"),
        ("top2_correct", "Hit@2 Accuracy", "Hit@2 Accuracy by Difficulty"),
    ]:
        ax = axes[0] if metric == "top1_correct" else axes[1]
        for i, (k, label, color, off) in enumerate(zip(keys, labels_short, colors, offsets)):
            vals = []
            for diff in DIFFICULTY_ORDER:
                sub = df[(df["config"] == k) & (df["level"] == diff)]
                vals.append(sub[metric].mean() if len(sub) > 0 else 0.0)
            bars = ax.bar(x + off, vals, w, label=label, color=color, alpha=0.85, edgecolor="white")
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                            f"{val*100:.0f}", ha="center", va="bottom", fontsize=7)

        ax.axhline(0.25, linestyle="--", color="#888", linewidth=1, alpha=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(DIFFICULTY_ORDER, fontsize=10)
        ax.set_ylabel("Accuracy")
        ax.set_title(title)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Performance by Difficulty Level — Top-2 Strategy", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "03_accuracy_by_difficulty.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 03_accuracy_by_difficulty.png")


def plot_04_by_violation(df: pd.DataFrame, outdir: Path):
    """Hit@2 and Top-1 accuracy by violation type for all configs."""
    keys = [c["key"] for c in CONFIGS]
    labels_short = [c["label_short"] for c in CONFIGS]
    colors = [c["color"] for c in CONFIGS]

    x = np.arange(len(VIOLATION_LABELS))
    w = 0.18
    offsets = np.linspace(-(len(keys)-1)/2 * w, (len(keys)-1)/2 * w, len(keys))

    fig, axes = plt.subplots(1, 2, figsize=(16, 5.5))

    for metric, title, ax in [
        ("top1_correct", "Top-1 Accuracy by Violation Type", axes[0]),
        ("top2_correct", "Hit@2 Accuracy by Violation Type", axes[1]),
    ]:
        for k, label, color, off in zip(keys, labels_short, colors, offsets):
            vals = []
            for vt in VIOLATION_LABELS:
                sub = df[(df["config"] == k) & (df["actual"] == vt)]
                vals.append(sub[metric].mean() if len(sub) > 0 else 0.0)
            bars = ax.bar(x + off, vals, w, label=label, color=color, alpha=0.85, edgecolor="white")
            for bar, val in zip(bars, vals):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                            f"{val*100:.0f}", ha="center", va="bottom", fontsize=7)

        ax.axhline(0.25, linestyle="--", color="#888", linewidth=1, alpha=0.6)
        ax.set_xticks(x)
        ax.set_xticklabels(VIOLATION_LABELS, fontsize=10)
        ax.set_ylabel("Accuracy")
        ax.set_title(title)
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Performance by Violation Type — Top-2 Strategy", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "04_accuracy_by_violation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 04_accuracy_by_violation.png")


def plot_05_confusion_matrices(df: pd.DataFrame, outdir: Path):
    """Confusion matrices for all 4 configs — Top-1 (pred1) and Top-2 resolved."""
    keys = [c["key"] for c in CONFIGS]
    labels_short = [c["label_short"] for c in CONFIGS]

    fig, axes = plt.subplots(2, 4, figsize=(22, 10))

    for col, (key, label) in enumerate(zip(keys, labels_short)):
        sub = df[df["config"] == key].copy()

        # Top-1 confusion
        cm1 = confusion_matrix_df(sub, "actual", "pred1", VIOLATION_LABELS)
        ax = axes[0][col]
        sns.heatmap(cm1, annot=True, fmt="d", cmap="Blues", ax=ax,
                    cbar=False, linewidths=0.5, linecolor="white")
        ax.set_title(f"{label}\nTop-1 (pred1)", fontsize=9)
        ax.set_xlabel("Predicted", fontsize=8)
        ax.set_ylabel("Actual", fontsize=8)
        ax.tick_params(labelsize=8)

        # Top-2 resolved confusion
        sub["resolved"] = sub.apply(
            lambda r: r["actual"] if r["top2_correct"] else r["pred1"], axis=1)
        cm2 = confusion_matrix_df(sub, "actual", "resolved", VIOLATION_LABELS)
        ax = axes[1][col]
        sns.heatmap(cm2, annot=True, fmt="d", cmap="Greens", ax=ax,
                    cbar=False, linewidths=0.5, linecolor="white")
        ax.set_title(f"{label}\nTop-2 Resolved", fontsize=9)
        ax.set_xlabel("Predicted", fontsize=8)
        ax.set_ylabel("Actual", fontsize=8)
        ax.tick_params(labelsize=8)

    fig.text(0.01, 0.75, "Top-1 (pred1)", va="center", rotation="vertical",
             fontsize=11, fontweight="bold")
    fig.text(0.01, 0.28, "Top-2 Resolved", va="center", rotation="vertical",
             fontsize=11, fontweight="bold")
    fig.suptitle("Confusion Matrices — All Configurations", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout()
    fig.savefig(outdir / "05_confusion_matrices_all.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 05_confusion_matrices_all.png")


def plot_06_diff_eval_confusion_detail(df: pd.DataFrame, outdir: Path):
    """Diff Eval detailed confusion: Top-1 / Pos-2 predictions / Top-2 resolved."""
    sub = df[df["config"] == "diff_eval"].copy()

    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5))
    titles = ["Top-1 Prediction (pred1)", "Top-2 Pos-2 Only (pred2)", "Top-2 Resolved (Hit@2)"]
    cmaps = ["Blues", "Oranges", "Greens"]

    # pred1
    cm1 = confusion_matrix_df(sub, "actual", "pred1", VIOLATION_LABELS)
    sns.heatmap(cm1, annot=True, fmt="d", cmap=cmaps[0], ax=axes[0], cbar=False,
                linewidths=0.5, linecolor="white")

    # pred2 (all examples — None where no second prediction)
    cm2 = confusion_matrix_df(sub[sub["pred2"].notna()], "actual", "pred2", VIOLATION_LABELS)
    sns.heatmap(cm2, annot=True, fmt="d", cmap=cmaps[1], ax=axes[1], cbar=False,
                linewidths=0.5, linecolor="white")

    # resolved
    sub["resolved"] = sub.apply(
        lambda r: r["actual"] if r["top2_correct"] else r["pred1"], axis=1)
    cm3 = confusion_matrix_df(sub, "actual", "resolved", VIOLATION_LABELS)
    sns.heatmap(cm3, annot=True, fmt="d", cmap=cmaps[2], ax=axes[2], cbar=False,
                linewidths=0.5, linecolor="white")

    for ax, title in zip(axes, titles):
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Predicted", fontsize=8)
        ax.set_ylabel("Actual", fontsize=8)
        ax.tick_params(labelsize=9)

    fig.suptitle("Diff Eval (9B) — Detailed Confusion Matrices", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "06_diff_eval_confusion_detail.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 06_diff_eval_confusion_detail.png")


def plot_07_difficulty_violation_heatmap(df: pd.DataFrame, outdir: Path):
    """Diff Eval: Hit@2 heatmap by difficulty x violation."""
    sub = df[df["config"] == "diff_eval"].copy()

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, metric, title in [
        (axes[0], "top1_correct", "Top-1 Accuracy"),
        (axes[1], "top2_correct", "Hit@2 Accuracy"),
    ]:
        matrix = pd.DataFrame(index=DIFFICULTY_ORDER, columns=VIOLATION_LABELS, dtype=float)
        for diff in DIFFICULTY_ORDER:
            for vt in VIOLATION_LABELS:
                cell = sub[(sub["level"] == diff) & (sub["actual"] == vt)]
                matrix.loc[diff, vt] = cell[metric].mean() if len(cell) > 0 else float("nan")
        sns.heatmap(matrix.astype(float), annot=True, fmt=".0%", cmap="RdYlGn",
                    vmin=0, vmax=1, ax=ax, linewidths=0.5, linecolor="white")
        ax.set_title(f"Diff Eval — {title}", fontsize=11)
        ax.set_xlabel("Violation Type")
        ax.set_ylabel("Difficulty")

    fig.suptitle("Diff Eval (9B): Difficulty × Violation Heatmap", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "07_difficulty_violation_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 07_difficulty_violation_heatmap.png")


def plot_08_per_class_f1(df: pd.DataFrame, outdir: Path):
    """Per-class F1 for all configs (Top-1 pred)."""
    keys = [c["key"] for c in CONFIGS]
    labels_short = [c["label_short"] for c in CONFIGS]
    colors = [c["color"] for c in CONFIGS]

    x = np.arange(len(VIOLATION_LABELS))
    w = 0.18
    offsets = np.linspace(-(len(keys)-1)/2 * w, (len(keys)-1)/2 * w, len(keys))

    fig, ax = plt.subplots(figsize=(14, 5.5))

    for k, label, color, off in zip(keys, labels_short, colors, offsets):
        sub = df[df["config"] == k]
        pcm = per_class_metrics(sub, "pred1")
        vals = pcm.set_index("class").reindex(VIOLATION_LABELS)["f1"].fillna(0).tolist()
        bars = ax.bar(x + off, vals, w, label=label, color=color, alpha=0.85, edgecolor="white")
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.2f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(VIOLATION_LABELS, fontsize=11)
    ax.set_ylabel("F1 Score")
    ax.set_title("Per-Class F1 Score by Violation Type (Top-1 Prediction)", fontsize=12)
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(outdir / "08_per_class_f1.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 08_per_class_f1.png")


def plot_09_rank_distribution(df: pd.DataFrame, outdir: Path):
    """Where does ground truth appear: pos 1, pos 2, or not found."""
    keys = [c["key"] for c in CONFIGS]
    labels_short = [c["label_short"] for c in CONFIGS]
    colors_pos1 = [c["color"] for c in CONFIGS]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    x = np.arange(len(keys))
    w = 0.28

    pos1_share = [(df[df["config"] == k]["correct_position"] == 1).mean() for k in keys]
    pos2_share = [(df[df["config"] == k]["correct_position"] == 2).mean() for k in keys]
    not_found = [1.0 - p1 - p2 for p1, p2 in zip(pos1_share, pos2_share)]

    b1 = ax.bar(x, pos1_share, w, color=[c["color"] for c in CONFIGS], alpha=0.9, label="Correct at Pos-1")
    b2 = ax.bar(x, pos2_share, w, bottom=pos1_share, color=[c["color"] for c in CONFIGS],
                alpha=0.45, hatch="///", label="Correct at Pos-2")
    b3 = ax.bar(x, not_found, w, bottom=[p1+p2 for p1, p2 in zip(pos1_share, pos2_share)],
                color="#cccccc", alpha=0.7, label="Not Found in Top-2")

    for i, (p1, p2, nf) in enumerate(zip(pos1_share, pos2_share, not_found)):
        ax.text(x[i], p1 / 2, f"{p1*100:.0f}%", ha="center", va="center", fontsize=8, fontweight="bold")
        if p2 > 0.02:
            ax.text(x[i], p1 + p2 / 2, f"{p2*100:.0f}%", ha="center", va="center", fontsize=8)
        if nf > 0.02:
            ax.text(x[i], p1 + p2 + nf / 2, f"{nf*100:.0f}%", ha="center", va="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, fontsize=10)
    ax.set_ylabel("Share of Examples")
    ax.set_title("Rank Distribution: Where Does Ground Truth Appear?", fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(outdir / "09_rank_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  Saved 09_rank_distribution.png")


# ---------------------------------------------------------------------------
# CSV outputs
# ---------------------------------------------------------------------------

def save_csvs(df: pd.DataFrame, outdir: Path):
    # Overall summary
    rows = []
    for cfg in CONFIGS:
        k = cfg["key"]
        sub = df[df["config"] == k]
        s = compute_summary(sub)
        rows.append({"Config": cfg["label_short"], **s})
    summary_df = pd.DataFrame(rows)
    summary_df.to_csv(outdir / "overall_metrics.csv", index=False, float_format="%.4f")
    print("  Saved overall_metrics.csv")

    # By difficulty
    rows = []
    for cfg in CONFIGS:
        k = cfg["key"]
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["config"] == k) & (df["level"] == diff)]
            s = compute_summary(sub) if len(sub) > 0 else {}
            rows.append({"Config": cfg["label_short"], "Difficulty": diff, **s})
    pd.DataFrame(rows).to_csv(outdir / "by_difficulty.csv", index=False, float_format="%.4f")
    print("  Saved by_difficulty.csv")

    # By violation
    rows = []
    for cfg in CONFIGS:
        k = cfg["key"]
        for vt in VIOLATION_LABELS:
            sub = df[(df["config"] == k) & (df["actual"] == vt)]
            s = compute_summary(sub) if len(sub) > 0 else {}
            rows.append({"Config": cfg["label_short"], "Violation": vt, **s})
    pd.DataFrame(rows).to_csv(outdir / "by_violation.csv", index=False, float_format="%.4f")
    print("  Saved by_violation.csv")

    # Per-class metrics for diff_eval
    sub_de = df[df["config"] == "diff_eval"]
    pcm = per_class_metrics(sub_de, "pred1")
    pcm.to_csv(outdir / "diff_eval_per_class_metrics.csv", index=False, float_format="%.4f")
    print("  Saved diff_eval_per_class_metrics.csv")

    # Detailed results
    df.to_csv(outdir / "detailed_results.csv", index=False, float_format="%.4f")
    print("  Saved detailed_results.csv")


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------

def save_report(df: pd.DataFrame, outdir: Path):
    lines = []
    lines.append("# Analysis Report: qwen3.5-9b (Local) vs Cloud — Top-2 Strategy")
    lines.append(f"## Dataset: 240 examples | Model: qwen3.5-9b (local) / qwen3.5 (cloud)\n")

    lines.append("---\n")
    lines.append("## 1. Overall Performance Summary\n")
    lines.append("| Config | N | Top-1 Acc | Hit@2 | MRR@2 | Macro-F1 (Top-1) | Macro-F1 (Resolved) | Set-F1@2 | Pos-2 Share | Mean Time (s) |")
    lines.append("|--------|---|-----------|-------|-------|-----------------|---------------------|----------|-------------|----------------|")
    for cfg in CONFIGS:
        k = cfg["key"]
        sub = df[df["config"] == k]
        s = compute_summary(sub)
        lines.append(
            f"| {cfg['label_short']} | {s['n']} | {s['top1_acc']:.2%} | {s['hit2_acc']:.2%} | "
            f"{s['mrr']:.4f} | {s['macro_f1_top1']:.4f} | {s['macro_f1_resolved']:.4f} | "
            f"{s['set_f1_at2']:.4f} | {s['pos2_share']:.2%} | {s['mean_time_s']:.1f}s |"
        )

    lines.append("\n---\n")
    lines.append("## 2. Performance by Difficulty Level\n")
    lines.append("| Config | Difficulty | N | Top-1 Acc | Hit@2 | MRR@2 | Pos-2 Share |")
    lines.append("|--------|-----------|---|-----------|-------|-------|-------------|")
    for cfg in CONFIGS:
        k = cfg["key"]
        for diff in DIFFICULTY_ORDER:
            sub = df[(df["config"] == k) & (df["level"] == diff)]
            if len(sub) == 0:
                continue
            s = compute_summary(sub)
            lines.append(f"| {cfg['label_short']} | {diff} | {s['n']} | {s['top1_acc']:.2%} | "
                         f"{s['hit2_acc']:.2%} | {s['mrr']:.4f} | {s['pos2_share']:.2%} |")

    lines.append("\n---\n")
    lines.append("## 3. Performance by Violation Type\n")
    lines.append("| Config | Violation | N | Top-1 Acc | Hit@2 | MRR@2 | Pos-2 Share |")
    lines.append("|--------|-----------|---|-----------|-------|-------|-------------|")
    for cfg in CONFIGS:
        k = cfg["key"]
        for vt in VIOLATION_LABELS:
            sub = df[(df["config"] == k) & (df["actual"] == vt)]
            if len(sub) == 0:
                continue
            s = compute_summary(sub)
            lines.append(f"| {cfg['label_short']} | {vt} | {s['n']} | {s['top1_acc']:.2%} | "
                         f"{s['hit2_acc']:.2%} | {s['mrr']:.4f} | {s['pos2_share']:.2%} |")

    lines.append("\n---\n")
    lines.append("## 4. Diff Eval — Per-Class Metrics (Top-1 Prediction)\n")
    sub_de = df[df["config"] == "diff_eval"]
    pcm = per_class_metrics(sub_de, "pred1")
    lines.append("| Class | Precision | Recall | F1 | TP | FP | FN |")
    lines.append("|-------|-----------|--------|----|----|----|-----|")
    for _, row in pcm.iterrows():
        lines.append(f"| {row['class']} | {row['precision']:.3f} | {row['recall']:.3f} | "
                     f"{row['f1']:.3f} | {int(row['tp'])} | {int(row['fp'])} | {int(row['fn'])} |")

    lines.append("\n---\n")
    lines.append("## 5. Multi-Violation Detection (Diff Eval)\n")
    sub_de2 = df[df["config"] == "diff_eval"].copy()
    has_dc = sub_de2["detected_count"].notna()
    if has_dc.any():
        sub_dc = sub_de2[has_dc]
        multi = (sub_dc["detected_count"] >= 2).sum()
        total = len(sub_dc)
        gt_anywhere = sub_dc["gt_detected_anywhere"].sum() if "gt_detected_anywhere" in sub_dc else 0
        lines.append(f"- Examples with 2+ violations detected: **{multi}/{total}** ({multi/total:.1%})")
        lines.append(f"- Ground truth detected anywhere in all_checks: **{gt_anywhere}/{total}** ({gt_anywhere/total:.1%})")
        lines.append(f"- Ground truth in Top-2 predictions: **{sub_dc['top2_correct'].sum()}/{total}** ({sub_dc['top2_correct'].mean():.1%})")
        gap = (gt_anywhere - sub_dc["top2_correct"].sum())
        lines.append(f"- Detection gap (detected but not surfaced in Top-2): **{gap}** ({gap/total:.1%})")

    report = "\n".join(lines)
    (outdir / "analysis_report.md").write_text(report, encoding="utf-8")
    print("  Saved analysis_report.md")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Output directory: {OUTDIR}")
    print("Loading data...")

    all_rows = []
    for cfg in CONFIGS:
        path = cfg["path"]
        if not path.exists():
            print(f"  WARNING: {path} not found — skipping")
            continue
        data = safe_json_load(path)
        rows = extract_rows(cfg, data)
        all_rows.extend(rows)
        n = len(rows)
        top2 = sum(r["top2_correct"] for r in rows) / n if n > 0 else 0
        print(f"  {cfg['label_short']}: {n} examples, Hit@2={top2:.2%}")

    if not all_rows:
        print("No data loaded. Exiting.")
        return

    df = pd.DataFrame(all_rows)

    print("\nGenerating plots...")
    plot_01_overall_comparison(df, OUTDIR)
    plot_02_metrics_dashboard(df, OUTDIR)
    plot_03_by_difficulty(df, OUTDIR)
    plot_04_by_violation(df, OUTDIR)
    plot_05_confusion_matrices(df, OUTDIR)
    plot_06_diff_eval_confusion_detail(df, OUTDIR)
    plot_07_difficulty_violation_heatmap(df, OUTDIR)
    plot_08_per_class_f1(df, OUTDIR)
    plot_09_rank_distribution(df, OUTDIR)

    print("\nSaving CSVs and report...")
    save_csvs(df, OUTDIR)
    save_report(df, OUTDIR)

    print(f"\nDone. All outputs in: {OUTDIR}")


if __name__ == "__main__":
    main()
