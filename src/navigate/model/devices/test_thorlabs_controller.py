"""
Test the KST device controller
"""
from stages.stage_tl_kcube_steppermotor import build_TLKSTStage_connection
import time

# test build connection function
serial_number = 26001318

# perform callibration
dv_units = 20000000
real_units = 9.957067 # mm
dv_per_mm = dv_units / real_units

# Open connection to stage
kcube_connection = build_TLKSTStage_connection(serial_number)
time.sleep(2)

# Move the stage to middle of travel
kcube_connection.KST_MoveToPosition(str(serial_number), int(12.5*dv_per_mm))

time.sleep(5)

current_pos = kcube_connection.KST_GetCurrentPosition(str(serial_number))
print(f"Stage currently at:{current_pos} dvUnits")


def time_move(distance):
    """Test how long commands take to excecute move some distance
    """
    start = kcube_connection.KST_GetCurrentPosition(str(serial_number))
    final_position = start + distance
    
    kcube_connection.KST_MoveToPosition(str(serial_number), int(final_position*dv_per_mm))
    time.sleep(5)

    tstart = time.time()
    kcube_connection.KST_MoveToPosition(str(serial_number), start)

    pos = None
    while pos!=start:
        pos = kcube_connection.KST_GetCurrentPosition(str(serial_number))
        tend = time.time()

    print(f"it takes {tend-tstart:.3f}s to move {distance:.3}mm")


def test_move(position):
    """ Test setPosition()
    
    :param position: stage position in mm
    """
    # Move the stage to the position
    kcube_connection.KST_MoveToPosition(str(serial_number), int(position*dv_per_mm))

    # needed to add a sleep call
    time.sleep(5)

    # Read the new position and varify it matches expectations
    pos = kcube_connection.KST_GetCurrentPosition(str(serial_number))

    print(f"Target position = {position} \n",
          f"The final position in device units:{pos}, in real units:{pos/dv_per_mm}mm")
    

def test_jog():
    """ Test MoveJog
    """
    # get the initial position
    start = kcube_connection.KST_GetCurrentPosition(str(serial_number))
    
    # Test a short jog
    kcube_connection.KST_MoveJog(str(serial_number), 1)
    time.sleep(2)
    kcube_connection.KST_MoveStop(str(serial_number))

    time.sleep(2)
    # read stage and make sure it moved
    jog_pos = kcube_connection.KST_GetCurrentPosition(str(serial_number))
    print(f"JogMove moved from {start} to {jog_pos}, starting jog back...")

    kcube_connection.KST_MoveJog(str(serial_number), 2)
    time.sleep(2)
    kcube_connection.KST_MoveStop(str(serial_number))

    time.sleep(2)
    end = kcube_connection.KST_GetCurrentPosition(str(serial_number))
    print(f"JogMove back moved from {jog_pos} to {end}")


def test_polling():
    """Start polling, then run the jog test
    """
    print("testing polling")
    # start polling
    kcube_connection.KST_StartPolling(str(serial_number), 100)
    
    # Run Jog during active polling 
    test_jog()
    
    # End polling
    kcube_connection.KST_StopPolling(str(serial_number))
    # pos = kcube_connection.KST_GetCurrentPosition(str(serial_number))
    
    # print(f"final position: {pos}")
    
test_move(12.5)
test_jog()
time_move(1.0)
test_polling()

# # close connection to stage
# kcube_connection.KST_Close(str(serial_number))
