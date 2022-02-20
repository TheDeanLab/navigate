from controller.sub_controllers.gui_controller import GUI_Controller
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg)
from matplotlib.figure import Figure


class Waveform_Tab_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)
        self.remote_focus_waveform = 0
        self.etl_r_waveform = 0
        self.galvo_l_waveform = 0
        self.galvo_r_waveform = 0
        self.laser_ao_waveforms = 0

        #TODO: Update waveforms according to the current model?
        #TODO: How do you detect changes to the model to rerun the code?
        #TODO: Concatenate each channel into a consecutive waveform as the microscope actually will.

    def update_waveforms(self):
        self.etl_l_waveform = self.parent_controller.model.daq.etl_l_waveform
        self.etl_r_waveform = self.parent_controller.model.daq.etl_r_waveform
        self.galvo_l_waveform = self.parent_controller.model.daq.galvo_l_waveform
        self.galvo_r_waveform = self.parent_controller.model.daq.galvo_r_waveform
        self.laser_ao_waveforms = self.parent_controller.model.daq.laser_ao_waveforms

    def plot_waveforms(self):
        self.parent_controller.model.daq.create_waveforms()
        self.update_waveforms()
        self.view.fig = Figure(figsize=(8, 4), dpi=100)

        self.view.plot1 = self.view.fig.add_subplot(511)
        self.view.plot1.plot(self.etl_l_waveform, label='ETL L')

        self.view.plot2 = self.view.fig.add_subplot(512)
        self.view.plot2.plot(self.galvo_l_waveform, label='GALVO L')

        self.view.plot3 = self.view.fig.add_subplot(513)
        self.view.plot3.plot(self.laser_ao_waveforms, label='LASER')

        self.view.plot4 = self.view.fig.add_subplot(514)
        self.view.plot4.plot(self.galvo_r_waveform, label='GALVO R')

        self.view.canvas = FigureCanvasTkAgg(self.view.fig, master=self.view)
        self.view.canvas.get_tk_widget().pack()

