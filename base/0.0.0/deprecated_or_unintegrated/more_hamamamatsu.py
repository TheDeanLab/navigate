if session.CameraParameters['type'] == 'HamamatsuCamera':
    # TODO: Implement Hamamatsu Camera as a subclass of CameraBase
    # Initialize Hamamatsu Camera
    if verbose:
        print("Initializing Hamamatsu Camera")

    # Camera Imports
    from model.camera.dcam import Dcam
    from model.camera.dcam import Dcamapi

    # Initialize Dcamapi
    if Dcamapi.init() is not False:
        n = Dcamapi.get_devicecount()
        if verbose:
            print("Found %d cameras" % n)

        # Initialize the cameras
        low_resolution_camera = Dcam(0)
        high_resolution_camera = Dcam(1)

        # Confirm cameras are open, and set default parameters
        if low_resolution_camera.dev_open() is not False:
            low_resolution_camera.dcam_set_default_light_sheet_mode_parameters()
        else:
            print('-NG: low_resolution_camera.dev_open() fails with error {}'.format(low_resolution_camera.lasterr()))
            sys.exit()

        if high_resolution_camera.dev_open() is not False:
            high_resolution_camera.dcam_set_default_light_sheet_mode_parameters()
        else:
            print('-NG: high_resolution_camera.dev_open() fails with error {}'.format(high_resolution_camera.lasterr()))
            sys.exit()

        if verbose:
            print("Cameras Initialized")

    else:
        print('-NG: Dcamapi.init() fails with error {}'.format(Dcamapi.lasterr()))
        sys.exit()