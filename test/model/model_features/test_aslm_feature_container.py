from multiprocessing.connection import wait
import unittest
from aslm.model.model_features.aslm_feature_container import SignalNode
from aslm.model.dummy_model import get_dummy_model

class DummyFeature:
    def __init__(self):
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.is_end = False

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

class TestFeatureContainer(unittest.TestCase):

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
        assert is_end == True
        assert feature.init_times == 1
        assert feature.running_times_main_func == 1
        assert feature.running_times_response_func == 1
        assert node.wait_response == False
        assert node.is_initialized == False

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