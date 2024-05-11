import tkinter as tk

class CollapsibleFrame(tk.Frame):
    def __init__(self, parent, title="", *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        
        self.title = title
        self.visible = False
        
        # Create a label to act as a title/header
        self.label = tk.Label(self, text=self.title, bg="lightgrey", relief="raised", padx=5)
        self.label.grid(row=0, column=0, sticky=tk.NSEW)
        
        # Create a frame to hold the contents of the collapsible frame
        self.content_frame = tk.Frame(self)
        self.toggle_visibility()

        self.label.bind("<Button-1>", lambda event: self.toggle_visibility())
        
    def toggle_visibility(self):
        if self.visible:
            self.label["text"] = self.title + " " + "\u25BC"
            self.content_frame.grid_forget()  # Hide the content frame
            self.visible = False
        else:
            self.label["text"] = self.title + " " + "\u25B2"
            self.content_frame.grid(row=1, column=0, sticky=tk.NSEW)  # Show the content frame
            self.visible = True

    def fold(self):
        if self.visible:
            self.toggle_visibility()

