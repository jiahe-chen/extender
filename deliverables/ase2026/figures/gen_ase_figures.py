"""Regenerate the paper figures in the original NIER visual style.

The canvases match their final physical size in the ACM two-column layout, so
9 pt plot text remains the same size as the figure captions after inclusion.
"""

from pathlib import Path

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np


OUT = Path(__file__).resolve().parent

# Original NIER palette.
TEAL = "#2FBA9B"
BLUE = "#347FBD"
PURPLE = "#6C4FC3"
COLORS = [TEAL, BLUE, PURPLE]
METHODS = ["Single Agent", "Two Agent", "Extender"]

# Light textures remain legible in grayscale without overpowering the colors.
HATCHES = ["///", "\\\\", "..."]
RANDOM = 0.40
CAPTION_PT = 9.0
DATA_PT = 7.0
BAR_DATA_PT = 6.0

# acmart typesets captions in Linux Libertine. Register the same family for all
# raster figures so the letterforms match the surrounding paper, not only size.
FONT_DIR = Path("/usr/local/texlive/2025/texmf-dist/fonts/opentype/public/libertine")
for font_file in FONT_DIR.glob("LinLibertine_*.otf"):
    font_manager.fontManager.addfont(font_file)

plt.rcParams.update(
    {
        "font.family": "Linux Libertine O",
        "font.size": CAPTION_PT,
        "axes.titlesize": CAPTION_PT,
        "axes.labelsize": CAPTION_PT,
        "xtick.labelsize": CAPTION_PT,
        "ytick.labelsize": CAPTION_PT,
        "legend.fontsize": CAPTION_PT,
        "hatch.linewidth": 0.45,
        "axes.linewidth": 0.7,
    }
)


def finish(fig, filename):
    fig.savefig(OUT / filename, dpi=600, facecolor="white")
    plt.close(fig)


def style_axes(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.yaxis.grid(True, linestyle=":", linewidth=0.6, color="#C9C9C9", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(width=0.7, length=3)


def add_bar_labels(ax, bars, values, offset=0.018):
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + offset,
            f"{value * 100:.0f}%",
            ha="center",
            va="bottom",
            fontsize=BAR_DATA_PT,
            fontweight="bold",
        )


def add_grouped_bar_labels(ax, bars, values, offset=0.014):
    """Use smaller horizontal labels above grouped bars."""
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + offset,
            f"{value * 100:.0f}%",
            ha="center",
            va="bottom",
            fontsize=BAR_DATA_PT,
            fontweight="bold",
            color="#202020",
        )


# Final width: 0.97 of one ACM column (approximately 3.23 in).
fig, ax = plt.subplots(figsize=(3.23, 1.38), constrained_layout=True)
overall = [0.7000, 0.5583, 0.8792]
bars = ax.bar(
    METHODS,
    overall,
    width=0.52,
    color=COLORS,
    edgecolor="#3F3F3F",
    linewidth=0.45,
    zorder=3,
)
for bar, hatch in zip(bars, HATCHES):
    bar.set_hatch(hatch)
add_bar_labels(ax, bars, overall, offset=0.022)
ax.axhline(RANDOM, color="#929292", linestyle="--", linewidth=0.9, zorder=2)
ax.text(
    0.50,
    RANDOM - 0.018,
    "Random 40%",
    ha="center",
    va="top",
    fontsize=BAR_DATA_PT,
    color="#666666",
    bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8},
)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Accuracy")
style_axes(ax)
finish(fig, "paper_fig_overall.pdf")


# Original grouped-bar principle comparison.
principles = ["SRP", "OCP", "LSP", "ISP", "DIP"]
principle_series = {
    "Single Agent": [0.8125, 0.9792, 0.6667, 0.8333, 0.2083],
    "Two Agent": [0.8750, 0.8125, 0.3333, 0.3750, 0.3958],
    "Extender": [0.9583, 0.7292, 0.8125, 0.9792, 0.9167],
}
x = np.arange(len(principles))
width = 0.24
fig, ax = plt.subplots(figsize=(3.23, 1.70))
fig.subplots_adjust(left=0.17, right=0.98, top=0.80, bottom=0.17)
for index, (method, values) in enumerate(principle_series.items()):
    bars = ax.bar(
        x + (index - 1) * width,
        values,
        width,
        label=method,
        color=COLORS[index],
        edgecolor="#3F3F3F",
        linewidth=0.4,
        hatch=HATCHES[index],
        zorder=3,
    )
    add_grouped_bar_labels(ax, bars, values)
ax.axhline(RANDOM, color="#929292", linestyle="--", linewidth=0.9, zorder=2)
ax.set_xticks(x, principles)
ax.set_ylim(0, 1.13)
ax.set_ylabel("Accuracy")
fig.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 1.0),
    ncol=3,
    columnspacing=0.7,
    handlelength=1.35,
    frameon=True,
)
style_axes(ax)
finish(fig, "paper_fig_violation.pdf")


# Original grouped-bar difficulty comparison.
difficulties = ["Easy", "Moderate", "Hard"]
difficulty_series = {
    "Single Agent": [0.7500, 0.7125, 0.6375],
    "Two Agent": [0.6000, 0.6250, 0.4500],
    "Extender": [0.9250, 0.9125, 0.8000],
}
x = np.arange(len(difficulties))
width = 0.24
fig, ax = plt.subplots(figsize=(3.23, 1.62))
fig.subplots_adjust(left=0.17, right=0.98, top=0.79, bottom=0.15)
for index, (method, values) in enumerate(difficulty_series.items()):
    bars = ax.bar(
        x + (index - 1) * width,
        values,
        width,
        label=method,
        color=COLORS[index],
        edgecolor="#3F3F3F",
        linewidth=0.4,
        hatch=HATCHES[index],
        zorder=3,
    )
    add_grouped_bar_labels(ax, bars, values)
ax.axhline(RANDOM, color="#929292", linestyle="--", linewidth=0.9, zorder=2)
ax.set_xticks(x, difficulties)
ax.set_ylim(0, 1.08)
ax.set_ylabel("Accuracy")
fig.legend(
    loc="upper center",
    bbox_to_anchor=(0.5, 1.0),
    ncol=3,
    columnspacing=0.7,
    handlelength=1.35,
    frameon=True,
)
style_axes(ax)
finish(fig, "paper_fig_difficulty.pdf")


# Original NIER confusion-matrix layout, resized for its 0.88-column placement.
classes = ["SRP", "OCP", "LSP", "ISP", "DIP"]
counts = np.array(
    [
        [46, 0, 1, 0, 1],
        [11, 35, 0, 0, 0],
        [5, 0, 39, 0, 4],
        [0, 0, 0, 47, 0],
        [3, 0, 0, 0, 44],
    ]
)
percentages = counts / np.array([48, 48, 48, 48, 48])[:, None] * 100
cmap = mcolors.LinearSegmentedColormap.from_list(
    "nier_purple", ["#F7F5FC", "#CFC7E8", PURPLE], N=256
)
fig, ax = plt.subplots(figsize=(2.93, 2.35), constrained_layout=True)
image = ax.imshow(percentages, cmap=cmap, vmin=0, vmax=100, aspect="equal")
for row in range(5):
    for col in range(5):
        value = percentages[row, col]
        ax.text(
            col,
            row,
            f"{counts[row, col]}\n{value:.0f}%",
            ha="center",
            va="center",
            fontsize=DATA_PT,
            fontweight="bold",
            color="white" if value > 55 else "#202020",
            linespacing=1.1,
        )
ax.set_xticks(range(5), classes)
ax.set_yticks(range(5), classes)
for label in [*ax.get_xticklabels(), *ax.get_yticklabels()]:
    label.set_fontweight("bold")
ax.set_xlabel("Predicted Class")
ax.set_ylabel("Actual Class", labelpad=0)
for boundary in np.arange(-0.5, 5, 1):
    ax.axhline(boundary, color="white", linewidth=0.55)
    ax.axvline(boundary, color="white", linewidth=0.55)
cbar = fig.colorbar(image, ax=ax, fraction=0.05, pad=0.03)
cbar.set_label("Row %")
cbar.ax.tick_params(width=0.6, length=2.5)
cbar.outline.set_linewidth(0.5)
finish(fig, "paper_fig_confusion.png")
