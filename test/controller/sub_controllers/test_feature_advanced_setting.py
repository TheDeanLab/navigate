from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from navigate.controller.sub_controllers.feature_advanced_setting import (
    FeatureAdvancedSettingController,
)


def test_save_parameters_adds_none_function_when_missing():
    """A function list without a default function gets a ``None`` entry."""
    controller = FeatureAdvancedSettingController.__new__(
        FeatureAdvancedSettingController
    )
    controller.popup = SimpleNamespace(
        inputs={
            "functions": [
                (
                    MagicMock(get=MagicMock(return_value="custom_function")),
                    MagicMock(get=MagicMock(return_value="/tmp/custom_function.py")),
                    MagicMock(),
                )
            ]
        },
        feature_name_widget=MagicMock(get=MagicMock(return_value="MyFeature")),
        popup=MagicMock(),
    )
    controller.is_valid_function = MagicMock(return_value=True)

    with patch(
        "navigate.controller.sub_controllers.feature_advanced_setting.os.path.exists",
        return_value=True,
    ), patch(
        "navigate.controller.sub_controllers.feature_advanced_setting.save_yaml_file"
    ) as save_yaml_file:
        controller.save_parameters()

    save_yaml_file.assert_called_once()
    assert save_yaml_file.call_args.args[1] == {
        "functions": {
            "custom_function": "/tmp/custom_function.py",
            "None": None,
        }
    }
