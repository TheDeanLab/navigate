import tkinter as tk

from navigate.view.display_backends.gl_backend import GLVolumeViewBackend

class TestWidget(tk.Frame):
    def __init__(self, master=None):
        super().__init__(
            master=tk.Tk() if master is None else master,
            width=400,
            height=400
            )
        
        self.pack()


if __name__ == "__main__":

    app = TestWidget()
    
    gl_backend = GLVolumeViewBackend()
    gl_backend.start()

    app.mainloop()