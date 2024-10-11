"""
Sub-controllers for navigate.
"""

from .stages import StageController  # noqa
from .acquire_bar import AcquireBarController  # noqa
from .channels_tab import ChannelsTabController  # noqa
from .camera_view import CameraViewController, MIPViewController  # noqa
from .camera_settings import CameraSettingController  # noqa
from .waveform_tab import WaveformTabController  # noqa
from .waveform_popup import WaveformPopupController  # noqa
from .autofocus import AutofocusPopupController  # noqa
from .features_popup import FeaturePopupController  # noqa
from .feature_advanced_setting import FeatureAdvancedSettingController  # noqa
from .keystrokes import KeystrokeController  # noqa
from .multiposition import MultiPositionController  # noqa
from .ilastik import IlastikPopupController  # noqa
from .camera_map import CameraMapSettingPopupController  # noqa
from .microscope_popup import MicroscopePopupController  # noqa
from .adaptive_optics import AdaptiveOpticsPopupController  # noqa
from .histogram import HistogramController  # noqa

# from .uninstall_plugin_controller import UninstallPluginController  # noqa
from .plugins import PluginsController, UninstallPluginController  # noqa
from .menus import MenuController  # noqa
