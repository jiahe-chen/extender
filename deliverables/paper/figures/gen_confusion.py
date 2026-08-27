"""
Generate a Top-2 resolved confusion matrix for Diff Eval (Qwen3.5-9B).
Style matches the bar-chart figures (same font, color palette, clean look).
"""
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

DATA_PATH = '/Users/he/jcSOLID/result/local/diff_eval/run_top2_new_model/qwen3-5-9b/detection_results.json'
CLASSES = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
N = len(CLASSES)

# ── same global style as gen_paper_figures.py ─────────────────────────────────
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 13})

C_DIFF   = '#ED7D31'   # orange – same as Diff Eval bars
C_HIT    = '#ED7D31'   # diagonal (correct) cells
C_MISS   = '#F8CBAD'   # light orange – off-diagonal (wrong) cells
C_ZERO   = '#FFFFFF'   # white – zero cells
C_GREEN  = '#27AE60'   # diagonal border

# ── read JSON and build confusion matrix ──────────────────────────────────────
with open(DATA_PATH) as f:
    data = json.load(f)

cm = np.zeros((N, N), dtype=int)
undetected = {c: 0 for c in CLASSES}

for principle in CLASSES:
    for r in data['by_violation_type'][principle]['results']:
        actual = r.get('ground_truth') or principle
        vt     = r.get('violation_type', '') or ''
        preds  = [x.strip() for x in str(vt).split(',') if x.strip()][:2]
        t2     = actual in preds[:2]
        if actual not in CLASSES:
            continue
        ai = CLASSES.index(actual)
        if t2:
            cm[ai][ai] += 1
        elif preds and preds[0] in CLASSES:
            cm[ai][CLASSES.index(preds[0])] += 1
        else:
            undetected[actual] += 1

# ── custom colormap: white → light-orange → deep-orange ──────────────────────
cmap = mcolors.LinearSegmentedColormap.from_list(
    'paper_cm', ['#FFFFFF', '#FCDBBF', '#ED7D31'], N=256)

# Normalise with the diagonal max so it looks vivid
total_per_row = cm.sum(axis=1) + np.array([undetected[c] for c in CLASSES])
pct_matrix = np.zeros_like(cm, dtype=float)
for i in range(N):
    if total_per_row[i] > 0:
        pct_matrix[i] = cm[i] / total_per_row[i] * 100

# ── plot ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5.8))
fig.patch.set_facecolor('white')

im = ax.imshow(pct_matrix, cmap=cmap, vmin=0, vmax=100, aspect='auto')

# Annotate: show count and % — dark text on light cells, white on dark
for i in range(N):
    for j in range(N):
        cnt  = cm[i, j]
        pct  = pct_matrix[i, j]
        dark = pct > 55            # threshold for white text
        clr  = 'white' if dark else '#1A1A1A'
        ax.text(j, i, f'{cnt}\n({pct:.0f}%)',
                ha='center', va='center',
                fontsize=10.5, fontweight='bold', color=clr,
                linespacing=1.3)

# Axes
ax.set_xticks(range(N))
ax.set_yticks(range(N))
ax.set_xticklabels(CLASSES, fontsize=13, fontweight='bold')
ax.set_yticklabels(CLASSES, fontsize=13, fontweight='bold')
ax.set_xlabel('Predicted Class', fontsize=13, labelpad=6)
ax.set_ylabel('Actual Class', fontsize=13, labelpad=6)
ax.set_title('Diff Eval — Top-2 Resolved Confusion Matrix',
             fontsize=14, fontweight='bold', pad=10)

# Thin grid lines between cells (visual separation)
for x in np.arange(-0.5, N, 1):
    ax.axhline(x, color='#CCCCCC', linewidth=0.7, zorder=1)
    ax.axvline(x, color='#CCCCCC', linewidth=0.7, zorder=1)

# Colourbar with matching style
cbar = fig.colorbar(im, ax=ax, fraction=0.040, pad=0.03)
cbar.set_label('Row %', fontsize=11)
cbar.ax.tick_params(labelsize=10)

total_undetected = sum(undetected.values())
if total_undetected > 0:
    fig.text(0.5, -0.01,
             f'Note: {total_undetected} examples with no valid prediction excluded.',
             ha='center', fontsize=9, color='#666666', style='italic')

plt.tight_layout()
plt.savefig('paper_fig_confusion.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print(f"Confusion matrix saved. Undetected: {undetected}")
print("     " + "  ".join(f"{c:>5}" for c in CLASSES))
for i, c in enumerate(CLASSES):
    print(f"  {c:>5}  " + "  ".join(f"{cm[i,j]:>5}" for j in range(N)))
