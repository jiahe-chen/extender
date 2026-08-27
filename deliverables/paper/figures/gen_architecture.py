import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 12})

fig, ax = plt.subplots(1, 1, figsize=(22, 9))
ax.set_xlim(0, 22)
ax.set_ylim(0, 9)
ax.axis('off')

C_BORDER = '#2C3E50'
C_ARROW  = '#5D6D7E'
C_INPUT  = '#D6EAF8'
C_RANK   = '#D5F5E3'
C_OUTPUT = '#FADBD8'
CHANNEL_COLORS = ['#FADBD8', '#FCF3CF', '#D5F5E3', '#D6EAF8', '#E8DAEF']

def box(x, y, w, h, fc, label, fs=11, bold=False):
    rect = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.1',
                          facecolor=fc, edgecolor=C_BORDER, linewidth=1.6)
    ax.add_patch(rect)
    fw = 'bold' if bold else 'normal'
    ax.text(x+w/2, y+h/2, label, ha='center', va='center',
            fontsize=fs, fontweight=fw, color=C_BORDER)

def arrow(x1, y1, x2, y2, lw=1.6, color=C_ARROW):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=lw,
                                connectionstyle='arc3,rad=0'))

# ── Layout constants ────────────────────────────────────────
# Centred in xlim(0,22): content spans x=2.0 to x=20.0
INPUT_X,  INPUT_W  = 2.0, 1.8
INPUT_MID_Y        = 4.4
FAN_X              = INPUT_X + INPUT_W          # 3.8 — fan-out origin at input right edge

BADGE_X,  BADGE_W  = 4.2, 0.75
stage_x            = [5.2, 7.7, 10.2, 12.7]
STAGE_W,  STAGE_H  = 2.0, 0.80
ROW_YS             = [7.0, 5.6, 4.2, 2.8, 1.4]  # SRP … DIP, spacing 1.4

RANK_X,   RANK_W   = 15.1, 2.0
OUT_X,    OUT_W    = 17.6, 2.4
OUT_H              = 1.8

# ── Input box ──────────────────────────────────────────────
box(INPUT_X, INPUT_MID_Y - 1.0, INPUT_W, 2.0, C_INPUT, 'Input\nCode', fs=12, bold=True)

# Fan-out dot at input right edge
ax.plot(FAN_X, INPUT_MID_Y, 'o', color='#ABB2B9', ms=5, zorder=5)

# ── 5 parallel channels ────────────────────────────────────
principles   = ['SRP', 'OCP', 'LSP', 'ISP', 'DIP']
stage_labels = ['Scenario\nGen', 'Code\nModify', 'Diff\nAnalyze', 'Pre-\nVerify']

for i, (p, cc) in enumerate(zip(principles, CHANNEL_COLORS)):
    ry = ROW_YS[i]
    cy = ry + STAGE_H / 2

    # Fan-out arrow from dot to badge
    ax.annotate('', xy=(BADGE_X - 0.03, cy), xytext=(FAN_X, INPUT_MID_Y),
                arrowprops=dict(arrowstyle='->', color='#ABB2B9', lw=1.1,
                                connectionstyle='arc3,rad=0'))

    # Principle badge
    badge = FancyBboxPatch((BADGE_X, ry + 0.03), BADGE_W, STAGE_H - 0.06,
                           boxstyle='round,pad=0.08', facecolor=cc,
                           edgecolor=C_BORDER, linewidth=1.3)
    ax.add_patch(badge)
    ax.text(BADGE_X + BADGE_W/2, cy, p, ha='center', va='center',
            fontsize=11, fontweight='bold', color=C_BORDER)

    # Arrow from badge to stage 1
    arrow(BADGE_X + BADGE_W + 0.03, cy, stage_x[0] - 0.03, cy)

    # 4 stage boxes + inter-stage arrows
    for j, (sx, sl) in enumerate(zip(stage_x, stage_labels)):
        box(sx, ry, STAGE_W, STAGE_H, cc, sl, fs=9.5)
        if j > 0:
            arrow(stage_x[j-1] + STAGE_W + 0.03, cy, sx - 0.03, cy)

# ── Stage headers ──────────────────────────────────────────
headers = ['1. Scenario\nGeneration', '2. Code\nModification',
           '3. Diff\nAnalysis', '4. Pre-\nVerification']
for sx, name in zip(stage_x, headers):
    ax.text(sx + STAGE_W/2, 8.3, name, ha='center', va='center',
            fontsize=10, fontweight='bold', color=C_BORDER)

# ── Unified Rank ───────────────────────────────────────────
rank_bottom = ROW_YS[-1]
rank_top    = ROW_YS[0] + STAGE_H
rank_h      = rank_top - rank_bottom
rank_mid_y  = rank_bottom + rank_h / 2
box(RANK_X, rank_bottom, RANK_W, rank_h, C_RANK, 'Unified\nRank', fs=13, bold=True)

for ry in ROW_YS:
    arrow(stage_x[-1] + STAGE_W + 0.03, ry + STAGE_H/2, RANK_X - 0.03, rank_mid_y)

# ── Top-2 Violations (RIGHT of Unified Rank) ───────────────
OUT_Y = rank_mid_y - OUT_H / 2
box(OUT_X, OUT_Y, OUT_W, OUT_H, C_OUTPUT, 'Top-2\nViolations', fs=12, bold=True)
arrow(RANK_X + RANK_W + 0.03, rank_mid_y, OUT_X - 0.03, rank_mid_y)

# ── Title ──────────────────────────────────────────────────
ax.text(11, 8.8, 'Diff Eval Workflow: 5-Channel Parallel SOLID Detection',
        ha='center', va='center', fontsize=14, fontweight='bold', color=C_BORDER)

plt.tight_layout(pad=0.4)
plt.savefig('/Users/he/jcSOLID/deliverables/paper/figures/architecture_diff_eval.png',
            dpi=300, bbox_inches='tight', facecolor='white')
plt.close()
print("Done!")
