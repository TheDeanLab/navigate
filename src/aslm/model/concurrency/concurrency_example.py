import numpy as np
from concurrency_tools import ObjectInSubprocess, CustodyThread, ResultThread, SharedNDArray
import time
import logging

# Logger Setup
p = __name__.split(".")[1]
logger = logging.getLogger(p)


# Tune these values to get reliable operation on your machine:
fps = 500           # Camera frames per second
shape = (16, 512, 512)  # Pixel dimensions of each data buffer
N = 10            # Number of data buffers to acquire
description = (
    "Record -> Deconvolve -> Display -> Detect motion -> Save\n" +
    "%d bursts of %d %dx%d frames at %d frames/second" % (N, *shape, fps))


def without_concurrency():
    # On my machine, this prints:
    # Camera spends 322 ms working, but also spends 2644 ms waiting!
    ####################################################################
    print("Simulating acquiring without concurrency...\n" + description)
    ####################################################################
    camera = Camera()
    preprocessor = Preprocessor()
    display = Display()
    postprocessor = Postprocessor()
    storage = Storage()
    data_buffers = [np.zeros(shape, dtype='uint16') for x in range(N)]

    def timelapse(data_buffer):
        camera.record(data_buffer, fps)
        preprocessor.deconvolve(data_buffer)
        display.show(data_buffer)
        postprocessor.detect_motion(data_buffer)
        storage.save(data_buffer)

    for db in data_buffers:
        timelapse(db)
    print(
        "Camera spends %0.0f ms working, but also spends %0.0f ms waiting!" %
        (camera.time_working * 1000, camera.time_waiting * 1000))


def with_concurrency():
    # On my machine, this prints:
    # Camera spends 323 ms working, but only spends 12 ms waiting.
    ####################################################################
    print("\nSimulating acquiring WITH concurrency...\n" + description)
    start_time = time.perf_counter()
    ####################################################################
    camera = ObjectInSubprocess(Camera)  # Can't tolerate threadswitching
    preprocessor = ObjectInSubprocess(Preprocessor)  # CPU-bound
    display = ObjectInSubprocess(Display)  # Slightly CPU-bound
    postprocessor = ObjectInSubprocess(Postprocessor)  # CPU-bound
    storage = Storage()  # IO-bound, not CPU-bound
    data_buffers = [SharedNDArray(shape, dtype='uint16') for x in range(N)]

    def timelapse(data_buffer, custody):
        # Wait in line to use the camera...
        custody.switch_from(None, to=camera)
        camera.record(data_buffer, fps)
        # Wait in the next line...
        custody.switch_from(camera, to=preprocessor)
        preprocessor.deconvolve(data_buffer)
        # Wait in the next line...
        custody.switch_from(preprocessor, to=display)
        display.show(data_buffer)
        # Wait in the last line...
        custody.switch_from(display, to=postprocessor)
        postprocessor.detect_motion(data_buffer)
        custody.switch_from(postprocessor, to=None)  # Use the disk immediately
        storage.save(data_buffer)

    threads = []
    for db in data_buffers:
        threads.append(CustodyThread(  # This provides the "custody" object above
            first_resource=camera, target=timelapse, args=(db,)).start())
    for th in threads:  # Wait for all our threads to finish
        th.get_result()
    end_time = time.perf_counter()
    print(
        "Camera spends %0.0f ms working, but only spends %0.0f ms waiting." %
        (camera.time_working * 1000, camera.time_waiting * 1000))
    print("total time cost: ", (end_time - start_time) * 1000)


def with_concurrency_lock():
    # On my machine, this prints:
    # Camera spends 323 ms working, but only spends 12 ms waiting.
    ####################################################################
    print("\nSimulating acquiring WITH concurrency_lock...\n" + description)
    start_time = time.perf_counter()
    ####################################################################
    # Can't tolerate threadswitching
    camera = ObjectInSubprocess(Camera, with_lock=True)
    preprocessor = ObjectInSubprocess(
        Preprocessor, with_lock=True)  # CPU-bound
    display = ObjectInSubprocess(Display, with_lock=True)  # Slightly CPU-bound
    postprocessor = ObjectInSubprocess(
        Postprocessor, with_lock=True)  # CPU-bound
    storage = Storage()  # IO-bound, not CPU-bound
    data_buffers = [SharedNDArray(shape, dtype='uint16') for x in range(N)]

    def timelapse(data_buffer):
        camera.record(data_buffer, fps)
        preprocessor.deconvolve(data_buffer)
        display.show(data_buffer)
        postprocessor.detect_motion(data_buffer)
        storage.save(data_buffer)

    threads = []
    for db in data_buffers:
        threads.append(ResultThread(  # This provides the "custody" object above
            target=timelapse, args=(db,)).start())
    for th in threads:  # Wait for all our threads to finish
        th.get_result()
    end_time = time.perf_counter()
    print(
        "Camera spends %0.0f ms working, but only spends %0.0f ms waiting." %
        (camera.time_working * 1000, camera.time_waiting * 1000))
    print("total time cost: ", (end_time - start_time) * 1000)
    ####################################################################
    # We got huge performance gains using threads, subprocesses, and
    # shared memory. The code only got ~1.5x longer, and didn't get too
    # ugly! This is much nicer than everything else I've tried.
    ####################################################################


class Camera:
    def record(self, out, fps):
        """Reliable high-framerate recording doesn't tolerate any pauses"""
        import time
        dt = 1 / fps
        frames_dropped = 0
        start = time.perf_counter()
        for which_frame in range(out.shape[0]):
            t_frame_available = (1 + which_frame) * dt
            t_frame_dropped = (3 + which_frame) * dt
            while time.perf_counter() - start < t_frame_available:
                pass  # Simulate polling for the next frame
            if time.perf_counter() - start >= t_frame_dropped:
                frames_dropped += 1
            out[which_frame, 0::2, 1::2].fill(1)  # Simulate copying a frame
            out[which_frame, 1::2, 0::2].fill(2)
        end = time.perf_counter()
        if frames_dropped > 0:
            print(
                "Warning: the dummy camera dropped",
                frames_dropped,
                "frames")
        # Timing bookkeeping:
        if not hasattr(self, 'time_working'):
            self.time_working = 0
            self.time_waiting = 0
        if hasattr(self, 'last_end'):
            self.time_waiting += (start - self.last_end)
        self.time_working += (end - start)
        self.last_end = end


class Preprocessor:
    def deconvolve(self, x):
        """Live (mock) linear deconvolution is very CPU-hungry"""
        x_ft = np.fft.rfftn(x)
        fourier_mask = np.ones_like(x_ft)  # Real decon mask would go here
        np.multiply(x_ft, fourier_mask, out=x_ft)
        x[:, :, :] = np.fft.irfftn(x_ft, s=x.shape)


class Display:
    def show(self, x):
        """Log-scale and normalize data, a little CPU-hungry"""
        im = np.log1p(x, dtype='float64')
        im -= im.min()
        if im.max() > 0:
            im /= im.max()


class Postprocessor:
    def detect_motion(self, x):
        """Motion detection is fairly CPU-hungry"""
        mean_img = np.median(x, axis=0)
        variance_img = np.var(x, axis=0)
        motion_map = np.zeros_like(mean_img)
        np.divide(variance_img, mean_img, out=motion_map, where=mean_img > 10)
        if np.max(np.abs(motion_map)) > 5:  # ~1 for Poisson data
            print("Motion detected!")


class Storage:
    def save(self, x):
        """Saving data to disk is IO-bound rather than CPU-bound"""
        from tempfile import TemporaryFile
        with TemporaryFile() as f:
            np.save(f, x)


if __name__ == '__main__':
    # without_concurrency()
    with_concurrency()
    with_concurrency_lock()
    ######################
    #  END EXAMPLE CODE  #
    ######################
