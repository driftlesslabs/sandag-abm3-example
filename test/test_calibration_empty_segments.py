"""Prevent unsupported tour segments from becoming zero-target successes."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest

from activitysim.core.calibration.component import _evaluate_and_update


@pytest.fixture
def helper():
    path = (
        Path(__file__).resolve().parents[1]
        / "configs/calibration/tour_mode_choice_calib_helper.py"
    )
    spec = importlib.util.spec_from_file_location("tour_mode_helper_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def context_for_segment(count, purpose="Work", sample_rate=1.0):
    return {
        "households": pd.DataFrame({"sample_rate": [sample_rate]}),
        "_prepared_model_tours": pd.DataFrame(
            {
                "auto_suff": ["0"] * count,
                "tour_purp_group": [purpose] * count,
                "tour_mode_group": ["WALK"] * count,
            }
        ),
    }


def set_targets(monkeypatch, helper, transit, walk, purpose="Work"):
    targets = pd.DataFrame(
        {
            "auto_suff": ["0"] * 3,
            "purpose": [purpose] * 3,
            "grouped_tour_mode": ["WALK-TRANSIT", "WALK", "All"],
            "tours": [transit, walk, transit + walk],
        }
    )
    monkeypatch.setattr(helper, "get_targets", lambda: targets)


@pytest.mark.parametrize("purpose", ["Work", "Work sub-tour"])
@pytest.mark.parametrize("transit, walk", [(4.0, 6.0), (4.0, 0.0), (0.0, 6.0)])
def test_empty_segment_with_positive_targets_is_rejected(
    helper, monkeypatch, purpose, transit, walk
):
    set_targets(monkeypatch, helper, transit, walk, purpose)
    # Other purposes have tours; only this segment lacks sample support.
    context = context_for_segment(10, purpose="School")
    for mode in ("WALK-TRANSIT", "WALK", "BIKE"):
        with pytest.raises(ValueError, match="no modeled tours") as error:
            helper.get_target_value(context, mode, "0", purpose)
        assert "auto_suff='0'" in str(error.value)
        assert repr(purpose) in str(error.value)
        assert "no sample support" in str(error.value)


def test_empty_segment_with_zero_targets_remains_zero(helper, monkeypatch):
    set_targets(monkeypatch, helper, 0.0, 0.0)
    context = context_for_segment(0)
    assert helper.get_model_value(context, "WALK", "0", "Work") == 0.0
    assert helper.get_target_value(context, "WALK", "0", "Work") == 0.0


@pytest.mark.parametrize(
    "count, sample_rate, transit, walk, expected_transit, expected_walk",
    [
        (10, 1.0, 4.0, 6.0, 4.0, 6.0),
        (10, 0.5, 4.0, 6.0, 4.0, 16.0),
        (2, 1.0, 4.0, 6.0, 0.8, 1.2),
        (2, 1.0, 4.0, 0.0, 2.0, 0.0),
    ],
)
def test_populated_segments_keep_existing_scaling(
    helper,
    monkeypatch,
    count,
    sample_rate,
    transit,
    walk,
    expected_transit,
    expected_walk,
):
    set_targets(monkeypatch, helper, transit, walk)
    context = context_for_segment(count, sample_rate=sample_rate)
    # A zero count for one mode does not make the entire segment unsupported.
    assert helper.get_model_value(context, "WALK-TRANSIT", "0", "Work") == 0.0
    assert helper.get_target_value(
        context, "WALK-TRANSIT", "0", "Work"
    ) == pytest.approx(expected_transit)
    assert helper.get_target_value(context, "WALK", "0", "Work") == pytest.approx(
        expected_walk
    )


def test_real_survey_empty_segment_cannot_report_convergence(helper):
    targets = helper.get_targets()
    observed = targets.loc[
        (targets.auto_suff == "0")
        & (targets.purpose == "Work")
        & (targets.grouped_tour_mode == "WALK-TRANSIT"),
        "tours",
    ].sum()
    assert observed > 4000
    # Exercise preparation on actual raw empty tables, not just the cache.
    context = {
        "households": pd.DataFrame(
            {
                "auto_ownership": [0],
                "num_adults": [1],
                "sample_rate": [1.0],
            }
        ),
        "tours": pd.DataFrame(
            columns=[
                "tour_type",
                "tour_category",
                "tour_mode",
                "household_id",
                "tour_id",
                "person_id",
            ]
        ),
    }
    eval_context = {
        "context": context,
        "get_model_value": helper.get_model_value,
        "get_target_value": helper.get_target_value,
    }
    spec = pd.DataFrame(
        [
            dict(
                description="zero-auto work transit",
                coefficient="coef",
                model_value="get_model_value(context, 'WALK-TRANSIT', '0', 'Work')",
                target_value="get_target_value(context, 'WALK-TRANSIT', '0', 'Work')",
                hold_fast=False,
                min=-15.0,
                max=15.0,
                damping=1.0,
                method="log_ratio",
                tolerance=100.0,
            )
        ]
    )
    coefficients = pd.DataFrame({"value": [0.0]}, index=["coef"])
    with pytest.raises(RuntimeError, match="error evaluating target_value") as error:
        _evaluate_and_update(
            "tour_mode_choice_simulate", spec, coefficients, eval_context, 1, 1
        )
    assert isinstance(error.value.__cause__, ValueError)
    assert "no modeled tours" in str(error.value.__cause__)
    assert coefficients.loc["coef", "value"] == 0.0
