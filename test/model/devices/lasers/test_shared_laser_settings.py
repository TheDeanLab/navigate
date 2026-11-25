"""Factory ownership and cross-microscope verification without physical hardware."""

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from copy import deepcopy
from itertools import count
from threading import Event
from unittest.mock import Mock

import pytest

from navigate.model.device_startup_functions import SerialConnectionFactory
from navigate.model.devices.laser.settings.base import LaserControlError, LaserMode
from navigate.model.devices.laser.settings.shared import SharedLaserSettings
from navigate.model.devices.laser.settings.synthetic import SyntheticLaserSettings
from navigate.model.devices.laser.software import add_software_control
from navigate.model.devices.laser.synthetic import SyntheticLaser
from test.model.devices.lasers.test_laser_software import configuration


@pytest.fixture
def shared_scopes(monkeypatch):
    """Create independent microscope policies backed by one emulated adapter."""
    monkeypatch.setattr(SerialConnectionFactory, "_connections", {})
    monkeypatch.setattr(SerialConnectionFactory, "_shared_connections", {})
    adapter = SyntheticLaserSettings(100)
    adapter.set_mode(LaserMode.CW)
    adapter.close = Mock(wraps=adapter.close)
    adapter.set_power_mw = Mock(wraps=adapter.set_power_mw)
    connect = Mock(return_value=SharedLaserSettings(adapter))
    monkeypatch.setattr(SharedLaserSettings, "connect", connect)
    owners = []

    def create(name="scope", port="COM7", **software):
        config = configuration(backend="Vortran")
        config["configuration"]["microscopes"][name] = deepcopy(
            config["configuration"]["microscopes"]["scope"]
        )
        entry = config["configuration"]["microscopes"][name]["laser"][0]
        entry["software_control"].update(port=port, **software)
        entry["power"]["percent_reference_mw"] = 10 if name == "scope" else 20
        external = SyntheticLaser(name, None, config, 0)
        external.turn_on = Mock()
        external.close = Mock()
        laser = add_software_control(external)
        owners.append(laser)
        return laser

    yield create, adapter, connect
    for owner in owners:
        owner.close()
    assert not SerialConnectionFactory._shared_connections


def test_aliases_share_one_connection_until_last_owner_closes(shared_scopes):
    create, adapter, connect = shared_scopes
    first, second = create(), create("other", port=r"\\.\com7")
    assert first.settings is second.settings
    assert first.settings_identity != second.settings_identity
    connect.assert_called_once()
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: first.close(), range(4)))
    first.external.close.assert_called_once()
    adapter.close.assert_not_called()
    assert second.advanced_settings_snapshot()["connection"] == "simulated"
    with pytest.raises(LaserControlError, match="closed"):
        first.prepare_acquisition()
    second.close()
    adapter.close.assert_called_once()
    assert not SerialConnectionFactory._connections


@pytest.mark.parametrize(
    "option", [{"type": "OBIS"}, {"baudrate": 9600}, {"timeout": 3}]
)
def test_incompatible_connection_options_do_not_reopen_or_close(shared_scopes, option):
    create, adapter, connect = shared_scopes
    first = create()
    with pytest.raises(ValueError, match="Incompatible"):
        create("other", **option)
    connect.assert_called_once()
    adapter.close.assert_not_called()
    assert first.advanced_settings_snapshot()["mode"] == "cw"


def test_legacy_connection_cannot_be_reused_as_a_laser(shared_scopes):
    create, _, connect = shared_scopes
    SerialConnectionFactory._connections["com7"] = object()
    with pytest.raises(ValueError, match="unmanaged owner"):
        create()
    connect.assert_not_called()


def test_managed_laser_cannot_be_reused_by_legacy_device(shared_scopes):
    create, _, _ = shared_scopes
    create()
    builder = Mock()
    with pytest.raises(ValueError, match="lease"):
        SerialConnectionFactory.build_connection(builder, ("com7",))
    builder.assert_not_called()


@pytest.mark.parametrize("port", [None, "COM9"])
def test_legacy_factory_keeps_existing_cache_and_optional_port_behavior(
    monkeypatch, port
):
    monkeypatch.setattr(SerialConnectionFactory, "_connections", {})
    monkeypatch.setattr(SerialConnectionFactory, "_shared_connections", {})
    connection = object()
    builder = Mock(return_value=connection)
    assert SerialConnectionFactory.build_connection(builder, (port,)) is connection
    assert SerialConnectionFactory.build_connection(builder, (port,)) is connection
    builder.assert_called_once_with(port)


def test_failed_startup_leaves_no_factory_entry_and_preserves_error(monkeypatch):
    from navigate.model import device_startup_functions as startup

    monkeypatch.setattr(SerialConnectionFactory, "_connections", {})
    monkeypatch.setattr(SerialConnectionFactory, "_shared_connections", {})
    monkeypatch.setattr(startup.time, "sleep", lambda duration: None)
    builder = Mock(side_effect=OSError("original serial failure"))
    with pytest.raises(OSError, match="original serial failure"):
        SerialConnectionFactory.acquire_connection(builder, ("COM7",), ("laser",))
    assert not SerialConnectionFactory._connections
    assert not SerialConnectionFactory._shared_connections
    connection = Mock()
    builder.side_effect = None
    builder.return_value = connection
    # Generic objects without serial instrumentation are valid factory results.
    del connection.serial
    lease = SerialConnectionFactory.acquire_connection(builder, ("COM7",), ("laser",))
    lease.close()
    connection.close.assert_called_once()


def test_power_write_invalidates_other_owner_and_preserves_local_reference(
    shared_scopes,
):
    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.prepare_acquisition()
    second.prepare_acquisition()
    first.set_power(25)
    assert first.power_metadata["confirmed_setpoint_mw"] == 2.5
    first.set_power(25)
    assert adapter.set_power_mw.call_count == 1
    second.set_power(25)
    assert second.power_metadata["confirmed_setpoint_mw"] == 5
    assert first.power_metadata is None
    assert first.needs_power_update(25)
    with pytest.raises(LaserControlError, match="confirmed"):
        first.turn_on()
    first.external.turn_on.assert_not_called()
    first.set_power(25)
    assert first.power_metadata["confirmed_setpoint_mw"] == 2.5
    assert second.power_metadata is None
    assert adapter.set_power_mw.call_count == 3


def test_mode_changes_and_failed_transactions_invalidate_every_owner(shared_scopes):
    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.prepare_acquisition()
    first.set_power(25)
    second.set_modulation_mode("digital")
    assert first.power_metadata is None
    assert first.prepared_mode is None
    with pytest.raises(LaserControlError, match="mode changed"):
        first.set_power(25)
    first.prepare_acquisition()
    first.set_power(25)
    original = adapter.set_mode
    adapter.set_mode = Mock(side_effect=LaserControlError("rejected"))
    with pytest.raises(LaserControlError, match="rejected"):
        second.set_modulation_mode("cw")
    assert first.power_metadata is None
    with pytest.raises(LaserControlError, match="Apply and confirm"):
        first.prepare_acquisition()
    adapter.set_mode = original
    second.set_modulation_mode("digital")
    first.prepare_acquisition()
    first.set_power(25)
    adapter.set_power_mw.side_effect = LaserControlError("write failed")
    with pytest.raises(LaserControlError, match="write failed"):
        second.settings.set_power_mw(4)
    assert first.power_metadata is None


def test_complete_power_and_metadata_transaction_holds_shared_lock(shared_scopes):
    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.prepare_acquisition()
    second.prepare_acquisition()
    entered, release, second_entered = Event(), Event(), Event()
    original = adapter.set_power_mw

    def write(power):
        if power == 2.5:
            entered.set()
            assert release.wait(5)
        else:
            second_entered.set()
        return original(power)

    adapter.set_power_mw = write
    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(first.set_power, 25)
        assert entered.wait(5)
        b = pool.submit(second.set_power, 25)
        try:
            assert not second_entered.wait(0.05)
        finally:
            release.set()
        a.result(timeout=5)
        b.result(timeout=5)
    assert second.power_metadata["confirmed_setpoint_mw"] == 5
    assert first.power_metadata is None


def test_concurrent_startup_opens_once_and_last_release_allows_reopen(shared_scopes):
    create, adapter, connect = shared_scopes
    with ThreadPoolExecutor(4) as pool:
        owners = list(pool.map(lambda index: create(str(index)), range(4)))
    connect.assert_called_once()
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda owner: owner.close(), owners))
    adapter.close.assert_called_once()
    replacement = SharedLaserSettings(SyntheticLaserSettings(100))
    connect.return_value = replacement
    reopened = create()
    assert connect.call_count == 2
    assert reopened.settings is replacement
    reopened.prepare_acquisition()


def test_failed_read_invalidates_shared_confirmations(shared_scopes):
    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.prepare_acquisition()
    first.set_power(25)
    adapter.get_status = Mock(side_effect=LaserControlError("read failed"))
    with pytest.raises(LaserControlError, match="read failed"):
        second.advanced_settings_snapshot()
    assert first.power_metadata is None
    with pytest.raises(LaserControlError, match="confirmed"):
        first.turn_on()


def test_final_close_failure_still_evicts_and_closes_external(shared_scopes):
    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.close()
    adapter.close.side_effect = OSError("close failed")
    with pytest.raises(OSError, match="close failed"):
        second.close()
    second.external.close.assert_called_once()
    second.close()
    adapter.close.assert_called_once()
    assert not SerialConnectionFactory._shared_connections
    assert not SerialConnectionFactory._connections


def test_metadata_publication_remains_in_shared_transaction(shared_scopes):
    from types import SimpleNamespace
    from navigate.model.microscope import Microscope
    from navigate.model.metadata_sources.laser_metadata import LaserMetadata

    create, adapter, _ = shared_scopes
    first, second = create(), create("other")
    first.prepare_acquisition()
    second.prepare_acquisition()
    scope = Microscope.__new__(Microscope)
    scope.microscope_name = "scope"
    scope.laser = {"488": first}
    scope.laser_wavelength = [488]
    scope.laser_metadata = LaserMetadata()
    scope.output_event_queue = None
    scope.shutter = SimpleNamespace(state=False, close_shutter=lambda: None)
    entered, release = Event(), Event()
    original = scope.laser_metadata.record

    def record(*args):
        entered.set()
        assert release.wait(5)
        return original(*args)

    scope.laser_metadata.record = record
    with ThreadPoolExecutor(2) as pool:
        a = pool.submit(
            scope.apply_laser_power, "channel_1", {"laser_index": 0, "laser_power": 25}
        )
        assert entered.wait(5)
        b = pool.submit(second.set_power, 25)
        try:
            with pytest.raises(FutureTimeoutError):
                b.result(timeout=0.05)
            assert adapter.set_power_mw.call_count == 1
        finally:
            release.set()
        a.result(timeout=5)
        b.result(timeout=5)
    assert scope.laser_metadata.read_since()[1][-1]["confirmed_setpoint_mw"] == 2.5
    assert second.power_metadata["confirmed_setpoint_mw"] == 5


@pytest.mark.parametrize("backend", ["Vortran", "OBIS", "LuxX"])
def test_start_device_shares_real_protocol_adapters(monkeypatch, backend):
    from navigate.model.device_startup_functions import start_device
    from navigate.model.devices.laser.settings.vortran import VortranLaserSettings
    from navigate.model.devices.laser.settings.obis import ObisLaserSettings
    from navigate.model.devices.laser.settings.luxx import LuxxLaserSettings
    from navigate.model.devices.APIs.coherent.ObisLaser import ObisLaser
    from navigate.model.devices.APIs.omicron.LuxxLaser import LuxxLaser
    from test.model.devices.lasers.test_laser_settings import StradusSerial
    from test.model.devices.lasers.test_obis_luxx_settings import LaserSerial

    clock = Mock(side_effect=count(step=0.0001))
    monkeypatch.setattr("navigate.model.devices.APIs.laser_serial.monotonic", clock)
    monkeypatch.setattr(
        "navigate.model.devices.laser.settings.vortran.monotonic", clock
    )
    monkeypatch.setattr(SerialConnectionFactory, "_connections", {})
    monkeypatch.setattr(SerialConnectionFactory, "_shared_connections", {})
    connection = StradusSerial() if backend == "Vortran" else LaserSerial(backend)
    connection.close = Mock(wraps=connection.close)
    classes = {
        "Vortran": VortranLaserSettings,
        "OBIS": ObisLaserSettings,
        "LuxX": LuxxLaserSettings,
    }

    def connect(*args):
        if backend == "Vortran":
            return VortranLaserSettings(connection)
        api = ObisLaser if backend == "OBIS" else LuxxLaser
        return classes[backend](api("TEST", timeout=1, connection=connection))

    builder = Mock(side_effect=connect)
    monkeypatch.setattr(classes[backend], "connect", builder)
    config = configuration(backend=backend)
    entry = config["configuration"]["microscopes"]["scope"]["laser"][0]
    entry["hardware"] = {"type": "Synthetic", "wavelength": 488}
    config["configuration"]["microscopes"]["other"] = deepcopy(
        config["configuration"]["microscopes"]["scope"]
    )
    first = start_device("scope", config, "laser")
    second = start_device("other", config, "laser")
    try:
        builder.assert_called_once()
        assert first.settings is second.settings
        first.prepare_acquisition()
        second.prepare_acquisition()
        first.set_power(10)
        second.set_power(20)
        assert first.power_metadata is None
        first.set_power(10)
        assert first.power_metadata["verification"] == "readback"
        first.close()
        connection.close.assert_not_called()
        assert second.advanced_settings_snapshot()["connection"] == "connected"
    finally:
        first.close()
        second.close()
    connection.close.assert_called_once()
