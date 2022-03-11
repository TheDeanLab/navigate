from tkinter import Menu


#  Menubar class
class menubar(Menu):
    def __init__(self, window, *args, **kwargs):
        #  Init Menu with parent
        Menu.__init__(self, window, *args, **kwargs)

        #  Creates operating system attribute
        self.opsystem = window.tk.call('tk', 'windowingsystem')

        #  Prevents menu from tearing off bar
        window.option_add('*tearOff', False)

        #  Linking menu to option of parent to this menu class
        window['menu'] = self

        #  File Menu
        self.menu_file = Menu(self)
        self.add_cascade(menu=self.menu_file, label='File')

        #  Multi-Position Menu
        self.menu_multi_positions = Menu(self)
        self.add_cascade(menu=self.menu_multi_positions, label='Multi-Position')

        #  Zoom Menu
        self.menu_zoom = Menu(self)
        self.add_cascade(menu=self.menu_zoom, label='Zoom')

        #  Resolution Menu
        self.menu_resolution = Menu(self)
        self.add_cascade(menu=self.menu_resolution, label='Resolution Mode')

