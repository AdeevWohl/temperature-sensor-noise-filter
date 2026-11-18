"""Reproduce the filter comparison: figures and a results summary.

    python scripts/run_analysis.py [--out DIR]

Writes DIR/figures/*.png and DIR/results/summary.md (default DIR: the repo).
"""
import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from filter_analysis import (  # noqa: E402
    C_FARADS, DATA_DIR, R_OHMS, SMOOTHING_SECONDS, analyze, cutoff_frequency, gain, load_run,
    reduction_percent, step_response, time_constant, volts_per_count,
)

ROOT = Path(__file__).resolve().parents[1]
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
COLOR = {"unfiltered": "#eb6834", "filtered": "#2a78d6"}
LABEL = {"unfiltered": "Unfiltered", "filtered": "Filtered (RC)"}
plt.rcParams.update({
    "figure.facecolor": "white", "savefig.facecolor": "white", "font.size": 9.5,
    "axes.titlesize": 10, "axes.titlelocation": "left", "axes.labelcolor": INK2, "axes.edgecolor": "#c3c2b7",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
    "grid.color": "#e8e7e3", "grid.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2,
    "legend.frameon": False,
})


# ---------------------------------------------------------------- figures
def _ground(ax, x, y):
    ax.plot([x, x], [y, y - 0.25], c=INK, lw=1.5)
    for k, w in enumerate((0.3, 0.2, 0.1)):
        yy = y - 0.25 - 0.1 * k
        ax.plot([x - w, x + w], [yy, yy], c=INK, lw=1.5)


def schematic():
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.6)
    ax.axis("off")
    wire = dict(c=INK, lw=1.5)

    ax.add_patch(Rectangle((0.6, 1.6), 1.8, 1.8, fill=False, ec=INK, lw=1.5))
    ax.text(1.5, 2.5, "TMP36", ha="center", va="center", fontsize=11, weight="bold")
    ax.plot([1.5, 1.5], [3.4, 3.9], **wire)
    ax.text(1.5, 4.0, "+Vs", ha="center", va="bottom", color=INK2)
    ax.plot([1.5, 1.5], [1.6, 1.0], **wire)
    _ground(ax, 1.5, 1.0)
    ax.text(2.45, 2.6, "Vout", ha="left", va="bottom", fontsize=8, color=INK2)

    # series resistor
    ax.plot([2.4, 3.3], [2.5, 2.5], **wire)
    zx = np.linspace(3.3, 4.7, 13)
    zy = 2.5 + 0.18 * np.array([0, 1, -1, 1, -1, 1, -1, 1, -1, 1, -1, 1, 0])
    ax.plot(zx, zy, c=COLOR["filtered"], lw=1.8)
    ax.text(4.0, 2.95, "R = 1 kΩ", ha="center", color=INK)
    ax.plot([4.7, 7.3], [2.5, 2.5], **wire)

    # shunt capacitor to ground
    ax.plot(5.8, 2.5, "o", c=INK, ms=5)
    ax.plot([5.8, 5.8], [2.5, 1.75], **wire)
    ax.plot([5.45, 6.15], [1.75, 1.75], c=COLOR["filtered"], lw=2.5)
    ax.plot([5.45, 6.15], [1.55, 1.55], c=COLOR["filtered"], lw=2.5)
    ax.plot([5.8, 5.8], [1.55, 1.0], **wire)
    _ground(ax, 5.8, 1.0)
    ax.text(6.3, 1.65, "C = 10 µF", ha="left", va="center", color=INK)
    ax.text(5.8, 2.7, "filtered\noutput", ha="center", va="bottom", fontsize=8, color=INK2)

    ax.add_patch(Rectangle((7.3, 1.6), 2.2, 1.8, fill=False, ec=INK, lw=1.5))
    ax.text(8.4, 2.5, "Arduino\nanalog input\n(ADC)", ha="center", va="center", fontsize=9.5)
    ax.plot([8.4, 8.4], [1.6, 1.0], **wire)
    _ground(ax, 8.4, 1.0)

    ax.text(5.0, 0.2, f"τ = RC = {time_constant() * 1e3:.0f} ms     "
            f"f_c = 1 / (2πRC) = {cutoff_frequency():.1f} Hz", ha="center", color=INK)
    ax.set_title("First-order passive RC low-pass filter between the TMP36 output and the ADC input")
    fig.tight_layout()
    return fig


def time_series(runs, res):
    fig, axs = plt.subplots(2, 1, figsize=(9, 5.4), sharex=True, sharey=True)
    for ax, key in zip(axs, ("unfiltered", "filtered")):
        df = runs[key]
        trend = df["temp_C"] - res[key]["residual"]
        ax.plot(df["time_s"], df["temp_C"], c=COLOR[key], lw=0.6, label=f"{LABEL[key]} readings")
        ax.plot(df["time_s"], trend, c=INK, lw=1.4, label=f"{SMOOTHING_SECONDS:g} s centred moving average")
        ax.set_ylabel("temperature (°C)")
        ax.set_title(f"{LABEL[key]}: mean {res[key]['mean_temp']:.2f} °C")
        ax.legend(loc="upper right", fontsize=8, ncol=2)
    axs[1].set_xlabel("elapsed time (s)")
    fig.tight_layout()
    return fig


def residual_series(runs, res):
    fig, axs = plt.subplots(2, 1, figsize=(9, 5.0), sharex=True, sharey=True)
    for ax, key in zip(axs, ("unfiltered", "filtered")):
        ax.plot(runs[key]["time_s"], res[key]["residual"], c=COLOR[key], lw=0.6)
        ax.axhline(0, c=INK2, lw=0.8)
        ax.set_ylabel("residual (°C)")
        ax.set_title(f"{LABEL[key]}: residual standard deviation {res[key]['residual_std']:.3f} °C")
    axs[1].set_xlabel("elapsed time (s)")
    fig.suptitle("Reading minus 5 s centred moving average (short-term fluctuations)", x=0.01, ha="left",
                 fontsize=10.5)
    fig.tight_layout()
    return fig


def residual_histogram(res):
    fig, ax = plt.subplots(figsize=(8, 4.2))
    bins = np.arange(-5, 5.01, 0.1)
    for key, alpha in (("unfiltered", 0.55), ("filtered", 0.65)):
        ax.hist(res[key]["residual"].dropna(), bins=bins, color=COLOR[key], alpha=alpha,
                label=f"{LABEL[key]} (σ = {res[key]['residual_std']:.3f} °C)")
    ax.set_xlabel("residual: reading minus 5 s moving average (°C)")
    ax.set_ylabel("samples per 0.1 °C bin")
    ax.set_title("Distribution of short-term fluctuations")
    ax.legend()
    fig.tight_layout()
    return fig


def frequency_response(fs):
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 4.0))
    f = np.logspace(-1, 3, 400)
    fc, nyq = cutoff_frequency(), fs / 2
    a.axvspan(f[0], nyq, color=COLOR["filtered"], alpha=0.08, lw=0)
    a.text(0.13, -27, f"band resolved by\nthe recorded data\n(0–{nyq:.2f} Hz)", fontsize=8, color=INK2)
    a.semilogx(f, 20 * np.log10(gain(f)), c=COLOR["filtered"], lw=2)
    for x, label in ((fc, f"f_c = {fc:.1f} Hz\n−3 dB"), (60, f"60 Hz\n{20 * np.log10(gain(60)):.1f} dB".replace("-", "−"))):
        a.axvline(x, c=INK2, ls=":", lw=0.9)
        a.plot(x, 20 * np.log10(gain(x)), "o", c=INK, ms=4)
        a.text(x * 1.15, 20 * np.log10(gain(x)) + 1.5, label, fontsize=8, color=INK)
    a.set_ylim(-32, 3)
    a.set_xlabel("frequency (Hz)")
    a.set_ylabel("|H(f)| (dB)")
    a.set_title("(a) Theoretical magnitude response")

    t = np.linspace(0, 0.15, 400)
    b.plot(t * 1e3, step_response(t) * 100, c=COLOR["filtered"], lw=2)
    tau = time_constant()
    b.axvline(tau * 1e3, c=INK2, ls=":", lw=0.9)
    b.text(tau * 1e3 + 2, 40, f"τ = {tau * 1e3:.0f} ms (63%)", fontsize=8, color=INK)
    b.axvline(1e3 / fs, c=INK2, ls="--", lw=0.9)
    b.text(1e3 / fs - 2, 40, f"sampling interval\n{1e3 / fs:.0f} ms", fontsize=8, color=INK, ha="right")
    b.set_xlabel("time after a step change at the sensor output (ms)")
    b.set_ylabel("% of step reached")
    b.set_title("(b) Theoretical step response")
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------- summary
def summary(runs, res):
    u, f = res["unfiltered"], res["filtered"]
    lsb_v = volts_per_count(runs["unfiltered"])
    fc, fs = cutoff_frequency(), u["sampling_hz"]
    rows = [
        ("Samples", f"{u['samples']:,}", f"{f['samples']:,}", ""),
        ("Duration (s)", f"{u['duration_s']:.1f}", f"{f['duration_s']:.1f}", ""),
        ("Sampling frequency (Hz, median interval)", f"{u['sampling_hz']:.2f}", f"{f['sampling_hz']:.2f}", ""),
        ("Moving-average window (samples)", f"{u['window']}", f"{f['window']}", ""),
        ("Residual samples used (complete windows)", f"{u['residual_samples']:,}", f"{f['residual_samples']:,}", ""),
        ("Mean temperature (°C)", f"{u['mean_temp']:.2f}", f"{f['mean_temp']:.2f}", ""),
        ("**Residual standard deviation (°C)**", f"**{u['residual_std']:.3f}**", f"**{f['residual_std']:.3f}**",
         f"**{reduction_percent(f['residual_std'], u['residual_std']):.1f}%**"),
        ("Successive-sample difference std (°C)", f"{u['step_std']:.3f}", f"{f['step_std']:.3f}",
         f"{reduction_percent(f['step_std'], u['step_std']):.1f}%"),
        ("Distinct ADC codes recorded", f"{u['adc_codes']}", f"{f['adc_codes']}", ""),
    ]
    table = ["| Quantity | Unfiltered | Filtered | Reduction |", "|---|---|---|---|"]
    table += [f"| {a} | {b} | {c} | {d} |" for a, b, c, d in rows]
    return "\n".join([
        "# Results", "",
        "Generated by `scripts/run_analysis.py` from `data/room_unfiltered.csv` and `data/room_filtered.csv`.", "",
        "## Measured (room temperature, two sequential runs)", "", *table, "",
        f"Residual = reading minus a centred {SMOOTHING_SECONDS:g} s moving average; edge samples without a "
        "complete window are excluded. Standard deviations use ddof = 1.", "",
        f"ADC step implied by the logged data: {lsb_v * 1e3:.3f} mV per count = {lsb_v * 100:.3f} °C per count "
        f"for the TMP36 (10 mV/°C). The filtered residual standard deviation is "
        f"{f['residual_std'] / (lsb_v * 100):.2f} counts.", "",
        "## Filter theory (R = 1 kΩ, C = 10 µF)", "",
        "| Quantity | Value |", "|---|---|",
        f"| Time constant τ = RC | {time_constant() * 1e3:.1f} ms |",
        f"| Cutoff frequency f_c = 1/(2πRC) | {fc:.1f} Hz |",
        f"| Nyquist frequency of the recorded data | {fs / 2:.2f} Hz |",
        f"| Theoretical attenuation at the Nyquist frequency | {gain(fs / 2):.3f} ({20 * np.log10(gain(fs / 2)):.2f} dB) |",
        f"| Theoretical attenuation at 60 Hz | {gain(60):.3f} ({20 * np.log10(gain(60)):.1f} dB) |",
        f"| Settling to 99% (4.6 τ) | {4.6 * time_constant() * 1e3:.0f} ms |", "",
    ])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT)
    args = ap.parse_args()
    fig_dir, res_dir = args.out / "figures", args.out / "results"
    fig_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    runs = {k: load_run(DATA_DIR / f"room_{k}.csv") for k in ("unfiltered", "filtered")}
    res = {k: analyze(df) for k, df in runs.items()}

    figures = {
        "01_circuit_schematic.png": schematic(),
        "02_temperature_vs_time.png": time_series(runs, res),
        "03_residual_noise.png": residual_series(runs, res),
        "04_residual_distribution.png": residual_histogram(res),
        "05_rc_frequency_response.png": frequency_response(res["unfiltered"]["sampling_hz"]),
    }
    for name, fig in figures.items():
        fig.savefig(fig_dir / name, dpi=150)
        plt.close(fig)
    (res_dir / "summary.md").write_text(summary(runs, res), encoding="utf-8")

    u, f = res["unfiltered"]["residual_std"], res["filtered"]["residual_std"]
    print(f"residual std: unfiltered {u:.3f} C, filtered {f:.3f} C, reduction {reduction_percent(f, u):.1f}%")


if __name__ == "__main__":
    main()
