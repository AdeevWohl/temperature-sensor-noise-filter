"""Unit tests. Run with ``pytest`` or ``python tests/test_filter_analysis.py``."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from filter_analysis import (  # noqa: E402
    DATA_DIR, analyze, cutoff_frequency, gain, load_run, reduction_percent, residuals, sampling_frequency,
    step_response, time_constant, window_samples,
)


def test_rc_time_constant_and_cutoff():
    assert np.isclose(time_constant(), 0.010)
    assert np.isclose(cutoff_frequency(), 15.915, atol=1e-3)
    assert np.isclose(gain(cutoff_frequency()), 1 / np.sqrt(2))
    assert np.isclose(gain(0), 1.0) and gain(60) < 0.26
    assert np.isclose(step_response(time_constant()), 1 - np.exp(-1))


def test_sampling_frequency_uses_median_interval():
    t = np.arange(0, 100) * 0.101
    t[50:] += 2.0                      # one long gap must not change the estimate
    assert np.isclose(sampling_frequency(t), 1 / 0.101)
    assert window_samples(9.901) == 50


def test_residuals_remove_linear_drift_and_drop_incomplete_windows():
    n, window = 500, 50
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 0.3, n)
    temp = 20 + 0.01 * np.arange(n) + noise
    r = residuals(temp, window)
    assert r.isna().sum() == window - 1
    # the moving average removes a linear trend up to a constant: with an even window the "centred"
    # average sits half a sample off-centre, an offset of half a sample's drift that leaves the std unchanged
    expected = pd.Series(noise) - pd.Series(noise).rolling(window, center=True).mean()
    diff = (r - expected).dropna()
    assert np.allclose(diff, 0.01 * 0.5) and np.isclose(r.std(), expected.std())


def test_reduction_percent():
    assert np.isclose(reduction_percent(0.25, 1.0), 75.0)
    assert np.isclose(reduction_percent(1.0, 1.0), 0.0)


def test_analysis_reproduces_reported_results():
    u = analyze(load_run(DATA_DIR / "room_unfiltered.csv"))
    f = analyze(load_run(DATA_DIR / "room_filtered.csv"))
    for run in (u, f):
        assert run["samples"] == 3273 and run["window"] == 50
        assert round(run["duration_s"], 1) == 330.6 and round(run["sampling_hz"], 2) == 9.90
    assert (round(u["mean_temp"], 2), round(f["mean_temp"], 2)) == (19.39, 19.73)
    assert (round(u["residual_std"], 3), round(f["residual_std"], 3)) == (1.278, 0.316)
    assert round(reduction_percent(f["residual_std"], u["residual_std"]), 1) == 75.3


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok ", name)
