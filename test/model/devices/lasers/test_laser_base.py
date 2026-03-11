from navigate.model.devices.laser.synthetic import SyntheticLaser


def _laser_configuration():
    return {
        "configuration": {
            "microscopes": {
                "TestScope": {
                    "laser": [
                        {
                            "power": {
                                "hardware": {
                                    "type": "Synthetic",
                                    "channel": "Dev1/ao0",
                                    "min": 0.0,
                                    "max": 5.0,
                                }
                            },
                            "onoff": {
                                "hardware": {
                                    "type": "Synthetic",
                                    "channel": "Dev1/port0/line0",
                                    "min": 0.0,
                                    "max": 5.0,
                                }
                            },
                        }
                    ]
                }
            }
        }
    }


def test_laser_base_functions():
    laser = SyntheticLaser("TestScope", None, _laser_configuration(), 0)

    laser.set_power(42)
    assert laser.laser_intensity == 42

    laser.turn_on()
    laser.turn_off()
    laser.close()
