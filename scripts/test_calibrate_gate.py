from calibrate_gate import sweep


def test_sweep_reports_kept_fraction_and_error():
    pairs = [(0.9, 50.0), (0.8, 60.0), (0.3, 500.0), (0.2, 800.0)]
    rows = sweep(pairs, thresholds=[0.5])
    assert rows == [
        {
            "threshold": 0.5,
            "kept_frac": 0.5,
            "median_error_ms": 55.0,
            "frac_under_100ms": 1.0,
        }
    ]


def test_sweep_threshold_keeping_nothing_yields_none_error():
    rows = sweep([(0.3, 500.0)], thresholds=[0.9])
    assert rows[0]["kept_frac"] == 0.0
    assert rows[0]["median_error_ms"] is None


def test_sweep_low_threshold_keeps_everything():
    pairs = [(0.9, 50.0), (0.2, 800.0)]
    rows = sweep(pairs, thresholds=[0.0])
    assert rows[0]["kept_frac"] == 1.0
    assert rows[0]["frac_under_100ms"] == 0.5
