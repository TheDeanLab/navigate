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
import tkinter as tk

import numpy as np
from numpy import sin as sin, cos as cos, tan as tan
import functools

# import arm_gui_attempt_4

# Local Imports
import aslm
from aslm.model.devices.APIs.mecademic.robot import Robot
from aslm.model.devices.robots.robots_base import RobotsBase
import aslm
from aslm.view.custom_widgets import (
    DockableNotebook,
    hover,
    hoverbar,
    hovermixin,
    LabelInputWidgetFactory,
    popup,
    scrollbars,
    validation,
)


# Logger Setup
# p = __name__.split(".")[1]
# logger = logging.getLogger(p)


def build_robot_connection(robot_address, timeout=0.25):
    #     """Build MecademicRobot device connection

    #     Parameters
    #     ----------
    #     robot_address : str
    #         IP address of the robot
    #     timeout : float
    #         Timeout for connecting to the robot

    #     Returns
    #     -------
    #     robot : Robot
    #         Mecademic Robot device connection
    #     """

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

        self.robot = build_robot_connection(device_connection)
        # self.microscope_name = microscope_name
        # self.configuration = configuration

        # Home the robot
        self.robot.ActivateAndHome()
        self.robot.WaitHomed()
        self.robot.SetSynchronousMode(False)

        self.pose_matrix = [[1,0,0],
                    [0,1,0],
                    [0,0,1]
                    ]

        self.CAROUSEL_MAX = 30

        #v probably get this from a yaml

        self.omnidict = {"Cartesian": {"axes_list": ["X","Y","Z","Rx","Ry","Rz"],
                                       "xyz_axis_limits": ["unimplemented"],
                                       "jog_weights": {"X": 10,
                                                       "Y": 10,
                                                       "Z": 10,
                                                       "Rx": .25,
                                                       "Ry": .25,
                                                       "Rz": .25}},
                         "Joints": {"joints_list": ["J1",
                                                    "J2",
                                                    "J3",
                                                    "J4",
                                                    "J5",
                                                    "J6"],
                                    "joint_limits":
                                    {"J1": [[-175,175], [tk.Variable(value=-175),
                                                         tk.Variable(value=175)]],
                                    "J2": [[-70, 90],[tk.Variable(value=-70),
                                                      tk.Variable(value=90)]],
                                    "J3": [[-135, 70], [tk.Variable(value=-135),
                                                        tk.Variable(value=70)]],
                                    "J4": [[-170,170], [tk.Variable(value=-170),
                                                        tk.Variable(value=170)]],
                                    "J5": [[-115,115], [tk.Variable(value=-115),
                                                        tk.Variable(value=115)]],
                                    "J6": [[-420, 420], [tk.Variable(value=-420),
                                                         tk.Variable(value=420)]]},
                                    "jog_weights": {"J1": 2,
                                                    "J2": 2,
                                                    "J3": 2,
                                                    "J4": 2,
                                                    "J5": 2,
                                                    "J6": 2}
                                    }

                         }


    def get_joint_limit(self, joint):
        return self.omnidict["Joints"]["joint_limits"][f"{joint}"]

    def move_to_home(self):
        self.robot.MoveJoints(0,0,0,0,0,0)

    def go_to_gravity_safe_pos(self):
        self.robot.MovePose(-21.29581, 0, 462.58891, 0, 5, 0)

    def run_path_test(self):
        """Moves the robot to and from a sample holder assembly,
        as discussed in the packet.

        Parameters
        ----------
        self : object
            MecademicRobot instance

        Returns
        -------
        None
        """

        # Commands to move from "Home" to the end point and back
        self.robot.MoveLin(190, 0, 308, 0, 90, 0)
        Meca.robot.SetCheckpoint(1)
        self.robot.MovePose(0, 189.21334, 308, -90, 0, 90)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(0, 189.21334, 158, -90, 0, 90)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(0, 189.21334, 158, 0, 90, 0)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(74, 189.21334, 157, 0, 90, 0)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(229.54733, 189.21334, 157, 0, 90, 0)
        self.robot.Delay(1)
        # We must deposit the sample holder
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(229.54733, 189.21334, 101, 0, 90, 0)
        #
        self.robot.Delay(2) # Wait 2s
        # Reverse path to navigate back.... since there is no longer a sample holder,
        # we can take a shortcut, as there is no risk of dropping/ spillage
        # ^^^^^ NO, we CANNOT, it is wayyyyy to close to colliding.
        #Just backtrack, it is safer T-T.
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(74, 187.345986751, 159.752456842, 0, 90, 0)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(0, 189.21334, 158, 0, 90, 0)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(0, 189.21334, 158, -90, 0, 90)
        Meca.robot.SetCheckpoint(1)
        self.robot.MoveLin(0, 189.21334, 308, -90, 0, 90)
        Meca.robot.SetCheckpoint(1)
        self.robot.MovePose(190, 0, 308, 0, 90, 0)


if __name__ == "__main__":
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.title("Robot Control")

    Meca = MecademicRobot("192.168.0.100")


    root.geometry("%dx%d" % (500, 500))
    notebook = DockableNotebook.DockableNotebook(root, root)
    frm_1 = tk.Frame(width=500, height=500)
    frm_2 = tk.Frame(width=500, height=500)
    frm_1.grid()

    frm_2.grid()

    notebook.add(frm_1, text="Robot")
    notebook.add(frm_2, text="Not Robot")
    notebook.set_tablist([frm_1, frm_2])
    notebook.grid()
    frm_1.bind('<Destroy>', notebook.add(frm_1))


#TODO: replace entry with validatedentry
    def color_update(var, indx, mode):
        try:
            trials_var_temp = int(trials_var.get())
            if trials_var_temp > Meca.CAROUSEL_MAX or trials_var_temp <= 0:
                Entry2["foreground"] = "maroon"

            else:
                Entry2["foreground"] = "limegreen"

        except ValueError:
            try:
                trials_var_temp = float(trials_var.get())
                Entry2["foreground"] = "maroon"
            except ValueError:
                Entry2["foreground"] = "red"

    trials_var = tk.StringVar()
    frm_entry = tk.Frame(frm_1, width=500, height=250)
    frm_entry.grid(column=3, row=0)
    Entry2 = tk.Entry(frm_entry, textvariable=trials_var, fg="black")
    Entry2.grid(padx=5, pady=5, row=0, column=1)

    trials_var.trace_add("write", color_update)

    def clear_pressed(event):
        Meca.robot.SetSynchronousMode(False)
        Meca.robot.ClearMotion()
        Meca.robot.ResetError()
        Meca.robot.ResumeMotion()
        set_current_motion_cart_linvel_angvel_acc()

    def bind_pseudo_button(frame, label, action):
        for pseudo_button_part in label, frame:
            pseudo_button_part.bind("<Button-1>", action)

    def run_command_x_times(event, command= None,n_runs=1):
        for i in range(n_runs):
            try:
                command(event)
            except:
                pass

    def set_up_all_other_widgets():
        """Creates buttons for jogging and robot motion

        DO NOT USE SETBLENDING(), LEST THE JOG BUTTONS LOSE FUNCTION
        ----------
        :(
        """

        universal_button_frame = tk.LabelFrame(frm_1,
                                           text="Buttons",
                                           font= ("DEFAULT_FONT", "10"),
                                           labelanchor="nw")
        universal_button_frame.grid(row=0, column = 1)

        def run_trials_pressed(event):
            run_frame["relief"] = tk.SUNKEN
            try:
                trials_var_temp = int(trials_var.get())
                if trials_var_temp > Meca.CAROUSEL_MAX or trials_var_temp <= 0:

                    messagebox.showinfo(
                        title="Information:",
                        message= \
                            f"Please enter a number between 1 and {Meca.CAROUSEL_MAX}.",
                    )
                else:

                    msg = f"{trials_var_temp} trial(s) will be ran."
                    messagebox.showinfo(title="Information:", message=msg)

            except ValueError:
                try:
                    trials_var_temp = float(trials_var.get())
                    messagebox.showinfo(
                        title="Error:", message="Please input an integer."
                    )
                except ValueError:

                    messagebox.showinfo(
                        title="Error:", message="Please input a valid number."
                    )
            run_frame["relief"] = tk.RAISED
            run_command_x_times(event,do_nothing, trials_var_temp)

        def gsp_pressed(event):
            Meca.go_to_gravity_safe_pos()


        def pause_pressed(event):
            if pause_frame["relief"] == tk.SUNKEN:
                pause_frame["relief"] = tk.RAISED
                pause_label.config(text="Pause ")
                Meca.robot.ResumeMotion()
            elif pause_frame["relief"] == tk.RAISED:
                pause_frame["relief"] = tk.SUNKEN
                pause_label.config(text="Resume")
                Meca.robot.PauseMotion()

# 88.80724, -64.40776, -58.47414, -0.05246, 49.82388, -264.80905 handshake joints

        def pose_pressed(event):
            joints = Meca.robot.GetRtTargetJointPos()
            carts = Meca.robot.GetRtTargetCartPos()
            print(f"Joint positions: {joints}")
            print(f"Cartesian position: {carts}")

        run_frame = tk.Frame(frm_entry, relief=tk.RAISED, bd=2)
        run_label = tk.Label(run_frame, text="Run Trial(s):")
        bind_pseudo_button(run_frame, run_label, run_trials_pressed)
        run_frame.grid(column=0, row=0, padx=5, pady=5)
        run_label.grid(padx=5, pady=5)

        swivel_frame = tk.Frame(frm_1, relief=tk.RAISED, bd=2)
        swivel_label = tk.Label(swivel_frame, text="GSP")
        bind_pseudo_button(swivel_frame, swivel_label, gsp_pressed)
        swivel_frame.grid(column=4, row=1, padx=5, pady=5)
        swivel_label.grid(padx=5, pady=5)

        pause_frame = tk.Frame(frm_1, relief=tk.RAISED, bd=2)
        pause_label = tk.Label(pause_frame, text="Pause")
        bind_pseudo_button(pause_frame, pause_label, pause_pressed)
        pause_frame.grid(column=4, row=2, padx=5, pady=5)
        pause_label.grid(padx=5, pady=5)

        clear_frame = tk.Frame(frm_1, bd=2)
        clear_button = tk.Button(clear_frame, text="Clear")
        clear_button.bind("<Button-1>", clear_pressed)
        clear_frame.grid(column=4, row=3, padx=5, pady=5)
        clear_button.grid(padx=5, pady=5)

        get_pose_frame = tk.Frame(frm_1, bd=2)
        get_pose_button = tk.Button(clear_frame, text="Get Pose")
        get_pose_button.bind("<Button-1>", pose_pressed)
        get_pose_frame.grid(column=4, row=4, padx=5, pady=5)
        get_pose_button.grid(padx=5, pady=5)

        tmm_frame = tk.Frame(frm_1, bd=2)
        tmm_button = tk.Button(tmm_frame, text="Mount")
        tmm_button.bind("<Button-1>", do_nothing)
        tmm_frame.grid(column=3, row=1, padx=5, pady=5)
        tmm_button.grid(padx=5, pady=5)

        run_path_test_frame = tk.Frame(frm_1, bd=2)
        run_path_test_button = tk.Button(clear_frame, text="Run Path Test")
        run_path_test_button.bind("<Button-1>", do_nothing)
        run_path_test_frame.grid(column=5, row=1, padx=5, pady=5)
        run_path_test_button.grid(padx=5, pady=5)

        def start_cart_jog(event,type_of_jog, amount,direction = 1):
            global job_id
            # print(type_of_jog,amount,direction)
            index = 0

            try:
                index = ["X", "Y", "Z", "RX", "RY", "RZ"].index(type_of_jog.upper())

            except Exception:
                messagebox.showinfo(
                    title="CoordinateError:",
                    message="A jogging Coordinate is not properly configured.",
                )
                Meca.robot.ClearMotion()
                root.after_cancel(job_id)
                job_id = None

            empty = [0,0,0,0,0,0]
            empty[index] = amount*direction
            if index > 2:
                Meca.robot.MoveLinRelWrf(empty[0],
                                         empty[1],
                                         empty[2],
                                         empty[3],
                                         empty[4],
                                         empty[5])
            else:
                current_pose = Meca.robot.GetRtTargetCartPos()
                # print(Meca.robot.GetStatusRobot(True,))
                Meca.robot.MoveLin(empty[0]+current_pose[0],
                                    empty[1]+current_pose[1],
                                    empty[2]+current_pose[2],
                                    empty[3]+current_pose[3],
                                    empty[4]+current_pose[4],
                                    empty[5]+current_pose[5])
                # print(Meca.robot.GetStatusRobot(True).error_status)


            job_id = root.after(5,
                                start_cart_jog,
                                event,
                                type_of_jog,
                                amount,
                                direction
                                )


        def start_joint_jog(event,joint, jog_weight = 2,direction = 1):
            global job_id
            # print(type_of_jog,amount,direction)
            joint_pos_index = 0

            try:
                joint_pos_index = Meca.omnidict[
                    "Joints"][
                        "joints_list"].index(joint)
                joint = joint

            except:

                try:
                    joint_pos_index = Meca.omnidict[
                        "Joints"][
                            "joints_list"].index(f"J{joint}")
                    joint = f"J{joint}"


                except:
                    print("Error:",
                          "A jogging Coordinate is not properly configured.")
                    Meca.robot.ClearMotion()
                    try:
                        root.after_cancel(job_id)
                        job_id = None
                    except:
                        pass

            # print(Meca.omnidict["Joints"]["joints_list"],"type:", joint)
            jangles = Meca.robot.GetJoints()
            print(joint, jangles[joint_pos_index], jog_weight, direction)

            jangles[joint_pos_index] += (float(jog_weight) * float(direction))
            # print("pre:", Meca.robot.GetJoints(), "post:", jangles)

            if jangles[joint_pos_index] >= Meca.get_joint_limit(f"{joint}")[0][1]-5:
                jangles[joint_pos_index] = Meca.get_joint_limit(f"{joint}")[0][1]-5
            elif jangles[joint_pos_index] <= \
                Meca.get_joint_limit(f"{joint}")[0][0]+5:
                jangles[joint_pos_index] = Meca.get_joint_limit(f"{joint}")[0][0]+5

            Meca.robot.MoveJoints(
                jangles[0], jangles[1], jangles[2], jangles[3], jangles[4], jangles[5]
            )
            job_id = root.after(10, start_joint_jog, event, joint, jog_weight, direction)


        


        def stop_jog(event):
            global job_id
            try:
                root.after_cancel(job_id)
            except:
                pass

        jogging_labelframe = tk.LabelFrame(frm_1,
                                           text="Jogging",
                                           font= ("DEFAULT_FONT", "10"),
                                           labelanchor="n")

        jogging_notebook = tk.ttk.Notebook(jogging_labelframe)

        jogging_notebook.grid(pady= 5, column=0,row=0)

        cartesian_jog_frame = tk.Frame()
        cartesian_jog_frame.grid(column=0,row=0)
        joint_jog_frame = tk.Frame()
        joint_jog_frame.grid()

        jogging_notebook.add(cartesian_jog_frame,text= "Cartesian")
        jogging_notebook.add(joint_jog_frame,text = "Joint")
        jogging_labelframe.grid(padx=5, pady=5, row=0, column=0, rowspan=8)

        def set_up_cart_jog_btns():

            cart_jog_btns = {}


            def make_lambda(type_of_jog,weight,direction):
                return lambda event: start_cart_jog(event,type_of_jog,
                                                              weight,
                                                              direction)

            for i in range(6):
                axis = Meca.omnidict["Cartesian"]["axes_list"][i]
                # print(axis)
                weight = Meca.omnidict["Cartesian"]["jog_weights"][axis]

                lbl_jog = tk.Label(cartesian_jog_frame, text=f"{axis}")
                lbl_jog.grid(column=1, row=0+2*i)
                btn_jog_negative = tk.Button(cartesian_jog_frame, text="  <- ")
                btn_jog_negative.grid(column=0, row=1+2*i)
                btn_jog_positive = tk.Button(cartesian_jog_frame, text=" +>  ")
                btn_jog_positive.grid(column=2, row=1+2*i)
                cart_jog_btns[f"{axis}"] = {"Widgets":
                                            [lbl_jog,
                                             btn_jog_negative,
                                             btn_jog_positive],
                                             "Axis": axis,
                                             "Weight": weight}
                Lambda = [
                    make_lambda(
                    cart_jog_btns[f"{axis}"]["Axis"],
                    cart_jog_btns[f"{axis}"]["Weight"],
                    -1),
                    make_lambda(
                    cart_jog_btns[f"{axis}"]["Axis"],
                    cart_jog_btns[f"{axis}"]["Weight"],
                    1)
                        ]
                cart_jog_btns[f"{axis}"]["Lambda"] = Lambda
            for axis in Meca.omnidict["Cartesian"]["axes_list"]:
                cart_jog_btns[f"{axis}"]["Widgets"][1].bind("<ButtonPress-1>",
                                       cart_jog_btns[f"{axis}"]["Lambda"][0])
                cart_jog_btns[f"{axis}"]["Widgets"][1].bind("<ButtonRelease-1>",
                                                            stop_jog)
                cart_jog_btns[f"{axis}"]["Widgets"][2].bind("<ButtonPress-1>",
                                       cart_jog_btns[f"{axis}"]["Lambda"][1])
                cart_jog_btns[f"{axis}"]["Widgets"][2].bind("<ButtonRelease-1>",
                                                            stop_jog)

        set_up_cart_jog_btns()

        


        


        

            

        
       

        def set_up_joint_jog_btns():

            joint_jog_btns = {}
            joint_jog_spinbox_dict = {}

            def make_lambda(type_of_jog,direction):
                return lambda event: start_joint_jog(event,type_of_jog,
                                                              get_weight(joint),
                                                              direction)
            

            # noqa This setup circumvents the error v
        # noqa "<lambda>() takes exactly 1 positional argument but 3 were given"... I dunno why I was having said issue in the 1st place
            def make_jjs_lambda(joint,a = None, b = None):
                return lambda event, a, b: sub_lambda(joint_jog_spinbox_dict[f"{joint}"].get())
            
            def sub_lambda(variable):
                Meca.omnidict[
                    "Joints"][
                        "jog_weights"][
                            f"{joint}"] = variable

            def get_weight(joint):
                return Meca.omnidict["Joints"]["jog_weights"][f"{joint}"]

            for i in range(6):

                joint = Meca.omnidict["Joints"]["joints_list"][i]

                

                lbl_jog = tk.Label(joint_jog_frame, text=f"{joint}")
                lbl_jog.grid(column=1, row=0+2*i)
                btn_jog_negative = tk.Button(joint_jog_frame, text="  <- ")
                btn_jog_negative.grid(column=0, row=1+2*i)
                btn_jog_positive = tk.Button(joint_jog_frame, text=" +>  ")
                btn_jog_positive.grid(column=2, row=1+2*i)
                joint_jog_btns[f"{joint}"] = {"Widgets":
                                              [lbl_jog,
                                               btn_jog_negative,
                                               btn_jog_positive],
                                               "Joint": joint,
                                               "Weight": get_weight(joint)}
                Lambda = [
                    make_lambda(
                    joint_jog_btns[f"{joint}"]["Joint"],
                    -1),
                    make_lambda(
                    joint_jog_btns[f"{joint}"]["Joint"],
                    1)
                        ]
                joint_jog_btns[f"{joint}"]["Lambda"] = Lambda

                joint_jog_spinbox_dict[f"{joint} textvariable"] = tk.DoubleVar()


                joint_jog_spinbox_dict[joint] = \
                validation.ValidatedSpinbox(
                                            joint_jog_frame,
                                            from_=.5,
                                            to=25.00,
                                            increment=.5,
                                            width=6,
                                            textvariable= joint_jog_spinbox_dict[
                                                f"{joint} textvariable"]
                                            )
                joint_jog_spinbox_dict[joint].variable.set(Meca.omnidict["Joints"]["jog_weights"][joint])

                joint_jog_spinbox_dict[joint].variable.trace_add("write",
                                                                make_jjs_lambda(f"{joint}"))
                joint_jog_spinbox_dict[joint].grid(row=1+2*i, column = 1)



            for joint in Meca.omnidict["Joints"]["joints_list"]:
                joint_jog_btns[f"{joint}"]["Widgets"][1].bind("<ButtonPress-1>",
                                       joint_jog_btns[f"{joint}"]["Lambda"][0])
                joint_jog_btns[f"{joint}"]["Widgets"][1].bind("<ButtonRelease-1>",
                                                              stop_jog)
                joint_jog_btns[f"{joint}"]["Widgets"][2].bind("<ButtonPress-1>",
                                       joint_jog_btns[f"{joint}"]["Lambda"][1])
                joint_jog_btns[f"{joint}"]["Widgets"][2].bind("<ButtonRelease-1>",
                                                              stop_jog)
            
            

        set_up_joint_jog_btns()

    def go_to_gravity_safe_pose():
        Meca.go_to_gravity_safe_pos()
        

    def do_nothing():
        pass

    def set_current_motion_cart_linvel_angvel_acc(linvel=150, angvel=45, acc=50):
        global current_motion_cart_linvel
        global current_motion_cart_angvel
        global current_motion_cart_acc

        current_motion_cart_linvel = linvel
        current_motion_cart_angvel = angvel
        current_motion_cart_acc = acc

        Meca.robot.SetCartLinVel(current_motion_cart_linvel)
        Meca.robot.SetCartAngVel(current_motion_cart_angvel)
        Meca.robot.SetCartAcc(current_motion_cart_acc)


def run_path_test(event):
    Meca.robot.SetSynchronousMode(False)
    Meca.run_path_test()




### Backwards facing
"""
1: -116.897,200.999,276.586,0,-90,180
2: -106.897,200.999,276.586,0,-90,180
3: -93.603,213.615,277.203,0,-90,180
4: -95.757,209.324,265.340,0,-51.879,-180
5: -78.231,209.324,287.675,0,-51.879,-180
6: -57.159,209.324,271.140,0,51.879,-180
7: -57.159,209.324,271.140,0,-51.879,-180
8: -57.159,209.324,271.140,0,-30.683,-180
9: -36.309,209.324,269.273,0,-45.340,-180
10: -37.683,194.062,260.826,90,-90,-90
11: -11.828,192.341,260.826,-90,33.664,90
12: 54.334, 110.992,260.826,-90,60.511,90
13: 153.569, 59.149, 260.826,-90,86.853,90
14: 217.236, 11.028, 260.826, 86.853, 90
15: 218.592, -55.456, 87.455, 90,62.568,-90

"""

##Retrieve, Relocate, Retreat, Remove, Retrace, Replace, Reset (big brain)



def singularity_check_back_facing_on_multiscale(event):
    pose_1 = [-116.897, 200.999, 276.586, 0, -90, 180]
    pose_2 = [-106.897, 200.999, 276.586, 0, -90, 180]
    pose_3 = [-93.603, 213.615, 277.203, 0, -90, 180]
    pose_4 = [-95.757, 209.324, 265.340, 0, -51.879, -180]
    pose_5 = [-78.231, 209.324, 287.675, 0, -51.879, -180]
    pose_6 = [-57.159, 209.324, 271.140, 0, 51.879, -180]
    pose_7 = [-57.159, 209.324, 271.140, 0, -51.879, -180]
    pose_8 = [-57.159, 209.324, 271.140, 0, -30.683, -180]
    pose_9 = [-36.309, 209.324, 269.273, 0, -45.340, -180]
    pose_10 = [-37.683, 194.062, 260.826, 90, -90, -90]
    pose_11 = [-11.828, 192.341, 260.826, -90, 33.664, 90]
    pose_12 = [54.334, 110.992, 260.826, -90, 60.511, 90]
    pose_13 = [153.569, 59.149, 260.826, -90, 86.853, 90]
    pose_14 = [217.236, 11.028, 260.826, 86.853, 90]
    pose_15 = [218.592, -55.456, 87.455, 90, 62.568, -90]
    # 5,7,12 Joint


set_up_all_other_widgets()
print(Meca.robot.GetJoints())
root.mainloop()
