"""
Test stage Class
"""
from stages.stage_tl_kcube_steppermotor import TLKSTStage

# Create configuration for microscope stage
serial_number = 26001318
dv_units = 20000000
real_units = 9.957067 # mm
dv_per_mm = dv_units / real_units
mm_per_dv = real_units / dv_units 
microscope_name = "test"
config = {"configuration":{"microscopes":{f"{microscope_name}":{"stage":{"hardware":{"serial_number":str(serial_number),
                                                                                     "axes":"f",
                                                                                     "axes_mapping":[1],
                                                                                     "device_units_per_mm":dv_per_mm,
                                                                                     "f_min":0,
                                                                                     "f_max":25
                                                                                     },
                                                                         "f_min":0,
                                                                         "f_max":25
                                                                         }
                                                                }
                                          }
                           }
          }

# Create the stage controller class
stage = TLKSTStage(microscope_name=microscope_name,
                   device_connection=None,
                   configuration=config
                   )
stage.run_homing()


def test_move_axis_absolute(distance):
    """ Test setPosition()
    """
    # Get the current position 
    stage.report_position()
    start = stage.f_pos
    print(f"starting stage position = {start}")
    
    # Move the target distance
    target = start + distance
    stage.move_axis_absolute("f", target, True)
    
    # Read the position and report
    stage.report_position()
    end = stage.f_pos
    
    print(f"The final position in device units:{end/dv_per_mm}, in real units:{end}mm,\n",
          f"Distance moved = {(end-start)}mm")


def test_move_absolute(distance):
    """ Test MoveAbsolute
    """    
    # Get the current position 
    stage.report_position()
    start = stage.f_pos
    print(f"starting stage position = {start}")
    
    # Move the target distance
    target = start + distance
    stage.move_to_position(target, True)
    
    # Read the position and report
    stage.report_position()
    end = stage.f_pos
    
    print(f"The final position in device units:{end}, in real units:{end}mm,\n",
          f"Distance moved = {(end-start)}mm")


def test_move_to_position(distance):
    # Get the current position 
    stage.report_position()
    start = stage.f_pos
    print(f"starting stage position = {start:.4f}")
    
    # move target distance, wait till done
    stage.move_to_position(start + distance, True)
    
    # get the final position
    stage.report_position()
    end = stage.f_pos
    print(f"End stage position = {end:.4f}",
          f"distance moved = {end-start:.6f}")
    
    
# Run tests 
test_move_to_position(0.100)
test_move_axis_absolute(0.100)
test_move_absolute(0.200)

