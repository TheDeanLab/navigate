import tkinter as tk
from tkinter import ttk
import time
import datetime as dt
import math

class RunTab(tk.Frame):
    """
    A run tab to select parameters such as
    - acquisition settings, e.g. nb of time points, which channels are imaged
    - Cycle laser (e.g. per stack or per plane)
    - which channel is displayed
    - preview button
    - number of planes
    - plane spacing
    """

    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, **kwargs)

        # intro-text
        welcometext = 'In this tab, select parameters to run preview, stack and time-lapse acquisitions \n'
        intro_text = tk.Label(self, text=welcometext, height=2, width=115, fg="black", bg="grey")
        intro_text.grid(row=0, column=0, columnspan=5000, sticky=(tk.E))

        self.preview_autoIntensity = tk.IntVar()

        #laser settings
        self.laser488_percentage = tk.IntVar()
        self.laser552_percentage = tk.IntVar()
        self.laser594_percentage = tk.IntVar()
        self.laser640_percentage = tk.IntVar()

        #Camera settings
        self.cam_lowresExposure = tk.IntVar()
        self.cam_highresExposure = tk.IntVar()
        self.cam_highresMode = tk.StringVar()

        #stack acquisition parameters
        self.stack_aq_progress = tk.DoubleVar()
        self.stack_aq_488on = tk.IntVar()
        self.stack_aq_552on = tk.IntVar()
        self.stack_aq_594on = tk.IntVar()
        self.stack_aq_640on = tk.IntVar()
        self.stack_aq_displayON = tk.IntVar()
        self.stack_aq_lowResCameraOn = tk.IntVar()
        self.stack_aq_highResCameraOn = tk.IntVar()
        self.stack_acq_laserCycleMode = tk.StringVar()
        self.stack_aq_numberOfPlanes_lowres = tk.IntVar()
        self.stack_aq_numberOfPlanes_highres = tk.IntVar()
        self.stack_aq_plane_spacing_lowres = tk.DoubleVar()
        self.stack_aq_plane_spacing_highres = tk.DoubleVar()

        #time-lapse setting parameters
        self.timelapse_aq_progress = tk.DoubleVar()
        self.timelapse_aq_nbTimepoints = 22
        self.timelapse_aq_timeinterval_min = tk.DoubleVar()
        self.timelapse_aq_timeinterval_min.set(15)
        self.timelapse_aq_timeinterval_seconds = tk.DoubleVar()
        self.timelapse_aq_timeinterval_seconds.set(0)
        self.timelapse_aq_length_hours = tk.DoubleVar()
        self.timelapse_aq_length_hours.set(5)
        self.timelapse_aq_length_min = tk.DoubleVar()
        self.timelapse_aq_length_min.set(30)
        self.timelapse_aq_length_seconds = tk.DoubleVar()
        self.timelapse_aq_length_seconds.set(00)

        #roi setting
        self.roi_startX = tk.IntVar()
        self.roi_startY = tk.IntVar()
        self.roi_width = tk.IntVar()
        self.roi_height = tk.IntVar()
        self.roi_ac_settings_type = tk.StringVar()


        #set the different label frames
        laser_settings = tk.LabelFrame(self, text="Laser Settings")
        camera_settings = tk.LabelFrame(self, text="Camera Settings")
        preview_settings = tk.LabelFrame(self, text="Preview")
        stack_aquisition_settings = tk.LabelFrame(self, text="Stack acquisition")
        timelapse_acquisition_settings = tk.LabelFrame(self, text="Time-lapse acquisition")
        statusprogress_settings = tk.LabelFrame(self, text="Progress")
        roi_settings = tk.LabelFrame(self, text="Region of Interest (ROI)")

        # overall positioning of label frames
        preview_settings.grid(row=1, column=2, rowspan=1, sticky = tk.W + tk.E+tk.S+tk.N)
        stack_aquisition_settings.grid(row=2, column=2, rowspan=2, sticky = tk.W + tk.E+tk.S+tk.N)
        timelapse_acquisition_settings.grid(row=4, column=2, rowspan=2,sticky=tk.W + tk.E+tk.S+tk.N)
        statusprogress_settings.grid(row=7, column=2, sticky=tk.W + tk.E+tk.S+tk.N)

        laser_settings.grid(row=1, column=3, rowspan=2, sticky=tk.W + tk.E + tk.S + tk.N)
        camera_settings.grid(row=3, column=3, sticky=tk.W + tk.E + tk.S + tk.N)
        roi_settings.grid(row=4, column=3, rowspan=2, sticky=tk.W + tk.E+tk.S+tk.N)

        #define some labels here to ensure existance for code
        self.stack_aq_progressindicator = tk.Label(statusprogress_settings, text=" 0 of 0")
        self.timelapse_aq_progressindicator = tk.Label(statusprogress_settings, text=" 0 of 0")

        ### ----------------------------laser settings -----------------------------------------------------------------
        # laser labels (positioned)
        laser488_label = ttk.Label(laser_settings, text="488 nm:").grid(row=2, column=0)
        laser552_label = ttk.Label(laser_settings, text="552 nm:").grid(row=4, column=0)
        laser594_label = ttk.Label(laser_settings, text="594 nm:").grid(row=6, column=0)
        laser640_label = ttk.Label(laser_settings, text="640 nm:").grid(row=8, column=0)

        #laser output indication
        self.laser488_output = tk.Label(laser_settings, text="0 mW")
        self.laser552_output = tk.Label(laser_settings, text="0 mW")
        self.laser594_output = tk.Label(laser_settings, text="0 mW")
        self.laser640_output = tk.Label(laser_settings, text="0 mW")

        #laser percentage input
        self.laser488_entry = tk.Entry(laser_settings, textvariable=self.laser488_percentage, width=3)
        self.laser552_entry = tk.Entry(laser_settings, textvariable=self.laser552_percentage, width=3)
        self.laser594_entry = tk.Entry(laser_settings, textvariable=self.laser594_percentage, width=3)
        self.laser640_entry = tk.Entry(laser_settings, textvariable=self.laser640_percentage, width=3)

        laser488_scale = tk.Scale(laser_settings, variable=self.laser488_percentage, from_=0, to=100, orient="horizontal")
        laser552_scale = tk.Scale(laser_settings, variable=self.laser552_percentage, from_=0, to=100, orient="horizontal")
        laser594_scale = tk.Scale(laser_settings, variable=self.laser594_percentage, from_=0, to=100, orient="horizontal")
        laser640_scale = tk.Scale(laser_settings, variable=self.laser640_percentage, from_=0, to=100, orient="horizontal")

        #default values
        self.laser488_percentage.set(20)
        self.laser552_percentage.set(20)
        self.laser594_percentage.set(20)
        self.laser640_percentage.set(20)

        #laser widgets layout
        self.laser488_entry.grid(row=3, column=3, sticky=tk.W + tk.E + tk.S)
        self.laser552_entry.grid(row=5, column=3, sticky=tk.W + tk.E + tk.S)
        self.laser594_entry.grid(row=7, column=3, sticky=tk.W + tk.E + tk.S)
        self.laser640_entry.grid(row=9, column=3, sticky=tk.W + tk.E + tk.S)
        self.laser488_output.grid(row=3, column=0, sticky=tk.W + tk.E)
        self.laser552_output.grid(row=5, column=0, sticky=tk.W + tk.E)
        self.laser594_output.grid(row=7, column=0, sticky=tk.W + tk.E)
        self.laser640_output.grid(row=9, column=0, sticky=tk.W + tk.E)
        laser488_scale.grid(row=2, column=2, rowspan =2, sticky=tk.W + tk.E)
        laser552_scale.grid(row=4, column=2, rowspan =2, sticky=tk.W + tk.E)
        laser594_scale.grid(row=6, column=2, rowspan =2, sticky=tk.W + tk.E)
        laser640_scale.grid(row=8, column=2, rowspan =2, sticky=tk.W + tk.E)


        ### ----------------------------camera settings -----------------------------------------------------------------
        # camera labels (positioned)
        exposure_lowrescameralabel = ttk.Label(camera_settings, text="Exposure Low Res (ms)").grid(row=2, column=0)
        exposure_highrescameralabel = ttk.Label(camera_settings, text="Exposure High Res (ms)").grid(row=4, column=0)
        framerate_highrescameralabel = ttk.Label(camera_settings, text="Frame rate Low Res (Hz)").grid(row=6, column=0)
        framerate_lowrescameralabel = ttk.Label(camera_settings, text="Frame rate Low Res (Hz)").grid(row=8, column=0)
        highresmode_label = ttk.Label(camera_settings, text="High Res Acquisition Mode").grid(row=10, column=0)

        self.cam_lowresExposure_entry = tk.Entry(camera_settings, textvariable=self.cam_lowresExposure, width=5)
        self.cam_highresExposure_entry = tk.Entry(camera_settings, textvariable=self.cam_highresExposure, width=5)
        self.cam_lowresFrameRate = tk.Label(camera_settings, text="0")
        self.cam_highresFrameRate = tk.Label(camera_settings, text="0")

        # choice of high res camera mode
        highresModeOptions = ('SPIM Mode', 'ASLM Mode')
        self.cam_highresModeOption = tk.OptionMenu(camera_settings, self.cam_highresMode,
                                                        *highresModeOptions)
        self.cam_highresMode.set(highresModeOptions[0])

        #set defaults
        self.cam_lowresExposure.set(200)
        self.cam_highresExposure.set(200)

        #Layout Camera settings
        self.cam_lowresExposure_entry.grid(row=2, column=3, sticky=tk.W + tk.E + tk.S)
        self.cam_highresExposure_entry.grid(row=4, column=3, sticky=tk.W + tk.E + tk.S)
        self.cam_lowresFrameRate.grid(row=6, column=3, sticky=tk.W + tk.E + tk.S)
        self.cam_highresFrameRate.grid(row=8, column=3, sticky=tk.W + tk.E + tk.S)
        self.cam_highresModeOption.grid(row=10, column=3, sticky=tk.W + tk.E + tk.S)
        ### ----------------------------preview buttons ---------------------------------------------------------------
        #preview settings-----------------------------------------------------------------------------------
        self.bt_changeTo488 = tk.Button(preview_settings, text="488 nm", command= lambda : self.preview_filter_select(self.bt_changeTo488), bg="#00f7ff")
        self.bt_changeTo552 = tk.Button(preview_settings, text="552 nm", command= lambda : self.preview_filter_select(self.bt_changeTo552), bg="#a9ff00")
        self.bt_changeTo594 = tk.Button(preview_settings, text="594 nm", command=lambda : self.preview_filter_select(self.bt_changeTo594), bg="#ffd200")
        self.bt_changeTo640 = tk.Button(preview_settings, text="640 nm", command=lambda : self.preview_filter_select(self.bt_changeTo640), bg="#ff2100")
        self.bt_changeTo_block = tk.Button(preview_settings, text="no filter", command=lambda : self.preview_filter_select(self.bt_changeTo_block))
        self.bt_changeTo_trans = tk.Button(preview_settings, text="block", command=lambda : self.preview_filter_select(self.bt_changeTo_trans))
        self.bt_preview_lowres = tk.Button(preview_settings, text="Low Res Preview")
        self.bt_preview_highres = tk.Button(preview_settings, text="High Res Preview")
        self.bt_preview_stop = tk.Button(preview_settings, text="Stop Preview")

        self.preview_rescale = tk.Checkbutton(preview_settings, text ='Autom. intensity rescaling', variable=self.preview_autoIntensity, onvalue=1, offvalue=0)


        #preview layout
        self.bt_changeTo488.grid(row=3, column=2)
        self.bt_changeTo552.grid(row=3, column=3)
        self.bt_changeTo594.grid(row=3, column=4)
        self.bt_changeTo640.grid(row=3, column=5)
        self.bt_changeTo_block.grid(row=3, column=6)
        self.bt_changeTo_trans.grid(row=3, column=7)
        self.bt_preview_lowres.grid(row=4, column=2, columnspan=2, sticky = (tk.W + tk.E))
        self.bt_preview_highres.grid(row=4, column=4, columnspan=2, sticky=(tk.W + tk.E))
        self.bt_preview_stop.grid(row=4, column=6, columnspan=2, sticky=(tk.W + tk.E))
        self.preview_rescale.grid(row=3, column=8)

        ### ----------------------------stack acquisition buttons ------------------------------------------------------
        #stack aquisition labels (positioned)
        laseron_label = ttk.Label(stack_aquisition_settings, text="Laser On:").grid(row=2, column=0)
        numberOfPlanes_label_lowres= ttk.Label(stack_aquisition_settings, text="Number of planes (lowres):").grid(row = 6, column = 0)
        numberOfPlanes_label_highres= ttk.Label(stack_aquisition_settings, text="Number of planes (highres):").grid(row = 7, column = 0)
        plane_spacing_label_lowres= ttk.Label(stack_aquisition_settings, text="Spacing of planes (um, lowres):").grid(row = 10, column = 0)
        plane_spacing_label_highres= ttk.Label(stack_aquisition_settings, text="Spacing of planes (um, highres):").grid(row = 11, column = 0)
        laser_cyclemode_label= ttk.Label(stack_aquisition_settings, text="Laser Cycle Mode:").grid(row = 3, column = 0)
        cameraOn_label= ttk.Label(stack_aquisition_settings, text="Camera On:").grid(row = 4, column = 0)


        #stack aquisition settings......................................................................................
        #choice of laser
        self.stack_aq_laserOn488 = tk.Checkbutton(stack_aquisition_settings, text ='488', variable=self.stack_aq_488on, onvalue=1, offvalue=0)
        self.stack_aq_laserOn552 = tk.Checkbutton(stack_aquisition_settings, text ='552', variable=self.stack_aq_552on, onvalue=1, offvalue=0)
        self.stack_aq_laserOn594 = tk.Checkbutton(stack_aquisition_settings, text ='594', variable=self.stack_aq_594on, onvalue=1, offvalue=0)
        self.stack_aq_laserOn640 = tk.Checkbutton(stack_aquisition_settings, text ='640', variable=self.stack_aq_640on, onvalue=1, offvalue=0)

        self.stack_aq_displayIm = tk.Checkbutton(stack_aquisition_settings, text ='Display Images during Stack Acquisition', variable=self.stack_aq_displayON, onvalue=1, offvalue=0)


        #choice of camera
        self.stack_aq_ckb_lowresCamera  = tk.Checkbutton(stack_aquisition_settings, text ='Low Res Camera', variable=self.stack_aq_lowResCameraOn, onvalue=1, offvalue=0)
        self.stack_aq_ckb_highresCamera = tk.Checkbutton(stack_aquisition_settings, text ='High Res Camera', variable=self.stack_aq_highResCameraOn, onvalue=1, offvalue=0)

        #laser cycle
        laserCycles = ('Change filter/stack', 'Change filter/plane')
        self.stack_aq_option_laserCycle = tk.OptionMenu(stack_aquisition_settings, self.stack_acq_laserCycleMode, *laserCycles)
        self.stack_acq_laserCycleMode.set(laserCycles[0])

        #number of planes
        self.stack_aq_entry_numberOfPlanes_lowres = tk.Entry(stack_aquisition_settings, textvariable=self.stack_aq_numberOfPlanes_lowres)
        self.stack_aq_numberOfPlanes_lowres.set(200)
        self.stack_aq_entry_numberOfPlanes_highres = tk.Entry(stack_aquisition_settings, textvariable=self.stack_aq_numberOfPlanes_highres)
        self.stack_aq_numberOfPlanes_highres.set(200)

        #plane spacing
        self.stack_aq_entry_plane_spacing_lowres = tk.Entry(stack_aquisition_settings, textvariable=self.stack_aq_plane_spacing_lowres)
        self.stack_aq_plane_spacing_lowres.set(10)
        self.stack_aq_entry_plane_spacing_highres = tk.Entry(stack_aquisition_settings,
                                                     textvariable=self.stack_aq_plane_spacing_highres)
        self.stack_aq_plane_spacing_highres.set(10)

        #run buttons
        self.stack_aq_bt_run_stack = tk.Button(stack_aquisition_settings, text="Acquire Stack")
        self.stack_aq_bt_abort_stack = tk.Button(stack_aquisition_settings, text="Abort Stack")

        #stack aquisition layout (labels positioned above)..............................................................
        self.stack_aq_laserOn488.grid(row =2, column=1)
        self.stack_aq_laserOn552.grid(row=2, column=2)
        self.stack_aq_laserOn594.grid(row=2, column=3)
        self.stack_aq_laserOn640.grid(row=2, column=4)
        self.stack_aq_option_laserCycle.grid(row=3,column =1, columnspan=3,sticky = tk.W + tk.E)

        self.stack_aq_ckb_lowresCamera.grid(row=4, column=1, columnspan=2)
        self.stack_aq_ckb_highresCamera.grid(row=4, column=3, columnspan=2)
        self.stack_aq_displayIm.grid(row=5, column=1, columnspan=4)
        self.stack_aq_entry_numberOfPlanes_lowres.grid(row =6, column=1, columnspan=3, sticky = tk.W + tk.E)
        self.stack_aq_entry_numberOfPlanes_highres.grid(row =7, column=1, columnspan=3, sticky = tk.W + tk.E)
        self.stack_aq_entry_plane_spacing_lowres.grid(row =10, column=1, columnspan=3, sticky = tk.W + tk.E)
        self.stack_aq_entry_plane_spacing_highres.grid(row =11, column=1, columnspan=3, sticky = tk.W + tk.E)
        self.stack_aq_bt_run_stack.grid(row = 15, column =0, columnspan=3, sticky = tk.W + tk.E)
        self.stack_aq_bt_abort_stack.grid(row=15, column=3, columnspan=4, sticky=tk.W + tk.E)

        ### ----------------------------time-lapse acquisition buttons ------------------------------------------------------
        # passive time-lapse aquisition labels (positioned)
        timeinterval_label = ttk.Label(timelapse_acquisition_settings, text="Time interval:").grid(row=2, column=0)
        timepointsnb_label = ttk.Label(timelapse_acquisition_settings, text="Number of timepoints:").grid(row=6, column=0)
        overall_length_label = ttk.Label(timelapse_acquisition_settings, text="Total length:").grid(row=5, column=0)
        start_time = ttk.Label(timelapse_acquisition_settings, text="Start time:").grid(row=12, column=0)
        end_time = ttk.Label(timelapse_acquisition_settings, text="End time:").grid(row=14, column=0)
        interval_min_time = ttk.Label(timelapse_acquisition_settings, text="min").grid(row=2, column=2)
        interval_seconds_time = ttk.Label(timelapse_acquisition_settings, text="seconds").grid(row=2, column=4)
        length_hours_time = ttk.Label(timelapse_acquisition_settings, text="hours").grid(row=5, column=2)
        length_min_time = ttk.Label(timelapse_acquisition_settings, text="min").grid(row=5, column=4)
        length_seconds_time = ttk.Label(timelapse_acquisition_settings, text="seconds").grid(row=5, column=6)

        #active labels
        self.timelapse_aq_lb_NbTimepoints = tk.Label(timelapse_acquisition_settings, text=str(self.timelapse_aq_nbTimepoints))
        self.timelapse_lb_starttime = tk.Label(timelapse_acquisition_settings, text=dt.datetime.now().strftime("%A-%Y-%m-%d %H:%M:%S"))
        self.timelapse_lb_endtime = tk.Label(timelapse_acquisition_settings, text=dt.datetime.now().strftime("%A-%Y-%m-%d %H:%M:%S"))

        # time-lapse aquisition settings
        self.timelapse_delta_entry_minute = tk.Entry(timelapse_acquisition_settings, textvariable=self.timelapse_aq_timeinterval_min, width=5)
        self.timelapse_delta_entry_seconds = tk.Entry(timelapse_acquisition_settings, textvariable=self.timelapse_aq_timeinterval_seconds, width=5)
        self.timelapse_length_entry_hours = tk.Entry(timelapse_acquisition_settings, textvariable=self.timelapse_aq_length_hours, width=5)
        self.timelapse_length_entry_minutes = tk.Entry(timelapse_acquisition_settings, textvariable=self.timelapse_aq_length_min, width=5)
        self.timelapse_length_entry_seconds = tk.Entry(timelapse_acquisition_settings, textvariable=self.timelapse_aq_length_seconds, width=5)

        self.timelapse_aq_timeinterval_min.trace("w", lambda name, index, mode, var = self.timelapse_aq_timeinterval_min: self.updateTimesTimelapse())
        self.timelapse_aq_timeinterval_seconds.trace("w", lambda name, index, mode, var = self.timelapse_aq_timeinterval_seconds: self.updateTimesTimelapse())
        self.timelapse_aq_length_hours.trace("w", lambda name, index, mode, var = self.timelapse_aq_length_hours: self.updateTimesTimelapse())
        self.timelapse_aq_length_min.trace("w", lambda name, index, mode, var = self.timelapse_aq_length_min: self.updateTimesTimelapse())
        self.timelapse_aq_length_seconds.trace("w", lambda name, index, mode, var = self.timelapse_aq_length_seconds: self.updateTimesTimelapse())


        self.timelapse_aq_bt_run_timelapse = tk.Button(timelapse_acquisition_settings, text="Run Timelapse")
        self.timelapse_aq_bt_abort_timelapse = tk.Button(timelapse_acquisition_settings, text="Abort Timelapse")


        # time-lapse aquisition layout (labels positioned above)
        self.timelapse_delta_entry_minute.grid(row=2, column=1,columnspan=1,sticky = tk.W + tk.E)
        self.timelapse_delta_entry_seconds.grid(row=2, column=3,columnspan=1, ipadx=5,sticky = tk.W + tk.E)
        self.timelapse_length_entry_hours.grid(row=5, column=1,columnspan=1, ipadx=5,sticky = tk.W + tk.E)
        self.timelapse_length_entry_minutes.grid(row=5, column=3,columnspan=1, ipadx=5,sticky = tk.W + tk.E)
        self.timelapse_length_entry_seconds.grid(row=5, column=5,columnspan=1, ipadx=5,sticky = tk.W + tk.E)
        self.timelapse_aq_lb_NbTimepoints.grid(row=6,column=1)
        self.timelapse_lb_starttime.grid(row=12, column=1,columnspan=3,sticky = tk.W)
        self.timelapse_lb_endtime.grid(row=14, column=1,columnspan=3,sticky = tk.W)
        self.timelapse_aq_bt_run_timelapse.grid(row=15, column=0, columnspan=2, sticky=tk.W + tk.E)
        self.timelapse_aq_bt_abort_timelapse.grid(row=15, column=2, columnspan=3, sticky=tk.W + tk.E)

        ### ----------------------------roi setting buttons ------------------------------------------------------
        # roi settings label
        roi_typelabel = ttk.Label(roi_settings, text="Roi type:").grid(row=2, column=0)
        roi_xstartlabel = ttk.Label(roi_settings, text="x start:").grid(row=6, column=0)
        roi_ystartlabel = ttk.Label(roi_settings, text="y start").grid(row=7, column=0)
        roi_widthlabel = ttk.Label(roi_settings, text="width").grid(row=8, column=0)
        roi_heightlabel = ttk.Label(roi_settings, text="height").grid(row=9, column=0)
        roi_reslabel = ttk.Label(roi_settings, text="Resolution").grid(row=4, column=5)

        # roi setting entries
        self.roi_xstartEntry = tk.Entry(roi_settings, textvariable=self.roi_startX, width=5)
        self.roi_ystartEntry = tk.Entry(roi_settings, textvariable=self.roi_startY, width=5)
        self.roi_widthEntry = tk.Entry(roi_settings, textvariable=self.roi_width, width=5)
        self.roi_heightEntry = tk.Entry(roi_settings, textvariable=self.roi_height, width=5)

        self.roi_startX.set(0)
        self.roi_startY.set(0)
        self.roi_width.set(5056)
        self.roi_height.set(2960)

        #roi types
        roiTypes = ('Full Chip', '1024x1024', '512x512', '256x256', 'Custom')
        self.roi_option_type = tk.OptionMenu(roi_settings, self.roi_ac_settings_type,
                                                        *roiTypes)
        self.roi_ac_settings_type.set(roiTypes[0])

        #low or high res roi
        self.roi_whichresolution = tk.StringVar(value="on")
        self.roi_low_on = tk.Radiobutton(roi_settings, text="Low", value="on",
                                                          variable=self.roi_whichresolution,
                                                          indicatoron=False)
        self.roi_low_off = tk.Radiobutton(roi_settings, text="High", value="off",
                                                           variable=self.roi_whichresolution,
                                                           indicatoron=False)

        self.roi_applybutton = tk.Button(roi_settings, text="Apply ROI")


        self.roi_option_type.grid(row=2,column =1, columnspan=5,sticky = tk.W + tk.E)
        self.roi_low_on.grid(row=4, column=0, columnspan=2, sticky=tk.W + tk.E)
        self.roi_low_off.grid(row=4, column=2, columnspan=2, sticky=tk.W + tk.E)
        self.roi_xstartEntry.grid(row=6, column=2,columnspan=1,sticky = tk.W + tk.E)
        self.roi_ystartEntry.grid(row=7, column=2,columnspan=1,sticky = tk.W + tk.E)
        self.roi_widthEntry.grid(row=8, column=2,columnspan=1,sticky = tk.W + tk.E)
        self.roi_heightEntry.grid(row=9, column=2,columnspan=1,sticky = tk.W + tk.E)
        self.roi_applybutton.grid(row=2, column=6,columnspan=1,sticky = tk.W + tk.E)

        ### ----------------------------progress display settings ------------------------------------------------------
        stackprogress_label = ttk.Label(statusprogress_settings, text="Stack progress:").grid(row=1, column=0)
        self.stack_aq_progressbar = ttk.Progressbar(statusprogress_settings, variable=self.stack_aq_progress,
                                                        maximum=self.stack_aq_numberOfPlanes_lowres.get())
        self.stack_aq_progressbar.grid(row=1, column=2, sticky=tk.E)
        self.stack_aq_progressindicator.config(text="0 of " + str(self.stack_aq_numberOfPlanes_lowres.get()))
        self.stack_aq_progressindicator.grid(row=1, column=4, sticky=tk.E)

        timelapseprogress_label = ttk.Label(statusprogress_settings, text="Timelapse progress:").grid(row=2, column=0)
        self.timelapse_aq_progressbar = ttk.Progressbar(statusprogress_settings, variable=self.timelapse_aq_progress, maximum=self.timelapse_aq_nbTimepoints)
        self.timelapse_aq_progressbar.grid(row=2, column=2, sticky=tk.E)
        self.timelapse_aq_progressindicator.config(text="0 of " + str(self.timelapse_aq_nbTimepoints))
        self.timelapse_aq_progressindicator.grid(row=2, column=4, sticky=tk.E)


#-------button press functions---------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------

    def preview_change(self, button):
        if (button.cget('relief') == "sunken"):
            button.config(relief="raised")
        else:
            button.config(relief="sunken")

    def preview_filter_select(self, button):
        self.bt_changeTo488.config(relief="raised")
        self.bt_changeTo552.config(relief="raised")
        self.bt_changeTo594.config(relief="raised")
        self.bt_changeTo640.config(relief="raised")
        self.bt_changeTo_block.config(relief="raised")
        self.bt_changeTo_trans.config(relief="raised")
        button.config(relief="sunken")

    def sunk_timelapseButton(self, event):
        print("sink timelapse button")
        self.bt_run_timelapse.config(relief="sunken")
        self.update()


    def updateTimesTimelapse(self):
        now = dt.datetime.now()
        nowtime = now.strftime("%A-%Y-%m-%d %H:%M:%S")
        self.timelapse_lb_starttime.config(text=nowtime)

        #capture some exceptions - like entering no valid number (maybe not best way)
        try:
            timeinterval_min = self.timelapse_aq_timeinterval_min.get()
        except:
            timeinterval_min = 0
        try:
            timeinterval_seconds = self.timelapse_aq_timeinterval_seconds.get()
        except:
            timeinterval_seconds = 0
        try:
            timelapse_hours = self.timelapse_aq_length_hours.get()
        except:
            timelapse_hours = 0
        try:
            timelapse_min = self.timelapse_aq_length_min.get()
        except:
            timelapse_min = 0
        try:
            timelapse_sec = self.timelapse_aq_length_seconds.get()
        except:
            timelapse_sec = 0

        timeinterval_in_seconds = (60*timeinterval_min + timeinterval_seconds)
        totallength_in_seconds =  (60*60*timelapse_hours + 60*timelapse_min + timelapse_sec)

        if timeinterval_in_seconds==0:
            self.timelapse_lb_endtime.config(text="invalid time interval zero")
            return

        self.timelapse_aq_nbTimepoints = math.floor(totallength_in_seconds/timeinterval_in_seconds)

        #set right number of timepoints
        self.timelapse_aq_lb_NbTimepoints.config(text=str(self.timelapse_aq_nbTimepoints))

        #calculate end time
        try:
            endtime = now + dt.timedelta(0, totallength_in_seconds)
        except:
            endtime = now #catch exception if all entries are deleted

        end = endtime.strftime("%A-%Y-%m-%d %H:%M:%S")
        self.timelapse_lb_endtime.config(text=end)

        try:
            outOftext = "0 of " + str(self.timelapse_aq_nbTimepoints)
        except:
            outOftext = "0 of 0"

        self.timelapse_aq_progressindicator.config(text=outOftext)


#---------------------------------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------
