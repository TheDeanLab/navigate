"""Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
provided that the following conditions are met:

     * Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.

     * Redistributions in binary form must reproduce the above copyright
     notice, this list of conditions and the following disclaimer in the
     documentation and/or other materials provided with the distribution.

     * Neither the name of the copyright holders nor the names of its
     contributors may be used to endorse or promote products derived from this
     software without specific prior written permission.

NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE.
"""
import unittest
import multiprocessing as mp
import threading
import time
import random

from aslm.model.model_features.aslm_feature_container import SignalNode, load_features

class DummyFeature:
    def __init__(self, *args):
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.is_end = False

        self.model = None if len(args) == 0 else args[0]
        self.feature_name = args[1] if len(args) > 1 else 'none'
        self.config_table = {'signal':{'name-for-test': self.feature_name,
                                       'init': self.signal_init_func,
                                       'main': self.signal_main_func},
                            'data':  {'name-for-test': self.feature_name,
                                      'init': self.data_init_func,
                                      'main': self.data_main_func},
                            'node': {}}

        if len(args) > 2 and args[2]:
            self.config_table['signal']['main-response'] = self.signal_wait_func

        if len(args) > 3:
            self.config_table['node']['device_related'] = args[3]

        self.target_frame_id = 0
        self.response_value = 0
        self.wait_lock = threading.Lock()

    def init_func(self):
        self.init_times += 1

    def main_func(self, value=None):
        self.running_times_main_func += 1
        return value

    def response_func(self, value=None):
        self.running_times_response_func += 1
        return value

    def end_func(self):
        return self.is_end

    def clear(self):
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.is_end = False

    def signal_init_func(self, *args):
        self.target_frame_id = -1
        if self.wait_lock.locked():
            self.wait_lock.release()

    def signal_main_func(self, *args):
        self.target_frame_id = self.model.signal_num
        self.model.signal_records.append((self.target_frame_id, self.feature_name))
        if 'main-response' in self.config_table['signal']:
            self.wait_lock.acquire()
            print(self.feature_name, ': wait lock is acquired!!!!')

        return True

    def signal_wait_func(self, *args):
        self.wait_lock.acquire()
        self.wait_lock.release()
        print(self.feature_name, ': wait response!(signal)', self.response_value)
        return self.response_value

    def data_init_func(self):
        pass

    def data_pre_main_func(self, frame_ids):
        return self.target_frame_id in frame_ids

    def data_main_func(self, frame_ids):
        # assert self.target_frame_id in frame_ids, 'frame is not ready'
        self.model.data_records.append((frame_ids[0], self.feature_name))

        if 'main-response' in self.config_table['signal'] and self.wait_lock.locked():
            # random Yes/No
            self.response_value = random.randint(0, 1)
            print(self.feature_name, ': wait lock is released!(data)', self.response_value)
            self.wait_lock.release()
            return self.response_value
        return True



class DummyDevice:
    def __init__(self, timecost=0.2):
        self.msg_count = mp.Value('i', 0)
        self.sendout_msg_count = 0
        self.out_port = None
        self.in_port = None
        self.timecost = timecost
        self.stop_flag = False

    def setup(self):
        signalPort, self.in_port = mp.Pipe()
        dataPort, self.out_port = mp.Pipe()
        in_process = mp.Process(target=self.listen)
        out_process = mp.Process(target=self.sendout)
        in_process.start()
        out_process.start()

        self.sendout_msg_count = 0
        self.msg_count.value = 0
        self.stop_flag = False

        return signalPort, dataPort

    def generate_message(self):
        time.sleep(self.timecost)
        self.msg_count.value += 1

    def clear(self):
        self.msg_count.value = 0

    def listen(self):
        while not self.stop_flag:
            signal = self.in_port.recv()
            if signal == 'shutdown':
                self.stop_flag = True
                break
            self.generate_message()
            self.in_port.send('done')

    def sendout(self, timeout=100):
        while not self.stop_flag:
            msg = self.out_port.recv()
            if msg == 'shutdown':
                break
            c = 0
            while self.msg_count.value == self.sendout_msg_count and c < timeout:
                time.sleep(0.01)
                c += 1
            self.out_port.send(list(range(self.sendout_msg_count, self.msg_count.value)))
            self.sendout_msg_count = self.msg_count.value

class DummyModel:
    def __init__(self):
        self.device = DummyDevice()
        self.signal_pipe, self.data_pipe = self.device.setup()

        self.signal_container = None
        self.data_container = None
        self.signal_thread = None
        self.data_thread = None

        self.stop_flag = False
        self.signal_num = 0

        self.data = []
        self.signal_records = []
        self.data_records = []

    def signal_func(self):
        self.signal_container.reset()
        while not self.signal_container.end_flag:
            if self.signal_container:
                self.signal_container.run()

            self.signal_pipe.send('signal')
            self.signal_pipe.recv()

            if self.signal_container:
                self.signal_container.run(wait_response=True)

            self.signal_num += 1

        self.signal_pipe.send('shutdown')

        self.stop_flag = True

    def data_func(self):
        while not self.stop_flag:
            self.data_pipe.send('getData')
            frame_ids = self.data_pipe.recv()
            print('receive: ', frame_ids)
            if not frame_ids:
                continue

            self.data.append(frame_ids)

            if self.data_container:
                self.data_container.run(frame_ids)
        self.data_pipe.send('shutdown')

    def start(self, feature_list):
        if feature_list is None:
            return False
        self.data = []
        self.signal_records = []
        self.data_records = []
        self.stop_flag = False
        self.signal_num = 0
        if not self.signal_pipe.closed:
            self.signal_pipe.send('shutdown')
        if not self.data_pipe.closed:
            self.data_pipe.send('shutdown')
        self.signal_pipe, self.data_pipe = self.device.setup()

        self.signal_container, self.data_container = load_features(self, feature_list)
        self.signal_thread = threading.Thread(target=self.signal_func, name='signal')
        self.data_thread = threading.Thread(target=self.data_func, name='data')
        self.signal_thread.start()
        self.data_thread.start()

        self.signal_thread.join()
        self.stop_flag = True
        self.data_thread.join()
        return True

def generate_random_feature_list(has_response_func=False):
    feature_list = []
    m = random.randint(1, 10)
    node_count = 0
    for i in range(m):
        n = random.randint(1, 10)
        temp = []
        for j in range(n):
            has_response = random.randint(0, 1) if has_response_func else 0
            device_related = random.randint(0, 1)
            feature = {'name': DummyFeature, 'args': (f'node{node_count}', has_response, device_related,)}
            if has_response:
                feature['node'] = {'need_response': True}
            temp.append(feature)
            node_count += 1
            # has response function means that node can only have child node
            if has_response:
                break
        feature_list.append(temp)
    return feature_list

def print_feature_list(feature_list):
    result = []
    for features in feature_list:
        temp = []
        for node in features:
            temp.append((node['args'][0], node['args'][1], node['args'][2]))
        result.append(temp)
    print('--------feature list-------------')
    print(result)
    print('---------------------------------')
    return str(result)

def convert_to_feature_list(feature_str):
    result = []
    for features in feature_str:
        temp = []
        for feature in features:
            node = {'name': DummyFeature, 'args': (*feature,)}
            temp.append(node)
        result.append(temp)
    return result


class TestFeatureContainer(unittest.TestCase):

    def setUp(self):
        print('-------------new test case-----------------')

    @unittest.skip('takes long time to finish the test')
    def test_feature_container(self):
        model = DummyModel()
        print('# test signal and data are synchronous')
        print('--all function nodes are single step')
        
        print('----all signal nodes are without waiting function')
        for i in range(10):
            feature_list = generate_random_feature_list()
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(feature_list)

        print('----some signal nodes have waiting function')
        for i in range(10):
            # feature_list = [[{'name': DummyFeature, 'args':('node0', 0, 0,)}, {'name': DummyFeature, 'args':('node1', 1, 0)}], [{'name': DummyFeature, 'args':('node2', 1, 1,)}], \
            #     [{'name': DummyFeature, 'args':('node3', 1, 1,)}], [{'name': DummyFeature, 'args':('node4', 0, 0,)}]]
            # feature_list = [[{'name': DummyFeature, 'args':('node0', 1, 0,)}], [{'name': DummyFeature, 'args':('node1', 0, 0,)}, {'name': DummyFeature, 'args':('node2', 1, 0)}]]
            # feature_list = convert_to_feature_list([[('node0', 1, 1)], [('node1', 1, 1)], [('node2', 1, 0)], [('node3', 1, 0)], [('node4', 0, 0), ('node5', 1, 1)], [('node6', 1, 1)], [('node7', 1, 0)]])
            feature_list = generate_random_feature_list(has_response_func=True)
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(feature_list)

    def test_load_feature(self):
        def check(tnode1, tnode2):
            if tnode1 is None and tnode2 is None:
                return True
            if tnode1 is None or tnode2 is None:
                return False
            return tnode1.node_funcs['name-for-test'] == tnode2.node_funcs['name-for-test']

        def is_isomorphic(tree1, tree2):
            p, q = tree1, tree2
            stack = []
            while p or q or stack:
                if not check(p, q):
                    return False
                if p:
                    stack.append((p.sibling, q.sibling))
                    p, q = p.child, q.child
                else:
                    p, q = stack.pop()
            return True

        # generates 10 random feature lists and verify whether they are loaded correctly
        for i in range(10):
            feature_list = generate_random_feature_list()
            signal_container, data_container = load_features(self, feature_list)
            assert is_isomorphic(signal_container.root, data_container.root)
            print('-', i, 'random feature list is correct!')       

    def test_signal_node(self):
        feature = DummyFeature()
        func_dict = {
            'init': feature.init_func,
            'main': feature.main_func,
            'end': feature.end_func
        }

        print('without waiting for a response:')
        node = SignalNode('test_1', func_dict)
        assert node.has_response_func == False
        assert node.node_funcs['end']() == False

        feature.is_end = True
        assert node.node_funcs['end']() == True

        result, is_end = node.run()
        assert feature.init_times == 1
        assert feature.running_times_main_func == 1
        assert result == None
        assert is_end == True
        assert node.is_initialized == False

        result, is_end = node.run(True)
        assert feature.init_times == 2
        assert feature.running_times_main_func == 2
        assert result == True
        assert is_end == True
        assert node.is_initialized == False
        assert node.wait_response == False

        print('--running with waiting option')
        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == True
        assert node.is_initialized == False
        assert node.wait_response == False
        assert feature.running_times_main_func == 1
        assert feature.init_times == 1

        print('--device related')
        feature.clear()
        node = SignalNode('test_1', func_dict, device_related=True)
        print(node.node_type)
        assert node.has_response_func == False
        result, is_end = node.run()
        assert is_end == True
        assert node.wait_response == False
        assert feature.running_times_main_func == 1

        print('----running with waitint option')
        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == False
        assert node.wait_response == False
        assert feature.running_times_main_func == 0
        assert node.is_initialized == True

        print('----multi-step function')
        feature.clear()
        node.node_type = 'multi-step'
        assert func_dict.get('main-response', None) == None
        assert node.has_response_func == False
        steps = 5
        for i in range(steps+1):
            feature.is_end = (i == steps)
            result, is_end = node.run()
            if i < steps:
                assert node.is_initialized == True
                assert is_end == False
            else:
                assert node.is_initialized == False
                assert is_end == True
            assert feature.running_times_main_func == i+1
            assert node.wait_response == False
            if i < steps:
                result, is_end = node.run(wait_response=True)
                assert is_end == False

        print('--multi-step function')
        feature.clear()
        node = SignalNode('test_1', func_dict, node_type='multi-step')
        assert func_dict.get('main-response') != None
        assert node.has_response_func == True
        steps = 5
        for i in range(steps+1):
            feature.is_end = (i == steps)
            result, is_end = node.run()
            assert is_end == False
            assert feature.running_times_main_func == i+1
            assert node.is_initialized == True
            assert node.wait_response == True
            result, is_end = node.run(wait_response=True)
            if i < steps:
                assert is_end == False
            else:
                assert is_end == True
        assert node.wait_response == False
        assert node.is_initialized == False

        print('wait for a response:')
        feature.clear()
        func_dict['main-response'] = feature.response_func
        node = SignalNode('test_2', func_dict)
        assert node.has_response_func == True
        assert node.wait_response == False

        print('--running without waiting option')
        result, is_end = node.run()
        assert result == None
        assert is_end == False
        assert node.is_initialized == True
        assert node.wait_response == True

        result, is_end = node.run(True)
        assert result == True
        assert is_end == False
        assert feature.init_times == 1
        assert feature.running_times_main_func == 2
        assert node.wait_response == True
        assert node.is_initialized == True

        print('--running with waiting option')
        result, is_end = node.run(wait_response=True)
        assert feature.running_times_main_func == 2
        assert feature.running_times_response_func == 1
        assert node.wait_response == False
        assert node.is_initialized == False
        assert is_end == True

        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == False
        assert feature.init_times == 1
        assert feature.running_times_main_func == 0
        assert feature.running_times_response_func == 0
        assert node.is_initialized == True

        print('----device related')
        node.device_related = True
        feature.clear()
        result, is_end = node.run()
        assert is_end == False
        assert feature.running_times_main_func == 1
        assert node.wait_response == True
        assert node.is_initialized == True

        result, is_end = node.run(wait_response=True)
        assert is_end == True
        assert feature.running_times_response_func == 1
        assert feature.running_times_main_func == 1
        assert node.wait_response == False
        assert node.is_initialized == False

        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == False
        assert feature.running_times_main_func == 0
        assert node.wait_response == False
        assert feature.init_times == 1
        assert node.is_initialized == True

        print('--multi-step function')
        feature.clear()
        node = SignalNode('test', func_dict, node_type='multi-step')
        steps = 5
        for i in range(steps+1):
            feature.is_end = (i == steps)
            result, is_end = node.run()
            assert is_end == False
            assert feature.running_times_main_func == i+1
            assert node.is_initialized == True
            result, is_end = node.run(wait_response=True)
            if i < steps:
                assert is_end == False
            else:
                assert is_end == True
            assert feature.running_times_response_func == i+1
            assert node.wait_response == False

if __name__ == '__main__':
    unittest.main()