
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox


class AdvancedSettingsTab(tk.Frame):
    """
    A tab for advanced settings such as rotational stage calibration etc

    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        # intro-text
        # intro-text
        intro_text = tk.Label(self, text='In this tab, you have some advanced settings available \n', height=2, width=115,
                              fg="black", bg="grey")
        intro_text.grid(row=0, column=0, columnspan=5000, sticky=(tk.E))

        #slit settings
        self.slit_currentsetting = tk.DoubleVar()
        self.slit_lowres = tk. DoubleVar()
        self.slit_highres = tk. DoubleVar()

        #stack acquisition settings
        self.stack_aq_camera_delay = tk.DoubleVar()
        self.stack_aq_stage_velocity = tk.DoubleVar()
        self.stack_aq_stage_acceleration = tk.DoubleVar()

        #ASLM settings
        self.ASLM_scanWidth = tk.DoubleVar()
        self.ASLM_volt_interval = tk.DoubleVar()
        self.ASLM_volt_middle = tk.DoubleVar()
        self.ASLM_volt_current = tk.DoubleVar()
        self.ASLM_alignmentmodeOn = tk.IntVar() #switch ASLM alignment mode on/off
        self.ASLM_SawToothOn = tk.IntVar() #choose SawTooth in ASLM alignment mode
        self.ASLM_constantVoltageOn = tk.IntVar() #choose constant voltage in ASLM alignment mode
        self.ASLM_volt_lowRes_static = tk.DoubleVar() #parameter for low resolution static light sheet
        self.ASLM_volt_highRes_static = tk.DoubleVar() #parameter for high resolution static light sheet
        self.ASLM_SawtoothORconstant = tk.StringVar()
        self.ASLM_voltageDirection = tk.StringVar()

        #mSPIM settings
        self.adv_settings_mSPIMvoltage = tk.DoubleVar() #set voltage for remote galvo mirror

        ### ----------------------------label frames-----------------------------------------------------------------

        #set the different label frames
        slit_settings = tk.LabelFrame(self, text="Slit Settings")
        stack_aq_settings = tk.LabelFrame(self, text="Stack Acquisition Settings")
        ASLM_settings = tk.LabelFrame(self, text="ASLM Settings")
        mSPIM_settings = tk.LabelFrame(self, text="mSPIM Settings")

        # overall positioning of label frames
        slit_settings.grid(row=2, column=0, sticky = tk.W + tk.E+tk.S+tk.N)
        stack_aq_settings.grid(row=4, column=0, sticky = tk.W + tk.E+tk.S+tk.N)
        ASLM_settings.grid(row=2, column=1, sticky = tk.W + tk.E+tk.S+tk.N)
        mSPIM_settings.grid(row=6, column=0, sticky = tk.W + tk.E+tk.S+tk.N)

        ### ----------------------------slit settings -----------------------------------------------------------------
        # slit labels (positioned)
        slit_opening_label = ttk.Label(slit_settings, text="Slit opening:").grid(row=2, column=0)
        slit_opening_label2 = ttk.Label(slit_settings, text="current:").grid(row=3, column=0)
        slit_lowres_label = ttk.Label(slit_settings, text="Low Res:").grid(row=4, column=0)
        slit_highres_label = ttk.Label(slit_settings, text="High Res:").grid(row=4, column=3)

        self.slit_opening_entry = tk.Entry(slit_settings, textvariable=self.slit_currentsetting, width=6)
        self.slit_lowres_entry = tk.Entry(slit_settings, textvariable=self.slit_lowres, width=6)
        self.slit_highres_entry = tk.Entry(slit_settings, textvariable=self.slit_highres, width=6)

        slit_scale = tk.Scale(slit_settings, variable=self.slit_currentsetting, from_=0, to=4558, orient="horizontal")

        # set defaults
        self.slit_lowres.set(3700)
        self.slit_highres.set(4558)

        # slit settings layout
        slit_scale.grid(row=2, column=1, rowspan=2, columnspan=4, sticky=tk.W + tk.E)
        self.slit_opening_entry.grid(row=3, column=5, sticky=tk.W + tk.E + tk.S)
        self.slit_lowres_entry.grid(row=4, column=1, columnspan=2, sticky=tk.W + tk.E + tk.S)
        self.slit_highres_entry.grid(row=4, column=4, columnspan=2, sticky=tk.W + tk.E + tk.S)

        ### ----------------------------stack acquisition settings -----------------------------------------------------------------
        # slit labels (positioned)
        delay_camera_label = ttk.Label(stack_aq_settings, text="Delay time camera after stage signal sent (ms):").grid(row=2, column=0)
        stage_velocity_label = ttk.Label(stack_aq_settings, text="Stage velocity:").grid(row=4, column=0)
        stage_acceleration_label = ttk.Label(stack_aq_settings, text="Stage acceleration:").grid(row=6, column=0)

        self.delay_camera_entry = tk.Entry(stack_aq_settings, textvariable=self.stack_aq_camera_delay, width=10)
        self.stage_velocity_entry = tk.Entry(stack_aq_settings, textvariable=self.stack_aq_stage_velocity, width=10)
        self.stage_acceleration_entry = tk.Entry(stack_aq_settings, textvariable=self.stack_aq_stage_acceleration, width=10)

        # set defaults
        self.stack_aq_camera_delay.set(1)
        self.stack_aq_stage_velocity.set(1)
        self.stack_aq_stage_acceleration.set(1)

        # layout
        self.delay_camera_entry.grid(row=2, column=1, sticky=tk.W + tk.E + tk.S)
        self.stage_velocity_entry.grid(row=4, column=1, sticky=tk.W + tk.E + tk.S)
        self.stage_acceleration_entry.grid(row=6, column=1, sticky=tk.W + tk.E + tk.S)

        ### ----------------------------mSPIM settings -----------------------------------------------------------------
        # slit labels (positioned)
        mSPIM_voltage_label = ttk.Label(mSPIM_settings, text="voltage @resonant galvo:").grid(
            row=2, column=0)

        self.mSPIM_voltage_entry = tk.Entry(mSPIM_settings, textvariable=self.adv_settings_mSPIMvoltage, width=4)

        # set defaults
        self.adv_settings_mSPIMvoltage.set(0.1)

        # layout
        self.mSPIM_voltage_entry.grid(row=2, column=1, sticky=tk.W + tk.E + tk.S)

        ### ----------------------------ASLM settings -----------------------------------------------------------------
        # ASLM labels (positioned)
        lineDelay_label = ttk.Label(ASLM_settings, text="Scan Width:").grid(row=2, column=0)
        voltageinterval_label = ttk.Label(ASLM_settings, text="ASLM remote voltage interval (mV):").grid(row=4, column=0)
        voltagemiddle_label = ttk.Label(ASLM_settings, text="ASLM remote voltage middle (mV):").grid(row=7, column=0)
        voltagecurrent_label = ttk.Label(ASLM_settings, text="Current ASLM remote mirror voltage (mV):").grid(row=13, column=0)
        voltagedirection_label = ttk.Label(ASLM_settings, text="Voltage up-down or down-up:").grid(row=9, column=0)
        voltagelowRes_label = ttk.Label(ASLM_settings, text="Low Resolution ASLM remote mirror voltage (static, mV):").grid(row=14, column=0)
        voltagehighRes_label = ttk.Label(ASLM_settings, text="High Resolution ASLM remote mirror voltage (static, mV):").grid(row=16, column=0)
        voltageminimal_label = ttk.Label(ASLM_settings, text="Min Vol@mirror:").grid(row=10, column=0)
        voltagemaximal_label = ttk.Label(ASLM_settings, text="Max Vol@mirror:").grid(row=11, column=0)

        self.scanWidth_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_scanWidth, width=6)
        self.voltageinterval_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_volt_interval, width=6)
        self.voltagemiddle_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_volt_middle, width=6)
        self.voltagecurrent_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_volt_current, width=6)
        self.voltageLowRes_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_volt_lowRes_static, width=6)
        self.voltageHighRes_entry = tk.Entry(ASLM_settings, textvariable=self.ASLM_volt_highRes_static, width=6)

        #Voltage choice indicator
        self.voltage_minIndicator = tk.Label(ASLM_settings, text="0.003")
        self.voltage_maxIndicator = tk.Label(ASLM_settings, text="-0.003")

        # choice of scan mode
        self.ASLM_alignmentmodeOn_chkbt = tk.Checkbutton(ASLM_settings, text='Alignment mode on',
                                                         variable=self.ASLM_alignmentmodeOn, onvalue=1, offvalue=0)

        # choice of voltage (from plus to minus OR minus to plus)
        ASLM_voltage_run = ('highTolow', 'lowToHigh')
        self.ASLM_runOptionsMenu_Voltage = tk.OptionMenu(ASLM_settings, self.ASLM_voltageDirection,
                                                 *ASLM_voltage_run)
        self.ASLM_voltageDirection.set(ASLM_voltage_run[1])

        # set defaults
        self.ASLM_scanWidth.set(60)
        self.ASLM_volt_interval.set(60)
        self.ASLM_volt_middle.set(0)
        self.ASLM_volt_current.set(0)
        self.ASLM_volt_lowRes_static.set(0)
        self.ASLM_volt_highRes_static.set(0)


        #ASLM settings layout
        self.scanWidth_entry.grid(row=2, column=1, sticky=tk.W + tk.E + tk.S)
        self.voltageinterval_entry.grid(row=4, column=1, sticky=tk.W + tk.E + tk.S)
        self.voltagemiddle_entry.grid(row=7, column=1, sticky=tk.W + tk.E + tk.S)
        self.ASLM_runOptionsMenu_Voltage.grid(row=9, column=1, sticky=tk.W + tk.E + tk.S)
        self.voltage_minIndicator.grid(row=10, column=3, sticky=tk.W + tk.E + tk.S)
        self.voltage_maxIndicator.grid(row=11, column=3, sticky=tk.W + tk.E + tk.S)

        self.ASLM_alignmentmodeOn_chkbt.grid(row=12, column=0, sticky=tk.W + tk.S)
        self.voltagecurrent_entry.grid(row=13, column=1, sticky=tk.W + tk.E + tk.S)
        self.voltageLowRes_entry.grid(row=14, column=1, sticky=tk.W + tk.S)
        self.voltageHighRes_entry.grid(row=16, column=1, sticky=tk.W + tk.S)

    def print_values(self):
        print("test")
