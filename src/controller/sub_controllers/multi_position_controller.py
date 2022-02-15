from tkinter import filedialog
import math
import pandas as pd
from pandastable import TableModel

from controller.sub_controllers.gui_controller import GUI_Controller


class Multi_Position_Controller(GUI_Controller):
    
    def __init__(self, view, parent_controller=None, verbose=None):
        super().__init__(view, parent_controller, verbose)

        self.table = self.view.pt

        self.table.rowheader.bind("<Double-Button-1>", self.handle_double_click)
        self.table.loadCSV = self.load_csv_func
        self.table.exportCSV = self.export_csv_func
        self.table.insertRow = self.insert_row_func
        self.table.generatePositions = self.generate_positions_func
        self.table.addStagePosition = self.add_stage_position_func

    def set_positions(self, positions):
        """
        # This function set positions to multi-position's table
        """
        axis_dict = {
            'x': 'X',
            'y': 'Y',
            'z': 'Z',
            'theta': 'R',
            'f': 'F'
        }
        data = {}
        for name in axis_dict:
            data[axis_dict[name]] = list(map(lambda pos: positions[pos][name], positions))
        self.table.model.df = pd.DataFrame(data)
        self.table.redraw()

        self.show_verbose_info('loaded new positions')

    def get_positions(self):
        """
        # This function will return all positions
        """
        axis_dict = {
            'X': 'x',
            'Y': 'y',
            'Z': 'z',
            'R': 'theta',
            'F': 'f'
        }
        positions = {}
        rows = self.table.model.df.shape[0]
        for i in range(rows):
            temp = list(self.table.model.df.iloc[i])
            if len(list(filter(lambda v: type(v) == float and not math.isnan(v), temp))) == 5:
                temp = dict(self.table.model.df.iloc[i])
                positions[i] = {}
                for k in axis_dict:
                    positions[i][axis_dict[k]] = temp[k]
        return positions

    def handle_double_click(self, event):
        """
        # when double clicked the row head, it will call the parent/central controller
        # to move stage and update stage view
        """
        rowclicked = self.table.get_row_clicked(event)
        df = self.table.model.df
        temp = list(df.loc[rowclicked])
        # validate position
        if list(filter(lambda v: type(v) != int and type(v) != float, temp)):
            #  TODO: show error: position is invalid
            print('position is invalid')
            return
        position = {
            'x': temp[0],
            'y': temp[1],
            'z': temp[2],
            'theta': temp[3],
            'f': temp[4]
        }
        self.parent_controller.execute('move_stage_and_update_info', position)
        self.show_verbose_info('move stage to', position)

    def get_position_num(self):
        """
        # this function return the number of positions
        """
        return self.table.model.df.shape[0]

    def load_csv_func(self):
        """
        # this function load a csv file,
        # the valid csv file should contain the line of headers ['X', 'Y', 'Z', 'R', 'F']
        """
        filename = filedialog.askopenfilenames(defaultextension='.csv', filetypes=(('CSV files', '*.csv'),
                                                                                   ('Text files', '*.txt')))
        if not filename:
            return
        df = pd.read_csv(filename[0])
        # validate the csv file
        df.columns = map(lambda v: v.upper(), df.columns)
        cmp_header = df.columns == ['X', 'Y', 'Z', 'R', 'F']
        if not cmp_header.all():
            #  TODO: show error message
            print("The csv file isn't right, it should contain [X, Y, Z, R, F]")
            return
        model = TableModel(dataframe=df)
        self.table.updateModel(model)
        self.table.redraw()
        self.show_verbose_info('loaded csv file', filename)

    def export_csv_func(self):
        """
        # this function opens a dialog that let the user input a filename
        # then, it will export positions to that csv file
        """
        filename = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=(('CSV file', '*.csv'),
                                                                                    ('Text file', '*.txt')))
        if not filename:
            return
        self.table.model.df.to_csv(filename, index=False)   
        self.show_verbose_info('exporting csv file', filename)

    def insert_row_func(self):
        """
        # this function insert a row before selected row
        """
        self.table.model.addRow(self.table.currentrow)
        self.table.update_rowcolors()
        self.table.redraw()
        self.table.tableChanged()
        self.show_verbose_info('insert a row before current row')

    def generate_positions_func(self):
        """
        # this function opens a dialog to let the user input start and end position
        # then it will generate positions for the user
        """
        pass

    def add_stage_position_func(self):
        """
        # this function will get the stage's current position,
        # then add it to position list
        """
        position = self.parent_controller.execute('get_stage_position')
        temp = list(map(lambda k: position[k], position))
        self.table.model.df = self.table.model.df.append(pd.DataFrame([temp], columns=list('XYZRF')), ignore_index=True)
        self.table.currentrow = self.table.model.df.shape[0]-1
        self.table.update_rowcolors()
        self.table.redraw()
        self.table.tableChanged()

        self.show_verbose_info('add current stage position to position list')
