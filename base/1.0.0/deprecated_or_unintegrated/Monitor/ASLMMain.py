"""
    UUTrack.View.Monitor.ASLMMain.py
    ========================================

    .. sectionauthor:: Aquiles Carattino <aquiles@aquicarattino.com>
    .. sectionauthor:: Sanli Faez <s.faez@uu.nl>
    .. sectionauthor:: Kevin Namink <k.w.namink@uu.nl>

    NOTES: -trajectoryWidget is used to plot the intensity of a clicked spot.
    -clicked spot 
"""
# Standard Imports
import os
import sys
import time
from datetime import datetime
from multiprocessing import Process, Queue

# Third Party Imports
#import h5py
import numpy as np
# import psutil
# from PyQt4.Qt import QApplication
# from pyqtgraph import ProgressDialog
# from pyqtgraph.Qt import QtGui, QtCore
# from pyqtgraph.dockarea import *

# Local Imports
# from UUTrack.Model._session import _session
# from UUTrack.View.hdfloader import HDFLoader
# from .ASLMMainWidget import ASLMMainWidget
# from .waterfallWidget import waterfallWidget
# from .cameraViewer import cameraViewer
# from .contrastViewer import contrastWindow
# from .clearQueueThread import clearQueueThread
# from .configWidget import configWidget
# from .crossCut import crossCutWindow
# from .specleWidget import SpecleWindow
# from .popOut import popOutWindow
# from .messageWidget import messageWidget
# from .workerThread import workThread
# from .trajectoryWidget import trajectoryWidget
# from UUTrack.Model.workerSaver import workerSaver, clearQueue
# from . import resources


class ASLMMain():
    """
    Main control window for showing the live captured images and initiating special tasks
    """

    def __init__(self, session, cam):
        """
        Inits the camera window 

        :param: session: session
        :param: cam: camera
        """
        super(ASLMMain, self).__init__()
        # self.setWindowTitle('Camera GUI')
        # self.setMouseTracking(True)
        self._session = session

        self.camera = cam
        # Queue of images. multiprocessing takes care of handling the data in and out
        # and the sharing between parent and child processes.
        self.q = Queue(0)

        # self.area = DockArea()
        # self.setCentralWidget(self.area)
        # self.resize(1064, 840)
        # self.area.setMouseTracking(True)

        # Program variables
        self.tempimage = []
        self.overlayimage = []
        self.bgimage = []
        self.vararray = np.array([], dtype=np.float64)
        self.vararray_length = 20
        self.vararray_location = 0
        self.trackinfo = np.zeros((1, 5))  # real particle trajectory filled by "LocateParticle" analysis
        self.spot_intensity = np.zeros(100)
        self.spot_tracking = False
        self.spot_coords = [0, 0]
        self.fps = 0
        self.realfps = 0
        self.buffertime = 0
        self.buffertimes = []
        self.refreshtimes = []
        self.totalframes = 0
        self.droppedframes = 0
        self.buffer_memory = 0
        self.waterfall_data = []
        self.watindex = 0  # Waterfall index
        self.corner_roi = []  # Real coordinates of the corner of the ROI region. (Min_x and Min_y).
        self.docks = []
        self.corner_roi.append(self._session.Camera['roi_x1'])
        self.corner_roi.append(self._session.Camera['roi_y1'])

        # Program status controllers
        self.continuous_saving = False
        self.show_waterfall = False
        self.subtract_background = False
        self.view_variance = False
        self.save_running = False
        self.accumulate_buffer = False
        self.dock_state = None

        # # Main widget
        # self.camWidget = ASLMMainWidget()
        # self.camWidget.setup_cross_cut(self.camera.maxHeight)
        # self.camWidget.setup_cross_hair([self.camera.maxWidth, self.camera.maxHeight])
        # self.camWidget.setup_roi_lines([self.camera.maxWidth, self.camera.maxHeight])
        # self.camWidget.setup_mouse_tracking()
        #
        # # Widget for displaying information to the user
        # self.messageWidget = messageWidget()
        # self.cheatSheet = popOutWindow()
        # # Small window to display the results of the special task
        # self.trajectoryWidget = trajectoryWidget()
        # # Window for the camera viewer
        # self.camViewer = cameraViewer(self._session, self.camera, parent=self)
        # # Configuration widget with a parameter tree
        # self.config = configWidget(self._session)
        # # Line cut widget
        # self.crossCut = crossCutWindow(parent=self)
        # # Line cut widget
        # self.specleWidget = SpecleWindow(parent=self)
        # # Line cut widget
        # self.contrastViewer = contrastWindow(parent=self)
        # # _future: for making long message pop-ups
        # self.popOut = popOutWindow(parent=self)
        # # Select settings Window
        # self.selectSettings = HDFLoader()
        #
        # self.refreshTimer = QtCore.QTimer()
        # self.connect(self.refreshTimer, QtCore.SIGNAL('timeout()'), self.updateGUI)
        # self.connect(self.refreshTimer, QtCore.SIGNAL('timeout()'), self.crossCut.update)
        # self.connect(self.refreshTimer, QtCore.SIGNAL('timeout()'), self.specleWidget.update)
        #
        # self.refreshTimer.start(self._session.GUI['refresh_time'])

        self.acquiring = False
        self.logmessage = []

        ''' Initialize the camera and the camera related things '''
        self.max_sizex = self.camera.get_CCD_width()
        self.max_sizey = self.camera.get_CCD_height()
        self.current_width = self.max_sizex
        self.current_height = self.max_sizey

        if self._session.Camera['roi_x1'] == 0:
            self._session.Camera = {'roi_x1': 1}
        if self._session.Camera['roi_x2'] == 0 or self._session.Camera['roi_x2'] > self.max_sizex:
            self._session.Camera = {'roi_x2': self.max_sizex}
        if self._session.Camera['roi_y1'] == 0:
            self._session.Camera = {'roi_y1': 1}
        if self._session.Camera['roi_y2'] == 0 or self._session.Camera['roi_y2'] > self.max_sizey:
            self._session.Camera = {'roi_y2': self.max_sizey}

        self.config.populateTree(self._session)
        self.lastBuffer = time.time()
        self.lastRefresh = time.time()
        #
        # self.setupActions()
        # self.setupToolbar()
        # self.setupMenubar()
        # self.setupDocks()
        # self.setupSignals()

        # ### This block should erased in due time and one must rely exclusively on Session variables.
        # self.filedir = self._session.Saving['directory']
        # self.snap_filename = self._session.Saving['filename_photo']
        # self.movie_filename = self._session.Saving['filename_video']
        # ###
        # self.messageWidget.appendLog('i', 'Program started by %s' % self._session.User['name'])

    def showHelp(self):
        """To show the cheatsheet for shortcuts in a pop-up meassage box
        OBSOLETE, will be deleted after transferring info into a better message viewer!
        """
        msgBox = QtGui.QMessageBox()
        msgBox.setIcon(QtGui.QMessageBox.Information)
        msgBox.setText("Keyboard shortcuts and Hotkeys")
        msgBox.setInformativeText("Press details for a full list")
        msgBox.setWindowTitle("UUTrack CheatSheet")
        msgBox.setDetailedText("""
            F1, Show cheatsheet\n
            F5, Snap image\n
            F6, Continuous run\n
            Alt+mouse: Select line \n
            Ctrl+mouse: Crosshair \n
            Ctrl+B: Toggle buffering\n
            Ctrl+G: Toggle background subtraction\n
            Ctrl+H: Toggle variance view\n
            Ctrl+F: Empty buffer\n
            Ctrl+C: Start tracking\n
            Ctrl+V: Stop tracking\n
            Ctrl+M: Autosave on\n
            Ctrl+N: Autosave off\n
            Ctrl+S: Save image\n
            Ctrl+W: Start waterfall\n
            Ctrl+X: Show speckle contrast\n
            Ctrl+Q: Exit application\n
            Ctrl+Shift+W: Save waterfall data\n
            Ctrl+Shift+T: Save trajectory\n
            """)
        msgBox.setStandardButtons(QtGui.QMessageBox.Close)
        retval = msgBox.exec_()

    def setupActions(self):
        """Setups the actions that the program will have. It is placed into a function
        to make it easier to reuse in other windows.

        :rtype: None
        """
        self.exitAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/power-icon.png'), '&Exit', self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.setStatusTip('Exit application')
        self.exitAction.triggered.connect(self.exitSafe)

        self.saveAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/floppy-icon.png'), '&Save image', self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.setStatusTip('Save Image')
        self.saveAction.triggered.connect(self.saveImage)

        self.showHelpAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/info-icon.png'), 'Show cheatsheet',
                                            self)
        self.showHelpAction.setShortcut(QtCore.Qt.Key_F1)
        self.showHelpAction.setStatusTip('Show Cheatsheet')
        self.showHelpAction.triggered.connect(self.cheatSheet.show)

        self.saveWaterfallAction = QtGui.QAction("Save Waterfall", self)
        self.saveWaterfallAction.setShortcut('Ctrl+Shift+W')
        self.saveWaterfallAction.setStatusTip('Save waterfall data to new file')
        self.saveWaterfallAction.triggered.connect(self.saveWaterfall)

        self.saveTrajectoryAction = QtGui.QAction("Save Trajectory", self)
        self.saveTrajectoryAction.setShortcut('Ctrl+Shift+T')
        self.saveTrajectoryAction.setStatusTip('Save trajectory data to new file')
        self.saveTrajectoryAction.triggered.connect(self.saveTrajectory)

        self.snapAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/snap.png'), 'S&nap photo', self)
        self.snapAction.setShortcut(QtCore.Qt.Key_F5)
        self.snapAction.setStatusTip('Snap Image')
        self.snapAction.triggered.connect(self.snap)

        self.movieAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/video-icon.png'), 'Start &movie', self)
        self.movieAction.setShortcut(QtCore.Qt.Key_F6)
        self.movieAction.setStatusTip('Start Movie')
        self.movieAction.triggered.connect(self.startMovie)

        self.movieSaveStartAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Download-Database-icon.png'),
                                                  'Continuous saves', self)
        self.movieSaveStartAction.setShortcut('Ctrl+M')
        self.movieSaveStartAction.setStatusTip('Continuous save to disk')
        self.movieSaveStartAction.triggered.connect(self.movieSave)

        self.movieSaveStopAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Delete-Database-icon.png'),
                                                 'Stop continuous saves', self)
        self.movieSaveStopAction.setShortcut('Ctrl+N')
        self.movieSaveStopAction.setStatusTip('Stop continuous save to disk')
        self.movieSaveStopAction.triggered.connect(self.movieSaveStop)

        self.startWaterfallAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Blue-Waterfall-icon.png'),
                                                  'Start &Waterfall', self)
        self.startWaterfallAction.setShortcut('Ctrl+W')
        self.startWaterfallAction.setStatusTip('Start Waterfall')
        self.startWaterfallAction.triggered.connect(self.startWaterfall)

        self.startContrastAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Specl.png'),
                                                 'Spec&kle Contrast', self)
        self.startContrastAction.setShortcut('Ctrl+X')
        self.startContrastAction.setStatusTip('Show Speckle Contrast')
        self.startContrastAction.triggered.connect(self.specleWidget.show)

        self.toggleBGAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/noBg.png'), 'Toggle B&G-reduction',
                                            self)
        self.toggleBGAction.setShortcut('Ctrl+G')
        self.toggleBGAction.setStatusTip('Toggle Background Reduction')
        self.toggleBGAction.triggered.connect(self.toggleBGReduction)

        self.toggleBGModeAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/BGmode.png'),
                                                'Toggle B&G-reduction mode', self)
        self.toggleBGModeAction.setShortcut('Ctrl+G')
        self.toggleBGModeAction.setStatusTip('Toggle Background Reduction Mode')
        self.toggleBGModeAction.triggered.connect(self.toggleBGMode)

        self.toggleVarViewAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/varV.png'),
                                                 'Toggle Variance View', self)
        self.toggleVarViewAction.setShortcut('Ctrl+G')
        self.toggleVarViewAction.setStatusTip('Toggle viewing variance')
        self.toggleVarViewAction.triggered.connect(self.toggleVarView)

        self.setROIAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Zoom-In-icon.png'), 'Set &ROI', self)
        self.setROIAction.setShortcut('Ctrl+T')
        self.setROIAction.setStatusTip('Set ROI')
        self.setROIAction.triggered.connect(self.getROI)

        self.clearROIAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Zoom-Out-icon.png'), 'Set R&OI',
                                            self)
        self.clearROIAction.setShortcut('Ctrl+T')
        self.clearROIAction.setStatusTip('Clear ROI')
        self.clearROIAction.triggered.connect(self.clearROI)

        self.accumulateBufferAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/disk-save.png'),
                                                    'Accumulate buffer', self)
        self.accumulateBufferAction.setShortcut('Ctrl+B')
        self.accumulateBufferAction.setStatusTip('Start or stop buffer accumulation')
        self.accumulateBufferAction.triggered.connect(self.bufferStatus)

        self.clearBufferAction = QtGui.QAction('Clear Buffer', self)
        self.clearBufferAction.setShortcut('Ctrl+F')
        self.clearBufferAction.setStatusTip('Clears the buffer')
        self.clearBufferAction.triggered.connect(self.emptyQueue)

        self.viewerAction = QtGui.QAction('Start Viewer', self)
        self.viewerAction.triggered.connect(self.camViewer.show)

        self.configAction = QtGui.QAction('Config Window', self)
        self.configAction.triggered.connect(self.config.show)

        self.dockAction = QtGui.QAction('Restore Docks', self)
        self.dockAction.triggered.connect(self.setupDocks)

        self.crossCutAction = QtGui.QAction(QtGui.QIcon('UUTrack/View/Monitor/Icons/Ruler-icon.png'), 'Show cross cut',
                                            self)
        self.crossCutAction.triggered.connect(self.crossCut.show)

        self.settingsAction = QtGui.QAction('Load config', self)
        self.settingsAction.triggered.connect(self.selectSettings.show)

    def setupToolbar(self):
        """Setups the toolbar with the desired icons. It's placed into a function
        to make it easier to reuse in other windows.
        """
        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(self.exitAction)
        self.toolbar2 = self.addToolBar('Image')
        self.toolbar2.addAction(self.saveAction)
        self.toolbar2.addAction(self.snapAction)
        self.toolbar2.addAction(self.crossCutAction)
        self.toolbar3 = self.addToolBar('Movie')
        self.toolbar3.addAction(self.movieAction)
        self.toolbar3.addAction(self.movieSaveStartAction)
        self.toolbar3.addAction(self.movieSaveStopAction)
        self.toolbar4 = self.addToolBar('Extra')
        self.toolbar4.addAction(self.startWaterfallAction)
        self.toolbar4.addAction(self.startContrastAction)
        self.toolbar4.addAction(self.setROIAction)
        self.toolbar4.addAction(self.clearROIAction)
        self.toolbar4.addAction(self.clearROIAction)
        self.toolbar4.addAction(self.toggleBGAction)
        self.toolbar4.addAction(self.toggleBGModeAction)
        self.toolbar4.addAction(self.toggleVarViewAction)
        self.toolbar5 = self.addToolBar('Help')
        self.toolbar5.addAction(self.showHelpAction)

    def setupMenubar(self):
        """Setups the menubar.
        """
        menubar = self.menuBar()
        self.fileMenu = menubar.addMenu('&File')
        self.fileMenu.addAction(self.settingsAction)
        self.fileMenu.addAction(self.saveAction)
        self.fileMenu.addAction(self.exitAction)
        self.snapMenu = menubar.addMenu('&Snap')
        self.snapMenu.addAction(self.snapAction)
        self.snapMenu.addAction(self.saveAction)
        self.movieMenu = menubar.addMenu('&Movie')
        self.movieMenu.addAction(self.movieAction)
        self.movieMenu.addAction(self.movieSaveStartAction)
        self.movieMenu.addAction(self.movieSaveStopAction)
        self.movieMenu.addAction(self.startWaterfallAction)
        self.movieMenu.addAction(self.startContrastAction)
        self.configMenu = menubar.addMenu('&Configure')
        self.configMenu.addAction(self.toggleBGAction)
        self.configMenu.addAction(self.toggleBGModeAction)
        self.configMenu.addAction(self.toggleVarViewAction)
        self.configMenu.addAction(self.setROIAction)
        self.configMenu.addAction(self.clearROIAction)
        self.configMenu.addAction(self.accumulateBufferAction)
        self.configMenu.addAction(self.clearBufferAction)
        self.configMenu.addAction(self.viewerAction)
        self.configMenu.addAction(self.configAction)
        self.configMenu.addAction(self.dockAction)
        self.saveMenu = menubar.addMenu('S&ave')
        self.snapMenu.addAction(self.saveAction)
        self.saveMenu.addAction(self.saveWaterfallAction)
        self.saveMenu.addAction(self.saveTrajectoryAction)
        self.helpMenu = menubar.addMenu('&Help')
        self.helpMenu.addAction(self.showHelpAction)

    def setupDocks(self):
        """Setups the docks in order to recover the initial configuration if one gets closed."""

        for d in self.docks:
            try:
                d.close()
            except:
                pass

        self.docks = []

        self.dmainImage = Dock("Camera", size=(80, 35))  # sizes are in percentage
        self.dwaterfall = Dock("Waterfall", size=(80, 35))
        self.dparams = Dock("Parameters", size=(20, 100))
        self.dtraj = Dock("Trajectory", size=(40, 30))
        self.dmessage = Dock("Messages", size=(40, 30))
        # self.dstatus = Dock("Status", size=(100, 3))

        self.area.addDock(self.dmainImage, 'right')
        self.area.addDock(self.dparams, 'left', self.dmainImage)
        self.area.addDock(self.dtraj, 'bottom', self.dmainImage)
        self.area.addDock(self.dmessage, 'right', self.dtraj)

        self.docks.append(self.dmainImage)
        self.docks.append(self.dtraj)
        self.docks.append(self.dmessage)
        self.docks.append(self.dparams)
        self.docks.append(self.dwaterfall)
        # self.area.addDock(self.dstatus, 'bottom', self.dparams)

        self.dmainImage.addWidget(self.camWidget)
        self.dmessage.addWidget(self.messageWidget)
        self.dparams.addWidget(self.config)
        self.dtraj.addWidget(self.trajectoryWidget)

        self.dock_state = self.area.saveState()

    def setupSignals(self):
        """Setups all the signals that are going to be handled during the excution of the program."""
        self.connect(self._session, QtCore.SIGNAL('updated'), self.config.populateTree)
        self.connect(self.config, QtCore.SIGNAL('updateSession'), self.updateSession)
        self.connect(self.camWidget, QtCore.SIGNAL('specialTask'), self.startSpecialTask)
        self.connect(self.camWidget, QtCore.SIGNAL('stopSpecialTask'), self.stopSpecialTask)
        self.connect(self.camViewer, QtCore.SIGNAL('stopMainAcquisition'), self.stopMovie)
        self.connect(self, QtCore.SIGNAL('stopChildMovie'), self.camViewer.stopCamera)
        self.connect(self, QtCore.SIGNAL('closeAll'), self.camViewer.closeViewer)
        self.connect(self.selectSettings, QtCore.SIGNAL("settings"), self.update_settings)
        self.connect(self, QtCore.SIGNAL('closeAll'), self.selectSettings.close)

    def snap(self):
        """Function for acquiring a single frame from the camera. It is triggered by the user.
        It gets the data the GUI will be updated at a fixed framerate.
        """
        if self.acquiring:  # If it is itself acquiring a message is displayed to the user warning him
            msgBox = QtGui.QMessageBox()
            msgBox.setIcon(QtGui.QMessageBox.Critical)
            msgBox.setText("You cant snap a photo while in free run")
            msgBox.setInformativeText("The program is already acquiring data")
            msgBox.setWindowTitle("Already acquiring")
            msgBox.setDetailedText("""When in free run, you can\'t trigger another acquisition. \n
                You should stop the free run acquisition and then snap a photo.""")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
            retval = msgBox.exec_()
            self.messageWidget.appendLog('e', 'Tried to snap while in free run')
        else:
            self.workerThread = workThread(self._session, self.camera)
            self.connect(self.workerThread, QtCore.SIGNAL('image'), self.getData)
            self.workerThread.origin = 'snap'
            self.workerThread.start()
            self.acquiring = True
            self.messageWidget.appendLog('i', 'Snapped photo')

    def toggleBGReduction(self):
        """Toggles between background cancellation on and off. Takes a background snap if necessary
        """

        if self.subtract_background:
            self.subtract_background = False
            self.messageWidget.appendLog('i', 'Background reduction deactivated')
        else:
            if self.view_variance:
                self.messageWidget.appendLog('i', 'Cannot start BG-reduction while variance view is active')
                return
            if len(self.tempimage) == 0:
                self.snap()
                self.messageWidget.appendLog('i', 'Snapped an image as background')
            else:
                self.subtract_background = True
                self.bgimage = self.tempimage.astype(float)
                self.messageWidget.appendLog('i', 'Background reduction active')

    def toggleBGMode(self):
        """Toggles between background cancellation modes.
        """
        print("Not implemented yet: toggleBGMode")

    def toggleVarView(self):
        """Toggles showing variance.
        """

        if self.view_variance:
            self.view_variance = False
            self.messageWidget.appendLog('i', 'Variance view deactivated')
            self.vararray = np.array([])
        else:
            if self.subtract_background:
                self.messageWidget.appendLog('i', 'Cannot start variance view while BG-reduction is active')
                return
            elif len(self.vararray) == 0:
                x, y = self.tempimage.shape
                for i in range(self.vararray_length):
                    self.vararray = np.append(self.vararray, np.zeros((x, y)))
                self.vararray = np.reshape(self.vararray, (self.vararray_length, x, y))
                self.messageWidget.appendLog('i', 'Initialized variance view array')
            self.view_variance = True
            self.messageWidget.appendLog('i', 'Variance view active')

    def saveImage(self):
        """Saves the image that is being displayed to the user.
        """
        if len(self.tempimage) >= 1:
            # Data will be appended to existing file
            fn = self._session.Saving['filename_photo']
            filename = '%s.hdf5' % (fn)
            fileDir = self._session.Saving['directory']
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)

            f = h5py.File(os.path.join(fileDir, filename), "a")
            now = str(datetime.now())
            g = f.create_group(now)
            dset = g.create_dataset('image', data=self.tempimage)
            meta = g.create_dataset('metadata', data=self._session.serialize())
            f.flush()
            f.close()
            self.messageWidget.appendLog('i', 'Saved photo')

    def startMovie(self):
        if self._session.Debug['to_screen']:
            print('Start Movie')
        else:
            if self.acquiring:
                self.stopMovie()
            else:
                self.emit(QtCore.SIGNAL('stopChildMovie'))
                self.messageWidget.appendLog('i', 'Continuous run started')
                # Worker thread to acquire images. Specially useful for long exposure time images
                self.workerThread = workThread(self._session, self.camera)
                self.connect(self.workerThread, QtCore.SIGNAL('image'), self.getData)
                self.connect(self.workerThread, QtCore.SIGNAL('finished()'), self.done)
                self.workerThread.start()
                self.acquiring = True

    def stopMovie(self):
        if self.acquiring:
            self.workerThread.keep_acquiring = False
            while self.workerThread.isRunning():
                pass
            self.acquiring = False
            self.camera.stopAcq()
            self.messageWidget.appendLog('i', 'Continuous run stopped')
            if self.continuous_saving:
                self.movieSaveStop()

    def movieData(self):
        """Function just to trigger and read the camera in the separate thread.
        """
        self.workerThread.start()

    def movieSave(self):
        """Saves the data accumulated in the queue continuously.
        """
        if not self.continuous_saving:
            # Child process to save the data. It runs continuously until and exit flag
            # is passed through the Queue. (self.q.put('exit'))
            self.accumulate_buffer = True
            if len(self.tempimage) > 1:
                im_size = self.tempimage.nbytes
                max_element = int(self._session.Saving['max_memory'] / im_size)
                # self.q = Queue(0)
            fn = self._session.Saving['filename_video']
            filename = '%s.hdf5' % (fn)
            fileDir = self._session.Saving['directory']
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)
            to_save = os.path.join(fileDir, filename)
            metaData = self._session.serialize()  # This prints a YAML-ready version of the session.
            self.p = Process(target=workerSaver, args=(to_save, metaData, self.q,))  #
            self.p.start()
            self.continuous_saving = True
            self.messageWidget.appendLog('i', 'Continuous autosaving started')
        else:
            self.messageWidget.appendLog('w', 'Continuous savings already triggered')

    def movieSaveStop(self):
        """Stops the saving to disk. It will however flush the queue.
        """
        if self.continuous_saving:
            self.q.put('Stop')
            self.accumulate_buffer = False
            # self.p.join()
            self.messageWidget.appendLog('i', 'Continuous autosaving stopped')
            self.continuous_saving = False

    def emptyQueue(self):
        """Clears the queue.
        """
        # Worker thread for clearing the queue.
        self.clearWorker = Process(target=clearQueue, args=(self.q,))
        self.clearWorker.start()

    def startWaterfall(self):
        """Starts the waterfall. The waterfall can be accelerated if camera supports hardware binning in the appropriate
        direction. If not, has to be done via software but the acquisition time cannot be improved.
        TODO: Fast waterfall should have separate window, since the acquisition of the full CCD will be stopped.
        """
        if not self.show_waterfall:
            self.watWidget = waterfallWidget()
            self.area.addDock(self.dwaterfall, 'bottom', self.dmainImage)
            self.dwaterfall.addWidget(self.watWidget)
            self.show_waterfall = True
            Sx, Sy = self.camera.getSize()
            self.waterfall_data = np.zeros((self._session.GUI['length_waterfall'], Sx))
            self.watWidget.img.setImage(np.transpose(self.waterfall_data), autoLevels=False, autoRange=False,
                                        autoHistogramRange=False)
            self.messageWidget.appendLog('i', 'Waterfall opened')
        else:
            self.closeWaterfall()

    def stopWaterfall(self):
        """Stops the acquisition of the waterfall.
        """
        pass

    def closeWaterfall(self):
        """Closes the waterfall widget.
        """
        if self.show_waterfall:
            self.watWidget.close()
            self.dwaterfall.close()
            self.show_waterfall = False
            del self.waterfall_data
            self.messageWidget.appendLog('i', 'Waterfall closed')

    def setROI(self, X, Y):
        """
        Gets the ROI from the lines on the image. It also updates the GUI to accommodate the changes.
        :param X:
        :param Y:
        :return:
        """
        if not self.acquiring:
            self.corner_roi[0] = X[0]
            self.corner_roi[1] = Y[0]
            if self._session.Debug['to_screen']:
                print('Corner: %s, %s' % (self.corner_roi[0], self.corner_roi[1]))
            self._session.Camera = {'roi_x1': int(X[0])}
            self._session.Camera = {'roi_x2': int(X[1])}
            self._session.Camera = {'roi_y1': int(Y[0])}
            self._session.Camera = {'roi_y2': int(Y[1])}
            self.messageWidget.appendLog('i', 'Updated roi_x1: %s' % int(X[0]))
            self.messageWidget.appendLog('i', 'Updated roi_x2: %s' % int(X[1]))
            self.messageWidget.appendLog('i', 'Updated roi_y1: %s' % int(Y[0]))
            self.messageWidget.appendLog('i', 'Updated roi_y2: %s' % int(Y[1]))

            Nx, Ny = self.camera.setROI(X, Y)
            Sx, Sy = self.camera.getSize()
            self.current_width = Sx
            self.current_height = Sy

            self.tempimage = np.zeros((Nx, Ny))
            self.camWidget.hline1.setValue(1)
            self.camWidget.hline2.setValue(Ny)
            self.camWidget.vline1.setValue(1)
            self.camWidget.vline2.setValue(Nx)
            self.trackinfo = np.zeros((1, 5))
            self.overlayimage = []
            # self.camWidget.img2.clear()
            if self.show_waterfall:
                self.waterfall_data = np.zeros((self._session.GUI['length_waterfall'], self.current_width))
                self.watWidget.img.setImage(np.transpose(self.waterfall_data))

            self.config.populateTree(self._session)
            self.messageWidget.appendLog('i', 'Updated the ROI')
        else:
            self.messageWidget.appendLog('e', 'Cannot change ROI while acquiring.')

    def getROI(self):
        """Gets the ROI coordinates from the GUI and updates the values."""
        y1 = np.int(self.camWidget.hline1.value())
        y2 = np.int(self.camWidget.hline2.value())
        x1 = np.int(self.camWidget.vline1.value())
        x2 = np.int(self.camWidget.vline2.value())
        X = np.sort((x1, x2))
        Y = np.sort((y1, y2))
        # Updates to the real values
        X += self.corner_roi[0] - 1
        Y += self.corner_roi[1] - 1
        self.setROI(X, Y)

    def clearROI(self):
        """Resets the roi to the full image.
        """
        if not self.acquiring:
            self.camWidget.hline1.setValue(1)
            self.camWidget.vline1.setValue(1)
            self.camWidget.vline2.setValue(self.max_sizex)
            self.camWidget.hline2.setValue(self.max_sizey)
            self.corner_roi = [1, 1]
            self.getROI()
        else:
            self.messageWidget.appendLog('e', 'Cannot change ROI while acquiring.')

    def bufferStatus(self):
        """Starts or stops the buffer accumulation.
        """
        if self.accumulate_buffer:
            self.accumulate_buffer = False
            self.messageWidget.appendLog('i', 'Buffer accumulation stopped')
        else:
            self.accumulate_buffer = True
            self.messageWidget.appendLog('i', 'Buffer accumulation started')

    def getData(self, data, origin):
        """Gets the data that is being gathered by the working thread.

        .. _getData:
        .. data: single image or a list of images (saved in buffer)
        .. origin: indicates which command has trigerred execution of this method (e.g. 'snap' of 'movie')
        both input variables are handed it through QThread signal that is "emit"ted
        """
        s = 0
        if origin == 'snap':  # Single snap.
            self.acquiring = False
            self.workerThread.origin = None
            self.workerThread.keep_acquiring = False  # This already happens in the worker thread itself.
            self.camera.stopAcq()

        if isinstance(data, list):
            for d in data:
                if self.accumulate_buffer:
                    s = float(self.q.qsize()) * int(d.nbytes) / 1024 / 1024
                    if s < self._session.Saving['max_memory']:
                        self.q.put(d)
                    else:
                        self.droppedframes += 1

                if self.show_waterfall:
                    if self.watindex == self._session.GUI['length_waterfall']:
                        if self._session.Saving['autosave_trajectory']:
                            self.saveWaterfall()

                        # self.waterfall_data = np.zeros((self._session.GUI['length_waterfall'], self.current_width))
                        self.watindex = 0

                    centerline = np.int(self.current_height / 2)
                    vbinhalf = np.int(self._session.GUI['vbin_waterfall'])
                    if vbinhalf >= self.current_height / 2 - 1:
                        wf = np.array([np.sum(d, 1)])
                    else:
                        wf = np.array([np.sum(d[:, centerline - vbinhalf:centerline + vbinhalf], 1)])
                    self.waterfall_data[self.watindex, :] = wf
                    self.watindex += 1
                self.totalframes += 1
            self.tempimage = d
        else:
            self.tempimage = data
            if self.accumulate_buffer:
                s = float(self.q.qsize()) * int(data.nbytes) / 1024 / 1024

                if s < self._session.Saving['max_memory']:
                    self.q.put(data)
                else:
                    self.droppedframes += 1

            if self.show_waterfall:
                if self.watindex == self._session.GUI['length_waterfall']:
                    # checks if the buffer variable for waterfall image is full, saves it if requested, and sets it to zero.
                    if self._session.Saving['autosave_trajectory']:
                        self.saveWaterfall()

                    self.waterfall_data = np.zeros((self._session.GUI['length_waterfall'], self.current_width))
                    self.watindex = 0

                centerline = np.int(self.current_height / 2)
                vbinhalf = np.int(self._session.GUI['vbin_waterfall'] / 2)

                if vbinhalf >= self.current_height - 1:
                    wf = np.array([np.sum(data, 1)])
                else:
                    wf = np.array([np.sum(data[:, centerline - vbinhalf:centerline + vbinhalf], 1)])
                self.waterfall_data[self.watindex, :] = wf
                self.watindex += 1

            self.totalframes += 1

        new_time = time.time()
        self.buffertime = new_time - self.lastBuffer
        self.lastBuffer = new_time
        self.buffer_memory = s
        if self._session.Debug['queue_memory']:
            print('Queue Memory: %3.2f MB' % self.buffer_memory)

    def getParticleLocation(self, tracktag):
        """Gets the coordinates emitted by the specialTaskTracking and stores them in an array
        the format of the emitted """
        if tracktag[0, 0] == 0:  # when particle is getting out of range, locator returns a line of zeros
            self.stopSpecialTask()
        else:
            self.trackinfo = np.append(self.trackinfo, tracktag, axis=0)
            # next line checks particle location along fiber axis and call for proper control feedback
            w = self.tempimage.shape[0]
            if tracktag[0, 1] < 50:
                self.messageWidget.appendLog('w', 'Particle approaching left limit')
            elif tracktag[0, 1] > w - 50:
                self.messageWidget.appendLog('w', 'Particle approaching right limit')
            # print(tracktag.astype(int)) #for debugging: prints particle mass and coordinates
            # self.overlayImage = self.camWidget.drawTargetPointer(self.overlayImage,tracktag[0][1:3]) #to overlay track and live image in viewport
            # future: in case of an image series one should plot all the trajectory instead of just one point

    def updateGUI(self):
        """Updates the image displayed to the user.
        """
        if len(self.tempimage) >= 1:
            if (self.subtract_background and len(self.bgimage) >= 1):
                bgcorrected = self.tempimage - self.bgimage + np.full_like(self.bgimage, self.bgimage.max())
                self.camWidget.img.setImage(bgcorrected, autoLevels=False, autoRange=False, autoHistogramRange=False)
            elif (self.view_variance):
                self.vararray[self.vararray_location] = self.tempimage.astype(
                    np.float64) - 96  # Substract 96 to counteract dark noise
                self.vararray_location += 1
                if self.vararray_location == self.vararray_length:
                    self.vararray_location = 0
                with np.errstate(divide='ignore'):
                    varview = np.var(self.vararray, axis=0) / np.mean(self.vararray, axis=0)
                self.camWidget.img.setImage(varview, autoLevels=False, autoRange=False, autoHistogramRange=False)
            else:
                self.camWidget.img.setImage(self.tempimage, autoLevels=False, autoRange=False, autoHistogramRange=False)
            if self.spot_tracking:
                self.spot_intensity[0:-1] = self.spot_intensity[1:]
                self.spot_coords = [self.camWidget.crosshair[0].getPos()[1], self.camWidget.crosshair[1].getPos()[0]]
                self.spot_intensity[-1] = self.tempimage[self.spot_coords[0], self.spot_coords[1]]
                self.trajectoryWidget.plot.setData(np.arange(-len(self.spot_intensity), 0), self.spot_intensity)
            self.buffer_memory = float(self.q.qsize()) * int(self.tempimage.nbytes) / 1024 / 1024
        # if self.trackinfo.shape[0] > 1:
        # self.camWidget.img2.setImage(self.overlayImage) #plotting the particle past trajectory on top of the camera frames
        # self.trajectoryWidget.plot.setData(self.trackinfo[1:,1],self.trackinfo[1:,2]) #updating the plotted trajectory in the tracking viewport

        if self.show_waterfall:
            self.waterfall_data = self.waterfall_data[:self._session.GUI['length_waterfall'], :]
            self.watWidget.img.setImage(np.transpose(self.waterfall_data), autoLevels=False, autoRange=False,
                                        autoHistogramRange=False)

        new_time = time.time()
        self.fps = new_time - self.lastRefresh
        self.realfps = self.camera.camera.getPropertyValue("internal_frame_rate")[0]
        self.lastRefresh = new_time

        self.messageWidget.updateMemory(self.buffer_memory / self._session.Saving['max_memory'] * 100)
        self.messageWidget.updateProcessor(psutil.cpu_percent())

        msg = '''<b>Buffer time:</b> %0.2f ms <br />
             <b>Refresh time:</b> %0.2f ms <br />
             <b>FPS from camera:</b> %0.2f <br />
             <b>Acquired Frames</b> %i <br />
             <b>Dropped Frames</b> %i <br />
             <b>Frames in buffer</b> %i''' % (
        self.buffertime * 1000, self.fps * 1000, self.realfps, self.totalframes, self.droppedframes, self.q.qsize())
        self.messageWidget.updateMessage(msg)
        # self.messageWidget.updateLog(self.logMessage)
        self.logmessage = []

    def saveWaterfall(self):
        """Saves the waterfall data, if any.
        """
        if len(self.waterfall_data) > 1:
            fn = self._session.Saving['filename_waterfall']
            filename = '%s.hdf5' % (fn)
            fileDir = self._session.Saving['directory']
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)

            f = h5py.File(os.path.join(fileDir, filename), "a")
            now = str(datetime.now())
            g = f.create_group(now)
            dset = g.create_dataset('waterfall', data=self.waterfall_data)
            meta = g.create_dataset('metadata', data=self._session.serialize().encode("ascii", "ignore"))
            f.flush()
            f.close()
            self.messageWidget.appendLog('i', 'Saved Waterfall')

    def saveTrajectory(self):
        """Saves the trajectory data, if any.
        """
        if len(self.trackinfo) > 1:
            fn = self._session.Saving['filename_trajectory']
            filename = '%s.hdf5' % (fn)
            fileDir = self._session.Saving['directory']
            if not os.path.exists(fileDir):
                os.makedirs(fileDir)

            f = h5py.File(os.path.join(fileDir, filename), "a")
            now = str(datetime.now())
            g = f.create_group(now)
            dset = g.create_dataset('trajectory', data=[self.trackinfo])
            meta = g.create_dataset('metadata', data=self._session.serialize().encode("ascii", "ignore"))
            f.flush()
            f.close()
            self.messageWidget.appendLog('i', 'Saved Trajectory')

    def update_settings(self, settings):
        new_session = _session(settings)
        self.updateSession(new_session)
        self.config.populateTree(self._session)

    def updateSession(self, session):
        """Updates the session variables passed by the config window.
        """
        update_cam = False
        update_roi = False
        update_exposure = False
        update_binning = True
        for k in session.params['Camera']:
            new_prop = session.params['Camera'][k]
            old_prop = self._session.params['Camera'][k]
            if new_prop != old_prop:
                update_cam = True
                if k in ['roi_x1', 'roi_x2', 'roi_y1', 'roi_y2']:
                    update_roi = True
                    if self._session.Debug['to_screen']:
                        print('Update ROI')
                elif k == 'exposure_time':
                    update_exposure = True
                elif k in ['binning_x', 'binning_y']:
                    update_binning = True

        if session.GUI['length_waterfall'] != self._session.GUI['length_waterfall']:
            if self.show_waterfall:
                self.closeWaterfall()
                self.restart_waterfall = True

        self.messageWidget.appendLog('i', 'Parameters updated')
        self.messageWidget.appendLog('i', 'Measurement: %s' % session.User['measurement'])
        self._session = session.copy()

        if update_cam:
            if self.acquiring:
                self.stopMovie()

            if update_roi:
                X = np.sort([session.Camera['roi_x1'], session.Camera['roi_x2']])
                Y = np.sort([session.Camera['roi_y1'], session.Camera['roi_y2']])
                self.setROI(X, Y)

            if update_exposure:
                new_exp = self.camera.setExposure(session.Camera['exposure_time'])
                self._session.Camera = {'exposure_time': new_exp}
                self.messageWidget.appendLog('i', 'Updated exposure: %s' % new_exp)
                if self._session.Debug['to_screen']:
                    print("New Exposure: %s" % new_exp)
                    print(self._session)

            if update_binning:
                self.camera.setBinning(session.Camera['binning_x'], session.Camera['binning_y'])

        self.refreshTimer.stop()
        self.refreshTimer.start(session.GUI['refresh_time'])

    def startSpecialTask(self):
        """Starts a special task. This is triggered by the user with a special combination of actions, for example clicking
        with the mouse on a plot, draggin a crosshair, etc."""
        if not self.spot_tracking:
            locy = self.camWidget.crosshair[0].getPos()[1]
            locx = self.camWidget.crosshair[1].getPos()[0]
            self.trajectoryWidget.plot.clear()
            self.spot_tracking = True
            self.spot_coords = [locx, locy]
            self.messageWidget.appendLog('i', 'Live tracking of intensity started')
        else:
            print('Special task already running')

    def stopSpecialTask(self):
        """Stops the special task"""
        if self.spot_tracking:
            self.spot_tracking = False
            self.messageWidget.appendLog('i', 'Live tracking stopped')

    def done(self):
        # self.saveRunning = False
        self.acquiring = False

    def exitSafe(self):
        self.close()

    def closeEvent(self, evnt):
        """Triggered at closing. Checks that the save is complete and closes the dataFile
        """
        self.messageWidget.appendLog('i', 'Closing the program')
        if self.acquiring:
            self.stopMovie()
        if self.spot_tracking:
            self.stopSpecialTask()
        self.emit(QtCore.SIGNAL('closeAll'))
        self.camera.stopCamera()
        self.movieSaveStop()
        try:
            # Checks if the process P exists and tries to close it.
            if self.p.is_alive():
                qs = self.q.qsize()
                with ProgressDialog("Finish saving data...", 0, qs) as dlg:
                    while self.q.qsize() > 1:
                        dlg.setValue(qs - self.q.qsize())
                        time.sleep(0.5)
            self.p.join()
        except AttributeError:
            pass
        if self.q.qsize() > 0:
            self.messageWidget.appendLog('i', 'The queue was not empty')
            print('Freeing up memory...')
            self.emptyQueue()

        # Save LOG.
        fn = self._session.Saving['filename_log']
        timestamp = datetime.now().strftime('%H%M%S')
        filename = '%s%s.log' % (fn, timestamp)
        fileDir = self._session.Saving['directory']
        if not os.path.exists(fileDir):
            os.makedirs(fileDir)

        f = open(os.path.join(fileDir, filename), "a")
        for line in self.messageWidget.logText:
            f.write(line + '\n')
        f.flush()
        f.close()
        print('Saved LOG')
        super(ASLMMain, self).closeEvent(evnt)


if __name__ == '__main__':
    pass