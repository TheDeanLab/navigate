from tkinter import *
from tkinter import ttk
from tkinter.font import Font

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from model.camera.synthetic_camera import Camera as camera

class stagecontrol_maxintensity_notebook(ttk.Notebook):
    def __init__(stagecontrol_maxintensity, frame_bot_right, *args, **kwargs):
        #Init notebook
        ttk.Notebook.__init__(stagecontrol_maxintensity, frame_bot_right, *args, **kwargs)
        #Putting notebook 3 into bottom right frame
        stagecontrol_maxintensity.grid(row=0,column=0)
        #Creating Stage Control Tab
        stagecontrol_maxintensity.stage_control_tab = stage_control_tab(stagecontrol_maxintensity)
        #Creating Max intensity projection Tab
        stagecontrol_maxintensity.maximum_intensity_projection_tab = maximum_intensity_projection_tab(stagecontrol_maxintensity)
        #Adding tabs to stagecontrol_maxintensity notebook
        stagecontrol_maxintensity.add(stagecontrol_maxintensity.stage_control_tab, text='Stage Control', sticky=NSEW)
        stagecontrol_maxintensity.add(stagecontrol_maxintensity.maximum_intensity_projection_tab, text='MIPs', sticky=NSEW)

class stage_control_tab(ttk.Frame):
    def __init__(stage_control_tab, note3, *args, **kwargs):
        
        #Init Frame
        ttk.Frame.__init__(stage_control_tab, note3, *args, **kwargs) 
        
        #Building out stage control elements, frame by frame
        
        #Position Frame
        stage_control_tab.position_frame = position_frame(stage_control_tab)
        
        #XY Frame
        stage_control_tab.x_y_frame = x_y_frame(stage_control_tab)
        
        #Z Frame
        stage_control_tab.z_frame = z_frame(stage_control_tab)
        
        #Theta Frame
        stage_control_tab.theta_frame = theta_frame(stage_control_tab)
        
        #Focus Frame
        stage_control_tab.focus_frame = focus_frame(stage_control_tab)
        
        #GoTo Frame
        stage_control_tab.goto_frame = goto_frame(stage_control_tab)
        stage_control_tab.goto_frame_label = ttk.Label(stage_control_tab.goto_frame, text="Goto Frame")
        stage_control_tab.goto_frame_label.pack() #For visual mockup purposes

        '''
        Grid for frames
                1   2   3   4   5
                6   7   8   9   10 

        Position frame is 1-5
        xy is 6
        z is 7
        theta is 8
        focus is 9
        goto is 10
        '''

        #Gridding out frames
        stage_control_tab.position_frame.grid(row=0, column=0, columnspan=5, sticky=(NSEW))
        stage_control_tab.x_y_frame.grid(row=1, column=0, sticky=(NSEW))
        stage_control_tab.z_frame.grid(row=1, column=1, sticky=(NSEW))
        stage_control_tab.theta_frame.grid(row=1, column=2, sticky=(NSEW))
        stage_control_tab.focus_frame.grid(row=1, column=3, sticky=(NSEW))
        stage_control_tab.goto_frame.grid(row=1, column=4, sticky=(NSEW))

class maximum_intensity_projection_tab(ttk.Frame):
    def __init__(maximum_intensity_projection_tab, note3, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(maximum_intensity_projection_tab, note3, *args, **kwargs)

        #TODO: Be able to change the channel number, load the data, and perform maximum intensity projection in parallel.
        #TODO: May need a button that specifies when to perform the maximum intensity projection.

        # the figure that will contain the plot
        fig = Figure(figsize=(8, 3), dpi=100)

        # Generate Waveform
        synthetic_image = camera.read_camera(camera)

        # XY
        plot1 = fig.add_subplot(131, title='XY')
        plot1.axis('off')
        plot1.imshow(synthetic_image, cmap='gray')

        # YZ
        plot2 = fig.add_subplot(132, title='YZ')
        plot2.axis('off')
        plot2.imshow(synthetic_image, cmap='gray')

        # XZ
        plot3 = fig.add_subplot(133, title='XZ')
        plot3.axis('off')
        plot3.imshow(synthetic_image, cmap='gray')

        # creating the Tkinter canvas containing the Matplotlib figure
        canvas = FigureCanvasTkAgg(fig, master=maximum_intensity_projection_tab)
        canvas.draw()

        # placing the canvas on the Tkinter window
        canvas.get_tk_widget().pack()

'''
Stage Control Tab Frame Classes
'''

class position_frame(ttk.Frame):
    def __init__(position_frame, stage_control_tab, *args, **kwargs):

        #Init Frame
        ttk.Frame.__init__(position_frame, stage_control_tab, *args, **kwargs)

        #Creating each entry frame for a label and entry

        #X Entry
        position_frame.x_entry_frame = ttk.Frame(position_frame)
        position_frame.x_entry = ttk.Entry(position_frame.x_entry_frame, width=15)
        position_frame.x_entry_label = ttk.Label(position_frame.x_entry_frame, text="X")
        position_frame.x_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.x_entry.grid(row=0, column=1, sticky="w")
        
        #Y Entry
        position_frame.y_entry_frame = ttk.Frame(position_frame)
        position_frame.y_entry = ttk.Entry(position_frame.y_entry_frame, width=15)
        position_frame.y_entry_label = ttk.Label(position_frame.y_entry_frame, text="Y")
        position_frame.y_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.y_entry.grid(row=0, column=1, sticky="w")

        #Z Entry
        position_frame.z_entry_frame = ttk.Frame(position_frame)
        position_frame.z_entry = ttk.Entry(position_frame.z_entry_frame, width=15)
        position_frame.z_entry_label = ttk.Label(position_frame.z_entry_frame, text="Z")
        position_frame.z_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.z_entry.grid(row=0, column=1, sticky="w")

        #Theta Entry
        position_frame.theta_entry_frame = ttk.Frame(position_frame)
        position_frame.theta_entry = ttk.Entry(position_frame.theta_entry_frame, width=15)
        position_frame.theta_entry_label = ttk.Label(position_frame.theta_entry_frame, text="\N{Greek Capital Theta Symbol}")
        position_frame.theta_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.theta_entry.grid(row=0, column=1, sticky="w")

        #Focus Entry
        position_frame.focus_entry_frame = ttk.Frame(position_frame)
        position_frame.focus_entry = ttk.Entry(position_frame.focus_entry_frame, width=15)
        position_frame.focus_entry_label = ttk.Label(position_frame.focus_entry_frame, text="Focus")
        position_frame.focus_entry_label.grid(row=0, column=0, sticky="e")
        position_frame.focus_entry.grid(row=0, column=1, sticky="w")

        '''
        Grid for frames

                1   2   3   4   5

        x is 1
        y is 2
        z is 3
        theta is 4
        focus is 5
        '''

        #Gridding out each frame in postiion frame
        position_frame.x_entry_frame.grid(row=0, column=0, padx=5, sticky=(NSEW))
        position_frame.y_entry_frame.grid(row=0, column=1, padx=5, sticky=(NSEW))
        position_frame.z_entry_frame.grid(row=0, column=2, padx=5, sticky=(NSEW))
        position_frame.theta_entry_frame.grid(row=0, column=3, padx=5, sticky=(NSEW))
        position_frame.focus_entry_frame.grid(row=0, column=4, padx=5, sticky=(NSEW))
        
class x_y_frame(ttk.Frame):
    def print_up():
            print('Up was pressed')
    def __init__(x_y_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(x_y_frame, stage_control_tab, *args, **kwargs) 

        #Setting up buttons for up, down, left, right, zero and increment spinbox
    
        #Up button
        x_y_frame.positive_y_btn = ttk.Button(
            x_y_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #command=
        )

        #Down button
        x_y_frame.negative_y_btn = ttk.Button(
            x_y_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Right button
        x_y_frame.positive_x_btn = ttk.Button(
            x_y_frame,
            text="\N{RIGHTWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Left button
        x_y_frame.negative_x_btn = ttk.Button(
            x_y_frame,
            text="\N{LEFTWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        x_y_frame.zero_x_y_btn = ttk.Button(
            x_y_frame,
            text="ZERO XY"
            #TODO command=function from connector
        )

        #Increment spinbox
        x_y_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        x_y_frame.increment_box = ttk.Spinbox(
            x_y_frame, 
            from_=0, 
            to=5000.0, 
            textvariable=x_y_frame.spinval, #this holds the data in the entry
            increment=25, 
            width=9
            #TODO command= function from connector
        )


        '''
        Grid for buttons

                01  02  03  04  05  06
                07  08  09  10  11  12
                13  14  15  16  17  18
                19  20  21  22  23  24
                25  26  27  28  29  30   
                31  32  33  34  35  36

        Up is 03,04,09,10
        Right is 17,18,23,24
        Down is 27,28,33,34
        Left is 13,14,19,20
        Increment is 15,16
        Zero XY is 21,22
        '''


        #Gridding out buttons
        x_y_frame.positive_y_btn.grid(row=0, column=2, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #UP
        x_y_frame.positive_x_btn.grid(row=2, column=4, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #RIGHT
        x_y_frame.negative_y_btn.grid(row=4, column=2, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #DOWN
        x_y_frame.negative_x_btn.grid(row=2, column=0, rowspan=2, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #LEFT
        x_y_frame.zero_x_y_btn.grid(row=2, column=2, rowspan=1, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #Zero xy
        x_y_frame.increment_box.grid(row=3, column=2, rowspan=1, columnspan=2, padx=2, pady=2, sticky=(NSEW)) #Increment spinbox


class z_frame(ttk.Frame):
    def __init__(z_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(z_frame, stage_control_tab, *args, **kwargs) 

        #Setting up buttons for up, down, zero and increment spinbox

        #Up button
        z_frame.up_btn = ttk.Button(
            z_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Down button
        z_frame.down_btn = ttk.Button(
            z_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        z_frame.zero_z_btn = ttk.Button(
            z_frame,
            text="ZERO Z"
            #TODO command=function from connector
        )

        #Increment spinbox
        z_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        z_frame.increment_box = ttk.Spinbox(
            z_frame, 
            from_=0, 
            to=5000.0, 
            textvariable=z_frame.spinval, #this holds the data in the entry
            increment=25, 
            width=9,
            #TODO command= function from connector
        )


        '''
        Grid for buttons

                1
                2
                3
                4
                5
                6

        Up is 1,2
        Down is 5,6
        Increment is 3
        Zero is 4
        '''


        #Gridding out buttons
        z_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        z_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        z_frame.zero_z_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero Z
        z_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox

class theta_frame(ttk.Frame):
    def __init__(theta_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(theta_frame, stage_control_tab, *args, **kwargs) 

        #Setting up rotation buttons

        #Up button
        theta_frame.up_btn = ttk.Button(
            theta_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Down button
        theta_frame.down_btn = ttk.Button(
            theta_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        theta_frame.zero_theta_btn = ttk.Button(
            theta_frame,
            text="ZERO \N{Greek Capital Theta Symbol}"
            #TODO command=function from connector
        )

        #Increment spinbox
        theta_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        theta_frame.increment_box = ttk.Spinbox(
            theta_frame, 
            from_=0, 
            to=5000.0, 
            textvariable=theta_frame.spinval, #this holds the data in the entry
            increment=25, 
            width=9,
            #TODO command= function from connector
        )


        '''
        Grid for buttons

                1
                2
                3
                4
                5
                6

        Up is 1,2
        Down is 5,6
        Increment is 3
        Zero is 4
        '''


        #Gridding out buttons
        theta_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        theta_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        theta_frame.zero_theta_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero theta
        theta_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox



class focus_frame(ttk.Frame):
    def __init__(focus_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(focus_frame, stage_control_tab, *args, **kwargs) 

        #Setting up focus buttons

        #Up button
        focus_frame.up_btn = ttk.Button(
            focus_frame,
            text="\N{UPWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Down button
        focus_frame.down_btn = ttk.Button(
            focus_frame,
            text="\N{DOWNWARDS BLACK ARROW}"
            #TODO command=function from connector
        )

        #Zero button
        focus_frame.zero_focus_btn = ttk.Button(
            focus_frame,
            text="ZERO Focus"
            #TODO command=function from connector
        )

        #Increment spinbox
        focus_frame.spinval = StringVar() #Will be changed by spinbox buttons, but is can also be changed by functions. This value is shown in the entry
        focus_frame.increment_box = ttk.Spinbox(
            focus_frame, 
            from_=0, 
            to=5000.0, 
            textvariable=focus_frame.spinval, #this holds the data in the entry
            increment=25, 
            width=9,
            #TODO command= function from connector
        )


        '''
        Grid for buttons

                1
                2
                3
                4
                5
                6

        Up is 1,2
        Down is 5,6
        Increment is 3
        Zero is 4
        '''


        #Gridding out buttons
        focus_frame.up_btn.grid(row=0, column=0, rowspan=2, pady=2, sticky=(NSEW)) #UP
        focus_frame.down_btn.grid(row=4, column=0, rowspan=2, pady=2, sticky=(NSEW)) #DOWN
        focus_frame.zero_focus_btn.grid(row=2, column=0, pady=2, sticky=(NSEW)) #Zero focus
        focus_frame.increment_box.grid(row=3, column=0, pady=2, sticky=(NSEW)) #Increment spinbox

class goto_frame(ttk.Frame):
    def __init__(goto_frame, stage_control_tab, *args, **kwargs):
        #Init Frame
        ttk.Frame.__init__(goto_frame, stage_control_tab, *args, **kwargs) 

'''
End of Stage Control Tab Frame Classes
'''