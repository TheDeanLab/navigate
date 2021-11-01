
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class StagesTab(tk.Frame):
    """
    A stages tab to select which positions will be imaged in a timelapse
    - table to display selected positions
    - activate keyboard for movement and add positions (a,s,w,d and r,t)
    - change speed of stages for selecting
    - a tool to make a mosaic of the selected positions

    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # intro-text
        self.stage_high_res_position_list = None
        intro_text = tk.Label(self, text='In this tab, select the positions to image \n', height=2, width=115, fg="black", bg="grey")
        intro_text.grid(row=0, column=0, columnspan= 5000, sticky=(tk.E))

        # general stage settings
        self.stage_trans_step_size = tk.DoubleVar()
        self.stage_rot_step_size = tk.DoubleVar()

        # parameters move to
        self.stage_move_to_lateral = tk.DoubleVar()
        self.stage_move_to_axial   = tk.DoubleVar()
        self.stage_move_to_up_down  = tk.DoubleVar()
        self.stage_move_to_angle   = tk.DoubleVar()

        # parameters save to position
        self.stage_current_pos_index = tk.IntVar()
        self.stage_current_pos_index.set(1)
        self.stage_current_high_res_pos_index = tk.IntVar()
        self.stage_current_high_res_pos_index.set(1)
        self.stage_position_list = [(1,0,0,0,0)]
        self.stage_save_position_list = [(1,0,0,0,0)]
        self.stage_old_position_list = [(1,0,0,0,0)]
        self.stage_high_res_position_list = [(1, 0, 0, 0, 0)]
        self.stage_high_res_save_position_list = [(1, 0, 0, 0, 0)]
        self.stage_high_res_old_position_list = [(1, 0, 0, 0, 0)]
        self.stage_mosaic_up_down = 2
        self.stage_mosaic_lateral = 2
        self.stage_last_key = tk.StringVar()
        self.stage_move_to_specific_position = tk.IntVar()

        #mosaic parameters
        self.stage_mosaic_up_down_nb = tk.IntVar()
        self.stage_mosaic_left_right_nb = tk.IntVar()
        self.stage_mosaic_up_down_spacing = tk.DoubleVar()
        self.stage_mosaic_left_right_spacing = tk.DoubleVar()

        # set the different label frames
        general_stage_settings = tk.LabelFrame(self, text="Stage Movement Settings")
        move_to_position = tk.LabelFrame(self, text="Move to ...")
        mosaic_settings = tk.LabelFrame(self, text="Mosaic settings")
        saved_low_res_positions = tk.LabelFrame(self, text="Low Resolution Positions")
        saved_high_res_positions = tk.LabelFrame(self, text="High Resolution Positions")

        # overall positioning of label frames
        general_stage_settings.grid(row=1, column=0, rowspan=2, sticky=tk.W + tk.E + tk.S + tk.N)
        move_to_position.grid(row=3, column=0, rowspan=17, sticky=tk.W + tk.E + tk.S + tk.N)
        mosaic_settings.grid(row=20, column=0, sticky=tk.W + tk.E + tk.S + tk.N)
        saved_low_res_positions.grid(row=1, column=1, rowspan=10, sticky=tk.W + tk.E + tk.S + tk.N)
        saved_high_res_positions.grid(row=12, column=1, rowspan=10, sticky=tk.W + tk.E + tk.S + tk.N)

        ### ----------------------------general stage settings -----------------------------------------------------------------
        # stage labels (positioned)
        stage_step_size_label = ttk.Label(general_stage_settings, text="Trans. stage step size:").grid(row=0, column=0)
        angle_step_size_label = ttk.Label(general_stage_settings, text="Rot. stage step size:").grid(row=5, column=0)
        mm_step_size_label = ttk.Label(general_stage_settings, text="mm").grid(row=2, column=4)
        angle_step_size_label = ttk.Label(general_stage_settings, text="degree").grid(row=8, column=4)
        rot_stage_step_size_label = ttk.Label(general_stage_settings, text="Rot. stage step size:").grid(row=6, column=0)

        trans_stage_scale = tk.Scale(general_stage_settings, variable=self.stage_trans_step_size,from_=0, to=2, resolution = 0.001, orient="horizontal")
        self.stage_trans_entry = tk.Entry(general_stage_settings, textvariable=self.stage_trans_step_size, width=7)
        self.stage_rot_entry = tk.Entry(general_stage_settings, textvariable=self.stage_rot_step_size, width=7)
        rot_stage_scale = tk.Scale(general_stage_settings, variable=self.stage_rot_step_size, from_=0, to=360,
                                  resolution=0.1, orient="horizontal")
        #default values
        self.stage_trans_step_size.set(2.000)
        self.stage_rot_step_size.set(2.000)

        #general stage settings widgets layout
        self.stage_trans_entry.grid(row=3, column=4, sticky=tk.W + tk.E)
        trans_stage_scale.grid(row=2, column=0, rowspan =2, sticky=tk.W + tk.E)
        rot_stage_scale.grid(row=6, column=0, rowspan=2, sticky=tk.W + tk.E)
        self.stage_rot_entry.grid(row=7, column=4, sticky=tk.W + tk.E)



        ### ----------------------------move to position -----------------------------------------------------------------
        # move to labels (positioned)
        position_label = ttk.Label(move_to_position, text="Position").grid(row=0, column=1)
        position_x_label = ttk.Label(move_to_position, text="X").grid(row=2, column=0)
        position_y_label = ttk.Label(move_to_position, text="Y").grid(row=4, column=0)
        position_z_label = ttk.Label(move_to_position, text="Z").grid(row=6, column=0)
        position_angle_label = ttk.Label(move_to_position, text="Phi").grid(row=8, column=0)
        move_to_specific_position_label = ttk.Label(move_to_position, text="Move to position:").grid(row=14, column=0, columnspan=2)

        self.stage_move_left_bt = tk.Button(move_to_position, text="<", command=lambda : self.change_current_position(self.stage_move_to_lateral, -1))
        self.stage_move_right_bt = tk.Button(move_to_position, text=">", command=lambda : self.change_current_position(self.stage_move_to_lateral, 1))
        self.stage_move_up_bt = tk.Button(move_to_position, text="/\ ", command=lambda : self.change_current_position(self.stage_move_to_up_down, 1))
        self.stage_move_down_bt = tk.Button(move_to_position, text="\/", command=lambda : self.change_current_position(self.stage_move_to_up_down, -1))
        self.stage_move_forward_axial_bt = tk.Button(move_to_position, text="Z-", command=lambda : self.change_current_position(self.stage_move_to_axial, -1))
        self.stage_move_backward_axial_bt = tk.Button(move_to_position, text="Z+", command=lambda : self.change_current_position(self.stage_move_to_axial, 1))
        self.stage_move_angle_left_bt = tk.Button(move_to_position, text="R-", command=lambda : self.change_angle(self.stage_move_to_angle, -1))
        self.stage_move_angle_right_bt = tk.Button(move_to_position, text="R+", command=lambda : self.change_angle(self.stage_move_to_angle, 1))

        self.stage_move_to_lateral_entry = tk.Entry(move_to_position, textvariable=self.stage_move_to_lateral, width=7)
        self.stage_move_to_up_down_entry = tk.Entry(move_to_position, textvariable=self.stage_move_to_up_down, width=7)
        self.stage_move_to_axial_entry = tk.Entry(move_to_position, textvariable=self.stage_move_to_axial, width=7)
        self.stage_move_to_angle_entry = tk.Entry(move_to_position, textvariable=self.stage_move_to_angle, width=7)

        self.keyboard_input = tk.StringVar(value="off")
        self.keyboard_input_on_bt = tk.Radiobutton(move_to_position, text="Enable Keyboard", value="on", variable =self.keyboard_input, indicatoron=False)
        self.keyboard_input_off_bt = tk.Radiobutton(move_to_position, text="Disable Keyboard", value="off", variable =self.keyboard_input, indicatoron=False)
        self.keyboard_entry = tk.Entry(move_to_position, textvariable=self.stage_last_key, width=7)

        self.move_to_specific_position_entry = tk.Entry(move_to_position, textvariable=self.stage_move_to_specific_position, width=7)
        self.move_to_specific_position_button = tk.Button(move_to_position, text="Move")
        self.move_to_specific_pos_resolution = tk.StringVar(value="on")
        self.move_to_specific_pos_low_on = tk.Radiobutton(move_to_position, text="Low", value="on",
                                                   variable=self.move_to_specific_pos_resolution, indicatoron=False)
        self.move_to_specific_pos_low_off = tk.Radiobutton(move_to_position, text="High", value="off",
                                                    variable=self.move_to_specific_pos_resolution, indicatoron=False)

        # move to widgets layout
        self.stage_move_to_lateral_entry.grid(row=2, column=1,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_to_up_down_entry.grid(row=4, column=1,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_to_axial_entry.grid(row=6, column=1,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_to_angle_entry.grid(row=8, column=1,columnspan=1,sticky = tk.W + tk.E)

        self.stage_move_left_bt.grid(row=2, column=3,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_right_bt.grid(row=2, column=5,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_up_bt.grid(row=4, column=3,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_down_bt.grid(row=4, column=5,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_forward_axial_bt.grid(row=6, column=3,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_backward_axial_bt.grid(row=6, column=5,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_angle_left_bt.grid(row=8, column=3,columnspan=1,sticky = tk.W + tk.E)
        self.stage_move_angle_right_bt.grid(row=8, column=5,columnspan=1,sticky = tk.W + tk.E)
        self.keyboard_input_on_bt.grid(row=12, column=0,columnspan=2,sticky = tk.W + tk.E)
        self.keyboard_input_off_bt.grid(row=12, column=2,columnspan=4,sticky = tk.W + tk.E)
        self.keyboard_entry.grid(row=12, column=6,columnspan=2,sticky = tk.W + tk.E)

        self.move_to_specific_position_entry.grid(row=15, column=0, columnspan=2, sticky=tk.W + tk.E)
        self.move_to_specific_position_button.grid(row=15, column=7, columnspan=2, sticky=tk.W + tk.E)
        self.move_to_specific_pos_low_on.grid(row=15, column=3, columnspan=2, sticky=tk.W + tk.E)
        self.move_to_specific_pos_low_off.grid(row=15, column=5, columnspan=2, sticky=tk.W + tk.E)

        ### ----------------------------mosaic settings -----------------------------------------------------------------
        # stage labels (positioned)
        mosaic_nb_up_down_label = ttk.Label(mosaic_settings, text="Up-Down #:").grid(row=0, column=0)
        mosaic_left_right_label = ttk.Label(mosaic_settings, text="Left-Right #:").grid(row=2, column=0)
        mosaic_step_size_up_down_label = ttk.Label(mosaic_settings, text="Up-Down Spacing:").grid(row=4, column=0)
        mosaic_left_right_up_down_label = ttk.Label(mosaic_settings, text="Left-Right Spacing:").grid(row=6, column=0)

        self.stage_mosaic_up_down_nb_entry = tk.Entry(mosaic_settings, textvariable=self.stage_mosaic_up_down_nb, width=7)
        self.stage_mosaic_left_right_nb_entry = tk.Entry(mosaic_settings, textvariable=self.stage_mosaic_left_right_nb, width=7)
        self.stage_mosaic_up_down_spa_entry = tk.Entry(mosaic_settings, textvariable=self.stage_mosaic_up_down_spacing, width=7)
        self.stage_mosaic_left_right_spa_entry = tk.Entry(mosaic_settings, textvariable=self.stage_mosaic_left_right_spacing, width=7)

        self.stage_make_low_res_mosaic_bt = tk.Button(mosaic_settings, text="Make Low Res Mosaic", command=lambda : self.make_mosaic("lowres"))
        self.stage_make_high_res_mosaic_bt = tk.Button(mosaic_settings, text="Make High Res Mosaic", command=lambda : self.make_mosaic("highres"))


        # default values
        self.stage_mosaic_up_down_nb.set(2)
        self.stage_mosaic_left_right_nb.set(1)
        self.stage_mosaic_up_down_spacing.set(0.500)
        self.stage_mosaic_left_right_spacing.set(0.500)

        # general stage settings widgets layout
        self.stage_mosaic_up_down_nb_entry.grid(row=0, column=3, sticky=tk.W + tk.E)
        self.stage_mosaic_left_right_nb_entry.grid(row=2, column=3, sticky=tk.W + tk.E)
        self.stage_mosaic_up_down_spa_entry.grid(row=4, column=3, sticky=tk.W + tk.E)
        self.stage_mosaic_left_right_spa_entry.grid(row=6, column=3, sticky=tk.W + tk.E)
        self.stage_make_low_res_mosaic_bt.grid(row=8, column=0, sticky=tk.W + tk.E)
        self.stage_make_high_res_mosaic_bt.grid(row=8, column=3, sticky=tk.W + tk.E)

        ### ----------------------------low resolution saved positions -----------------------------------------------------------------
        # labels (positioned)
        position_label_low_res = ttk.Label(saved_low_res_positions, text="Position:").grid(row=0, column=0)
        self.stage_saved_pos_tree = ttk.Treeview(saved_low_res_positions, columns=("Position", "X", "Y", "Z", "Phi"), show="headings", height=9)
        self.stage_add_pos_bt = tk.Button(saved_low_res_positions, text="Add position", command=lambda : self.add_pos())
        self.stage_delete_pos_bt = tk.Button(saved_low_res_positions, text="Delete position", command=lambda : self.deletePos())
        self.stage_save_pos_bt = tk.Button(saved_low_res_positions, text="Save list", command=lambda : self.savepos_list())
        self.stage_load_pos_bt = tk.Button(saved_low_res_positions, text="Load saved list", command=lambda : self.loadpos_list())
        self.stage_revert_bt = tk.Button(saved_low_res_positions, text="Revert", command=lambda : self.revert_list())
        self.stage_add_pos_index_entry = tk.Entry(saved_low_res_positions, textvariable=self.stage_current_pos_index, width=4)

        y_bar_scrolling = tk.Scrollbar(saved_low_res_positions, orient =tk.VERTICAL, command=self.stage_saved_pos_tree.yview())
        self.stage_saved_pos_tree.configure(yscroll=y_bar_scrolling.set)

        self.stage_saved_pos_tree.heading("Position", text="Position")
        self.stage_saved_pos_tree.heading("X", text="X")
        self.stage_saved_pos_tree.heading("Y", text="Y")
        self.stage_saved_pos_tree.heading("Z", text="Z")
        self.stage_saved_pos_tree.heading("Phi", text="Angle")
        self.stage_saved_pos_tree.column("Position", minwidth=0, width=55, stretch="NO", anchor="center")
        self.stage_saved_pos_tree.column("X", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_saved_pos_tree.column("Y", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_saved_pos_tree.column("Z", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_saved_pos_tree.column("Phi", minwidth=0, width=100, stretch="NO", anchor="center")

        # Add content using (where index is the position/row of the treeview)
        # iid is the item index (used to access a specific element in the treeview)
        # you can set iid to be equal to the index
        tuples = [(1, 0,0,0,0)]
        index = iid = 1
        for row in tuples:
            self.stage_saved_pos_tree.insert("", 1, iid='item1', values=row)
            index = iid = index + 1


        # saved position layout
        self.stage_add_pos_bt.grid(row=0,column=2,sticky = tk.W)
        self.stage_add_pos_index_entry.grid(row=0,column=1,sticky = tk.W)
        self.stage_delete_pos_bt.grid(row=0,column=3,sticky = tk.W)
        self.stage_save_pos_bt.grid(row=0,column=4,sticky = tk.W)
        self.stage_load_pos_bt.grid(row=0,column=5,sticky = tk.W)
        self.stage_revert_bt.grid(row=0,column=6,sticky = tk.W)
        self.stage_saved_pos_tree.grid(row=2, column=0, columnspan=400)

        ### ----------------------------high resolution saved positions -----------------------------------------------------------------
        # labels (positioned)
        position_label_high_res = ttk.Label(saved_low_res_positions, text="Position:").grid(row=0, column=0)
        self.stage_high_res_add_pos_bt = tk.Button(saved_high_res_positions, text="Add position",
                                         command=lambda: self.add_high_res_pos())
        self.stage_high_res_delete_pos_bt = tk.Button(saved_high_res_positions, text="Delete position", command=lambda : self.deletehighresPos())
        self.stage_hig_hres_save_pos_bt = tk.Button(saved_high_res_positions, text="Save list", command=lambda: self.savehighrespos_list())
        self.stage_high_res_load_pos_bt = tk.Button(saved_high_res_positions, text="Load saved list",
                                          command=lambda: self.loadhighrespos_list())
        self.stage_high_res_revert_bt = tk.Button(saved_high_res_positions, text="Revert", command=lambda: self.revert_high_res_list())
        self.stage_high_res_add_pos_index_entry = tk.Entry(saved_high_res_positions, textvariable=self.stage_current_high_res_pos_index,
                                                 width=4)
        self.stage_high_res_saved_pos_tree = ttk.Treeview(saved_high_res_positions, columns=("Position", "X", "Y", "Z", "Phi"),
                                                show="headings", height=9)

        y_bar_scrolling = tk.Scrollbar(saved_high_res_positions, orient=tk.VERTICAL,
                                    command=self.stage_high_res_saved_pos_tree.yview())
        self.stage_high_res_saved_pos_tree.configure(yscroll=y_bar_scrolling.set)

        self.stage_high_res_saved_pos_tree.heading("Position", text="Position")
        self.stage_high_res_saved_pos_tree.heading("X", text="X")
        self.stage_high_res_saved_pos_tree.heading("Y", text="Y")
        self.stage_high_res_saved_pos_tree.heading("Z", text="Z")
        self.stage_high_res_saved_pos_tree.heading("Phi", text="Angle")
        self.stage_high_res_saved_pos_tree.column("Position", minwidth=0, width=55, stretch="NO", anchor="center")
        self.stage_high_res_saved_pos_tree.column("X", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_high_res_saved_pos_tree.column("Y", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_high_res_saved_pos_tree.column("Z", minwidth=0, width=100, stretch="NO", anchor="center")
        self.stage_high_res_saved_pos_tree.column("Phi", minwidth=0, width=100, stretch="NO", anchor="center")

        # Add content using (where index is the position/row of the treeview)
        # iid is the item index (used to access a specific element in the treeview)
        # you can set iid to be equal to the index
        tuples = [(1, 0, 0, 0, 0)]
        index = iid = 1
        for row in tuples:
            self.stage_high_res_saved_pos_tree.insert("", 1, iid='item1', values=row)
            index = iid = index + 1

        # saved position layout
        self.stage_high_res_add_pos_bt.grid(row=0, column=2, sticky=tk.W)
        self.stage_high_res_add_pos_index_entry.grid(row=0, column=1, sticky=tk.W)
        self.stage_high_res_delete_pos_bt.grid(row=0,column=3,sticky = tk.W)
        self.stage_hig_hres_save_pos_bt.grid(row=0, column=4, sticky=tk.W)
        self.stage_high_res_load_pos_bt.grid(row=0, column=5, sticky=tk.W)
        self.stage_high_res_revert_bt.grid(row=0, column=6, sticky=tk.W)
        self.stage_high_res_saved_pos_tree.grid(row=2, column=0, columnspan=400)
    #-------functions---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------

    def change_current_position(self, direction, factor):
        new_position = round(direction.get() + self.stage_trans_step_size.get() * factor,7)
        direction.set(new_position)

    def change_angle(self, direction, factor):
        new_position = round(direction.get() + self.stage_rot_step_size.get() * factor, 5)

        if new_position < 0:
            new_position = 360 + new_position
        if new_position > 360:
            new_position = new_position-360

        direction.set(new_position)

    def save_pos_list(self):
        self.stage_save_position_list = self.stage_save_position_list.copy()

    def save_high_res_pos_list(self):
        self.save_high_res_pos_list = self.save_high_res_pos_list.copy()

    def delete_pos(self):
        # save previous state
        self.stage_old_position_list = self.stage_position_list.copy()

        #find and remove element from list
        for list_iter in range(len(self.stage_position_list)):
            print(self.stage_position_list[list_iter][0])
            if self.stage_position_list[list_iter][0] == self.stage_current_pos_index.get():
                self.stage_position_list.remove(self.stage_position_list[list_iter])
                break # you remove one element - break for loop as otherwise error message appears (out of range)

        #display new tree
        self.display_tree(self.stage_saved_pos_tree, self.stage_position_list)

    def delete_high_res_pos(self):
        # save previous state
        self.stage_high_res_old_position_list = self.stage_high_res_position_list.copy()

        # find and remove element from list
        for list_iter in range(len(self.stage_high_res_position_list)):
            if self.stage_high_res_position_list[list_iter][0] == self.stage_current_high_res_pos_index.get():
                self.stage_high_res_position_list.remove(self.stage_high_res_position_list[list_iter])
                break # you remove one element - break for loop as otherwise error message appears (out of range)

        # display new tree
        self.display_tree(self.stage_high_res_saved_pos_tree, self.stage_high_res_position_list)

    def load_pos_list(self):
        # save previous state
        self.stage_old_position_list = self.stage_position_list.copy()
        #load list
        self.stage_position_list = self.stage_save_position_list.copy()
        # display tree
        self.display_tree(self.stage_saved_pos_tree, self.stage_position_list)

    def load_high_res_pos_list(self):
        # save previous state
        self.stage_high_res_old_position_list = self.stage_high_res_position_list.copy()
        #load list
        self.stage_high_res_position_list = self.stage_high_res_position_list.copy()
        # display tree
        self.display_tree(self.stage_high_res_saved_pos_tree, self.stage_high_res_position_list)

    def revert_list(self):
        self.stage_position_list = self.stage_old_position_list.copy()
        # display tree
        self.display_tree(self.stage_saved_pos_tree, self.stage_position_list)

    def revert_high_res_list(self):
        self.stage_high_res_position_list = self.stage_high_res_old_position_list.copy()
        # display tree
        self.display_tree(self.stage_high_res_saved_pos_tree, self.stage_high_res_position_list)

    def add_pos(self):
        #save previous state
        self.stage_old_position_list = self.stage_position_list.copy()

        #new position to add or update
        newentry = (self.stage_current_pos_index.get(), self.stage_move_to_lateral.get(), self.stage_move_to_up_down.get(), self.stage_move_to_axial.get(), self.stage_move_to_angle.get())

        #check if element is already there
        modified =0
        for list_iter in range(len(self.stage_position_list)):
            if self.stage_position_list[list_iter][0] == self.stage_current_pos_index.get():
                print(self.stage_position_list[list_iter])
                modified=1
                self.stage_position_list[list_iter] = newentry

        if modified==0:
            self.stage_position_list.append(newentry)

        #sort list
        self.stage_position_list.sort()

        #display tree
        self.display_tree(self.stage_saved_pos_tree, self.stage_position_list)

    def add_high_res_pos(self):
        #save previous state
        self.stage_high_res_old_position_list = self.stage_high_res_position_list.copy()

        #new position to add or update
        newentry = (self.stage_current_high_res_pos_index.get(), self.stage_move_to_lateral.get(), self.stage_move_to_up_down.get(), self.stage_move_to_axial.get(), self.stage_move_to_angle.get())

        #check if element is already there
        modified =0
        for list_iter in range(len(self.stage_high_res_position_list)):
            if self.stage_high_res_position_list[list_iter][0] == self.stage_current_high_res_pos_index.get():
                print(self.stage_high_res_position_list[list_iter])
                modified=1
                self.stage_high_res_position_list[list_iter] = newentry

        if modified==0:
            self.stage_high_res_position_list.append(newentry)

        #sort list
        self.stage_high_res_position_list.sort()

        #display tree
        self.display_tree(self.stage_high_res_saved_pos_tree, self.stage_high_res_position_list)

    def display_tree(self, tree, positionlist):
        #delete current tree
        tree.delete(*tree.get_children())

        #generate new tree for display
        iter =0
        for listelement in positionlist:
            iter=iter+1
            newitem = 'item%i' % iter
            tree.insert("", index=iter, iid=newitem, values=listelement)

    def make_mosaic(self, camera):

        #backup and select which camera
        if camera == "highres":
            pos_list = self.stage_high_res_position_list
            self.stage_high_res_old_position_list = self.stage_high_res_position_list.copy()
        else:
            pos_list = self.stage_position_list
            self.stage_old_position_list = self.stage_position_list.copy()

        #make mosaic
        new_list = []
        position_iter =1
        for list_iter in range(len(pos_list)):
            current_position = pos_list[list_iter]
            for updown_iter in range(self.stage_mosaic_up_down_nb.get()):
                for left_right_iter in range(self.stage_mosaic_left_right_nb.get()):
                    new_position = (position_iter,
                                   current_position[1] + left_right_iter * self.stage_mosaic_left_right_spacing.get(),
                                   current_position[2] + updown_iter * self.stage_mosaic_up_down_spacing.get(),
                                   current_position[3],
                                   current_position[4])
                    new_list.append(new_position)
                    position_iter = position_iter+1

        # display tree
        if camera == "highres":
            self.stage_high_res_position_list = new_list
            self.display_tree(self.stage_high_res_saved_pos_tree, self.stage_high_res_position_list)
            self.update_idletasks()
        else:
            self.stage_position_list = new_list
            self.display_tree(self.stage_saved_pos_tree, self.stage_position_list)
            self.update_idletasks()
