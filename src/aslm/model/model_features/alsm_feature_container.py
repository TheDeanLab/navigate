"""
ASLM Model.

Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

class TreeNode:
    def __init__(self, feature_name, func_dict, *, node_type='one-step', wait_next=False):
        self.node_name = str(feature_name)
        self.node_funcs = func_dict
        self.node_type = node_type # 'one-step', 'multi-step'
        self.wait_next = wait_next
        self.is_initialized = False
        self.child = None
        self.sibling = None

    def set_property(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

class SignalNode(TreeNode):
    def __init__(self, feature_name, func_dict, *, node_type='one-step', wait_next=False, device_related=False):
        super().__init__(feature_name, func_dict, node_type=node_type, wait_next=wait_next)
        self.has_response_func = func_dict.get('main-response', None)
        self.wait_response = False
        self.device_related = device_related

    def run(self, *args, wait_response=False):
        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs['init']()
            self.is_initialized = True

        if not wait_response:
            # print(self.node_name, 'running function:', self.node_funcs['main'])
            result = self.node_funcs['main'](*args)
            if self.has_response_func:
                self.wait_response = True
                return result, False

        elif self.wait_response:
            # print(self.node_name, 'running response function:', self.node_funcs['main-response'])
            result = self.node_funcs['main-response'](*args)
            self.wait_response = False
        elif self.device_related:
            return None, False
        else:
            result = self.node_funcs['main'](*args)
            if self.has_response_func:
                result = self.node_funcs['main-response'](*args)

        if self.node_type == 'multi-step' and not self.node_funcs['end']():
            return result, False
        
        self.is_initialized = False
        return result, True

class DataNode(TreeNode):
    def __init__(self, feature_name, func_dict, *, node_type='one-step', wait_next=False):
        super().__init__(feature_name, func_dict, node_type=node_type, wait_next=wait_next)

    def run(self, *args):
        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs['init']()
            self.is_initialized = True

        result = self.node_funcs['main'](*args)

        if self.node_type == 'multi-step' and not self.node_funcs['end']():
            return result, False

        # erase flag when exit the node
        self.is_initialized = False
        return result, True


class Container:
    def __init__(self, root=None):
        self.root = root # root node of the tree
        self.curr_node = None # current running node
        self.end_flag = False # stop running flag

    def reset(self):
        self.curr_node = None
        self.end_flag = False


class SignalContainer(Container):
    def __init__(self, root=None, number_of_execution=1):
        super().__init__(root)
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
            print('running signal node:', self.curr_node.node_name)
            result, is_end = self.curr_node.run(*args, wait_response=wait_response)
            if not is_end:
                return
            if not self.curr_node.sibling:
                break
            self.curr_node = self.curr_node.sibling
            if self.curr_node.wait_next:
                return

        if result and self.curr_node.child:
            print('Signal running child of', self.curr_node.node_name)
            self.curr_node = self.curr_node.child
            if not self.curr_node.wait_next:
                self.run(*args)
        else:
            self.curr_node = None
            if self.remaining_number_of_execution > 0:
                self.remaining_number_of_execution -= 1
                self.end_flag = (self.remaining_number_of_execution == 0)


class DataContainer(Container):
    def __init__(self, root=None):
        super().__init__(root)

    def run(self, *args):
        if self.end_flag or not self.root:
            return
        if not self.curr_node:
            self.curr_node = self.root
        while self.curr_node:
            result, is_end = self.curr_node.run(*args)
            print('Data running node:', self.curr_node.node_name, 'get result:', result)
            if not is_end:
                return
            if not self.curr_node.sibling:
                break
            self.curr_node = self.curr_node.sibling
            if self.curr_node.wait_next:
                return

        if result and self.curr_node.child:
            print('Data running child of', self.curr_node.node_name)
            self.curr_node = self.curr_node.child
            if not self.curr_node.wait_next:
                self.run(*args)
        else:
            self.curr_node = None


def get_registered_funcs(feature_module, func_type='signal'):
    func_dict = feature_module.config_table[func_type]
    if 'init' not in func_dict:
        func_dict['init'] = dummy_func
    if 'main' not in func_dict:
        func_dict['main'] = feature_module.generate_meta_data
    if 'end' not in func_dict:
        func_dict['end'] = dummy_True
    return func_dict

def load_features(model, feature_list):
    """ turn list to child-sibling tree"""
    signal_root, data_root = TreeNode('none', None), TreeNode('none', None)
    pre_signal = signal_root
    pre_data = data_root
    for temp in feature_list:
        for i in range(len(temp)):
            args = ()
            if 'args' in temp[i]:
                args = temp[i]['args']
            feature = temp[i]['name'](model, *args)
            signal_node = SignalNode(temp[i]['name'].__name__, get_registered_funcs(feature, 'signal'))
            data_node = DataNode(temp[i]['name'].__name__, get_registered_funcs(feature, 'data'))
            if 'node' in feature.config_table:
                signal_node.set_property(**feature.config_table['node'])
                data_node.set_property(**feature.config_table['node'])
            if i == 0:
                pre_signal.child = signal_node
                pre_data.child = data_node
            else:
                pre_signal.sibling = signal_node
                pre_data.sibling = data_node
            pre_signal = signal_node
            pre_data = data_node
            
    return SignalContainer(signal_root.child), DataContainer(data_root.child)


def dummy_True():
    return True

def dummy_func(*args):
    pass