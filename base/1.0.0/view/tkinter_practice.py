#Think of tkinter as HTML, ttk as CSS, and Python as javascript

from tkinter import *
from tkinter import ttk

#This starts the main window, and makes sure that any child widgets can be resized with the window
root_window = Tk()
root_window.columnconfigure(0,weight=1)
root_window.rowconfigure(0,weight=1)

#A frame is needed first and this holds all content in the window, its parent is the root window, children will be other widgets. Padding is for aesthetics
content = ttk.Frame(root_window, padding=(5,5))

#####This creates the basic start of the layout for our GUI######

#Notebook 1 setup, packing a label to help distinguish
frame_left = ttk.Frame(content)
left_frame_label = ttk.Label(frame_left, text="Notebook #1")
left_frame_label.pack()

#Notebook 2 setup
frame_top_right = ttk.Frame(content)
top_right_frame_label = ttk.Label(frame_top_right, text="Notebook #2")
top_right_frame_label.pack()

#Notebook 3 setup
frame_bottom_right = ttk.Frame(content)
bottom_right_frame_label = ttk.Label(frame_bottom_right, text="Notebook #3")
bottom_right_frame_label.pack()


'''
Placing the notebooks using grid. While the grid is called on each frame it is actually calling 
the main window since those are the parent to the frames. The labels have already been packed into each respective
frame so can be ignored in the grid setup. This layout uses a 2x2 grid to start. 

       # 1   2
        #3   4 

The above is the grid "spots" the left frame will take spots 1 & 3 while top right takes
spot 2 and bottom right frame takes spot 4.
'''
#Gridding out foundational frames
content.grid(column=0, row=0, sticky=(N, S, E, W)) #Sticky tells which walls of gridded cell the widget should stick to
frame_left.grid(row=0, column=0, rowspan=2)
frame_top_right.grid(row=0, column=1)
frame_bottom_right.grid(row=1, column=1)

#This dictates how to weight each piece of the grid, so that when the window is resized the notebooks get the proper screen space. 
# Content is the frame holding all the other frames that hold the notebooks to help modularize the code
content.columnconfigure(0, weight=1)
content.columnconfigure(1, weight=1) #weights are relative to each other so if there is a 3 and 1 the 3 weight will give that col/row 3 pixels for every one the others get
content.rowconfigure(0, weight=1)
content.rowconfigure(1,weight=1)


root_window.mainloop()