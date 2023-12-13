import pytest
import time
import threading
import multiprocessing as mp
from navigate.model.features.feature_container import load_features


class DummyDevice:
    def __init__(self, timecost=0.2):
        self.msg_count = mp.Value("i", 0)
        self.sendout_msg_count = 0
        self.out_port = None
        self.in_port = None
        self.timecost = timecost
        self.stop_acquisition = False

    def setup(self):
        signalPort, self.in_port = mp.Pipe()
        dataPort, self.out_port = mp.Pipe()
        in_process = mp.Process(target=self.listen)
        out_process = mp.Process(target=self.sendout)
        in_process.start()
        out_process.start()

        self.sendout_msg_count = 0
        self.msg_count.value = 0
        self.stop_acquisition = False

        return signalPort, dataPort

    def generate_message(self):
        time.sleep(self.timecost)
        self.msg_count.value += 1

    def clear(self):
        self.msg_count.value = 0

    def listen(self):
        while not self.stop_acquisition:
            signal = self.in_port.recv()
            if signal == "shutdown":
                self.stop_acquisition = True
                self.in_port.close()
                break
            self.generate_message()
            self.in_port.send("done")

    def sendout(self, timeout=100):
        while not self.stop_acquisition:
            msg = self.out_port.recv()
            if msg == "shutdown":
                self.out_port.close()
                break
            c = 0
            while self.msg_count.value == self.sendout_msg_count and c < timeout:
                time.sleep(0.01)
                c += 1
            self.out_port.send(
                list(range(self.sendout_msg_count, self.msg_count.value))
            )
            self.sendout_msg_count = self.msg_count.value


class RecordObj:
    def __init__(self, name_list, record_list, frame_id, frame_id_completed=-1):
        self.name_list = name_list
        self.record_list = record_list
        self.frame_id = frame_id
        self.frame_id_completed = frame_id_completed

    def __getattr__(self, __name: str):
        self.name_list += "." + __name
        return self

    def __call__(self, *args, **kwargs):
        kwargs["__test_frame_id"] = self.frame_id
        kwargs["__test_frame_id_completed"] = self.frame_id_completed
        print("* calling", self.name_list, args, kwargs)
        self.record_list.append((self.name_list, args, kwargs))


class DummyModelToTestFeatures:
    def __init__(self, configuration):
        self.configuration = configuration

        self.device = DummyDevice()
        self.signal_pipe, self.data_pipe = None, None

        self.signal_container = None
        self.data_container = None
        self.signal_thread = None
        self.data_thread = None

        self.stop_acquisition = False
        self.frame_id = 0  # signal_num
        self.frame_id_completed = -1

        self.data = []
        self.signal_records = []
        self.data_records = []

    def signal_func(self):
        self.signal_container.reset()
        while not self.signal_container.end_flag:
            if self.signal_container:
                self.signal_container.run()

            self.signal_pipe.send("signal")
            self.signal_pipe.recv()

            self.frame_id_completed += 1

            if self.signal_container:
                self.signal_container.run(wait_response=True)

            self.frame_id += 1  # signal_num

        self.signal_pipe.send("shutdown")

        self.stop_acquisition = True

    def data_func(self):
        while not self.stop_acquisition:
            self.data_pipe.send("getData")
            frame_ids = self.data_pipe.recv()
            print("receive: ", frame_ids)
            if not frame_ids:
                continue

            self.data.append(frame_ids)

            if self.data_container:
                self.data_container.run(frame_ids)
        self.data_pipe.send("shutdown")

    def start(self, feature_list):
        if feature_list is None:
            return False
        self.data = []
        self.signal_records = []
        self.data_records = []
        self.stop_acquisition = False
        self.frame_id = 0  # signal_num
        self.frame_id_completed = -1

        self.signal_pipe, self.data_pipe = self.device.setup()

        self.signal_container, self.data_container = load_features(self, feature_list)
        self.signal_thread = threading.Thread(target=self.signal_func, name="signal")
        self.data_thread = threading.Thread(target=self.data_func, name="data")
        self.signal_thread.start()
        self.data_thread.start()

        self.signal_thread.join()
        self.stop_acquisition = True
        self.data_thread.join()

        return True

    def get_stage_position(self):
        axes = ["x", "y", "z", "theta", "f"]
        stage_pos = self.configuration["experiment"]["StageParameters"]
        return dict(map(lambda axis: (axis + "_pos", stage_pos[axis]), axes))

    def __getattr__(self, __name: str):
        return RecordObj(
            __name, self.signal_records, self.frame_id, self.frame_id_completed
        )


@pytest.fixture(scope="module")
def dummy_model_to_test_features(dummy_model):
    model = DummyModelToTestFeatures(dummy_model.configuration)
    return model
