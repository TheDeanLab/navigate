# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print("Launching the Toy MVC Example")  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    import tkinter as tk
    from Controller import Controller

    root = tk.Tk()
    root.withdraw()
    app = Controller(root)
    root.mainloop()


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
