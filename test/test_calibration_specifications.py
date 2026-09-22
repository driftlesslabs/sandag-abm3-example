"""Check calibration-to-utility connections without running the regional model."""
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
import yaml

from activitysim.core.calibration.component import (
    _extract_utility_coefficient_names,
    _read_calibration_spec,
    _validate_calibration_coefficients_against_utility_spec,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIRS = [ROOT / "configs/calibration", ROOT / "configs/resident"]


def config_path(name):
    return next(
        directory / name for directory in CONFIG_DIRS if (directory / name).exists()
    )


@pytest.mark.parametrize(
    "component_name, settings_file",
    [
        ("auto_ownership_simulate", "auto_ownership.yaml"),
        ("workplace_location", "workplace_location.yaml"),
        ("tour_mode_choice_simulate", "tour_mode_choice.yaml"),
        ("atwork_subtour_mode_choice", "tour_mode_choice.yaml"),
    ],
)
def test_calibration_coefficients_reach_utilities(component_name, settings_file):
    calibration = yaml.safe_load(config_path("calibration.yaml").read_text())
    settings = yaml.safe_load(config_path(settings_file).read_text())
    state = SimpleNamespace(
        filesystem=SimpleNamespace(get_config_file_path=config_path)
    )
    spec = _read_calibration_spec(
        state, calibration["model_settings"][component_name]["calibration_spec"]
    )
    names = _extract_utility_coefficient_names(state, settings)
    _validate_calibration_coefficients_against_utility_spec(component_name, spec, names)


def test_zero_auto_shared2_remains_fixed_reference():
    utility = pd.read_csv(
        config_path("tour_mode_choice.csv"), comment="#", index_col="Label"
    )
    template = pd.read_csv(
        config_path("tour_mode_choice_coefficients_template.csv"),
        comment="#",
        index_col="coefficient_name",
    )
    coefficients = pd.read_csv(
        config_path("tour_mode_choice_coefficients.csv"),
        comment="#",
        index_col="coefficient_name",
    )
    reference = utility.loc["util_calib_za", "SHARED2"]
    assert reference == "coef_calib_base"
    assert (template.loc[reference] == reference).all()
    assert coefficients.loc[reference, "value"] == 0.0
    for name in (
        "tour_mode_choice_calibration.csv",
        "atwork_tour_mode_choice_calibration.csv",
    ):
        calibration = pd.read_csv(config_path(name), comment="#")
        assert not calibration.coefficient.str.startswith(
            "coef_calib_za_SHARED2_"
        ).any()
        assert reference not in set(calibration.coefficient)
