#!/usr/bin/env python3
"""
Top-2 (run_1) vs Top-1 (run_2) analysis across workflows, with diff_eval as the focus.

Inputs (qwen3-8b):
  - Top-2 strategy: result/local/{single_agent,two_agent,diff_eval}/run_1/qwen3-8b/detection_results.json
  - Top-1 strategy: result/local/{single_agent,two_agent,diff_eval}/run_2/qwen3-8b/detection_results.json

Outputs:
  - analysis/analysis_output_top2_diff_eval_focus/*

This script is self-contained (no network) and aims to produce:
  - per-workflow performance (Top-1/Top-2 acc, MRR, F1)
  - cross-workflow comparisons (Top-2 run_1) and Top-2 vs Top-1 (run_2) improvements
  - difficulty (EASY/MODERATE/HARD) and code-length (LOC quantiles) breakdowns
  - confusion matrices (Top-1; plus a "Top-2 resolved" view to reflect Hit@2 usage)
  - literature top-1 accuracy context from analysis/literature_analysis/literature_analysis_report.txt
"""

from __future__ import annotations

import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

# Matplotlib writes cache to ~/.matplotlib by default; in some sandboxed setups it's not writable.
os.environ.setdefault("MPLCONFIGDIR", str(Path.cwd() / ".mplconfig"))

import matplotlib
# Headless backend (prevents macOS GUI-related crashes under sandboxing).
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns


VIOLATION_LABELS = ["SRP", "OCP", "LSP", "ISP", "DIP"]
PRED_NONE = "NONE"


def _safe_read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def safe_json_load(path: Path) -> Dict[str, Any]:
    raw = _safe_read_text(path)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Minimal cleanup for common trailing-comma issues.
        raw2 = raw.replace(",]", "]").replace(",}", "}")
        return json.loads(raw2)


def normalize_label(label: Optional[str]) -> Optional[str]:
    if label is None:
        return None
    s = str(label).strip().upper()
    if not s:
        return None
    # Some outputs might contain extra text; keep only known labels.
    if s in VIOLATION_LABELS:
        return s
    # Try to extract a known label from within the string.
    for v in VIOLATION_LABELS:
        if v in s:
            return v
    return None


def parse_detected_list(detected_violation_type: Any) -> List[str]:
    if not detected_violation_type:
        return []
    s = str(detected_violation_type)
    parts = [p.strip() for p in s.split(",")]
    out: List[str] = []
    for p in parts:
        n = normalize_label(p)
        if n and n not in out:
            out.append(n)
    return out


def parse_predictions_single_or_two_agent(result: Dict[str, Any], top_k: int = 2) -> List[str]:
    model_response = result.get("model_response") or ""
    predictions: List[str] = []

    # Primary: structured JSON in model_response.
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
            # fall back below
            pass

    # Fallback: detected_violation_type is typically a comma-separated list.
    if not predictions:
        predictions = parse_detected_list(result.get("detected_violation_type") or "")

    return predictions[:top_k]


def parse_predictions_diff_eval(result: Dict[str, Any], top_k: int = 2) -> List[str]:
    # Prefer the workflow output field (this is what differs between run_1(top2) and run_2(top1)).
    preds = parse_detected_list(result.get("violation_type"))
    if not preds:
        preds = parse_detected_list(result.get("detected_violation_type"))
    if preds:
        return preds[:top_k]

    # Fallback: infer ordering from detected checks.
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
    # Very rough token proxy: word-like chunks.
    tokens = len(re.findall(r"[A-Za-z_]+|\\d+|[^\\s]", code))
    return {"loc": float(loc), "chars": float(chars), "tokens": float(tokens)}


@dataclass(frozen=True)
class RunKey:
    strategy: str  # single_agent/two_agent/diff_eval
    run: str       # run_1 (top_2) / run_2 (top_1)


def extract_rows(strategy: str, run: str, data: Dict[str, Any], top_k: int = 2) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    by_violation = data.get("by_violation_type", {}) or {}

    for bucket_violation, bucket in by_violation.items():
        for result in bucket.get("results", []) or []:
            # Ground truth label: diff_eval stores it in ground_truth; others use the bucket key.
            if strategy == "diff_eval":
                actual = normalize_label(result.get("ground_truth")) or normalize_label(bucket_violation)
            else:
                actual = normalize_label(bucket_violation)

            if strategy == "diff_eval":
                preds = parse_predictions_diff_eval(result, top_k=top_k)
            else:
                preds = parse_predictions_single_or_two_agent(result, top_k=top_k)

            pred1 = preds[0] if len(preds) > 0 else None
            pred2 = preds[1] if len(preds) > 1 else None

            # Reciprocal rank within top_k.
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
                "level": result.get("level"),
                "language": result.get("language"),
                "actual": actual,
                "pred1": pred1,
                "pred2": pred2,
                "top1_correct": bool(actual is not None and pred1 == actual),
                "top2_correct": bool(actual is not None and (pred1 == actual or pred2 == actual)),
                "reciprocal_rank": rr,
                "correct_position": correct_pos,  # 0/1/2
                "processing_time_s": float(result.get("processing_time_seconds") or 0.0),
                "workflow": result.get("workflow"),
                "detected_violation_type_raw": result.get("detected_violation_type"),
                "detection_success": bool(result.get("detection_success")) if "detection_success" in result else None,
                "detected_count_raw": None,
                **code_metrics,
            }

            if strategy == "diff_eval":
                all_checks = result.get("all_checks", []) or []
                row["detected_count_raw"] = int(sum(1 for c in all_checks if isinstance(c, dict) and c.get("is_detected", False)))
                # Whether the ground-truth label appears anywhere in detected checks.
                gt = row["actual"]
                if gt is not None:
                    row["gt_detected_anywhere"] = bool(any(
                        isinstance(c, dict) and c.get("is_detected", False) and normalize_label(c.get("violation_type")) == gt
                        for c in all_checks
                    ))
                else:
                    row["gt_detected_anywhere"] = False
            else:
                row["gt_detected_anywhere"] = None

            rows.append(row)

    return rows


def confusion_matrix(df: pd.DataFrame, actual_col: str, pred_col: str, labels: List[str]) -> pd.DataFrame:
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


def f1_macro_micro(df: pd.DataFrame, pred_col: str = "pred1") -> Tuple[float, float]:
    """Macro-F1 across the 5 SOLID classes (excludes NONE), micro-F1 across all examples."""
    actual = df["actual"].fillna(PRED_NONE).astype(str)
    pred = df[pred_col].fillna(PRED_NONE).astype(str)

    # Micro-F1 for single-label multiclass equals accuracy.
    micro_f1 = float((actual == pred).mean())

    f1s: List[float] = []
    for lab in VIOLATION_LABELS:
        tp = int(((actual == lab) & (pred == lab)).sum())
        fp = int(((actual != lab) & (pred == lab)).sum())
        fn = int(((actual == lab) & (pred != lab)).sum())
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
    macro_f1 = float(np.mean(f1s)) if f1s else 0.0
    return macro_f1, micro_f1


def f1_set_at_k(df: pd.DataFrame) -> float:
    """Example-averaged set-F1 for top-2 predictions (ground truth is single label)."""
    f1s: List[float] = []
    for _, r in df.iterrows():
        gt = r["actual"]
        preds = [r.get("pred1"), r.get("pred2")]
        pred_set = [p for p in preds if p is not None]
        if gt is None or not pred_set:
            f1s.append(0.0)
            continue
        hit = 1.0 if gt in pred_set else 0.0
        precision = hit / len(set(pred_set))
        recall = hit  # single-label ground truth
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    return float(np.mean(f1s)) if f1s else 0.0


def parse_literature_report(path: Path) -> Dict[str, float]:
    """
    Extract per-model top1 accuracy from literature_analysis_report.txt.
    Returns {"overall": 0.xx, "gpt-4o-mini": 0.xx, ...} in [0,1].
    """
    text = _safe_read_text(path)
    out: Dict[str, float] = {}

    m_overall = re.search(r"Overall Accuracy:\s*([0-9.]+)%", text)
    if m_overall:
        out["overall"] = float(m_overall.group(1)) / 100.0

    lines = text.splitlines()

    # Parse only the "ACCURACY BY MODEL" section to avoid mixing in per-violation blocks.
    start = None
    end = None
    for i, line in enumerate(lines):
        if "## ACCURACY BY MODEL" in line:
            start = i + 1
        if "## ACCURACY BY VIOLATION TYPE" in line and start is not None:
            end = i
            break
    section = lines[start:end] if start is not None else lines

    # Line-oriented parse: <model>:\n ... \n  Accuracy: xx%
    cur_model: Optional[str] = None
    for line in section:
        s = line.strip()
        if not s:
            continue
        if s.endswith(":") and not s.startswith("#") and " " not in s[:-1]:
            # e.g., "gpt-4o-mini:"
            cur_model = s[:-1]
            continue
        if cur_model:
            m = re.search(r"Accuracy:\s*([0-9.]+)%", s)
            if m:
                out[cur_model] = float(m.group(1)) / 100.0
                cur_model = None

    return out


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_overall_accuracy(df: pd.DataFrame, outdir: Path) -> None:
    # Bars: run_2 Top-1, run_1 Top-1, run_1 Top-2
    rows = []
    for strategy in ["single_agent", "two_agent", "diff_eval"]:
        for run in ["run_2", "run_1"]:
            d = df[(df["strategy"] == strategy) & (df["run"] == run)]
            if d.empty:
                continue
            rows.append({
                "strategy": strategy,
                "run": run,
                "top1_acc": d["top1_correct"].mean(),
                "top2_acc": d["top2_correct"].mean(),
                "mrr": d["reciprocal_rank"].mean(),
            })
    mdf = pd.DataFrame(rows)

    order = ["single_agent", "two_agent", "diff_eval"]
    pretty = {s: s.replace("_", " ").title() for s in order}
    x = np.arange(len(order))
    w = 0.25

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

    # Left: Top-1 accuracies (run_2 vs run_1)
    ax = axes[0]
    run2 = [mdf[(mdf["strategy"] == s) & (mdf["run"] == "run_2")]["top1_acc"].iloc[0] for s in order]
    run1_top1 = [mdf[(mdf["strategy"] == s) & (mdf["run"] == "run_1")]["top1_acc"].iloc[0] for s in order]
    ax.bar(x - w/2, run2, w, label="Top-1 strategy (run_2) Top-1 Acc", color="#4C78A8")
    ax.bar(x + w/2, run1_top1, w, label="Top-2 strategy (run_1) Top-1 Acc", color="#F58518")
    ax.axhline(0.25, linestyle="--", color="gray", linewidth=1, label="Random baseline (Top-1 = 25%)")
    ax.set_xticks(x)
    ax.set_xticklabels([pretty[s] for s in order])
    ax.set_ylabel("Accuracy")
    ax.set_title("Top-1 Accuracy: run_2 (Top-1) vs run_1 (Top-2 prompt, position-1)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8)

    # Right: Top-2 accuracies (run_1)
    ax = axes[1]
    run1_top2 = [mdf[(mdf["strategy"] == s) & (mdf["run"] == "run_1")]["top2_acc"].iloc[0] for s in order]
    ax.bar(x, run1_top2, w * 1.4, label="Top-2 strategy (run_1) Hit@2", color="#54A24B")
    ax.axhline(0.40, linestyle="--", color="gray", linewidth=1, label="Random baseline (Top-2 = 40%)")
    ax.set_xticks(x)
    ax.set_xticklabels([pretty[s] for s in order])
    ax.set_title("Top-2 Accuracy (Hit@2): run_1")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(outdir / "01_overall_accuracy_top1_top2.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_diff_eval_rank_distribution(df: pd.DataFrame, outdir: Path) -> None:
    d = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    if d.empty:
        return
    pos = d["correct_position"].value_counts().to_dict()
    n = len(d)
    pct1 = pos.get(1, 0) / n
    pct2 = pos.get(2, 0) / n
    pct0 = pos.get(0, 0) / n

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(["Pos1 (Top1)", "Pos2 only", "Miss"], [pct1, pct2, pct0], color=["#2ecc71", "#3498db", "#e74c3c"])
    ax.set_ylabel("Share of examples")
    ax.set_title("diff_eval (run_1) ranking distribution: where GT appears in Top-2")
    for i, v in enumerate([pct1, pct2, pct0]):
        ax.text(i, v + 0.01, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(outdir / "02_diff_eval_rank_distribution.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_accuracy_by_difficulty(df: pd.DataFrame, outdir: Path) -> None:
    levels = ["EASY", "MODERATE", "HARD"]
    strategies = ["single_agent", "two_agent", "diff_eval"]
    pretty = {s: s.replace("_", " ").title() for s in strategies}

    rows = []
    for strategy in strategies:
        for run in ["run_2", "run_1"]:
            d0 = df[(df["strategy"] == strategy) & (df["run"] == run)]
            if d0.empty:
                continue
            for lvl in levels:
                d = d0[d0["level"] == lvl]
                if d.empty:
                    continue
                rows.append({
                    "strategy": strategy,
                    "run": run,
                    "level": lvl,
                    "top1_acc": d["top1_correct"].mean(),
                    "top2_acc": d["top2_correct"].mean(),
                    "pos2_benefit": (d["correct_position"] == 2).mean(),
                })
    mdf = pd.DataFrame(rows)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    for i, strategy in enumerate(strategies):
        ax = axes[i]
        sub = mdf[mdf["strategy"] == strategy]
        # Compare run_2 top1 vs run_1 top2 per level.
        x = np.arange(len(levels))
        w = 0.35
        run2 = [sub[(sub["run"] == "run_2") & (sub["level"] == lvl)]["top1_acc"].iloc[0] for lvl in levels]
        run1 = [sub[(sub["run"] == "run_1") & (sub["level"] == lvl)]["top2_acc"].iloc[0] for lvl in levels]
        ax.bar(x - w/2, run2, w, label="run_2 Top-1", color="#4C78A8")
        ax.bar(x + w/2, run1, w, label="run_1 Hit@2", color="#54A24B")
        ax.set_xticks(x)
        ax.set_xticklabels(levels)
        ax.set_title(f"{pretty[strategy]}: Accuracy by Difficulty")
        ax.grid(axis="y", alpha=0.3)
        if i == 0:
            ax.set_ylabel("Accuracy")
        if i == 2:
            ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(outdir / "03_accuracy_by_difficulty.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_diff_eval_accuracy_by_loc(df: pd.DataFrame, outdir: Path) -> None:
    d1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    d2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")].copy()
    if d1.empty or d2.empty:
        return

    # Use run_1 distribution to define bins, then apply to both.
    qs = np.quantile(d1["loc"].values, [0, 0.25, 0.5, 0.75, 1.0])
    # Ensure strictly increasing bins.
    bins = [float(qs[0]), float(qs[1] + 1e-9), float(qs[2] + 2e-9), float(qs[3] + 3e-9), float(qs[4] + 4e-9)]
    labels = ["Q1 (short)", "Q2", "Q3", "Q4 (long)"]

    def assign_bin(x: float) -> str:
        # pd.cut needs right-closed; keep manual to avoid edge issues.
        for i in range(4):
            if i < 3 and bins[i] <= x < bins[i + 1]:
                return labels[i]
            if i == 3 and bins[i] <= x <= bins[i + 1]:
                return labels[i]
        return labels[-1]

    d1["loc_bin"] = d1["loc"].apply(assign_bin)
    d2["loc_bin"] = d2["loc"].apply(assign_bin)

    run1_hit2 = d1.groupby("loc_bin")["top2_correct"].mean().reindex(labels)
    run2_top1 = d2.groupby("loc_bin")["top1_correct"].mean().reindex(labels)
    run1_pos2 = d1.groupby("loc_bin")["correct_position"].apply(lambda s: (s == 2).mean()).reindex(labels)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w/2, run2_top1.values, w, label="Top-1 strategy (run_2) Top-1", color="#4C78A8")
    ax.bar(x + w/2, run1_hit2.values, w, label="Top-2 strategy (run_1) Hit@2", color="#54A24B")
    ax2 = ax.twinx()
    ax2.plot(x, run1_pos2.values, marker="o", color="#F58518", label="run_1 Pos2-only share")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Accuracy")
    ax2.set_ylabel("Pos2-only share")
    ax.set_title("diff_eval: accuracy vs code length (LOC quantiles)")
    ax.grid(axis="y", alpha=0.3)

    # Merge legends.
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")

    fig.tight_layout()
    fig.savefig(outdir / "04_diff_eval_accuracy_by_loc.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_diff_eval(df: pd.DataFrame, outdir: Path) -> None:
    labels = VIOLATION_LABELS + [PRED_NONE]
    d_run2 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_2")].copy()
    d_run1 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    if d_run1.empty or d_run2.empty:
        return

    # Top-1 confusion for run_2.
    cm_run2 = confusion_matrix(d_run2, "actual", "pred1", labels)

    # "Top-2 resolved" view for run_1: if GT is present in top2, treat it as predicted correctly.
    d_run1["pred_top2_resolved"] = d_run1.apply(
        lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
        axis=1,
    )
    cm_run1_resolved = confusion_matrix(d_run1, "actual", "pred_top2_resolved", labels)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.heatmap(cm_run2, annot=True, fmt="d", cmap="Blues", ax=axes[0], cbar=False)
    axes[0].set_title("diff_eval run_2 (Top-1 strategy) confusion (Top-1)")
    axes[0].set_xlabel("Predicted")
    axes[0].set_ylabel("Actual")

    sns.heatmap(cm_run1_resolved, annot=True, fmt="d", cmap="Greens", ax=axes[1], cbar=False)
    axes[1].set_title("diff_eval run_1 (Top-2 strategy) confusion (Top-2 resolved / Hit@2)")
    axes[1].set_xlabel("Predicted")
    axes[1].set_ylabel("Actual")

    fig.tight_layout()
    fig.savefig(outdir / "05_confusion_matrices_diff_eval.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_confusion_all_workflows(df: pd.DataFrame, outdir: Path) -> None:
    labels = VIOLATION_LABELS + [PRED_NONE]
    strategies = ["single_agent", "two_agent", "diff_eval"]
    pretty = {s: s.replace("_", " ").title() for s in strategies}

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    for j, strategy in enumerate(strategies):
        d_run2 = df[(df["strategy"] == strategy) & (df["run"] == "run_2")].copy()
        d_run1 = df[(df["strategy"] == strategy) & (df["run"] == "run_1")].copy()
        if d_run2.empty or d_run1.empty:
            continue

        cm_run2 = confusion_matrix(d_run2, "actual", "pred1", labels)
        sns.heatmap(cm_run2, annot=False, fmt="d", cmap="Blues", ax=axes[0, j], cbar=False)
        axes[0, j].set_title(f"{pretty[strategy]} run_2 (Top-1)\\nTop-1 confusion")
        axes[0, j].set_xlabel("Predicted")
        axes[0, j].set_ylabel("Actual")

        d_run1["pred_top2_resolved"] = d_run1.apply(
            lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
            axis=1,
        )
        cm_run1 = confusion_matrix(d_run1, "actual", "pred_top2_resolved", labels)
        sns.heatmap(cm_run1, annot=False, fmt="d", cmap="Greens", ax=axes[1, j], cbar=False)
        axes[1, j].set_title(f"{pretty[strategy]} run_1 (Top-2)\\nTop-2 resolved / Hit@2")
        axes[1, j].set_xlabel("Predicted")
        axes[1, j].set_ylabel("Actual")

    fig.tight_layout()
    fig.savefig(outdir / "07_confusion_matrices_all_workflows.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_literature_vs_ours(df: pd.DataFrame, outdir: Path, literature: Dict[str, float]) -> None:
    # Compare top-1 accuracies (all are top1-style) with baseline 25%.
    rows = []
    for strategy in ["single_agent", "two_agent", "diff_eval"]:
        d = df[(df["strategy"] == strategy) & (df["run"] == "run_2")]
        rows.append((f"ours_qwen3-8b_{strategy}", float(d["top1_correct"].mean())))
    # Literature
    for k, v in literature.items():
        if k == "overall":
            continue
        rows.append((f"lit_{k}", float(v)))
    if "overall" in literature:
        rows.append(("lit_overall", float(literature["overall"])))

    # Order: ours first, then literature, then overall.
    order = [r[0] for r in rows if r[0].startswith("ours_")] + \
            sorted([r[0] for r in rows if r[0].startswith("lit_") and r[0] != "lit_overall"]) + \
            (["lit_overall"] if any(r[0] == "lit_overall" for r in rows) else [])
    vals = {k: v for k, v in rows}

    fig, ax = plt.subplots(figsize=(12, 4.8))
    x = np.arange(len(order))
    y = [vals[k] for k in order]
    ax.bar(x, y, color=["#4C78A8" if k.startswith("ours_") else "#B279A2" for k in order])
    ax.axhline(0.25, linestyle="--", color="gray", linewidth=1, label="Random baseline (Top-1 = 25%)")
    ax.set_xticks(x)
    ax.set_xticklabels(order, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Top-1 Accuracy")
    ax.set_title("Top-1 accuracy: ours (run_2) vs literature (top1)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(outdir / "06_literature_vs_ours_top1.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def build_summary_tables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    overall_rows = []
    by_level_rows = []
    by_violation_rows = []

    for strategy in ["single_agent", "two_agent", "diff_eval"]:
        for run in ["run_1", "run_2"]:
            d = df[(df["strategy"] == strategy) & (df["run"] == run)]
            if d.empty:
                continue
            macro_f1, micro_f1 = f1_macro_micro(d, pred_col="pred1")
            d_res = d.copy()
            d_res["pred_top2_resolved"] = d_res.apply(
                lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
                axis=1,
            )
            macro_f1_res, micro_f1_res = f1_macro_micro(d_res, pred_col="pred_top2_resolved")
            overall_rows.append({
                "strategy": strategy,
                "run": run,
                "n": int(len(d)),
                "top1_acc": float(d["top1_correct"].mean()),
                "top2_acc": float(d["top2_correct"].mean()),
                "mrr@2": float(d["reciprocal_rank"].mean()),
                "macro_f1_top1": macro_f1,
                "micro_f1_top1": micro_f1,
                "macro_f1_top2_resolved": macro_f1_res,
                "micro_f1_top2_resolved": micro_f1_res,
                "set_f1@2": float(f1_set_at_k(d)),
                "pos2_only_share": float((d["correct_position"] == 2).mean()),
                "mean_time_s": float(d["processing_time_s"].mean()),
                "median_time_s": float(d["processing_time_s"].median()),
                "mean_loc": float(d["loc"].mean()),
            })

            for lvl, g in d.groupby("level"):
                macro_f1_l, micro_f1_l = f1_macro_micro(g, pred_col="pred1")
                g_res = g.copy()
                g_res["pred_top2_resolved"] = g_res.apply(
                    lambda r: r["actual"] if (r["actual"] is not None and r["actual"] in [r.get("pred1"), r.get("pred2")]) else r.get("pred1"),
                    axis=1,
                )
                macro_f1_l_res, micro_f1_l_res = f1_macro_micro(g_res, pred_col="pred_top2_resolved")
                by_level_rows.append({
                    "strategy": strategy,
                    "run": run,
                    "level": lvl,
                    "n": int(len(g)),
                    "top1_acc": float(g["top1_correct"].mean()),
                    "top2_acc": float(g["top2_correct"].mean()),
                    "mrr@2": float(g["reciprocal_rank"].mean()),
                    "macro_f1_top1": macro_f1_l,
                    "macro_f1_top2_resolved": macro_f1_l_res,
                    "set_f1@2": float(f1_set_at_k(g)),
                    "pos2_only_share": float((g["correct_position"] == 2).mean()),
                    "mean_loc": float(g["loc"].mean()),
                })

            for vt, g in d.groupby("actual"):
                if vt is None:
                    continue
                by_violation_rows.append({
                    "strategy": strategy,
                    "run": run,
                    "violation": vt,
                    "n": int(len(g)),
                    "top1_acc": float(g["top1_correct"].mean()),
                    "top2_acc": float(g["top2_correct"].mean()),
                    "mrr@2": float(g["reciprocal_rank"].mean()),
                    "pos2_only_share": float((g["correct_position"] == 2).mean()),
                })

    overall = pd.DataFrame(overall_rows).sort_values(["run", "strategy"])
    by_level = pd.DataFrame(by_level_rows).sort_values(["run", "strategy", "level"])
    by_violation = pd.DataFrame(by_violation_rows).sort_values(["run", "strategy", "violation"])
    return overall, by_level, by_violation


def write_report(df: pd.DataFrame, outdir: Path, overall: pd.DataFrame, by_level: pd.DataFrame,
                 by_violation: pd.DataFrame, literature: Dict[str, float]) -> None:
    report = outdir / "analysis_report.md"

    # Focus metrics for diff_eval.
    def _get(strategy: str, run: str) -> pd.Series:
        return overall[(overall["strategy"] == strategy) & (overall["run"] == run)].iloc[0]

    de_run1 = _get("diff_eval", "run_1")
    de_run2 = _get("diff_eval", "run_2")
    de_improve = float(de_run1["top2_acc"] - de_run2["top1_acc"])
    de_pos2 = float(de_run1["pos2_only_share"])

    # Cross-workflow snapshot for run_1.
    r1 = overall[overall["run"] == "run_1"].copy()
    best_hit2 = r1.sort_values("top2_acc", ascending=False).iloc[0]
    best_time = r1.sort_values("mean_time_s", ascending=True).iloc[0]

    # Top-2 vs Top-1 deltas (run_1 Hit@2 - run_2 Top-1).
    delta_rows = []
    for s in ["single_agent", "two_agent", "diff_eval"]:
        r1 = _get(s, "run_1")
        r2 = _get(s, "run_2")
        delta_rows.append({
            "workflow": s,
            "run_2_top1_acc": float(r2["top1_acc"]),
            "run_1_hit@2": float(r1["top2_acc"]),
            "abs_delta": float(r1["top2_acc"] - r2["top1_acc"]),
        })
    delta_df = pd.DataFrame(delta_rows)

    # diff_eval: ranking gap (GT detected somewhere but not surfaced in Top-2).
    d_de = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1")].copy()
    if not d_de.empty and "gt_detected_anywhere" in d_de.columns:
        gt_any = d_de["gt_detected_anywhere"].fillna(False).astype(bool)
        hit2 = d_de["top2_correct"].astype(bool)
        de_detect_any_rate = float(gt_any.mean())
        de_gap_rate = float((gt_any & ~hit2).mean())
    else:
        de_detect_any_rate = None
        de_gap_rate = None

    # OCP_6 case (diff_eval run_1).
    ocp6 = df[(df["strategy"] == "diff_eval") & (df["run"] == "run_1") & (df["example_id"] == "OCP_6")]
    ocp6_txt = ""
    if not ocp6.empty:
        r = ocp6.iloc[0]
        ocp6_txt = (
            f"- `OCP_6` (HARD, {int(r['loc'])} LOC): `pred1={r['pred1']}` / `pred2={r['pred2']}` / `actual={r['actual']}`；"
            f"Top-1错误但Top-2命中（Pos2-only={r['correct_position']==2}）。\n"
        )

    # Literature short table.
    lit_lines = []
    if literature:
        overall_lit = literature.get("overall")
        if overall_lit is not None:
            lit_lines.append(f"- 文献overall(top1): {overall_lit*100:.2f}%")
        for k in sorted([k for k in literature.keys() if k not in {"overall"}]):
            lit_lines.append(f"- 文献 {k} (top1): {literature[k]*100:.2f}%")

    # Baseline note: user requested 25%/40%.
    baseline_note = (
        "备注：按你的要求在图中标注随机baseline：Top-1=25%，Top-2=40%。"
        "（Top-2=2/5=40%与5类标签一致；Top-1=25%对应4类假设，若按5类则应为20%。）"
    )

    with report.open("w", encoding="utf-8") as f:
        f.write("# Top-2策略数据分析（重点：diff_eval）\n\n")
        f.write("数据范围：qwen3-8b，240样本；Top-2策略=run_1；Top-1策略=run_2；workflow=single_agent/two_agent/diff_eval。\n\n")

        f.write("## 关键结论（diff_eval优先）\n")
        f.write(f"- diff_eval：run_2 Top-1 Acc={de_run2['top1_acc']*100:.2f}%；run_1 Hit@2={de_run1['top2_acc']*100:.2f}%；绝对提升=+{de_improve*100:.2f}%\n")
        f.write(f"- diff_eval：MRR@2={de_run1['mrr@2']:.4f}；Top-2的“Pos2-only贡献”={de_pos2*100:.2f}%（Top-1错但Top-2命中）\n")
        if de_detect_any_rate is not None and de_gap_rate is not None:
            f.write(f"- diff_eval：GT在all_checks“被检测到(任意位置)”的比例={de_detect_any_rate*100:.2f}%；但未进入Top-2的比例={de_gap_rate*100:.2f}%（Top-2排序/裁剪损失）\n")
        f.write(
            f"- run_1横向对比：Hit@2最高的是{best_hit2['strategy']}={best_hit2['top2_acc']*100:.2f}%；"
            f"但diff_eval的平均耗时={de_run1['mean_time_s']:.1f}s/样本（single/two agent为秒级）\n"
        )
        f.write(f"- {baseline_note}\n\n")

        f.write("## Top-2相对Top-1的提升（run_1 Hit@2 vs run_2 Top-1）\n")
        f.write("```text\n")
        f.write(delta_df.to_string(index=False, float_format="{:.4f}".format))
        f.write("\n```\n\n")

        f.write("## Overall Performance（各workflow）\n")
        f.write("```text\n")
        f.write(overall.to_string(index=False, float_format="{:.4f}".format))
        f.write("\n```\n\n")

        f.write("## 按难度（EASY/MODERATE/HARD）\n")
        f.write("```text\n")
        f.write(by_level.to_string(index=False, float_format="{:.4f}".format))
        f.write("\n```\n\n")

        f.write("## 按Violation类型（SRP/OCP/LSP/ISP/DIP）\n")
        f.write("```text\n")
        f.write(by_violation.to_string(index=False, float_format="{:.4f}".format))
        f.write("\n```\n\n")

        f.write("## Confusion Matrix（重点diff_eval）\n")
        f.write("- 图：`05_confusion_matrices_diff_eval.png` 左=run_2 Top-1；右=run_1 Top-2 resolved/Hit@2（用于体现Top-2可覆盖的错误）\n\n")
        f.write("## Confusion Matrix（全部workflow）\n")
        f.write("- 图：`07_confusion_matrices_all_workflows.png` 上排=run_2 Top-1；下排=run_1 Top-2 resolved/Hit@2\n\n")

        f.write("## 代码难度/长度：Top-2在长代码上的收益（diff_eval）\n")
        f.write("- 图：`04_diff_eval_accuracy_by_loc.png`（按LOC四分位）\n")
        f.write("- 直觉：长输入更容易出现“多个violations并存/边界模糊”，Top-2能减少把次优候选挤到Top-1之外带来的误判。\n\n")

        f.write("## 关键案例：长代码多violations（用于justify Top-2）\n")
        if ocp6_txt:
            f.write(ocp6_txt)
        else:
            f.write("- 未在diff_eval run_1中定位到`OCP_6`（如example_id不同可再查）。\n")
        f.write("\n")

        f.write("## Literature（Top-1）对齐对比\n")
        if lit_lines:
            f.write("\n".join(lit_lines) + "\n")
            f.write("- 图：`06_literature_vs_ours_top1.png`（注意：文献数据集与本项目数据集不完全一致，这里主要用于量级对齐/参考）\n")
        else:
            f.write("- 未解析到文献报告数据。\n")
        f.write("\n")

        f.write("## 生成的图表/文件\n")
        f.write("- `01_overall_accuracy_top1_top2.png`\n")
        f.write("- `02_diff_eval_rank_distribution.png`\n")
        f.write("- `03_accuracy_by_difficulty.png`\n")
        f.write("- `04_diff_eval_accuracy_by_loc.png`\n")
        f.write("- `05_confusion_matrices_diff_eval.png`\n")
        f.write("- `06_literature_vs_ours_top1.png`\n")
        f.write("- `07_confusion_matrices_all_workflows.png`\n")
        f.write("- `overall_metrics.csv`, `by_difficulty.csv`, `by_violation.csv`\n")


def main() -> None:
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (12, 7)

    base = Path.cwd()
    outdir = base / "analysis" / "analysis_output_top2_diff_eval_focus"
    ensure_dir(outdir)

    # Load all six runs.
    strategies = ["single_agent", "two_agent", "diff_eval"]
    runs = ["run_1", "run_2"]

    all_rows: List[Dict[str, Any]] = []
    for strategy in strategies:
        for run in runs:
            path = base / "result" / "local" / strategy / run / "qwen3-8b" / "detection_results.json"
            data = safe_json_load(path)
            all_rows.extend(extract_rows(strategy, run, data, top_k=2))

    df = pd.DataFrame(all_rows)

    # Normalize a few fields.
    df["level"] = df["level"].fillna("UNKNOWN")
    df["language"] = df["language"].fillna("UNKNOWN")

    # Summary tables.
    overall, by_level, by_violation = build_summary_tables(df)
    overall.to_csv(outdir / "overall_metrics.csv", index=False)
    by_level.to_csv(outdir / "by_difficulty.csv", index=False)
    by_violation.to_csv(outdir / "by_violation.csv", index=False)
    df.to_csv(outdir / "detailed_results.csv", index=False)

    # Literature parse.
    lit_path = base / "analysis" / "literature_analysis" / "literature_analysis_report.txt"
    literature = parse_literature_report(lit_path) if lit_path.exists() else {}

    # Plots.
    plot_overall_accuracy(df, outdir)
    plot_diff_eval_rank_distribution(df, outdir)
    plot_accuracy_by_difficulty(df, outdir)
    plot_diff_eval_accuracy_by_loc(df, outdir)
    plot_confusion_diff_eval(df, outdir)
    plot_confusion_all_workflows(df, outdir)
    if literature:
        plot_literature_vs_ours(df, outdir, literature)

    # Report.
    write_report(df, outdir, overall, by_level, by_violation, literature)

    print(f"[OK] Wrote outputs to: {outdir}")


if __name__ == "__main__":
    main()
