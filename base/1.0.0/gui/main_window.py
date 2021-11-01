from tkinter import *

import tkinter as tk
from tkinter import ttk
from welcome_window import WelcomeTab
from run_window import RunTab
from stages_window import StagesTab
from advanced_settings_window import AdvancedSettingsTab

class MultiScopeMainGui(ttk.Notebook):
    """
    This is the main GUI class for the multi-scale microscope. It arranges the microscope GUI into different tabs:
    a welcome tab, a settings tab, a stage settings tab, a run tab and the advanced settings
    """


    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

        # set the window properties
        # define the individual sheets: a welcome tab, a settings tab,
        # a stage settings tab, a run tab and the advanced settings

        self.run_tab = RunTab(self)
        #self.welcome_tab = WelcomeTab(self)
        self.stages_settings_tab = StagesTab(self)
        self.advanced_settings_tab = AdvancedSettingsTab(self)

        # add the individual sheets to the Notebook
        self.add(self.run_tab, text="Run")
        #self.add(self.welcome_tab, text = "Welcome")
        self.add(self.stages_settings_tab, text="Stages")
        self.add(self.advanced_settings_tab, text="Advanced Settings")

        #pack the sheets
        #self.pack(expand=1, fill='both')
        self.pack()

if __name__ == '__main__':
    root = tk.Tk()
    print("Root is type", type(root))
    root.geometry("2000x800")
    root.title("Multiscale Cleared Tissue Microscope")
    option = 2
    if option == 1:
        notebook = ttk.Notebook(root)
        all_tabs_main_GUI = ttk.Notebook(root)
        GUI_main_window = MultiScopeMainGui(all_tabs_main_GUI)
        print("The type of window is ", type(GUI_main_window))

    if option == 2:
        # root -> frame -> notebook -> tabs
        frame_left = ttk.Frame(root, width=800, height=800)
        notebook_left= ttk.Notebook(frame_left)
        all_tabs_main_GUI = ttk.Notebook(frame_left)
        GUI_main_window = MultiScopeMainGui(all_tabs_main_GUI)
        frame_right = ttk.Frame(root, width=800, height=800, x=800, y=800)
        notebook_right = ttk.Notebook(frame_right)
        GUI_second_window = MultiScopeMainGui(all_tabs_main_GUI)

    if option == 3:
        frame_left = ttk.Frame(root, width=800, height=800)
        notebook_left= ttk.Notebook(frame_left)
        #all_tabs_main_GUI = ttk.Notebook(notebook_left)
        #GUI_main_window = MultiScopeMainGui(all_tabs_main_GUI)

        frame_right = ttk.Frame(root, width=800, height=800)
        tabControl = ttk.Notebook(frame_right)

        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)

        tabControl.add(tab1, text ='Tab 1')
        tabControl.add(tab2, text ='Tab 2')
        tabControl.pack(expand = 1, fill ="both")

        ttk.Label(tab1, text ="Lets dive into the world of computers").grid(
            column = 0, row = 0, padx = 30, pady = 30)

        ttk.Label(tab2, text ="Lets dive into the world of computers").grid(
            column = 0, row = 0, padx = 30, pady = 30)

    if option == 4:
        root = tk.Tk()

        test = tk.Label(root, text="red", bg="red", fg="white")
        test.pack(padx=5, pady=15, side=tk.LEFT)
        test = tk.Label(root, text="green", bg="green", fg="white")
        test.pack(padx=5, pady=20, side=tk.LEFT)
        test = tk.Label(root, text="purple", bg="purple", fg="white")
        test.pack(padx=5, pady=20, side=tk.LEFT)



root.mainloop()


    #GUI_main_window.pack(fill='both', expand=True)
    #root = Tk()


    #frame1 = ttk.Frame(notebook, width=400, height=280)
    #notebook.add(frame1, text ='Notebook tab1')

    #frame2 = ttk.Frame(notebook, width=400, height=280)

    #frame1.pack(fill='both', expand=True)
    #frame2.pack(fill='both', expand=True)

    #notebook.add(frame1, text='General Information')
    #notebook.add(frame2, text='Profile')

    #Make the first notebook
    #program = ttk.Notebook(root) #Create the program notebook
    #program.pack()

    #Make the terms frames for the program notebook

'''for r in range(1,4):
    termName = 'Term'+str(r) #concatenate term name(will come from dict)
    term = Frame(program)   #create frame widget to go in program nb
    program.add(term, text=termName)# add the newly created frame widget to the program notebook
    nbName=termName+'courses'#concatenate notebook name for each iter
    nbName = ttk.Notebook(term)#Create the notebooks to go in each of the terms frames
    nbName.pack()#pack the notebook

    for a in range (1,6):
        courseName = termName+"Course"+str(a)#concatenate coursename(will come from dict)
        course = Frame(nbName) #Create a course frame for the newly created term frame for each iter
        nbName.add(course, text=courseName)#add the course frame to the new notebook

root.mainloop()



root = Tk() #Makes the window
root.geometry("1600x800")
root.wm_title("Multiscale Microscope") #Makes the title that will appear in the top left
root.config(background = "#FFFFFF")

def redCircle():
    circleCanvas.create_oval(20, 20, 80, 80, width=0, fill='red')
    colorLog.insert(0.0, "Red\n")

def yelCircle():
    circleCanvas.create_oval(20, 20, 80, 80, width=0, fill='yellow')
    colorLog.insert(0.0, "Yellow\n")

def grnCircle():
    circleCanvas.create_oval(20, 20, 80, 80, width=0, fill='green')
    colorLog.insert(0.0, "Green\n")


#Left Frame and its contents
left_frame = Frame(root, width=800, height = 800)
left_notebook = ttk.Notebook(left_frame)


#left_frame.grid(row=0, column=0, padx=10, pady=2)
#Label(left_frame, text="Instructions:").grid(row=0, column=0, padx=10, pady=2)

Instruct = Label(left_frame, text="1\n2\n2\n3\n4\n5\n6\n7\n8\n9\n")
Instruct.grid(row=1, column=0, padx=10, pady=2)

try:
    imageEx = PhotoImage(file = 'image.gif')
    Label(leftFrame, image=imageEx).grid(row=2, column=0, padx=10, pady=2)
except:
    print("Image not found")

#Right Frame and its contents
rightFrame = Frame(root, width=200, height = 600)
rightFrame.grid(row=0, column=1, padx=10, pady=2)

circleCanvas = Canvas(rightFrame, width=100, height=100, bg='white')
circleCanvas.grid(row=0, column=0, padx=10, pady=2)

btnFrame = Frame(rightFrame, width=200, height = 200)
btnFrame.grid(row=1, column=0, padx=10, pady=2)

colorLog = Text(rightFrame, width = 30, height = 10, takefocus=0)
colorLog.grid(row=2, column=0, padx=10, pady=2)

redBtn = Button(btnFrame, text="Red", command=redCircle)
redBtn.grid(row=0, column=0, padx=10, pady=2)

yellowBtn = Button(btnFrame, text="Yellow", command=yelCircle)
yellowBtn.grid(row=0, column=1, padx=10, pady=2)

greenBtn = Button(btnFrame, text="Green", command=grnCircle)
greenBtn.grid(row=0, column=2, padx=10, pady=2)


root.mainloop() #start monitoring and updating the GUI
'''