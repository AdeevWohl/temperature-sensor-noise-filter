"""RC filter theory and the residual-noise analysis of the logged runs."""
from pathlib import Path

import numpy as np
import pandas as pd

R_OHMS = 1_000.0
C_FARADS = 10e-6
SMOOTHING_SECONDS = 5.0          # length of the centred moving average used to remove slow drift

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


# ---------------------------------------------------------------- filter theory
def time_constant(r=R_OHMS, c=C_FARADS):
    return r * c


def cutoff_frequency(r=R_OHMS, c=C_FARADS):
    """-3 dB frequency of a first-order RC low-pass filter, f_c = 1 / (2 pi R C)."""
    return 1.0 / (2.0 * np.pi * r * c)


def gain(f, r=R_OHMS, c=C_FARADS):
    """Magnitude of the transfer function, |H(f)| = 1 / sqrt(1 + (f / f_c)^2)."""
    return 1.0 / np.sqrt(1.0 + (np.asarray(f) / cutoff_frequency(r, c)) ** 2)


def step_response(t, r=R_OHMS, c=C_FARADS):
    """Fraction of a step change reached after time t, 1 - exp(-t / RC)."""
    return 1.0 - np.exp(-np.asarray(t) / time_constant(r, c))


# ---------------------------------------------------------------- data analysis
def load_run(path):
    """One logged run, with elapsed time in seconds from the first sample."""
    df = pd.read_csv(path)
    missing = {"time_ms", "raw", "voltage", "temp_C"} - set(df.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    df["time_s"] = (df["time_ms"] - df["time_ms"].iloc[0]) / 1000.0
    return df


def sampling_frequency(time_s):
    """Sampling frequency from the median interval between samples (Hz)."""
    return 1.0 / np.median(np.diff(np.asarray(time_s)))


def window_samples(fs, seconds=SMOOTHING_SECONDS):
    return max(3, int(round(fs * seconds)))


def residuals(temp, window):
    """Reading minus its centred moving average. Samples near the ends,
    where the window is incomplete, are NaN and excluded from statistics."""
    temp = pd.Series(temp)
    return temp - temp.rolling(window=window, center=True).mean()


def reduction_percent(filtered, unfiltered):
    return 100.0 * (1.0 - filtered / unfiltered)


def analyze(df):
    """Noise metrics for one run. The primary metric is ``residual_std``."""
    fs = sampling_frequency(df["time_s"])
    window = window_samples(fs)
    resid = residuals(df["temp_C"], window)
    valid = resid.dropna()
    return {
        "samples": len(df),
        "duration_s": df["time_s"].iloc[-1],
        "sampling_hz": fs,
        "window": window,
        "residual_samples": len(valid),
        "mean_temp": df["temp_C"].mean(),
        "residual_std": valid.std(),
        "step_std": df["temp_C"].diff().std(),
        "adc_codes": df["raw"].nunique(),
        "residual": resid,
    }


def volts_per_count(df):
    """ADC step size implied by the logged raw and voltage columns."""
    return float(np.median(df["voltage"] / df["raw"]))
