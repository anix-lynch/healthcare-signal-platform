"""
DRIFT ALERT REGRESSION TEST.

Synthetic drift: take baseline embeddings, perturb 30% of them with noise.
The drift monitor MUST fire an alert.

Inverse: pass identical embeddings → MUST NOT alert.
"""

import pytest


@pytest.mark.skip(reason="implement once drift.py is ready")
def test_synthetic_drift_alerts():
    pass


@pytest.mark.skip(reason="implement once drift.py is ready")
def test_no_drift_no_alert():
    pass
