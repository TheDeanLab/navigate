# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

#  Standard Library Imports
import logging
import time

# MacGyvering
import sys
# sys.path.append('C:\\Users\\3vanw\\OneDrive\\Documents\\_UTSW ROBOT ARM\\Arm')
# import arm_gui_attempt_4

# Local Imports
from aslm.model.devices.robots.robots_base import RobotsBase
from aslm.model.devices.APIs.mecademic.robot import Robot
from aslm.view.custom_widgets import DockableNotebook, hover, hoverbar, hovermixin, LabelInputWidgetFactory, popup, scrollbars, validation



# Logger Setup
# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


def build_robot_connection(robot_address, timeout=0.25):
    """Build MecademicRobot device connection

    Parameters
    ----------
    robot_address : str
        IP address of the robot
    timeout : float
        Timeout for connecting to the robot

    Returns
    -------
    robot : Robot
        Mecademic Robot device connection
    """

    block_flag = True
    wait_start = time.time()
    while block_flag:
        robot = Robot()
        robot.Connect(robot_address)
        if robot.IsConnected():
            block_flag = False
        else:
            print("Trying to connect to the Mecademic Robot again")
            elapsed = time.time()
            if (elapsed - wait_start) > timeout:
                break
            time.sleep(0.1)
    return robot


class MecademicRobot:
    """Mecademic Robot Class

    Child class for controlling Mecademic Meca500 robots.

    Parameters
    ----------
    # microscope_name : str
    #     Name of the microscope
    device_connection : Robot
        Mecademic Robot device connection
    # configuration : dict
    #     Configuration dictionary for the microscope

    Attributes
    ----------
    robot : Robot
        Mecademic Robot device connection
    # microscope_name : str
    #     Name of the microscope
    # configuration : dict
    #     Configuration dictionary for the microscope

    Methods
    -------
    move_to_home()

    """

    def __init__(
        self,
        # microscope_name,
        device_connection,
        # configuration
    ):
        # super().__init__(microscope_name, device_connection, configuration)
        """
        self.robot = build_robot_connection(device_connection)
        # self.microscope_name = microscope_name
        # self.configuration = configuration

        # Home the robot
        self.robot.ActivateAndHome()
        self.robot.WaitHomed()
        self.robot.SetSynchronousMode(True)
        """
    def forklift_grab_mock_sample_holder(self):
        self.go_to_gravity_safe_pos()
        self.robot.SetCartLinVel(150)
        self.robot.MoveJoints(0, 60, 30, -90, -90, 0)
        self.robot.MoveJoints(90, 60, 30, -90, -90, 0)
        self.robot.MoveLin(
            -92.07303, 137.35033, 109.50408, -161.00945, -89.95403, 19.06194
        )
        self.robot.MoveLin(
            -194.25064, 137.35033, 109.50408, -161.00945, -89.95403, 19.06194
        )
        self.robot.SetCartLinVel(50)
        self.robot.MoveLin(
            -194.25064, 137.35033, 140.50408, -161.00945, -89.95403, 19.06194
        )
        self.robot.SetCartLinVel(20)
        self.robot.MoveLin(
            -174.25064, 137.35033, 150.50408, -161.00945, -89.95403, 19.06194
        )
        self.robot.SetCartLinVel(50)
        self.robot.MoveLin(
            -92.07303, 137.35033, 109.50408, -161.00945, -89.95403, 19.06194
        )
        self.robot.MoveLin(-83.43991, 119.21656, 308, 90, -89.97672, -90)
        self.robot.SetJointVel(5)
        self.robot.MoveJoints(96.431, 0, 0, -90, 83.593, 90)
        self.robot.MoveJoints(0, 0, 0, -90, -83.593, 90)
        self.robot.SetJointVel(25)
        self.robot.MoveLin(146.00102, -54.63446, 116.66917, -90, 77.162, 90)
        self.robot.MoveLin(
            146.26919, -54.87656, 137.52685, -70.46068, 76.12708, 64.4133
        )
        self.robot.MovePose(74.59977, -144.59977, 131.91343, 90, 0, -90)
        self.robot.MoveLin(74.59977, -144.59977, 160.91343, 90, 0, -90)
        self.robot.MoveLin(119.89491, -186.17773, 173.31124, 90, 0, -90)
        self.robot.MoveLin(119.89491, -186.17773, 118.18298, 90, 0, -90)
        self.robot.MoveLin(119.89491, -186.17773, 108.18298, 90, 0, -90)
        self.robot.MoveLin(119.89491, -130.17773, 108.18298, 90, 0, -90)
        self.robot.MovePose(-21.29581, 0, 462.58891, 0, 5, 0)

    def go_to_gravity_safe_pos(self):
        self.robot.MovePose(-21.29581, 0, 462.58891, 0, 5, 0)
    
    

    def nod(self):
        self.robot.MoveJoints(-135,  30,  -30,  0,  15,  0)
        self.robot.SetJointVel(50)
        for i in range(3):
            self.robot.MoveJoints(-135,  30,  -15,  0,  15,  0)
            self.robot.MoveJoints(-135,  30,  -30,  0,  15,  0)
        self.robot.SetJointVel(25)
    def shake(self):
        # self.robot.set
        self.robot.MoveJoints(-135,  30,  -30,  90,  0,  -90)
        self.robot.SetJointVel(50)
        for i in range(3):
            self.robot.MoveJoints(-135,  30,  -15,  90,  45,  -90)
            self.robot.MoveJoints(-135,  30,  -15,  90,  -45,  -90)
        self.robot.MoveJoints(-135,  30,  -15,  90,  15,  -90)
        self.robot.MoveJoints(-135,  30,  -30,  0,  15,  0)

        self.robot.SetJointVel(25)

    def chuckle(self):
        self.robot.MoveJoints(-135,  30,  -30,  90,  0,  -90)
        self.robot.SetJointVel(50)
        for i in range(12):
            self.robot.MoveJoints(-135,  30,  -45, 0,  -45,  0)
            self.robot.MoveJoints(-135,  30,  0,  0,  -90,  0)
        self.robot.MoveJoints(-135,  30,  -30,  90,  0,  -90)
        self.robot.SetJointVel(50)

if __name__ == "__main__":
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title(f"Robot Control")
    root.geometry("%dx%d" % (500, 500))
    notebook = DockableNotebook.DockableNotebook(root,root)
    frm_1=tk.Frame(width=500,height=500)
    frm_2=tk.Frame(width=500,height=500)
    frm_1.grid()

    frm_2.grid()
    
    notebook.add(frm_1,text="Robot")
    notebook.add(frm_2,text="Not Robot")
    notebook.set_tablist([frm_1,frm_2])
    notebook.grid()

    
    # Meca = MecademicRobot('192.168.0.100')
    # Meca = None

    CAROUSEL_MAX = 30

    def color_update(var, indx, mode):
        try:
            trials_var_temp = (int(trials_var.get()))
            if trials_var_temp > CAROUSEL_MAX or trials_var_temp <= 0:
                Entry2["foreground"]="maroon"
                
            else:
                Entry2["foreground"]="limegreen"
                
        except ValueError:
            try:
                trials_var_temp = (float(trials_var.get()))
                Entry2["foreground"]="maroon"
            except ValueError:
                Entry2["foreground"]="red"
        
    trials_var = tk.StringVar()
    frm_entry = tk.Frame(frm_1,width=500,height=250)
    frm_entry.grid(column=0,row=0)
    Entry2 = tk.Entry(frm_entry,textvariable=trials_var, fg="black")
    Entry2.grid(padx=5,pady=5)

    trials_var.trace_add('write',color_update)

    def run_trials_pressed(event):
        run_frame["relief"] = tk.SUNKEN
        try:
            trials_var_temp = (int(trials_var.get()))
            if trials_var_temp > CAROUSEL_MAX or trials_var_temp <= 0:

                messagebox.showinfo(

                    title = "Information:",
                    message = f"Please enter a number between 1 and {CAROUSEL_MAX}."
                )
            else:
                
                msg = f"{trials_var_temp} trial(s) will be ran."
                messagebox.showinfo(

                    title = "Information:",
                    message = msg
                )
        except ValueError:
            try:
                trials_var_temp = float(trials_var.get())
                messagebox.showinfo(

                    title = "Error:",
                    message = "Please input an integer."
                )
            except ValueError:

                messagebox.showinfo(

                    title = "Error:",
                    message = "Please input a valid number."
                )
        run_frame["relief"] = tk.RAISED

    run_frame = tk.Frame(frm_1,relief=tk.RAISED, bd=2)
    run_label = tk.Label(run_frame, text = "Run Trial(s)")
    for pseudo_button_part in run_label,run_frame:
        pseudo_button_part.bind("<Button-1>", run_trials_pressed)
    run_frame.grid(padx=5,pady=5)
    run_label.grid(padx=5,pady=5)


    def go_to_gravity_safe_pose():
        # Meca.go_to_gravity_safe_pos()
        pass

    def do_nothing():
        pass

    """
    right_frame= tk.Frame(root)
    gravity_safe_button = tk.Button(right_frame,text= "Gravity Safe Pose", command=go_to_gravity_safe_pose)
    right_frame.grid(padx=5,pady=5)
    gravity_safe_button.grid(padx=5,pady=5)

    puppet_lg_frame = tk.Frame(root)
    puppet_lg_frame.rowconfigure(0, minsize=50, weight=1)
    puppet_lg_frame.columnconfigure([0, 1, 2], minsize=50, weight=1)

    puppet_nod_button = tk.Button(puppet_lg_frame, text = "Nod", command = do_nothing)
    #Meca.nod
    puppet_lg_frame.grid(padx=5,pady=5)
    puppet_nod_button.grid(row=0, column=0,padx=5,pady=5)

    puppet_shake_button = tk.Button(puppet_lg_frame, text = "Shake", command = do_nothing)
    # Meca.shake
    puppet_shake_button.grid(row=0, column=1,padx=5,pady=5)

    puppet_chuckle_button = tk.Button(puppet_lg_frame, text = "Laugh", command = do_nothing)
    # Meca.chuckle
    puppet_chuckle_button.grid(row=0, column=2,padx=5,pady=5)
    """
    root.mainloop()
