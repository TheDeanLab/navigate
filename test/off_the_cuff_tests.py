def test_addition():
    a = 1
    b = 2

    assert (a+b) == 3

def test_filter_wheel_init():
    # import worked, no "compile" error, no syntax errors
    import filter_wheels

    dummy_model = {}

    fw = filter_wheels.SutterFilterWheel(dummy_model)  # no runtime error in SutterFilterWheel.__init__()

    assert True

def test_filter_wheel_spin():
    ## fill in logic to assign a value to spin_happened
    assert(spin_happened)


def test_waveform_generation():
    import numpy as np
    theoretical_waveform = np.ones(10)

    # logic to call waveform generation from our code
    generated_waveform = my_waveform_generator(with, initial, parameters, that, should, yield, array, of, ones)

    np.testing.assert_almost_equal(theoretical_waveform, generated_waveform, decimal=7)  

# we need XVFB
def test_gui():
    import tkinter

    import my_gui

    my_gui.MainLoop()

    assert True

def test_button_callback():
    # Don't load the GUI, just call the function that gets called when you click the button
    import numpy as np

    random_vals = np.random.rand(100)

    for random_val in random_vals:
        my_button_callback(random_val)

    assert True