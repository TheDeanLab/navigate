# Copyright (c) 2021-2024  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the limitations in the disclaimer below)
# provided that the following conditions are met:

#      * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.

#      * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.

#      * Neither the name of the copyright holders nor the names of its
#      contributors may be used to endorse or promote products derived from this
#      software without specific prior written permission.

# NO EXPRESS OR IMPLIED LICENSES TO ANY PARTY'S PATENT RIGHTS ARE GRANTED BY
# THIS LICENSE. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
# CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
import unittest
import random
import threading

from navigate.model.features.feature_container import (
    SignalNode,
    DataNode,
    DataContainer,
    load_features,
)
from navigate.model.features.common_features import WaitToContinue, LoopByCount
from navigate.model.features.feature_container import dummy_True
from test.model.dummy import DummyModel


class DummyFeature:
    def __init__(self, *args):
        """
        args:
            0: model
            1: name
            2: with response (True/False) (1/0)
            3: device related (True/False) (1/0)
            4: multi step (integer >= 1)
            5: has data function? There could be no data functions when node_type is 'multi-step'
        """
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.running_times_cleanup_func = 0
        self.is_end = False
        self.is_closed = False

        self.model = None if len(args) == 0 else args[0]
        self.feature_name = args[1] if len(args) > 1 else "none"
        self.config_table = {
            "signal": {
                "name-for-test": self.feature_name,
                "init": self.signal_init_func,
                "main": self.signal_main_func,
            },
            "data": {
                "name-for-test": self.feature_name,
                "init": self.data_init_func,
                "main": self.data_main_func,
            },
            "node": {},
        }

        if len(args) > 2 and args[2]:
            self.config_table["signal"]["main-response"] = self.signal_wait_func
            self.has_response_func = True
        else:
            self.has_response_func = False

        if len(args) > 3:
            self.config_table["node"]["device_related"] = args[3] == 1

        if len(args) > 4 and args[4] > 1:
            self.config_table["node"]["node_type"] = "multi-step"
            self.multi_steps = args[4]
            self.config_table["signal"]["end"] = self.signal_end_func
            self.config_table["data"]["end"] = self.data_end_func
        else:
            self.multi_steps = 1

        if len(args) > 5 and args[4] > 1 and args[2] == False and args[5] == False:
            self.config_table["data"] = {}

        self.target_frame_id = 0
        self.response_value = 0
        self.current_signal_step = 0
        self.current_data_step = 0
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

    def close(self):
        self.is_closed = True
        self.running_times_cleanup_func += 1

    def clear(self):
        self.init_times = 0
        self.running_times_main_func = 0
        self.running_times_response_func = 0
        self.running_times_cleanup_func = 0
        self.is_end = False
        self.is_closed = False

    def signal_init_func(self, *args):
        self.target_frame_id = -1
        self.current_signal_step = 0
        if self.wait_lock.locked():
            self.wait_lock.release()

    def signal_main_func(self, *args):
        self.target_frame_id = self.model.frame_id  # signal_num
        if self.feature_name.startswith("node"):
            self.model.signal_records.append((self.target_frame_id, self.feature_name))
        if self.has_response_func:
            self.wait_lock.acquire()
            print(
                self.feature_name, ": wait lock is acquired!!!!", self.target_frame_id
            )

        return True

    def signal_wait_func(self, *args):
        self.wait_lock.acquire()
        self.wait_lock.release()
        print(self.feature_name, ": wait response!(signal)", self.response_value)
        return self.response_value

    def signal_end_func(self):
        self.current_signal_step += 1
        return self.current_signal_step >= self.multi_steps

    def data_init_func(self):
        self.current_data_step = 0
        pass

    def data_pre_main_func(self, frame_ids):
        return self.target_frame_id in frame_ids

    def data_main_func(self, frame_ids):
        # assert self.target_frame_id in frame_ids, 'frame is not ready'
        if self.feature_name.startswith("node"):
            self.model.data_records.append((frame_ids[0], self.feature_name))

        if self.has_response_func and self.wait_lock.locked():
            # random Yes/No
            self.response_value = random.randint(0, 1)
            print(
                self.feature_name,
                ": wait lock is released!(data)",
                frame_ids,
                self.response_value,
            )
            self.wait_lock.release()
            return self.response_value
        return True

    def data_end_func(self):
        self.current_data_step += 1
        return self.current_data_step >= self.multi_steps


def generate_random_feature_list(
    has_response_func=False, multi_step=False, with_data_func=True, loop_node=False
):
    feature_list = []
    m = random.randint(1, 10)
    node_count = 0
    for i in range(m):
        n = random.randint(1, 10)
        temp = []
        for j in range(n):
            has_response = random.randint(0, 1) if has_response_func else 0
            device_related = random.randint(0, 1)
            steps = random.randint(1, 10) if multi_step else 1
            steps = 1 if steps < 5 else steps
            if with_data_func == False:
                no_data_func = random.randint(0, 1)
            else:
                no_data_func = 0
            if steps >= 5 and no_data_func:
                has_response = False
                feature = {
                    "name": DummyFeature,
                    "args": (
                        f"multi-step{node_count}",
                        has_response,
                        1,
                        steps,
                        False,
                    ),
                }
                temp.append(feature)
                temp.append({"name": WaitToContinue})
            else:
                feature = {
                    "name": DummyFeature,
                    "args": (
                        f"node{node_count}",
                        has_response,
                        device_related,
                        steps,
                    ),
                }
                if has_response:
                    feature["node"] = {"need_response": True}
                temp.append(feature)
            node_count += 1
            # has response function means that node can only have child node
            if has_response:
                break
        turn_to_loop_flag = random.randint(0, 1) if loop_node else 0
        if turn_to_loop_flag:
            temp.append({"name": LoopByCount, "args": (3,)})
            node_count += 1
            temp = tuple(temp)
        feature_list.append(temp)
    return feature_list


def print_feature_list(feature_list):
    result = []
    for features in feature_list:
        temp = []
        for node in features:
            if "args" in node:
                temp.append(node["args"])
            else:
                temp.append(node["name"].__name__)
        if type(features) is tuple:
            temp = tuple(temp)
        result.append(temp)
    print("--------feature list-------------")
    print(result)
    print("---------------------------------")
    return str(result)


def convert_to_feature_list(feature_str):
    result = []
    for features in feature_str:
        temp = []
        for feature in features:
            if type(feature) == str:
                node = {"name": WaitToContinue}
            else:
                node = {"name": DummyFeature, "args": (*feature,)}
            temp.append(node)
        result.append(temp)
    return result


class TestFeatureContainer(unittest.TestCase):
    def setUp(self):
        print("-------------new test case-----------------")

    @unittest.skip("takes long time to finish the test")
    def test_feature_container(self):
        model = DummyModel()
        print("# test signal and data are synchronous")
        print("--all function nodes are single step")

        print("----all signal nodes are without waiting function")
        for i in range(10):
            feature_list = generate_random_feature_list()
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print("----some signal nodes have waiting function")
        for i in range(10):
            # feature_list = convert_to_feature_list([[('node0', 1, 1, 1)], [('node1', 1, 0, 1)], [('node2', 1, 1, 1)], [('node3', 1, 0, 1)], [('node4', 1, 0, 1)], [('node5', 1, 0, 1)], [('node6', 1, 0, 1)], [('node7', 1, 1, 1)], [('node8', 0, 1, 1), ('node9', 0, 1, 1), ('node10', 1, 0, 1)], [('node11', 1, 1, 1)]])
            feature_list = generate_random_feature_list(has_response_func=True)
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print("--Some function nodes are multi-step")
        print(
            "----multi-step nodes have both signal and data functions, and without waiting function"
        )
        for i in range(10):
            feature_list = generate_random_feature_list(multi_step=True)
            # feature_list = convert_to_feature_list([[('node0', 0, 0, 10), ('node1', 0, 1, 5), ('node2', 0, 0, 1), ('node3', 0, 0, 9)], [('node4', 0, 1, 8), ('node5', 0, 1, 10), ('node6', 0, 1, 6), ('node7', 0, 0, 1), ('node8', 0, 0, 6), ('node9', 0, 1, 1), ('node10', 0, 0, 6)], [('node11', 0, 0, 1), ('node12', 0, 0, 1), ('node13', 0, 0, 1), ('node14', 0, 1, 7), ('node15', 0, 0, 1)], [('node16', 0, 0, 1), ('node17', 0, 1, 1), ('node18', 0, 1, 7), ('node19', 0, 1, 7), ('node20', 0, 1, 10), ('node21', 0, 0, 1), ('node22', 0, 1, 9), ('node23', 0, 1, 1), ('node24', 0, 0, 10), ('node25', 0, 0, 6)], [('node26', 0, 1, 1), ('node27', 0, 1, 7), ('node28', 0, 1, 8), ('node29', 0, 1, 7), ('node30', 0, 0, 5), ('node31', 0, 1, 1), ('node32', 0, 0, 10)]])
            # feature_list = convert_to_feature_list([[('node0', 0, 1, 2), ('node1', 0, 0, 3)]])
            # feature_list = convert_to_feature_list([[('node0', 0, 0, 5)], [('node1', 0, 0, 5), ('node2', 0, 0, 10), ('node3', 0, 1, 7), ('node4', 0, 0, 1), ('node5', 0, 0, 9), ('node6', 0, 1, 9)], [('node7', 0, 0, 9), ('node8', 0, 0, 6), ('node9', 0, 0, 7), ('node10', 0, 1, 3), ('node11', 0, 1, 6), ('node12', 0, 1, 5), ('node13', 0, 0, 4), ('node14', 0, 0, 1), ('node15', 0, 0, 2)], [('node16', 0, 0, 5), ('node17', 0, 1, 2), ('node18', 0, 0, 6), ('node19', 0, 0, 3)], [('node20', 0, 0, 9), ('node21', 0, 0, 7), ('node22', 0, 0, 1), ('node23', 0, 0, 8), ('node24', 0, 0, 2), ('node25', 0, 1, 7), ('node26', 0, 0, 9)], [('node27', 0, 0, 2), ('node28', 0, 1, 3), ('node29', 0, 0, 3), ('node30', 0, 0, 8)], [('node31', 0, 0, 8), ('node32', 0, 0, 10), ('node33', 0, 1, 4), ('node34', 0, 1, 2), ('node35', 0, 1, 8), ('node36', 0, 1, 4), ('node37', 0, 0, 5), ('node38', 0, 0, 9)], [('node39', 0, 0, 9), ('node40', 0, 1, 8), ('node41', 0, 1, 4)], [('node42', 0, 0, 1), ('node43', 0, 0, 1), ('node44', 0, 1, 1), ('node45', 0, 0, 2), ('node46', 0, 1, 3)]])
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print(
            "----multi-step nodes have both signal and data functions, and with waiting function"
        )
        for i in range(10):
            # feature_list = convert_to_feature_list([[('node0', 0, 0, 1), ('node1', 1, 1, 1)], [('node2', 1, 1, 7)], [('node3', 0, 1, 1), ('node4', 0, 1, 9), ('node5', 1, 1, 1)], [('node6', 1, 0, 1)], [('node7', 0, 1, 6), ('node8', 1, 1, 1)], [('node9', 0, 1, 7), ('node10', 1, 0, 1)], [('node11', 0, 0, 7), ('node12', 0, 0, 6), ('node13', 0, 0, 5)], [('node14', 0, 1, 6), ('node15', 0, 0, 1), ('node16', 0, 1, 9), ('node17', 0, 1, 10), ('node18', 0, 0, 1), ('node19', 0, 0, 1), ('node20', 0, 0, 1), ('node21', 1, 1, 1)], [('node22', 1, 0, 1)]])
            # feature_list = convert_to_feature_list([[('node0', 1, 1, 5)], [('node1', 0, 1, 5), ('node2', 1, 1, 1)], [('node3', 1, 1, 6)], [('node4', 1, 1, 9)], [('node5', 0, 1, 6), ('node6', 1, 0, 1)], [('node7', 1, 1, 6)], [('node8', 1, 1, 5)]])
            # feature_list = convert_to_feature_list([[('node0', 0, 0, 6), ('node1', 0, 1, 1), ('node2', 0, 1, 8)], [('node3', 0, 1, 1), ('node4', 0, 1, 1), ('node5', 1, 0, 6)], [('node6', 0, 1, 1), ('node7', 1, 0, 1)]])
            feature_list = generate_random_feature_list(
                has_response_func=True, multi_step=True
            )
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print("----some multi-step nodes don't have data functions")
        for i in range(10):
            # feature_list = convert_to_feature_list([[('node0', 0, 1, 1), ('multi-step1', False, 0, 6, False), 'WaitToContinue', ('multi-step2', False, 0, 8, False), 'WaitToContinue', ('node3', 0, 1, 1), ('multi-step4', False, 0, 9, False), 'WaitToContinue'], [('node5', 0, 0, 6)]])
            # feature_list = convert_to_feature_list([[('node0', 1, 1, 1)], [('node1', 0, 1, 9), ('node2', 0, 1, 1), ('node3', 0, 0, 1), ('multi-step4', False, 0, 9, False), 'WaitToContinue', ('multi-step5', False, 0, 5, False), 'WaitToContinue', ('node6', 1, 1, 1)]])
            # feature_list = convert_to_feature_list([[('multi-step0', False, 1, 9, False), 'WaitToContinue', ('multi-step1', False, 1, 8, False), 'WaitToContinue', ('multi-step2', False, 1, 7, False), 'WaitToContinue', ('multi-step3', False, 1, 7, False), 'WaitToContinue', ('multi-step4', False, 1, 7, False), 'WaitToContinue', ('node5', 1, 0, 5)], [('node6', 1, 1, 1)], [('node7', 0, 0, 1), ('node8', 0, 1, 1), ('node9', 1, 0, 1)], [('node10', 1, 1, 10)], [('multi-step11', False, 1, 6, False), 'WaitToContinue', ('node12', 1, 0, 1)], [('multi-step13', False, 1, 8, False), 'WaitToContinue', ('multi-step14', False, 1, 9, False), 'WaitToContinue', ('node15', 0, 1, 1), ('multi-step16', False, 1, 9, False), 'WaitToContinue', ('node17', 1, 0, 10)], [('multi-step18', False, 1, 9, False), 'WaitToContinue'], [('node19', 1, 1, 7)], [('node20', 1, 1, 1)]])
            feature_list = generate_random_feature_list(
                has_response_func=True, multi_step=True, with_data_func=False
            )
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print("----with loop node")
        # test case: (,)
        feature_list = [
            (
                {
                    "name": DummyFeature,
                    "args": (
                        "node0",
                        0,
                        0,
                        1,
                    ),
                },
                {"name": LoopByCount, "args": (3,)},
            )
        ]
        model.start(feature_list)
        print(model.signal_records)
        print(model.data_records)
        assert model.signal_records == model.data_records, print_feature_list(
            feature_list
        )
        assert model.signal_records == [(0, "node0"), (1, "node0"), (2, "node0")]

        # test case: random loop
        for i in range(10):
            # feature_list = [({'name': DummyFeature, 'args': ('node0', 0, 0, 1,),}, {'name': LoopByCount, 'args': (3,)}), [{'name': DummyFeature, 'args': ('node1', 0, 0, 1,),}, {'name': DummyFeature, 'args': ('node2', 0, 0, 1,),}], ({'name': DummyFeature, 'args': ('node3', 0, 0, 1,),}, {'name': LoopByCount, 'args': (3,)}), ({'name': DummyFeature, 'args': ('node4', 0, 0, 1,),}, {'name': DummyFeature, 'args': ('node5', 0, 0, 1,),}, {'name': LoopByCount, 'args': (3,)})]
            feature_list = generate_random_feature_list(
                has_response_func=True,
                multi_step=True,
                with_data_func=False,
                loop_node=True,
            )
            print_feature_list(feature_list)
            model.start(feature_list)
            print(model.signal_records)
            print(model.data_records)
            assert model.signal_records == model.data_records, print_feature_list(
                feature_list
            )

        print("----nested loop nodes")
        # test case: ((), , ), , ,
        feature_list = [
            (
                (
                    generate_random_feature_list(
                        has_response_func=True,
                        multi_step=True,
                        with_data_func=False,
                        loop_node=True,
                    ),
                    {"name": LoopByCount, "args": (3,)},
                ),
                {
                    "name": DummyFeature,
                    "args": (
                        "node100",
                        0,
                        1,
                        1,
                    ),
                },
                {"name": LoopByCount, "args": (3,)},
            ),
            {
                "name": DummyFeature,
                "args": (
                    "node101",
                    0,
                    1,
                    1,
                ),
            },
            {
                "name": DummyFeature,
                "args": (
                    "node102",
                    0,
                    1,
                    1,
                ),
            },
        ]
        model.start(feature_list)
        print(model.signal_records)
        print(model.data_records)
        assert model.signal_records == model.data_records, print_feature_list(
            feature_list
        )

        # test case: (,,(),), ,
        feature_list = [
            (
                {
                    "name": DummyFeature,
                    "args": (
                        "node200",
                        0,
                        0,
                        1,
                    ),
                },
                {
                    "name": DummyFeature,
                    "args": (
                        "node201",
                        0,
                        1,
                        1,
                    ),
                },
                (
                    generate_random_feature_list(
                        has_response_func=True,
                        multi_step=True,
                        with_data_func=False,
                        loop_node=True,
                    ),
                    {"name": LoopByCount, "args": (3,)},
                ),
                {
                    "name": DummyFeature,
                    "args": (
                        "node100",
                        0,
                        1,
                        1,
                    ),
                },
                {"name": LoopByCount, "args": (3,)},
            ),
            {
                "name": DummyFeature,
                "args": (
                    "node101",
                    0,
                    1,
                    1,
                ),
            },
            {
                "name": DummyFeature,
                "args": (
                    "node102",
                    0,
                    0,
                    1,
                ),
            },
        ]
        model.start(feature_list)
        print(model.signal_records)
        print(model.data_records)
        assert model.signal_records == model.data_records, print_feature_list(
            feature_list
        )

        # test case: (((((),),),),), ,
        feature_list = [
            (
                (
                    (
                        (
                            generate_random_feature_list(loop_node=True),
                            {"name": LoopByCount, "args": (3,)},
                        ),
                        {"name": LoopByCount, "args": (3,)},
                    ),
                    {"name": LoopByCount, "args": (3,)},
                ),
                {"name": LoopByCount, "args": (3,)},
            ),
            {
                "name": DummyFeature,
                "args": (
                    "node101",
                    0,
                    1,
                    1,
                ),
            },
            {
                "name": DummyFeature,
                "args": (
                    "node102",
                    0,
                    0,
                    1,
                ),
            },
        ]
        model.start(feature_list)
        print(model.signal_records)
        print(model.data_records)
        assert model.signal_records == model.data_records, print_feature_list(
            feature_list
        )

        # test case: (,(,(,(,(),),),),), ,
        feature_list = [
            {
                "name": DummyFeature,
                "args": (
                    "node200",
                    0,
                    0,
                    1,
                ),
            },
            (
                {
                    "name": DummyFeature,
                    "args": (
                        "node300",
                        0,
                        0,
                        1,
                    ),
                },
                (
                    {
                        "name": DummyFeature,
                        "args": (
                            "node400",
                            0,
                            0,
                            1,
                        ),
                    },
                    (
                        {
                            "name": DummyFeature,
                            "args": (
                                "node500",
                                0,
                                0,
                                1,
                            ),
                        },
                        (
                            generate_random_feature_list(loop_node=True),
                            {"name": LoopByCount, "args": (3,)},
                        ),
                        {"name": LoopByCount, "args": (3,)},
                    ),
                    {"name": LoopByCount, "args": (3,)},
                ),
                {"name": LoopByCount, "args": (3,)},
            ),
            {
                "name": DummyFeature,
                "args": (
                    "node101",
                    0,
                    1,
                    1,
                ),
            },
            {
                "name": DummyFeature,
                "args": (
                    "node102",
                    0,
                    0,
                    1,
                ),
            },
        ]
        model.start(feature_list)
        print(model.signal_records)
        print(model.data_records)
        assert model.signal_records == model.data_records, print_feature_list(
            feature_list
        )

    def test_load_feature(self):
        def check(tnode1, tnode2):
            if tnode1 is None and tnode2 is None:
                return True
            if tnode1 is None or tnode2 is None:
                return False
            return tnode1.node_name == tnode2.node_name

        def is_isomorphic(tree1, tree2):
            p, q = tree1, tree2
            stack = []
            visited = {}
            while p or q or stack:
                if not check(p, q):
                    return False
                if p is None:
                    p, q = stack.pop()
                elif p.node_name not in visited:
                    visited[p.node_name] = True
                    stack.append((p.sibling, q.sibling))
                    p, q = p.child, q.child
                else:
                    p, q = None, None
            return True

        # generates 10 random feature lists and verify whether they are loaded correctly
        for i in range(10):
            feature_list = generate_random_feature_list(loop_node=True)
            signal_container, data_container = load_features(self, feature_list)
            assert is_isomorphic(signal_container.root, data_container.root)
            print("-", i, "random feature list is correct!")

    def test_signal_node(self):
        feature = DummyFeature()
        func_dict = {
            "init": feature.init_func,
            "main": feature.main_func,
            "end": feature.end_func,
        }

        print("without waiting for a response:")
        node = SignalNode("test_1", func_dict)
        assert node.need_response == False
        assert node.node_funcs["end"]() == False

        feature.is_end = True
        assert node.node_funcs["end"]() == True

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

        print("--running with waiting option")
        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == True
        assert node.is_initialized == False
        assert node.wait_response == False
        assert feature.running_times_main_func == 1
        assert feature.init_times == 1

        print("--device related")
        feature.clear()
        node = SignalNode("test_1", func_dict, device_related=True)
        print(node.node_type)
        assert node.need_response == False
        result, is_end = node.run()
        assert is_end == True
        assert node.wait_response == False
        assert feature.running_times_main_func == 1

        print("----running with waitint option")
        feature.clear()
        result, is_end = node.run(wait_response=True)
        assert is_end == False
        assert node.wait_response == False
        assert feature.running_times_main_func == 0
        assert node.is_initialized == True

        print("----multi-step function")
        feature.clear()
        node = SignalNode(
            "test_1", func_dict, device_related=True, node_type="multi-step"
        )
        # node.node_type = "multi-step"
        func_dict["main-response"] = dummy_True
        # assert func_dict.get("main-response", None) == None
        assert node.need_response == True
        steps = 5
        for i in range(steps + 1):
            feature.is_end = i == steps
            if i == 0:
                assert node.is_initialized == False
            else:
                assert node.is_initialized == True
            result, is_end = node.run()
            if i <= steps:
                assert node.is_initialized == True
                assert is_end == False
            assert feature.running_times_main_func == i + 1
            assert node.wait_response == True
            result, is_end = node.run(wait_response=True)
            if i < steps:
                assert is_end == False
            else:
                assert is_end == True

        print("--multi-step function")
        feature.clear()
        node = SignalNode(
            "test_1", func_dict, node_type="multi-step", device_related=True
        )
        # assert func_dict.get("main-response") == None
        assert node.need_response == True
        assert node.device_related == True
        steps = 5
        for i in range(steps + 1):
            feature.is_end = i == steps
            result, is_end = node.run()
            if i < steps:
                assert is_end == False
            assert is_end == False
            assert feature.running_times_main_func == i + 1
            assert node.is_initialized == True
            assert node.wait_response == True
            result, is_end = node.run(wait_response=True)
        assert node.wait_response == False
        assert node.is_initialized == False

        print("wait for a response:")
        feature.clear()
        func_dict["main-response"] = feature.response_func
        node = SignalNode("test_2", func_dict, need_response=True)
        assert node.need_response == True
        assert node.wait_response == False

        print("--running without waiting option")
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

        print("--running with waiting option")
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

        print("----device related")
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

        print("--multi-step function")
        feature.clear()
        node = SignalNode("test", func_dict, node_type="multi-step", need_response=True)
        steps = 5
        for i in range(steps + 1):
            feature.is_end = i == steps
            result, is_end = node.run()
            assert is_end == False
            assert feature.running_times_main_func == i + 1
            assert node.is_initialized == True
            result, is_end = node.run(wait_response=True)
            if i < steps:
                assert is_end == False
            else:
                assert is_end == True
            assert feature.running_times_response_func == i + 1
            assert node.wait_response == False

    def test_node_cleanup(self):
        def wrap_error_func(func):
            def temp_func(raise_error=False):
                if raise_error:
                    raise Exception
                func()

            return temp_func

        feature = DummyFeature()
        func_dict = {
            "init": feature.init_func,
            "pre-main": dummy_True,
            "main": wrap_error_func(feature.main_func),
            "end": feature.end_func,
        }
        # one-step node without response
        print("- one-step node without response")
        node = DataNode("cleanup_node", func_dict)
        data_container = DataContainer(node)
        assert data_container.root == node
        data_container.run()
        assert feature.running_times_main_func == 1, feature.running_times_main_func
        assert data_container.end_flag == True
        data_container.reset()
        data_container.run(True)
        assert node.is_marked == True
        assert feature.running_times_main_func == 1, feature.running_times_main_func

        feature.clear()
        data_container.reset()
        func_dict["cleanup"] = feature.close
        node = DataNode("cleanup_node", func_dict)
        data_container = DataContainer(node)
        data_container.run()
        data_container.reset()
        data_container.run(True)
        assert feature.is_closed == True
        assert node.is_marked == True
        assert feature.running_times_main_func == 1
        data_container.run()
        assert feature.running_times_main_func == 1

        # node with response
        print("- node with response")
        feature.clear()
        node = DataNode("cleanup_node", func_dict, need_response=True)
        data_container = DataContainer(node, [node])
        assert data_container.root == node
        data_container.run()
        assert feature.running_times_main_func == 1, feature.running_times_main_func
        data_container.reset()
        data_container.run(True)
        assert feature.running_times_cleanup_func == 1
        assert feature.is_closed == True
        assert node.is_marked == False
        assert feature.running_times_main_func == 1
        assert data_container.end_flag == True
        data_container.run()
        assert feature.running_times_main_func == 1

        # multiple nodes
        print("- multiple nodes")
        feature.clear()
        node1 = DataNode("cleanup_node1", func_dict)
        node2 = DataNode("cleanup_node2", func_dict, device_related=True)
        node3 = DataNode(
            "cleanup_node3", func_dict, need_response=True, device_related=True
        )
        node1.sibling = node2
        node2.sibling = node3
        cleanup_list = [node1, node2, node3]
        data_container = DataContainer(node1, cleanup_list)
        assert data_container.root == node1
        assert feature.running_times_main_func == 0

        for i in range(1, 4):
            data_container.run()
            assert feature.running_times_main_func == i, feature.running_times_main_func
        # mark a single node
        data_container.reset()
        data_container.run(True)
        assert feature.is_closed == True
        assert feature.running_times_cleanup_func == 1
        feature.is_closed = False
        assert node1.is_marked == True
        assert feature.running_times_main_func == 3
        assert data_container.end_flag == False
        data_container.run()
        assert feature.running_times_main_func == 4
        assert node2.is_marked == False
        data_container.run()
        assert feature.running_times_main_func == 5
        assert node3.is_marked == False
        # run node1 which is marked
        data_container.reset()
        data_container.run()
        assert feature.running_times_main_func == 5
        # run node2
        data_container.run()
        assert feature.running_times_main_func == 6
        assert node2.is_marked == False
        # run node3 and clean up all nodes
        data_container.run(True)
        assert feature.running_times_cleanup_func == 4
        assert feature.running_times_main_func == 6
        assert data_container.end_flag == True


if __name__ == "__main__":
    unittest.main()
