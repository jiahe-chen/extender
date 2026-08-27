"""
Generate clean Top-2-only figures for the paper, plus a refreshed architecture diagram.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 13})

# ────────────────────────────────────────────────────────────
# COLOURS
# ────────────────────────────────────────────────────────────
C_SINGLE  = '#5B9BD5'   # blue
C_TWO     = '#70AD47'   # green
C_DIFF    = '#ED7D31'   # orange
METHODS   = ['Single Agent', 'Two Agent', 'Diff Eval']
COLORS    = [C_SINGLE, C_TWO, C_DIFF]
RANDOM_BL = 0.40        # 40 % random baseline for Top-2 (2/5 classes)

# ────────────────────────────────────────────────────────────
# FIG 1 – Overall Accuracy (Top-2 only)
# ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 5))

top2 = [0.7000, 0.5583, 0.8792]
bars = ax.bar(METHODS, top2, color=COLORS, width=0.5, zorder=3, edgecolor='white', linewidth=1.2)

for bar, val in zip(bars, top2):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.012,
            f'{val*100:.1f}%', ha='center', va='bottom', fontsize=14, fontweight='bold')

ax.axhline(RANDOM_BL, color='#999999', linestyle='--', linewidth=1.4, zorder=2, label='Random baseline (40%)')
ax.set_ylim(0, 1.05)
ax.set_ylabel('Accuracy', fontsize=13)
ax.set_title('Overall Accuracy (Qwen3.5-9B, 240 examples)', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.spines[['top', 'right']].set_visible(False)
ax.yaxis.grid(True, linestyle=':', alpha=0.6, zorder=0)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('paper_fig_overall.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("fig1 done")

# ────────────────────────────────────────────────────────────
# FIG 2 – Accuracy by Difficulty (Top-2 only)
# ────────────────────────────────────────────────────────────
difficulties = ['Easy\n(33 LOC)', 'Moderate\n(140 LOC)', 'Hard\n(306 LOC)']
data = {
    'Single Agent': [0.7500, 0.7125, 0.6375],
    'Two Agent':    [0.6000, 0.6250, 0.4500],
    'Diff Eval':    [0.9250, 0.9125, 0.8000],
}

x = np.arange(len(difficulties))
width = 0.25

fig, ax = plt.subplots(figsize=(9, 5))
for i, (method, vals) in enumerate(data.items()):
    offset = (i - 1) * width
    bars = ax.bar(x + offset, vals, width, label=method, color=COLORS[i],
                  zorder=3, edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.012,
                f'{val*100:.0f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

ax.axhline(RANDOM_BL, color='#999999', linestyle='--', linewidth=1.4, zorder=2, label='Random baseline (40%)')
ax.set_xticks(x)
ax.set_xticklabels(difficulties, fontsize=13)
ax.set_ylim(0, 1.1)
ax.set_ylabel('Accuracy', fontsize=13)
ax.set_title('Accuracy by Difficulty Level', fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='upper right')
ax.spines[['top', 'right']].set_visible(False)
ax.yaxis.grid(True, linestyle=':', alpha=0.6, zorder=0)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('paper_fig_difficulty.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("fig2 done")

# ────────────────────────────────────────────────────────────
# FIG 3 – Accuracy by SOLID Principle (Top-2 only)
# ────────────────────────────────────────────────────────────
principles = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
data = {
    'Single Agent': [0.8125, 0.9792, 0.6667, 0.8333, 0.2083],
    'Two Agent':    [0.8750, 0.8125, 0.3333, 0.3750, 0.3958],
    'Diff Eval':    [0.9583, 0.7292, 0.8125, 0.9792, 0.9167],
}

x = np.arange(len(principles))
width = 0.25

fig, ax = plt.subplots(figsize=(11, 5))
for i, (method, vals) in enumerate(data.items()):
    offset = (i - 1) * width
    bars = ax.bar(x + offset, vals, width, label=method, color=COLORS[i],
                  zorder=3, edgecolor='white', linewidth=0.8)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.012,
                f'{val*100:.0f}%', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

ax.axhline(RANDOM_BL, color='#999999', linestyle='--', linewidth=1.4, zorder=2, label='Random baseline (40%)')
ax.set_xticks(x)
ax.set_xticklabels(principles, fontsize=14)
ax.set_ylim(0, 1.12)
ax.set_ylabel('Accuracy', fontsize=13)
ax.set_title('Accuracy by SOLID Principle', fontsize=14, fontweight='bold')
ax.legend(fontsize=11)
ax.spines[['top', 'right']].set_visible(False)
ax.yaxis.grid(True, linestyle=':', alpha=0.6, zorder=0)
ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('paper_fig_violation.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("fig3 done")

# ────────────────────────────────────────────────────────────
# FIG 4 – Architecture (refreshed, larger fonts)
# ────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(20, 11))
ax.set_xlim(0, 20)
ax.set_ylim(0, 11)
ax.axis('off')
fig.patch.set_facecolor('#FAFAFA')

C_BG      = '#FAFAFA'
C_BORDER  = '#2C3E50'
C_ARROW   = '#5D6D7E'
C_INPUT   = '#D6EAF8'
C_RANK    = '#D5F5E3'
C_OUTPUT  = '#FADBD8'
CHANNEL_COLORS = ['#FADBD8', '#FCF3CF', '#D5F5E3', '#D6EAF8', '#E8DAEF']

def box(x, y, w, h, fc, label, fs=12, bold=False, sub=None, ec=C_BORDER):
    rect = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.12',
                           facecolor=fc, edgecolor=ec, linewidth=1.8)
    ax.add_patch(rect)
    fw = 'bold' if bold else 'normal'
    if sub:
        ax.text(x+w/2, y+h/2+0.18, label, ha='center', va='center',
                fontsize=fs, fontweight=fw, color=C_BORDER)
        ax.text(x+w/2, y+h/2-0.28, sub, ha='center', va='center',
                fontsize=9.5, fontstyle='italic', color='#555')
    else:
        ax.text(x+w/2, y+h/2, label, ha='center', va='center',
                fontsize=fs, fontweight=fw, color=C_BORDER)

def arrow(x1, y1, x2, y2, lw=1.8, rad=0):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=C_ARROW, lw=lw,
                                connectionstyle=f'arc3,rad={rad}'))

# Input
box(0.25, 4.3, 1.9, 2.4, C_INPUT, 'Input\nCode', fs=14, bold=True)

# Channel labels + 4 stage boxes
principles = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
stage_labels = ['Scenario\nGen', 'Code\nModify', 'Diff\nAnalyze', 'Pre-\nVerify']
stage_x = [3.5, 6.2, 8.9, 11.6]
stage_w, stage_h = 2.1, 0.92

for i, (p, cc) in enumerate(zip(principles, CHANNEL_COLORS)):
    row_y = 9.0 - i * 1.72

    # Principle badge
    badge = FancyBboxPatch((2.2, row_y + 0.02), 1.0, stage_h - 0.04,
                            boxstyle='round,pad=0.1', facecolor=cc, edgecolor=C_BORDER, linewidth=1.4)
    ax.add_patch(badge)
    ax.text(2.7, row_y + stage_h/2, p, ha='center', va='center',
            fontsize=13, fontweight='bold', color=C_BORDER)

    for j, (sx, sl) in enumerate(zip(stage_x, stage_labels)):
        box(sx, row_y, stage_w, stage_h, cc, sl, fs=11)
        if j > 0:
            arrow(stage_x[j-1]+stage_w+0.05, row_y+stage_h/2, sx-0.05, row_y+stage_h/2)

    # arrow from principle badge to first stage
    arrow(3.2, row_y+stage_h/2, stage_x[0]-0.05, row_y+stage_h/2)

    # fan-out from input
    ax.annotate('', xy=(2.2-0.05, row_y+stage_h/2), xytext=(2.15, 5.5),
                arrowprops=dict(arrowstyle='->', color='#ABB2B9', lw=1.2))

# Input box right edge to fan-out origin
ax.plot([2.15, 2.15], [5.5, 5.5], 'o', color='#ABB2B9', ms=4)
arrow(0.25+1.9+0.05, 5.5, 2.15, 5.5, lw=1.4)

# Stage header labels
for sx, name in zip(stage_x, ['1. Scenario\n    Generation',
                                '2. Code\n    Modification',
                                '3. Diff\n    Analysis',
                                '4. Pre-\n    Verification']):
    ax.text(sx + stage_w/2, 10.25, name, ha='center', va='center',
            fontsize=11, fontweight='bold', color=C_BORDER)

# Unified Rank
rank_x, rank_y, rank_w, rank_h = 14.5, 3.1, 2.2, 5.0
box(rank_x, rank_y, rank_w, rank_h, C_RANK, 'Unified\nRank', fs=15, bold=True)

# Arrows from Pre-Verify channels to Unified Rank
for i in range(5):
    row_y = 9.0 - i * 1.72
    arrow(stage_x[-1]+stage_w+0.05, row_y+stage_h/2, rank_x-0.05, rank_y+rank_h/2)

# Output
box(rank_x+0.2, 0.4, rank_w-0.4, 1.7, C_OUTPUT, 'Top-N\nViolations', fs=13, bold=True,
    sub='Ranked by confidence')
arrow(rank_x+rank_w/2, rank_y-0.05, rank_x+rank_w/2, 2.1+0.05)

# Title
ax.text(10, 10.8, 'Diff Eval Workflow: 5-Channel Parallel SOLID Detection',
        ha='center', va='center', fontsize=16, fontweight='bold', color=C_BORDER)

plt.tight_layout(pad=0.5)
plt.savefig('paper_architecture.png', dpi=300, bbox_inches='tight', facecolor='#FAFAFA')
plt.close()
print("fig4 architecture done")
