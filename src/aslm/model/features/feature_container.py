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

import logging

p = __name__.split(".")[1]

logger = logging.getLogger(p)

class TreeNode:
    def __init__(self, feature_name, func_dict, *, node_type='one-step', device_related=False, need_response=False):
        self.node_name = str(feature_name)
        self.node_funcs = func_dict
        self.node_type = node_type # 'one-step', 'multi-step'
        self.device_related = device_related
        self.need_response = need_response # True, False
        self.is_initialized = False
        self.child = None
        self.sibling = None

    def set_property(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

class SignalNode(TreeNode):
    def __init__(self, feature_name, func_dict, *, node_type='one-step', device_related=False, need_response=False, **kwargs):
        super().__init__(feature_name, func_dict, node_type=node_type, device_related=device_related, need_response=need_response)
        self.wait_response = False

    def run(self, *args, wait_response=False):
        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs['init']()
            self.is_initialized = True

        if not wait_response:
            # print(self.node_name, 'running function:', self.node_funcs['main'])
            result = self.node_funcs['main'](*args)
            if self.need_response:
                self.wait_response = True
                return result, False

        elif self.wait_response:
            # print(self.node_name, 'running response function:', self.node_funcs['main-response'])
            result = self.node_funcs['main-response'](*args)
            self.wait_response = False
        elif self.device_related or self.need_response:
            return None, False
        else:
            # run(wait_response=True)
            result = self.node_funcs['main'](*args)

        if self.wait_response or self.node_type == 'multi-step' and not self.node_funcs['end']():
            return result, False
        
        self.is_initialized = False
        return result, True

class DataNode(TreeNode):
    def __init__(self, feature_name, func_dict, *, node_type='one-step', device_related=False, need_response=False, **kwargs):
        super().__init__(feature_name, func_dict, node_type=node_type, device_related=device_related, need_response=need_response)
        self.is_marked = False

    def run(self, *args):
        if self.is_marked:
            return None, True

        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs['init']()
            self.is_initialized = True

        # to decide whether it is the target frame
        if not self.node_funcs['pre-main'](*args):
            return False, False

        result = self.node_funcs['main'](*args)

        if self.node_type == 'multi-step' and not self.node_funcs['end']():
            return result, False

        # erase flag when exit the node
        self.is_initialized = False
        return result, True


class Container:
    def __init__(self, root=None, cleanup_list=[]):
        self.root = root # root node of the tree
        self.curr_node = None # current running node
        self.end_flag = False # stop running flag
        self.cleanup_list = cleanup_list # a list of nodes containing 'cleanup' functions.
        self.is_closed = False

    def reset(self):
        self.curr_node = None
        self.end_flag = False

    def cleanup(self):
        for node in self.cleanup_list:
            try:
                node.node_funcs['cleanup']()
            except:
                pass
        self.is_closed = True


class SignalContainer(Container):
    def __init__(self, root=None, cleanup_list=[], number_of_execution=1):
        super().__init__(root, cleanup_list)
        self.number_of_execution = number_of_execution
        self.remaining_number_of_execution = number_of_execution

    def reset(self):
        super().reset()
        self.remaining_number_of_execution = self.number_of_execution

    def run(self, *args, wait_response=False):
        if self.end_flag or not self.root:
            self.end_flag = True
            return
        if not self.curr_node:
            self.curr_node = self.root
        while self.curr_node:
            logger.debug(f'running signal node: {self.curr_node.node_name}')
            try:
                result, is_end = self.curr_node.run(*args, wait_response=wait_response)
            except Exception as e:
                logger.debug(f'SignalContainer - {e}')
                self.end_flag = True
                self.cleanup()
                return
            if not is_end:
                return
            if self.curr_node.sibling:
                self.curr_node = self.curr_node.sibling
            elif result and self.curr_node.child:
                logger.debug(f'Signal running child of {self.curr_node.node_name}')
                self.curr_node = self.curr_node.child
            else:
                self.curr_node = None
                if self.remaining_number_of_execution > 0:
                    self.remaining_number_of_execution -= 1
                    self.end_flag = (self.remaining_number_of_execution == 0)
                return
            
            if self.curr_node.device_related:
                return       


class DataContainer(Container):
    def __init__(self, root=None, cleanup_list=[]):
        super().__init__(root, cleanup_list)
        self.returned_a_response = False

    def run(self, *args):
        if self.end_flag or not self.root:
            return
        if not self.curr_node:
            self.curr_node = self.root
        self.returned_a_response = False
        while self.curr_node:
            try:
                result, is_end = self.curr_node.run(*args)
            except Exception as e:
                logger.debug(f'DataContainer - {e}')
                if self.curr_node.need_response == False and self.curr_node.node_type == 'one-step':
                    try:
                        self.curr_node.node_funcs.get('cleanup', dummy_func)()
                    except:
                        logger.debug(f'The node({self.curr_node.node_name}) is not closed correctly! Please check the cleanup function')
                        pass
                    self.curr_node.is_marked = True
                    result, is_end = False, True
                else:
                    # terminate the container.
                    # the signal container may stuck there waiting a response, 
                    # the cleanup function of that node should give it a fake response to make it stop
                    self.end_flag = True
                    self.cleanup()
                    return
            # print('Data running node:', self.curr_node.node_name, 'get result:', result)
            if not is_end:
                return
            if self.curr_node.need_response:
                self.returned_a_response = True
            if self.curr_node.sibling:
                self.curr_node = self.curr_node.sibling
            elif result and self.curr_node.child:
                # print('Data running child of', self.curr_node.node_name)
                self.curr_node = self.curr_node.child
            else:
                self.curr_node = None
                return

            if self.curr_node.device_related or (self.curr_node.need_response and self.returned_a_response):
                return


def get_registered_funcs(feature_module, func_type='signal'):
    func_dict = feature_module.config_table.get(func_type, {})
    
    if 'init' not in func_dict:
        func_dict['init'] = dummy_func
    if 'main' not in func_dict:
        func_dict['main'] = dummy_True
    if 'end' not in func_dict:
        func_dict['end'] = dummy_True
    if func_type == 'data' and 'pre-main' not in func_dict:
        func_dict['pre-main'] = dummy_True
    return func_dict

def load_features(model, feature_list):
    """ turn list to child-sibling tree"""
    signal_cleanup_list, data_cleanup_list = [], []
    signal_root, data_root = TreeNode('none', None), TreeNode('none', None)
    pre_signal = signal_root
    pre_data = data_root
    for temp in feature_list:
        for i in range(len(temp)):
            args = ()
            if 'args' in temp[i]:
                args = temp[i]['args']
            feature = temp[i]['name'](model, *args)

            node_config = feature.config_table.get('node', {})
            # if signal function has a waiting func, then the nodes are 'need_response' nodes
            if 'main-response' in feature.config_table.get('signal', {}):
                node_config['need_response'] = True
            if 'node' in temp[i]:
                for k, v in temp[i]['node'].items():
                    node_config[k] = v
            # 'multi-step' must set to be 'device_related'
            if node_config.get('node_type', '') == 'multi-step':
                node_config['device_related'] = True

            signal_node = SignalNode(temp[i]['name'].__name__, get_registered_funcs(feature, 'signal'), **node_config)
            data_node = DataNode(temp[i]['name'].__name__, get_registered_funcs(feature, 'data'), **node_config)

            if 'cleanup' in feature.config_table.get('signal', {}):
                signal_cleanup_list.append(signal_node)
            if 'cleanup' in feature.config_table.get('data', {}):
                data_cleanup_list.append(data_node)

            if i == 0:
                pre_signal.child = signal_node
                pre_data.child = data_node
            else:
                pre_signal.sibling = signal_node
                pre_data.sibling = data_node
            pre_signal = signal_node
            pre_data = data_node

    return SignalContainer(signal_root.child, signal_cleanup_list), DataContainer(data_root.child, data_cleanup_list)


def dummy_True(*args):
    return True

def dummy_func(*args):
    pass