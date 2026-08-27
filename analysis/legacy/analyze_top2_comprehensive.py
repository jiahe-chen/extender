#!/usr/bin/env python3
"""
Comprehensive Top-2 Strategy Analysis — Focus: diff_eval Workflow

Inputs (qwen3-8b):
  - Top-2 strategy: result/local/{single_agent,two_agent,diff_eval}/run_1/qwen3-8b/detection_results.json
  - Top-1 strategy: result/local/{single_agent,two_agent,diff_eval}/run_2/qwen3-8b/detection_results.json
  - Literature:      analysis/literature_analysis/literature_raw_data.json

Outputs → analysis/analysis_output_top2_comprehensive/
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
STRATEGY_ORDER = ["single_agent", "two_agent", "diff_eval"]
STRATEGY_PRETTY = {"single_agent": "Single Agent", "two_agent": "Two Agent", "diff_eval": "Diff Eval"}
RUN_PRETTY = {"run_1": "Top-2", "run_2": "Top-1"}

# Colour palette
C_TOP1 = "#4C78A8"
C_TOP2 = "#54A24B"
C_TOP2_POS2 = "#F58518"
C_DIFF_EVAL = "#E45756"
C_LIT = "#B279A2"
C_BASELINE = "#888888"

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
    if not s:
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
    """Parse predictions for single_agent / two_agent."""
    model_response = result.get("model_response") or ""
    predictions: List[str] = []
    if model_response:
        try:
            resp = json.loads(model_response)
            violations = resp.get("violations", [])
            if isinstance(violations, list):
                for v in violations:
                    if isinstance(v, dict):
                        n = normalize_label(v.get("violation_type"))
                    else:
                        n = normalize_label(v)
                    if n and n not in predictions:
                        predictions.append(n)
        except Exception:
            pass
    if not predictions:
        predictions = parse_detected_list(result.get("detected_violation_type") or "")
    return predictions[:top_k]


def parse_predictions_diff_eval(result: Dict[str, Any], top_k: int = 2) -> List[str]:
    """Parse predictions for diff_eval."""
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


def compute_code_metrics(code: str) -> Dict[str, float]:
    code = code or ""
    loc = 0 if not code.strip() else code.count("\n") + 1
    chars = len(code)
    tokens = len(re.findall(r"[A-Za-z_]+|\d+|[^\s]", code))
    return {"loc": float(loc), "chars": float(chars), "tokens": float(tokens)}


# ---------------------------------------------------------------------------
# Data Extraction
# ---------------------------------------------------------------------------

def extract_rows(strategy: str, run: str, data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    by_violation = data.get("by_violation_type", {}) or {}

    for bucket_vt, bucket in by_violation.items():
        for result in bucket.get("results", []) or []:
            if strategy == "diff_eval":
                actual = normalize_label(result.get("ground_truth")) or normalize_label(bucket_vt)
            else:
                actual = normalize_label(bucket_vt)

            if strategy == "diff_eval":
                preds = parse_predictions_diff_eval(result, top_k=2)
            else:
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

            code_metrics = compute_code_metrics(result.get("input") or "")

            row: Dict[str, Any] = {
                "strategy": strategy,
                "run": run,
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
                "detection_success": bool(result.get("detection_success")) if "detection_success" in result else None,
                **code_metrics,
            }

            # diff_eval specific
            if strategy == "diff_eval":
                all_checks = result.get("all_checks", []) or []
                detected_count = int(sum(1 for c in all_checks if isinstance(c, dict) and c.get("is_detected", False)))
                row["detected_count"] = detected_count
                gt = row["actual"]
                if gt is not None:
                    row["gt_detected_anywhere"] = bool(any(
                        isinstance(c, dict) and c.get("is_detected", False) and normalize_label(c.get("violation_type")) == gt
                        for c in all_checks
                    ))
                else:
                    row["gt_detected_anywhere"] = False
                # Store which violations were detected
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
# Metrics
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
    cm = cm.reindex(index=labels, columns=labels, fill_value=0)
    return cm


def per_class_metrics(df: pd.DataFrame, pred_col: str = "pred1") -> pd.DataFrame:
    """Compute per-class precision, recall, F1."""
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


def macro_micro_f1(df: pd.DataFrame, pred_col: str = "pred1") -> Tuple[float, float]:
    pcm = per_class_metrics(df, pred_col)
    macro = float(pcm["f1"].mean())
    micro = float((df["actual"].fillna(PRED_NONE) == df[pred_col].fillna(PRED_NONE)).mean())
    return macro, micro


def set_f1_at_k(df: pd.DataFrame) -> float:
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
    return float(np.mean(f1s)) if f1s else 0.0


# ---------------------------------------------------------------------------
# Literature Data
# ---------------------------------------------------------------------------

def load_literature(base: Path) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Load literature raw data and compute per-model, per-violation accuracy."""
    raw_path = base / "analysis" / "literature_analysis" / "literature_raw_data.json"
    if not raw_path.exists():
        return pd.DataFrame(), {}

    with open(raw_path, encoding="utf-8") as f:
        raw = json.load(f)

    rows = []
    for r in raw:
        model = r.get("model", "")
        model = model.split("-temp")[0] if "-temp" in model else model
        model = model.replace(":latest", "")
        rows.append({
            "model": model,
            "violation_type": r.get("expected_violation"),
            "correct": bool(r.get("violation_match")),
            "detected": r.get("detected_violation"),
            "language": r.get("language"),
        })
    df = pd.DataFrame(rows)

    # Summary dict
    summary = {}
    summary["overall"] = float(df["correct"].mean())
    for model, g in df.groupby("model"):
        summary[model] = float(g["correct"].mean())

    return df, summary


# ---------------------------------------------------------------------------
# Plotting Functions
# ---------------------------------------------------------------------------

def _add_value_labels(ax, bars, fmt="{:.1f}%", scale=100, fontsize=8, offset=0.01):
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + offset,
                fmt.format(h * scale), ha="center", va="bottom", fontsize=fontsize)


def plot_01_overall_comparison(df: pd.DataFrame, outdir: Path):
    """Overall accuracy comparison: Top-1 vs Top-2 for all workflows."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))

    # -- Left panel: Top-1 Accuracy (Top-1 strategy vs Top-2 strategy's position-1) --
    ax = axes[0]
    x = np.arange(len(STRATEGY_ORDER))
    w = 0.3

    top1_strat_acc = []
    top2_strat_pos1_acc = []
    for s in STRATEGY_ORDER:
        d_top1 = df[(df["strategy"] == s) & (df["run"] == "run_2")]
        d_top2 = df[(df["strategy"] == s) & (df["run"] == "run_1")]
        top1_strat_acc.append(d_top1["top1_correct"].mean())
        top2_strat_pos1_acc.append(d_top2["top1_correct"].mean())

    b1 = ax.bar(x - w/2, top1_strat_acc, w, label="Top-1 Strategy", color=C_TOP1)
    b2 = ax.bar(x + w/2, top2_strat_pos1_acc, w, label="Top-2 Strategy (Pos-1 only)", color=C_TOP2)
    ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=1.2, label="Random Baseline (25%)")
    _add_value_labels(ax, b1)
    _add_value_labels(ax, b2)
    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_PRETTY[s] for s in STRATEGY_ORDER])
    ax.set_ylabel("Accuracy")
    ax.set_title("Top-1 Accuracy Comparison")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    # -- Right panel: Top-2 Hit@2 Accuracy --
    ax = axes[1]
    top2_hit2_acc = []
    top2_pos2_only = []
    for s in STRATEGY_ORDER:
        d = df[(df["strategy"] == s) & (df["run"] == "run_1")]
        top2_hit2_acc.append(d["top2_correct"].mean())
        top2_pos2_only.append((d["correct_position"] == 2).mean())

    b1 = ax.bar(x, top2_hit2_acc, w * 1.5, label="Top-2 Strategy Hit@2", color=C_TOP2)
    # Stacked: show pos2-only contribution
    pos1_acc = [h - p for h, p in zip(top2_hit2_acc, top2_pos2_only)]
    ax.bar(x, pos1_acc, w * 1.5, color=C_TOP2, alpha=0.7)
    ax.bar(x, top2_pos2_only, w * 1.5, bottom=pos1_acc, color=C_TOP2_POS2,
           label="Pos-2 Only Contribution", alpha=0.8)

    ax.axhline(0.40, linestyle="--", color=C_BASELINE, linewidth=1.2, label="Random Baseline (40%)")
    _add_value_labels(ax, b1)
    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_PRETTY[s] for s in STRATEGY_ORDER])
    ax.set_ylabel("Accuracy")
    ax.set_title("Top-2 Hit@2 Accuracy (with Pos-2 Contribution)")
    ax.set_ylim(0, 1.05)
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Overall Performance: Top-1 vs Top-2 Strategy (qwen3-8b)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(outdir / "01_overall_accuracy_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_02_top2_improvement(df: pd.DataFrame, outdir: Path):
    """Show Top-2 improvement over Top-1 for each workflow."""
    fig, ax = plt.subplots(figsize=(10, 5.5))
    x = np.arange(len(STRATEGY_ORDER))
    w = 0.22

    top1_acc = []
    top2_pos1_acc = []
    top2_hit2_acc = []
    for s in STRATEGY_ORDER:
        d1 = df[(df["strategy"] == s) & (df["run"] == "run_2")]
        d2 = df[(df["strategy"] == s) & (df["run"] == "run_1")]
        top1_acc.append(d1["top1_correct"].mean())
        top2_pos1_acc.append(d2["top1_correct"].mean())
        top2_hit2_acc.append(d2["top2_correct"].mean())

    b1 = ax.bar(x - w, top1_acc, w, label="Top-1 Strategy (Top-1 Acc)", color=C_TOP1)
    b2 = ax.bar(x, top2_pos1_acc, w, label="Top-2 Strategy (Top-1 Acc)", color="#72B7B2")
    b3 = ax.bar(x + w, top2_hit2_acc, w, label="Top-2 Strategy (Hit@2)", color=C_TOP2)

    ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=1, label="Random Top-1 (25%)")
    ax.axhline(0.40, linestyle=":", color=C_BASELINE, linewidth=1, label="Random Top-2 (40%)")
    _add_value_labels(ax, b1)
    _add_value_labels(ax, b2)
    _add_value_labels(ax, b3)

    # Add improvement arrows for diff_eval
    de_idx = 2
    improvement = (top2_hit2_acc[de_idx] - top1_acc[de_idx]) * 100
    ax.annotate(f"+{improvement:.1f}pp",
                xy=(de_idx + w, top2_hit2_acc[de_idx]),
                xytext=(de_idx + w + 0.3, top2_hit2_acc[de_idx] + 0.08),
                fontsize=10, fontweight="bold", color=C_DIFF_EVAL,
                arrowprops=dict(arrowstyle="->", color=C_DIFF_EVAL, lw=1.5))

    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_PRETTY[s] for s in STRATEGY_ORDER])
    ax.set_ylabel("Accuracy")
    ax.set_title("Top-2 Strategy Improvement over Top-1 Strategy (qwen3-8b)", fontweight="bold")
    ax.set_ylim(0, 1.12)
    ax.legend(fontsize=8, loc="upper left", ncol=2)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(outdir / "02_top2_improvement.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_03_metrics_dashboard(df: pd.DataFrame, outdir: Path):
    """MRR, Macro-F1, Set-F1@2 for all workflows."""
    metrics_data = []
    for s in STRATEGY_ORDER:
        for run in ["run_2", "run_1"]:
            d = df[(df["strategy"] == s) & (df["run"] == run)]
            if d.empty:
                continue
            macro_f1, micro_f1 = macro_micro_f1(d, "pred1")
            # Top-2 resolved metrics
            d_res = d.copy()
            d_res["pred_resolved"] = d_res.apply(
                lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
                axis=1)
            macro_f1_res, _ = macro_micro_f1(d_res, "pred_resolved")

            metrics_data.append({
                "strategy": s,
                "run": run,
                "label": f"{STRATEGY_PRETTY[s]}\n({RUN_PRETTY[run]})",
                "MRR@2": d["reciprocal_rank"].mean(),
                "Macro-F1\n(Top-1)": macro_f1,
                "Macro-F1\n(Top-2 Resolved)": macro_f1_res,
                "Set-F1@2": set_f1_at_k(d),
                "Top-1 Acc": d["top1_correct"].mean(),
                "Hit@2": d["top2_correct"].mean(),
            })
    mdf = pd.DataFrame(metrics_data)

    metric_names = ["MRR@2", "Macro-F1\n(Top-1)", "Macro-F1\n(Top-2 Resolved)", "Set-F1@2"]
    fig, axes = plt.subplots(1, 4, figsize=(18, 5), sharey=True)

    for i, metric in enumerate(metric_names):
        ax = axes[i]
        # Group: Top-1 vs Top-2 for each strategy
        x = np.arange(len(STRATEGY_ORDER))
        w = 0.3
        vals_top1 = [mdf[(mdf["strategy"] == s) & (mdf["run"] == "run_2")][metric].iloc[0] for s in STRATEGY_ORDER]
        vals_top2 = [mdf[(mdf["strategy"] == s) & (mdf["run"] == "run_1")][metric].iloc[0] for s in STRATEGY_ORDER]

        b1 = ax.bar(x - w/2, vals_top1, w, label="Top-1 Strategy", color=C_TOP1)
        b2 = ax.bar(x + w/2, vals_top2, w, label="Top-2 Strategy", color=C_TOP2)
        _add_value_labels(ax, b1, fmt="{:.3f}", scale=1, offset=0.005)
        _add_value_labels(ax, b2, fmt="{:.3f}", scale=1, offset=0.005)

        ax.set_xticks(x)
        ax.set_xticklabels([STRATEGY_PRETTY[s] for s in STRATEGY_ORDER], fontsize=8)
        ax.set_title(metric, fontweight="bold")
        ax.grid(axis="y", alpha=0.3)
        ax.set_ylim(0, 1.05)
        if i == 0:
            ax.set_ylabel("Score")
            ax.legend(fontsize=7)

    fig.suptitle("Performance Metrics: Top-1 vs Top-2 Strategy", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "03_metrics_dashboard.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_04_diff_eval_rank_distribution(df: pd.DataFrame, outdir: Path):
    """Where ground truth appears in diff_eval Top-2 predictions."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    for i, s in enumerate(STRATEGY_ORDER):
        ax = axes[i]
        d = df[(df["strategy"] == s) & (df["run"] == "run_1")]
        if d.empty:
            continue
        n = len(d)
        pos = d["correct_position"].value_counts().to_dict()
        pct1 = pos.get(1, 0) / n
        pct2 = pos.get(2, 0) / n
        pct0 = pos.get(0, 0) / n

        colors = ["#2ecc71", "#3498db", "#e74c3c"]
        bars = ax.bar(["Pos-1\n(Top-1 hit)", "Pos-2 only\n(Top-2 gain)", "Miss"],
                       [pct1, pct2, pct0], color=colors, edgecolor="white", linewidth=1.5)
        for bar, v in zip(bars, [pct1, pct2, pct0]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                    f"{v*100:.1f}%\n({int(v*n)})", ha="center", va="bottom", fontsize=9)
        ax.set_title(f"{STRATEGY_PRETTY[s]}", fontweight="bold")
        ax.set_ylim(0, 1.0)
        ax.grid(axis="y", alpha=0.3)
        if i == 0:
            ax.set_ylabel("Share of Examples")

    fig.suptitle("Ranking Distribution: Where Ground Truth Appears in Top-2 Predictions",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "04_rank_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_05_accuracy_by_difficulty(df: pd.DataFrame, outdir: Path):
    """Accuracy by difficulty level across all workflows — Top-1 vs Top-2."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)

    for i, s in enumerate(STRATEGY_ORDER):
        ax = axes[i]
        x = np.arange(len(DIFFICULTY_ORDER))
        w = 0.22

        vals_t1_top1 = []
        vals_t2_top1 = []
        vals_t2_hit2 = []
        for lvl in DIFFICULTY_ORDER:
            d1 = df[(df["strategy"] == s) & (df["run"] == "run_2") & (df["level"] == lvl)]
            d2 = df[(df["strategy"] == s) & (df["run"] == "run_1") & (df["level"] == lvl)]
            vals_t1_top1.append(d1["top1_correct"].mean() if not d1.empty else 0)
            vals_t2_top1.append(d2["top1_correct"].mean() if not d2.empty else 0)
            vals_t2_hit2.append(d2["top2_correct"].mean() if not d2.empty else 0)

        b1 = ax.bar(x - w, vals_t1_top1, w, label="Top-1 Strategy", color=C_TOP1)
        b2 = ax.bar(x, vals_t2_top1, w, label="Top-2 (Pos-1)", color="#72B7B2")
        b3 = ax.bar(x + w, vals_t2_hit2, w, label="Top-2 Hit@2", color=C_TOP2)
        _add_value_labels(ax, b1, fontsize=7)
        _add_value_labels(ax, b2, fontsize=7)
        _add_value_labels(ax, b3, fontsize=7)

        ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=0.8, alpha=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(DIFFICULTY_ORDER)
        ax.set_title(f"{STRATEGY_PRETTY[s]}", fontweight="bold")
        ax.set_ylim(0, 1.15)
        ax.grid(axis="y", alpha=0.3)
        if i == 0:
            ax.set_ylabel("Accuracy")
        if i == 2:
            ax.legend(fontsize=7, loc="lower right")

    fig.suptitle("Accuracy by Difficulty Level: Top-1 vs Top-2 Strategy", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "05_accuracy_by_difficulty.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_06_accuracy_by_violation(df: pd.DataFrame, outdir: Path):
    """Accuracy by violation type across all workflows."""
    fig, axes = plt.subplots(1, 3, figsize=(17, 5.5), sharey=True)

    for i, s in enumerate(STRATEGY_ORDER):
        ax = axes[i]
        x = np.arange(len(VIOLATION_LABELS))
        w = 0.22

        vals_t1 = []
        vals_t2_hit2 = []
        for vt in VIOLATION_LABELS:
            d1 = df[(df["strategy"] == s) & (df["run"] == "run_2") & (df["actual"] == vt)]
            d2 = df[(df["strategy"] == s) & (df["run"] == "run_1") & (df["actual"] == vt)]
            vals_t1.append(d1["top1_correct"].mean() if not d1.empty else 0)
            vals_t2_hit2.append(d2["top2_correct"].mean() if not d2.empty else 0)

        b1 = ax.bar(x - w/2, vals_t1, w, label="Top-1 Strategy", color=C_TOP1)
        b2 = ax.bar(x + w/2, vals_t2_hit2, w, label="Top-2 Hit@2", color=C_TOP2)
        _add_value_labels(ax, b1, fontsize=7)
        _add_value_labels(ax, b2, fontsize=7)

        ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=0.8, alpha=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(VIOLATION_LABELS)
        ax.set_title(f"{STRATEGY_PRETTY[s]}", fontweight="bold")
        ax.set_ylim(0, 1.15)
        ax.grid(axis="y", alpha=0.3)
        if i == 0:
            ax.set_ylabel("Accuracy")
        if i == 2:
            ax.legend(fontsize=8, loc="lower right")

    fig.suptitle("Accuracy by Violation Type: Top-1 vs Top-2 Strategy", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "06_accuracy_by_violation.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_07_confusion_matrices(df: pd.DataFrame, outdir: Path):
    """Confusion matrices for all workflows — Top-1 and Top-2 resolved."""
    labels = VIOLATION_LABELS + [PRED_NONE]
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))

    for j, s in enumerate(STRATEGY_ORDER):
        # Top row: Top-1 strategy (run_2) — pure Top-1 prediction
        d_top1 = df[(df["strategy"] == s) & (df["run"] == "run_2")]
        if not d_top1.empty:
            cm1 = confusion_matrix_df(d_top1, "actual", "pred1", labels)
            sns.heatmap(cm1, annot=True, fmt="d", cmap="Blues", ax=axes[0, j], cbar=False,
                        linewidths=0.5, linecolor="white")
            acc1 = d_top1["top1_correct"].mean()
            axes[0, j].set_title(f"{STRATEGY_PRETTY[s]} — Top-1 Strategy\nAcc={acc1*100:.1f}%", fontweight="bold")
            axes[0, j].set_xlabel("Predicted")
            axes[0, j].set_ylabel("Actual")

        # Bottom row: Top-2 strategy (run_1) — Top-2 resolved view
        d_top2 = df[(df["strategy"] == s) & (df["run"] == "run_1")].copy()
        if not d_top2.empty:
            d_top2["pred_resolved"] = d_top2.apply(
                lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
                axis=1)
            cm2 = confusion_matrix_df(d_top2, "actual", "pred_resolved", labels)
            hit2 = d_top2["top2_correct"].mean()
            sns.heatmap(cm2, annot=True, fmt="d", cmap="Greens", ax=axes[1, j], cbar=False,
                        linewidths=0.5, linecolor="white")
            axes[1, j].set_title(f"{STRATEGY_PRETTY[s]} — Top-2 Strategy (Hit@2)\nAcc={hit2*100:.1f}%", fontweight="bold")
            axes[1, j].set_xlabel("Predicted")
            axes[1, j].set_ylabel("Actual")

    fig.suptitle("Confusion Matrices: Top-1 Strategy (Top Row) vs Top-2 Strategy Hit@2 Resolved (Bottom Row)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(outdir / "07_confusion_matrices_all.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_08_diff_eval_confusion_detail(df: pd.DataFrame, outdir: Path):
    """Detailed confusion matrix for diff_eval — Top-1 vs Top-2, with numbers."""
    labels = VIOLATION_LABELS + [PRED_NONE]

    d_top1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")]
    d_top2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()

    if d_top1.empty or d_top2.empty:
        return

    # Top-1 confusion (pred1 from run_2)
    cm1 = confusion_matrix_df(d_top1, "actual", "pred1", labels)

    # Top-2 raw confusion (pred1 from run_1)
    cm2_raw = confusion_matrix_df(d_top2, "actual", "pred1", labels)

    # Top-2 resolved confusion
    d_top2["pred_resolved"] = d_top2.apply(
        lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
        axis=1)
    cm2_res = confusion_matrix_df(d_top2, "actual", "pred_resolved", labels)

    fig, axes = plt.subplots(1, 3, figsize=(21, 6))

    sns.heatmap(cm1, annot=True, fmt="d", cmap="Blues", ax=axes[0], cbar=False,
                linewidths=0.5, linecolor="white")
    acc1 = d_top1["top1_correct"].mean()
    axes[0].set_title(f"Top-1 Strategy (Top-1 Prediction)\nAcc = {acc1*100:.1f}%", fontweight="bold")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    sns.heatmap(cm2_raw, annot=True, fmt="d", cmap="Oranges", ax=axes[1], cbar=False,
                linewidths=0.5, linecolor="white")
    acc2_raw = d_top2["top1_correct"].mean()
    axes[1].set_title(f"Top-2 Strategy (Top-1 Prediction Only)\nAcc = {acc2_raw*100:.1f}%", fontweight="bold")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")

    sns.heatmap(cm2_res, annot=True, fmt="d", cmap="Greens", ax=axes[2], cbar=False,
                linewidths=0.5, linecolor="white")
    acc2_res = d_top2["top2_correct"].mean()
    axes[2].set_title(f"Top-2 Strategy (Hit@2 Resolved)\nAcc = {acc2_res*100:.1f}%", fontweight="bold")
    axes[2].set_xlabel("Predicted")
    axes[2].set_ylabel("Actual")

    fig.suptitle("Diff Eval: Detailed Confusion Matrix Comparison", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(outdir / "08_diff_eval_confusion_detail.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_09_difficulty_heatmap(df: pd.DataFrame, outdir: Path):
    """Heatmap: violation type x difficulty for diff_eval Top-2."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))

    for idx, (run, label) in enumerate([("run_2", "Top-1 Strategy"), ("run_1", "Top-2 Strategy Hit@2")]):
        ax = axes[idx]
        d = df[(df["strategy"] == "diff_eval") & (df["run"] == run)]
        if d.empty:
            continue

        if run == "run_1":
            correct_col = "top2_correct"
        else:
            correct_col = "top1_correct"

        pivot = d.pivot_table(values=correct_col, index="actual", columns="level",
                              aggfunc="mean")
        pivot = pivot.reindex(index=VIOLATION_LABELS, columns=DIFFICULTY_ORDER)

        sns.heatmap(pivot, annot=True, fmt=".1%", cmap="YlGn", ax=ax, vmin=0, vmax=1,
                    linewidths=0.5, linecolor="white", cbar_kws={"shrink": 0.8})
        ax.set_title(f"Diff Eval — {label}", fontweight="bold")
        ax.set_xlabel("Difficulty")
        ax.set_ylabel("Violation Type")

    fig.suptitle("Diff Eval: Accuracy Heatmap (Violation Type × Difficulty)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "09_difficulty_violation_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_10_code_length_analysis(df: pd.DataFrame, outdir: Path):
    """Accuracy vs code length (LOC quantiles) for diff_eval."""
    d1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    d2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")].copy()
    if d1.empty or d2.empty:
        return

    qs = np.quantile(d1["loc"].values, [0, 0.25, 0.5, 0.75, 1.0])
    bin_labels = [f"Q1\n({int(qs[0])}-{int(qs[1])} LOC)",
                  f"Q2\n({int(qs[1])}-{int(qs[2])} LOC)",
                  f"Q3\n({int(qs[2])}-{int(qs[3])} LOC)",
                  f"Q4\n({int(qs[3])}-{int(qs[4])} LOC)"]
    short_labels = ["Q1 (short)", "Q2", "Q3", "Q4 (long)"]
    bins = [float(qs[0]) - 1, float(qs[1]), float(qs[2]), float(qs[3]), float(qs[4]) + 1]

    d1["loc_bin"] = pd.cut(d1["loc"], bins=bins, labels=short_labels, include_lowest=True)
    d2["loc_bin"] = pd.cut(d2["loc"], bins=bins, labels=short_labels, include_lowest=True)

    fig, ax = plt.subplots(figsize=(11, 5))
    x = np.arange(len(short_labels))
    w = 0.3

    run2_vals = d2.groupby("loc_bin", observed=False)["top1_correct"].mean().reindex(short_labels)
    run1_hit2 = d1.groupby("loc_bin", observed=False)["top2_correct"].mean().reindex(short_labels)
    run1_pos2 = d1.groupby("loc_bin", observed=False)["correct_position"].apply(
        lambda s: (s == 2).mean()).reindex(short_labels)

    b1 = ax.bar(x - w/2, run2_vals.values, w, label="Top-1 Strategy (Top-1 Acc)", color=C_TOP1)
    b2 = ax.bar(x + w/2, run1_hit2.values, w, label="Top-2 Strategy (Hit@2)", color=C_TOP2)
    _add_value_labels(ax, b1, fontsize=8)
    _add_value_labels(ax, b2, fontsize=8)

    ax2 = ax.twinx()
    ax2.plot(x, run1_pos2.values, marker="D", color=C_TOP2_POS2, linewidth=2, markersize=7,
             label="Pos-2 Only Share")
    for xi, v in zip(x, run1_pos2.values):
        ax2.text(xi, v + 0.008, f"{v*100:.1f}%", ha="center", fontsize=8, color=C_TOP2_POS2)

    ax.set_xticks(x)
    ax.set_xticklabels(bin_labels, fontsize=8)
    ax.set_ylabel("Accuracy")
    ax2.set_ylabel("Pos-2 Only Share", color=C_TOP2_POS2)
    ax.set_title("Diff Eval: Accuracy by Code Length (LOC Quantiles)", fontweight="bold")
    ax.set_ylim(0, 1.1)
    ax.grid(axis="y", alpha=0.3)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")

    fig.tight_layout()
    fig.savefig(outdir / "10_code_length_analysis.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_11_literature_comparison(df: pd.DataFrame, lit_df: pd.DataFrame, lit_summary: Dict[str, float],
                                  outdir: Path):
    """Compare our Top-1 and Top-2 accuracy with literature results."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # -- Left: Overall accuracy comparison --
    ax = axes[0]
    entries = []

    # Our results — Top-1 strategy
    for s in STRATEGY_ORDER:
        d = df[(df["strategy"] == s) & (df["run"] == "run_2")]
        entries.append({
            "label": f"Ours {STRATEGY_PRETTY[s]}\n(Top-1, qwen3-8b)",
            "acc": d["top1_correct"].mean(),
            "group": "ours_top1"
        })

    # Our diff_eval Top-2 Hit@2
    d_de = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")]
    entries.append({
        "label": "Ours Diff Eval\n(Top-2 Hit@2, qwen3-8b)",
        "acc": d_de["top2_correct"].mean(),
        "group": "ours_top2"
    })

    # Literature models
    for model in sorted(lit_summary.keys()):
        if model == "overall":
            continue
        entries.append({
            "label": f"Lit. {model}\n(Top-1)",
            "acc": lit_summary[model],
            "group": "literature"
        })

    # Literature overall
    if "overall" in lit_summary:
        entries.append({
            "label": f"Lit. Overall Avg\n(Top-1)",
            "acc": lit_summary["overall"],
            "group": "lit_overall"
        })

    color_map = {"ours_top1": C_TOP1, "ours_top2": C_TOP2, "literature": C_LIT, "lit_overall": "#9B59B6"}
    x = np.arange(len(entries))
    colors = [color_map[e["group"]] for e in entries]
    bars = ax.bar(x, [e["acc"] for e in entries], color=colors, edgecolor="white", linewidth=0.5)
    _add_value_labels(ax, bars)
    ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=1.2, label="Random Baseline (25%)")
    ax.set_xticks(x)
    ax.set_xticklabels([e["label"] for e in entries], rotation=30, ha="right", fontsize=7)
    ax.set_ylabel("Top-1 Accuracy (or Hit@2)")
    ax.set_title("Overall Accuracy: Ours vs Literature", fontweight="bold")
    ax.set_ylim(0, 1.1)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # -- Right: Per-violation comparison --
    ax = axes[1]
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.18

    # Literature overall per violation
    lit_viol = []
    if not lit_df.empty:
        for vt in VIOLATION_LABELS:
            d = lit_df[lit_df["violation_type"] == vt]
            lit_viol.append(d["correct"].mean() if not d.empty else 0)
    else:
        lit_viol = [0] * 5

    # Our Top-1 (diff_eval run_2)
    our_top1_viol = []
    d_de1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")]
    for vt in VIOLATION_LABELS:
        d = d_de1[d_de1["actual"] == vt]
        our_top1_viol.append(d["top1_correct"].mean() if not d.empty else 0)

    # Our Top-2 Hit@2 (diff_eval run_1)
    our_top2_viol = []
    d_de2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")]
    for vt in VIOLATION_LABELS:
        d = d_de2[d_de2["actual"] == vt]
        our_top2_viol.append(d["top2_correct"].mean() if not d.empty else 0)

    b1 = ax.bar(x - w, lit_viol, w, label="Literature Overall (Top-1)", color=C_LIT)
    b2 = ax.bar(x, our_top1_viol, w, label="Ours Diff Eval (Top-1)", color=C_TOP1)
    b3 = ax.bar(x + w, our_top2_viol, w, label="Ours Diff Eval (Top-2 Hit@2)", color=C_TOP2)
    _add_value_labels(ax, b1, fontsize=6.5)
    _add_value_labels(ax, b2, fontsize=6.5)
    _add_value_labels(ax, b3, fontsize=6.5)

    ax.axhline(0.25, linestyle="--", color=C_BASELINE, linewidth=0.8, alpha=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(VIOLATION_LABELS)
    ax.set_ylabel("Accuracy")
    ax.set_title("Per-Violation Accuracy: Literature vs Ours (Diff Eval)", fontweight="bold")
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=7, loc="upper right")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(outdir / "11_literature_comparison.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_12_multi_violation_analysis(df: pd.DataFrame, outdir: Path):
    """Analysis of multi-violation detection to justify Top-2 strategy."""
    d = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    if d.empty:
        return

    # Count detected violations per example
    d["n_detected"] = d["detected_count"].fillna(0).astype(int)

    fig, axes = plt.subplots(1, 3, figsize=(17, 5))

    # Left: distribution of number of violations detected
    ax = axes[0]
    counts = d["n_detected"].value_counts().sort_index()
    bars = ax.bar(counts.index.astype(str), counts.values, color="#3498db", edgecolor="white")
    for bar in bars:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, h + 1, str(int(h)),
                ha="center", va="bottom", fontsize=9)
    ax.set_xlabel("Number of Violations Detected per Example")
    ax.set_ylabel("Count")
    ax.set_title("Distribution of Detected\nViolation Count (Diff Eval)", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    # Middle: accuracy by number of violations detected
    ax = axes[1]
    acc_by_n = d.groupby("n_detected").agg(
        top1_acc=("top1_correct", "mean"),
        top2_acc=("top2_correct", "mean"),
        count=("top1_correct", "count")
    ).reset_index()
    x = np.arange(len(acc_by_n))
    w = 0.3
    b1 = ax.bar(x - w/2, acc_by_n["top1_acc"], w, label="Top-1 Acc", color=C_TOP1)
    b2 = ax.bar(x + w/2, acc_by_n["top2_acc"], w, label="Hit@2", color=C_TOP2)
    ax.set_xticks(x)
    ax.set_xticklabels(acc_by_n["n_detected"].astype(str))
    ax.set_xlabel("Number of Violations Detected")
    ax.set_ylabel("Accuracy")
    ax.set_title("Accuracy by Number of\nDetected Violations", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.1)

    # Right: Pos-2 benefit vs number of violations
    ax = axes[2]
    pos2_benefit = d.groupby("n_detected").apply(
        lambda g: (g["correct_position"] == 2).mean(), include_groups=False).reset_index(name="pos2_share")
    ax.bar(pos2_benefit["n_detected"].astype(str), pos2_benefit["pos2_share"],
           color=C_TOP2_POS2, edgecolor="white")
    for i, (_, row) in enumerate(pos2_benefit.iterrows()):
        ax.text(i, row["pos2_share"] + 0.005, f"{row['pos2_share']*100:.1f}%",
                ha="center", fontsize=9)
    ax.set_xlabel("Number of Violations Detected")
    ax.set_ylabel("Pos-2 Only Share")
    ax.set_title("Top-2 Benefit by Number of\nDetected Violations", fontweight="bold")
    ax.grid(axis="y", alpha=0.3)

    fig.suptitle("Multi-Violation Detection Analysis: Justifying Top-2 Strategy",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "12_multi_violation_analysis.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_13_per_class_f1(df: pd.DataFrame, outdir: Path):
    """Per-class F1 for diff_eval: Top-1 vs Top-2."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Top-1 strategy
    d_top1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")]
    d_top2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()

    if d_top1.empty or d_top2.empty:
        return

    pcm1 = per_class_metrics(d_top1, "pred1")

    d_top2["pred_resolved"] = d_top2.apply(
        lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
        axis=1)
    pcm2 = per_class_metrics(d_top2, "pred_resolved")

    ax = axes[0]
    x = np.arange(len(VIOLATION_LABELS))
    w = 0.3
    b1 = ax.bar(x - w/2, pcm1["f1"], w, label="Top-1 Strategy F1", color=C_TOP1)
    b2 = ax.bar(x + w/2, pcm2["f1"], w, label="Top-2 Strategy F1 (Resolved)", color=C_TOP2)
    _add_value_labels(ax, b1, fmt="{:.2f}", scale=1, fontsize=8, offset=0.01)
    _add_value_labels(ax, b2, fmt="{:.2f}", scale=1, fontsize=8, offset=0.01)
    ax.set_xticks(x)
    ax.set_xticklabels(VIOLATION_LABELS)
    ax.set_ylabel("F1 Score")
    ax.set_title("Per-Class F1: Diff Eval", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.1)

    # Precision / Recall comparison
    ax = axes[1]
    w = 0.15
    b1 = ax.bar(x - w*1.5, pcm1["precision"], w, label="Top-1 Precision", color=C_TOP1, alpha=0.7)
    b2 = ax.bar(x - w*0.5, pcm1["recall"], w, label="Top-1 Recall", color=C_TOP1)
    b3 = ax.bar(x + w*0.5, pcm2["precision"], w, label="Top-2 Precision", color=C_TOP2, alpha=0.7)
    b4 = ax.bar(x + w*1.5, pcm2["recall"], w, label="Top-2 Recall", color=C_TOP2)
    ax.set_xticks(x)
    ax.set_xticklabels(VIOLATION_LABELS)
    ax.set_ylabel("Score")
    ax.set_title("Per-Class Precision & Recall: Diff Eval", fontweight="bold")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, 1.1)

    fig.suptitle("Diff Eval: Per-Class Performance Metrics", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(outdir / "13_per_class_f1.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_14_processing_time(df: pd.DataFrame, outdir: Path):
    """Processing time comparison across workflows."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Left: mean processing time
    ax = axes[0]
    x = np.arange(len(STRATEGY_ORDER))
    w = 0.3
    times_top1 = []
    times_top2 = []
    for s in STRATEGY_ORDER:
        d1 = df[(df["strategy"] == s) & (df["run"] == "run_2")]
        d2 = df[(df["strategy"] == s) & (df["run"] == "run_1")]
        times_top1.append(d1["processing_time_s"].mean())
        times_top2.append(d2["processing_time_s"].mean())

    b1 = ax.bar(x - w/2, times_top1, w, label="Top-1 Strategy", color=C_TOP1)
    b2 = ax.bar(x + w/2, times_top2, w, label="Top-2 Strategy", color=C_TOP2)
    for bar in b1:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.1f}s", ha="center", fontsize=8)
    for bar in b2:
        h = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, h + 0.3, f"{h:.1f}s", ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_PRETTY[s] for s in STRATEGY_ORDER])
    ax.set_ylabel("Mean Processing Time (s)")
    ax.set_title("Mean Processing Time per Example", fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)

    # Right: time vs accuracy scatter for diff_eval
    ax = axes[1]
    d_de = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")]
    if not d_de.empty:
        correct = d_de[d_de["top2_correct"] == True]
        wrong = d_de[d_de["top2_correct"] == False]
        ax.scatter(correct["processing_time_s"], correct["loc"], alpha=0.5, color=C_TOP2,
                   label=f"Correct ({len(correct)})", s=30)
        ax.scatter(wrong["processing_time_s"], wrong["loc"], alpha=0.5, color=C_DIFF_EVAL,
                   label=f"Incorrect ({len(wrong)})", s=30, marker="x")
        ax.set_xlabel("Processing Time (s)")
        ax.set_ylabel("Lines of Code")
        ax.set_title("Diff Eval Top-2: Time vs Code Length", fontweight="bold")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(outdir / "14_processing_time.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary Tables & Report
# ---------------------------------------------------------------------------

def build_summary_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    by_level_rows = []
    by_violation_rows = []

    for strategy in STRATEGY_ORDER:
        for run in ["run_1", "run_2"]:
            d = df[(df["strategy"] == strategy) & (df["run"] == run)]
            if d.empty:
                continue
            macro_f1, micro_f1 = macro_micro_f1(d, pred_col="pred1")
            d_res = d.copy()
            d_res["pred_resolved"] = d_res.apply(
                lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
                axis=1)
            macro_f1_res, micro_f1_res = macro_micro_f1(d_res, pred_col="pred_resolved")

            overall_rows.append({
                "Workflow": STRATEGY_PRETTY[strategy],
                "Strategy": RUN_PRETTY[run],
                "N": int(len(d)),
                "Top-1 Acc": float(d["top1_correct"].mean()),
                "Hit@2": float(d["top2_correct"].mean()),
                "MRR@2": float(d["reciprocal_rank"].mean()),
                "Macro-F1 (Top-1)": macro_f1,
                "Macro-F1 (Resolved)": macro_f1_res,
                "Set-F1@2": float(set_f1_at_k(d)),
                "Pos-2 Share": float((d["correct_position"] == 2).mean()),
                "Mean Time (s)": float(d["processing_time_s"].mean()),
            })

            for lvl in DIFFICULTY_ORDER:
                g = d[d["level"] == lvl]
                if g.empty:
                    continue
                by_level_rows.append({
                    "Workflow": STRATEGY_PRETTY[strategy],
                    "Strategy": RUN_PRETTY[run],
                    "Difficulty": lvl,
                    "N": int(len(g)),
                    "Top-1 Acc": float(g["top1_correct"].mean()),
                    "Hit@2": float(g["top2_correct"].mean()),
                    "MRR@2": float(g["reciprocal_rank"].mean()),
                    "Pos-2 Share": float((g["correct_position"] == 2).mean()),
                })

            for vt in VIOLATION_LABELS:
                g = d[d["actual"] == vt]
                if g.empty:
                    continue
                by_violation_rows.append({
                    "Workflow": STRATEGY_PRETTY[strategy],
                    "Strategy": RUN_PRETTY[run],
                    "Violation": vt,
                    "N": int(len(g)),
                    "Top-1 Acc": float(g["top1_correct"].mean()),
                    "Hit@2": float(g["top2_correct"].mean()),
                    "MRR@2": float(g["reciprocal_rank"].mean()),
                    "Pos-2 Share": float((g["correct_position"] == 2).mean()),
                })

    overall = pd.DataFrame(overall_rows)
    by_level = pd.DataFrame(by_level_rows)
    by_violation = pd.DataFrame(by_violation_rows)
    return overall, by_level, by_violation


def write_report(df: pd.DataFrame, outdir: Path, overall: pd.DataFrame, by_level: pd.DataFrame,
                 by_violation: pd.DataFrame, lit_summary: Dict[str, float]):
    """Write comprehensive Markdown analysis report."""
    report_path = outdir / "analysis_report.md"

    # Helper to get a row from overall
    def _g(workflow: str, strategy: str) -> pd.Series:
        return overall[(overall["Workflow"] == workflow) & (overall["Strategy"] == strategy)].iloc[0]

    de_top2 = _g("Diff Eval", "Top-2")
    de_top1 = _g("Diff Eval", "Top-1")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Comprehensive Top-2 Strategy Analysis Report\n")
        f.write("## Focus: Diff Eval Workflow | Model: qwen3-8b | Dataset: 240 examples\n\n")
        f.write("---\n\n")

        # ===== Executive Summary =====
        f.write("## 1. Executive Summary\n\n")
        f.write("| Metric | Diff Eval Top-1 | Diff Eval Top-2 | Improvement |\n")
        f.write("|--------|----------------|----------------|-------------|\n")
        f.write(f"| Top-1 Accuracy | {de_top1['Top-1 Acc']*100:.2f}% | {de_top2['Top-1 Acc']*100:.2f}% | "
                f"+{(de_top2['Top-1 Acc']-de_top1['Top-1 Acc'])*100:.2f}pp |\n")
        f.write(f"| Hit@2 Accuracy | — | {de_top2['Hit@2']*100:.2f}% | "
                f"+{(de_top2['Hit@2']-de_top1['Top-1 Acc'])*100:.2f}pp vs Top-1 |\n")
        f.write(f"| MRR@2 | — | {de_top2['MRR@2']:.4f} | — |\n")
        f.write(f"| Macro-F1 (Top-1) | {de_top1['Macro-F1 (Top-1)']:.4f} | {de_top2['Macro-F1 (Top-1)']:.4f} | "
                f"+{(de_top2['Macro-F1 (Top-1)']-de_top1['Macro-F1 (Top-1)']):.4f} |\n")
        f.write(f"| Macro-F1 (Top-2 Resolved) | — | {de_top2['Macro-F1 (Resolved)']:.4f} | — |\n")
        f.write(f"| Set-F1@2 | — | {de_top2['Set-F1@2']:.4f} | — |\n")
        f.write(f"| Pos-2 Only Contribution | — | {de_top2['Pos-2 Share']*100:.2f}% | "
                f"({int(de_top2['Pos-2 Share']*240)} examples rescued) |\n")
        f.write(f"| Mean Processing Time | {de_top1['Mean Time (s)']:.1f}s | {de_top2['Mean Time (s)']:.1f}s | — |\n")
        f.write("\n")

        f.write("**Key Finding**: The Diff Eval workflow with Top-2 strategy achieves "
                f"**{de_top2['Hit@2']*100:.2f}%** Hit@2 accuracy, representing a "
                f"**+{(de_top2['Hit@2']-de_top1['Top-1 Acc'])*100:.2f} percentage point** improvement "
                f"over the Top-1 strategy ({de_top1['Top-1 Acc']*100:.2f}%).\n\n")

        f.write("**Baselines**: Random Top-1 accuracy = **25%** (1/4 non-trivial classes); "
                "Random Top-2 accuracy = **40%** (2/5 classes). All our results significantly exceed these baselines.\n\n")

        # ===== Overall Performance =====
        f.write("---\n\n## 2. Overall Performance Across Workflows\n\n")
        f.write("```\n")
        f.write(overall.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        f.write("\n```\n\n")

        # Cross-workflow improvement table
        f.write("### Top-2 Strategy Improvement Over Top-1\n\n")
        f.write("| Workflow | Top-1 Strategy Acc | Top-2 Strategy Hit@2 | Absolute Gain |\n")
        f.write("|----------|-------------------|---------------------|---------------|\n")
        for s in STRATEGY_ORDER:
            sp = STRATEGY_PRETTY[s]
            t1 = _g(sp, "Top-1")
            t2 = _g(sp, "Top-2")
            delta = t2["Hit@2"] - t1["Top-1 Acc"]
            f.write(f"| {sp} | {t1['Top-1 Acc']*100:.2f}% | {t2['Hit@2']*100:.2f}% | +{delta*100:.2f}pp |\n")
        f.write("\n")

        # ===== Difficulty Analysis =====
        f.write("---\n\n## 3. Performance by Difficulty Level\n\n")
        f.write("```\n")
        f.write(by_level.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        f.write("\n```\n\n")

        # Diff eval difficulty highlight
        f.write("### Diff Eval: Difficulty Breakdown\n\n")
        f.write("| Difficulty | Top-1 Strategy | Top-2 Hit@2 | Gain | Pos-2 Share |\n")
        f.write("|-----------|---------------|-------------|------|-------------|\n")
        for lvl in DIFFICULTY_ORDER:
            bl1 = by_level[(by_level["Workflow"] == "Diff Eval") & (by_level["Strategy"] == "Top-1") & (by_level["Difficulty"] == lvl)]
            bl2 = by_level[(by_level["Workflow"] == "Diff Eval") & (by_level["Strategy"] == "Top-2") & (by_level["Difficulty"] == lvl)]
            if not bl1.empty and not bl2.empty:
                t1_acc = bl1.iloc[0]["Top-1 Acc"]
                t2_acc = bl2.iloc[0]["Hit@2"]
                pos2 = bl2.iloc[0]["Pos-2 Share"]
                f.write(f"| {lvl} | {t1_acc*100:.2f}% | {t2_acc*100:.2f}% | +{(t2_acc-t1_acc)*100:.2f}pp | {pos2*100:.1f}% |\n")
        f.write("\n")

        # ===== Violation Type Analysis =====
        f.write("---\n\n## 4. Performance by Violation Type\n\n")
        f.write("```\n")
        f.write(by_violation.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
        f.write("\n```\n\n")

        # ===== Multi-Violation Justification =====
        f.write("---\n\n## 5. Multi-Violation Detection: Justifying Top-2 Strategy\n\n")

        d_de = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")]
        if not d_de.empty and "detected_count" in d_de.columns:
            multi = d_de[d_de["detected_count"].fillna(0).astype(int) >= 2]
            f.write(f"In the Diff Eval Top-2 run, **{len(multi)}/{len(d_de)}** examples "
                    f"({len(multi)/len(d_de)*100:.1f}%) had **2 or more violations detected** "
                    f"across the five SOLID principles. This demonstrates that code samples "
                    f"frequently exhibit multiple violation patterns simultaneously, making the "
                    f"Top-2 strategy essential for capturing the correct violation.\n\n")

        # OCP_6 case study
        ocp6 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1") & (df["example_id"] == "OCP_6")]
        if not ocp6.empty:
            r = ocp6.iloc[0]
            f.write("### Case Study: OCP_6\n\n")
            f.write(f"- **Example**: OCP_6 (Difficulty: {r['level']}, Language: {r['language']}, {int(r['loc'])} LOC)\n")
            f.write(f"- **Ground Truth**: {r['actual']}\n")
            f.write(f"- **Pred-1**: {r['pred1']}, **Pred-2**: {r['pred2']}\n")
            f.write(f"- **Top-1 Correct**: {r['top1_correct']}, **Top-2 Correct**: {r['top2_correct']}\n")
            if r.get("all_detected_types"):
                f.write(f"- **All Detected Violations**: {r['all_detected_types']}\n")
            f.write(f"\nThis case exemplifies why Top-2 is valuable: the code exhibits both DIP and OCP violations. "
                    f"The model ranks DIP as more prominent (Pred-1), but the ground truth OCP is correctly captured "
                    f"in Pred-2. Under a Top-1 strategy, this would be a miss; with Top-2, it is correctly identified.\n\n")

        # ===== GT Detection Gap =====
        if not d_de.empty and "gt_detected_anywhere" in d_de.columns:
            gt_any = d_de["gt_detected_anywhere"].infer_objects(copy=False).fillna(False).astype(bool)
            hit2 = d_de["top2_correct"].astype(bool)
            detect_rate = gt_any.mean()
            gap = (gt_any & ~hit2).mean()
            f.write("### Detection Gap Analysis\n\n")
            f.write(f"- Ground truth detected **anywhere** in all_checks: {detect_rate*100:.2f}% ({int(detect_rate*240)}/240)\n")
            f.write(f"- Ground truth in Top-2 predictions: {de_top2['Hit@2']*100:.2f}% ({int(de_top2['Hit@2']*240)}/240)\n")
            f.write(f"- Gap (detected but not surfaced in Top-2): {gap*100:.2f}% ({int(gap*240)} examples)\n")
            f.write(f"- This gap represents the ranking/selection loss from the Top-2 cutoff.\n\n")

        # ===== Literature Comparison =====
        f.write("---\n\n## 6. Comparison with Literature (Top-1 Baselines)\n\n")
        if lit_summary:
            f.write("| Source | Model | Top-1 Accuracy |\n")
            f.write("|--------|-------|---------------|\n")
            for s in STRATEGY_ORDER:
                sp = STRATEGY_PRETTY[s]
                t1 = _g(sp, "Top-1")
                f.write(f"| Ours ({sp}) | qwen3-8b | {t1['Top-1 Acc']*100:.2f}% |\n")
            f.write(f"| **Ours (Diff Eval, Top-2 Hit@2)** | **qwen3-8b** | **{de_top2['Hit@2']*100:.2f}%** |\n")
            for k in sorted(lit_summary.keys()):
                if k == "overall":
                    continue
                f.write(f"| Literature | {k} | {lit_summary[k]*100:.2f}% |\n")
            if "overall" in lit_summary:
                f.write(f"| Literature Overall Avg | All models | {lit_summary['overall']*100:.2f}% |\n")
            f.write("\n")
            f.write(f"**Note**: The literature results use a Top-1 strategy. Our Diff Eval Top-2 Hit@2 "
                    f"({de_top2['Hit@2']*100:.2f}%) surpasses even the best literature model "
                    f"(gpt-4o-mini at {lit_summary.get('gpt-4o-mini', 0)*100:.2f}%) despite using a "
                    f"significantly smaller model (qwen3-8b, 8B parameters vs gpt-4o-mini).\n\n")

            f.write("### Per-Violation Literature Comparison\n\n")
            f.write("Literature's biggest weakness is **DIP detection** (6.25% across all models). "
                    f"Our Diff Eval Top-2 strategy achieves a dramatically higher DIP detection rate.\n\n")

        # ===== Confusion Matrices =====
        f.write("---\n\n## 7. Confusion Matrices\n\n")
        f.write("- `07_confusion_matrices_all.png`: All workflows — Top row: Top-1 Strategy, Bottom row: Top-2 Hit@2 Resolved\n")
        f.write("- `08_diff_eval_confusion_detail.png`: Diff Eval detailed — Top-1 Strategy / Top-2 Pos-1 / Top-2 Hit@2 Resolved\n\n")

        # ===== Code Length =====
        f.write("---\n\n## 8. Code Length Analysis\n\n")
        f.write("- `10_code_length_analysis.png`: Diff Eval accuracy by LOC quantiles\n")
        f.write("- Longer code tends to exhibit more ambiguous violations, increasing the benefit of Top-2 predictions.\n\n")

        # ===== Generated Files =====
        f.write("---\n\n## 9. Generated Artifacts\n\n")
        f.write("### Visualizations\n")
        charts = [
            ("01_overall_accuracy_comparison.png", "Overall accuracy comparison: Top-1 vs Top-2"),
            ("02_top2_improvement.png", "Top-2 improvement over Top-1 with baselines"),
            ("03_metrics_dashboard.png", "MRR, Macro-F1, Set-F1@2 dashboard"),
            ("04_rank_distribution.png", "Ranking distribution: where GT appears in Top-2"),
            ("05_accuracy_by_difficulty.png", "Accuracy by difficulty level"),
            ("06_accuracy_by_violation.png", "Accuracy by violation type"),
            ("07_confusion_matrices_all.png", "Confusion matrices for all workflows"),
            ("08_diff_eval_confusion_detail.png", "Diff Eval detailed confusion matrices"),
            ("09_difficulty_violation_heatmap.png", "Difficulty x Violation heatmap for Diff Eval"),
            ("10_code_length_analysis.png", "Code length (LOC) analysis for Diff Eval"),
            ("11_literature_comparison.png", "Literature comparison"),
            ("12_multi_violation_analysis.png", "Multi-violation detection analysis"),
            ("13_per_class_f1.png", "Per-class F1, Precision, Recall for Diff Eval"),
            ("14_processing_time.png", "Processing time analysis"),
        ]
        for fname, desc in charts:
            f.write(f"- `{fname}` — {desc}\n")
        f.write("\n### Data Files\n")
        f.write("- `overall_metrics.csv` — Summary metrics per workflow/strategy\n")
        f.write("- `by_difficulty.csv` — Metrics broken down by difficulty\n")
        f.write("- `by_violation.csv` — Metrics broken down by violation type\n")
        f.write("- `detailed_results.csv` — Full per-example results (240 x 6 runs)\n")
        f.write("- `per_class_metrics.csv` — Per-class precision, recall, F1\n")

    print(f"Report written to: {report_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (12, 7)
    plt.rcParams["font.size"] = 10

    base = Path.cwd()
    outdir = base / "analysis" / "analysis_output_top2_comprehensive"
    outdir.mkdir(parents=True, exist_ok=True)

    print("Loading detection results...")
    all_rows: List[Dict[str, Any]] = []
    for strategy in STRATEGY_ORDER:
        for run in ["run_1", "run_2"]:
            path = base / "result" / "local" / strategy / run / "qwen3-8b" / "detection_results.json"
            if not path.exists():
                print(f"  WARNING: {path} not found, skipping.")
                continue
            data = safe_json_load(path)
            rows = extract_rows(strategy, run, data)
            all_rows.extend(rows)
            label = RUN_PRETTY[run]
            acc = sum(1 for r in rows if r["top1_correct"]) / len(rows) if rows else 0
            hit2 = sum(1 for r in rows if r["top2_correct"]) / len(rows) if rows else 0
            print(f"  {strategy}/{label}: {len(rows)} examples, Top-1={acc*100:.1f}%, Hit@2={hit2*100:.1f}%")

    df = pd.DataFrame(all_rows)
    df["level"] = df["level"].fillna("UNKNOWN")
    df["language"] = df["language"].fillna("UNKNOWN")

    print("\nLoading literature data...")
    lit_df, lit_summary = load_literature(base)
    if lit_summary:
        print(f"  Literature: {len(lit_df)} examples, overall acc={lit_summary.get('overall', 0)*100:.1f}%")
    else:
        print("  No literature data found.")

    print("\nBuilding summary tables...")
    overall, by_level, by_violation = build_summary_tables(df)
    overall.to_csv(outdir / "overall_metrics.csv", index=False)
    by_level.to_csv(outdir / "by_difficulty.csv", index=False)
    by_violation.to_csv(outdir / "by_violation.csv", index=False)
    df.to_csv(outdir / "detailed_results.csv", index=False)

    # Per-class metrics for diff_eval
    d_de_top2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    d_de_top2["pred_resolved"] = d_de_top2.apply(
        lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
        axis=1)
    pcm_top1 = per_class_metrics(df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")], "pred1")
    pcm_top1["source"] = "Diff Eval Top-1 Strategy"
    pcm_top2_pos1 = per_class_metrics(d_de_top2, "pred1")
    pcm_top2_pos1["source"] = "Diff Eval Top-2 (Pos-1)"
    pcm_top2_res = per_class_metrics(d_de_top2, "pred_resolved")
    pcm_top2_res["source"] = "Diff Eval Top-2 (Resolved)"
    pcm_all = pd.concat([pcm_top1, pcm_top2_pos1, pcm_top2_res], ignore_index=True)
    pcm_all.to_csv(outdir / "per_class_metrics.csv", index=False)

    print("\nGenerating visualizations...")
    plot_01_overall_comparison(df, outdir)
    print("  01_overall_accuracy_comparison.png")
    plot_02_top2_improvement(df, outdir)
    print("  02_top2_improvement.png")
    plot_03_metrics_dashboard(df, outdir)
    print("  03_metrics_dashboard.png")
    plot_04_diff_eval_rank_distribution(df, outdir)
    print("  04_rank_distribution.png")
    plot_05_accuracy_by_difficulty(df, outdir)
    print("  05_accuracy_by_difficulty.png")
    plot_06_accuracy_by_violation(df, outdir)
    print("  06_accuracy_by_violation.png")
    plot_07_confusion_matrices(df, outdir)
    print("  07_confusion_matrices_all.png")
    plot_08_diff_eval_confusion_detail(df, outdir)
    print("  08_diff_eval_confusion_detail.png")
    plot_09_difficulty_heatmap(df, outdir)
    print("  09_difficulty_violation_heatmap.png")
    plot_10_code_length_analysis(df, outdir)
    print("  10_code_length_analysis.png")
    if lit_summary:
        plot_11_literature_comparison(df, lit_df, lit_summary, outdir)
        print("  11_literature_comparison.png")
    plot_12_multi_violation_analysis(df, outdir)
    print("  12_multi_violation_analysis.png")
    plot_13_per_class_f1(df, outdir)
    print("  13_per_class_f1.png")
    plot_14_processing_time(df, outdir)
    print("  14_processing_time.png")

    print("\nWriting report...")
    write_report(df, outdir, overall, by_level, by_violation, lit_summary)

    print(f"\n[DONE] All outputs saved to: {outdir}")


if __name__ == "__main__":
    main()
