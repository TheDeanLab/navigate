# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted for academic and research use only (subject to the
# limitations in the disclaimer below) provided that the following conditions are met:

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

# Standard Library Imports
import logging
import traceback

# Third Party Imports

# Local Imports

p = __name__.split(".")[1]

logger = logging.getLogger(p)


class TreeNode:
    """
    TreeNode class for representing a node in a control sequence tree.

    This class represents a node in a control sequence tree used for controlling the
    behavior of a microscope or similar device. Each node has a name, associated
    functions, and properties that define its behavior in the control sequence.

    Parameters:
    ----------
    feature_name : str
        The name or identifier of the feature associated with this node.

    func_dict : dict
        A dictionary containing functions associated with this node. The dictionary
        should include keys for different signals or events and corresponding function
        references to be executed when those signals are received.

    node_type : str, optional
        The type of the node, which can be 'one-step' or 'multi-step'. Default is
        'one-step'.

    device_related : bool, optional
        A boolean indicating whether the node is related to device control. Default
        is False.

    need_response : bool, optional
        A boolean indicating whether a response is needed from this node. Default is
        False.

    Attributes:
    ----------
    node_name : str
        The name or identifier of the feature associated with this node.

    node_funcs : dict
        A dictionary containing functions associated with this node.

    node_type : str
        The type of the node, which can be 'one-step' or 'multi-step'.

    device_related : bool
        A boolean indicating whether the node is related to device control.

    need_response : bool
        A boolean indicating whether a response is needed from this node.

    is_initialized : bool
        A boolean indicating whether the node has been initialized.

    child : TreeNode or None
        A reference to the child node if one exists, otherwise None.

    sibling : TreeNode or None
        A reference to the sibling node if one exists, otherwise None.

    Methods:
    --------
    set_property(**kwargs):
        Set the properties of the TreeNode object using keyword arguments.

    Notes:
    ------
    - This class is used to represent nodes in a control sequence tree where each node
      corresponds to a feature or action in the control sequence.

    - The `node_funcs` attribute contains a dictionary of functions associated with this
      node, which are executed in response to specific signals or events.

    - The `node_type` attribute specifies whether the node is a 'one-step' node or a
      'multi-step' node.

    - The `device_related` attribute indicates whether the node is related to device
      control.

    - The `need_response` attribute indicates whether a response is expected from this
      node when it is executed.
    """

    def __init__(
        self,
        feature_name,
        func_dict,
        *,
        node_type="one-step",
        device_related=False,
        need_response=False,
    ):
        self.node_name = str(feature_name)
        self.node_funcs = func_dict
        self.node_type = node_type  # 'one-step', 'multi-step'
        self.device_related = device_related
        self.need_response = need_response  # True, False
        self.is_initialized = False
        self.child = None
        self.sibling = None

    def set_property(self, **kwargs):
        """
        Set the properties of the TreeNode object using keyword arguments.

        This method allows setting or updating the properties of the TreeNode object
        using keyword arguments. The method iterates through the provided keyword-
        argument pairs and updates the corresponding attributes of the TreeNode
        object.

        Parameters:
        ----------
        **kwargs : dict
            Keyword arguments with attribute names as keys and values to set as
            values.

        Returns:
        -------
        None
        """

        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])


class SignalNode(TreeNode):
    """
    SignalNode class for representing a signal-processing node in a control sequence
    tree.

    This class represents a signal-processing node in a control sequence tree used for
    controlling the behavior of a microscope or similar device. It inherits from the
    TreeNode class and adds signal processing capabilities.

    Parameters:
    ----------
    feature_name : str
        The name or identifier of the feature associated with this node.

    func_dict : dict
        A dictionary containing functions associated with this node. The dictionary
        should include keys for different signals or events and corresponding function
        references to be executed when those signals are received.

    node_type : str, optional
        The type of the node, which can be 'one-step' or 'multi-step'. Default is
        'one-step'.

    device_related : bool, optional
        A boolean indicating whether the node is related to device control. Default
        is False.

    need_response : bool, optional
        A boolean indicating whether a response is needed from this node. Default is
        False.

    wait_response : bool, optional
        A boolean indicating whether the node is currently waiting for a response.
        Default is False.

    Attributes:
    ----------
    node_name : str
        The name or identifier of the feature associated with this node.

    node_funcs : dict
        A dictionary containing functions associated with this node.

    node_type : str
        The type of the node, which can be 'one-step' or 'multi-step'.

    device_related : bool
        A boolean indicating whether the node is related to device control.

    need_response : bool
        A boolean indicating whether a response is needed from this node.

    wait_response : bool
        A boolean indicating whether the node is currently waiting for a response.

    is_initialized : bool
        A boolean indicating whether the node has been initialized.

    child : TreeNode or None
        A reference to the child node if one exists, otherwise None.

    sibling : TreeNode or None
        A reference to the sibling node if one exists, otherwise None.

    Methods:
    --------
    run(*args, wait_response=False):
        Execute the main function associated with this node and handle response.

    Notes:
    ------
    - This class is used to represent signal-processing nodes in a control sequence
      tree where each node corresponds to a feature or action in the control sequence.

    - The `node_funcs` attribute contains a dictionary of functions associated with this
      node, which are executed in response to specific signals or events.

    - The `node_type` attribute specifies whether the node is a 'one-step' node or a
      'multi-step' node.

    - The `device_related` attribute indicates whether the node is related to device
      control.

    - The `need_response` attribute indicates whether a response is expected from this
      node when it is executed.

    - The `wait_response` attribute indicates whether the node is currently waiting for
      a response, typically set to True after running the `main` function and before
      running the `main-response` function when `need_response` is True.
    """

    def __init__(
        self,
        feature_name,
        func_dict,
        *,
        node_type="one-step",
        device_related=False,
        need_response=False,
        **kwargs,
    ):
        super().__init__(
            feature_name,
            func_dict,
            node_type=node_type,
            device_related=device_related,
            need_response=need_response,
        )
        self.wait_response = False
        if self.device_related and self.node_type == "multi-step":
            self.need_response = True

    def run(self, *args, wait_response=False):
        """
        Execute the main function associated with this node and handle response.

        This method is used to execute the main function associated with this node and
        handle response logic based on the node's properties. It can be used with or
        without waiting for a response.

        Parameters:
        ----------
        *args : any
            Additional arguments to pass to the main function.

        wait_response : bool, optional
            A boolean indicating whether to wait for a response from this node. Default
            is False.

        Returns:
        -------
        tuple
            A tuple containing the result of executing the main function and a boolean
            indicating whether the node execution is complete (True if complete,
            otherwise False).
        """

        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs["init"]()
            self.is_initialized = True

        if not wait_response:
            # print(self.node_name, 'running function:', self.node_funcs['main'])
            result = self.node_funcs["main"](*args)
            if self.need_response:
                self.wait_response = True
                return result, False

        elif self.wait_response:
            # print(self.node_name, 'running response function:',
            #       self.node_funcs['main-response'])
            result = self.node_funcs["main-response"](*args)
            self.wait_response = False
        elif self.device_related or self.need_response:
            return None, False
        else:
            # run(wait_response=True)
            result = self.node_funcs["main"](*args)

        if (
            self.wait_response
            or self.node_type == "multi-step"
            and not self.node_funcs["end"]()
        ):
            return result, False

        self.is_initialized = False
        return result, True


class DataNode(TreeNode):
    """
    DataNode class for representing a data-processing node in a control sequence tree.

    This class represents a data-processing node in a control sequence tree used for
    controlling the behavior of a microscope or similar device. It inherits from the
    TreeNode class and adds data processing capabilities.

    Parameters:
    ----------
    feature_name : str
        The name or identifier of the feature associated with this node.

    func_dict : dict
        A dictionary containing functions associated with this node. The dictionary
        should include keys for different data processing steps and corresponding
        function references to be executed during those steps.

    node_type : str, optional
        The type of the node, which can be 'one-step' or 'multi-step'. Default is
        'one-step'.

    device_related : bool, optional
        A boolean indicating whether the node is related to device control. Default
        is False.

    need_response : bool, optional
        A boolean indicating whether a response is needed from this node. Default is
        False.

    is_marked : bool, optional
        A boolean indicating whether the node is marked. Default is False.

    Attributes:
    ----------
    node_name : str
        The name or identifier of the feature associated with this node.

    node_funcs : dict
        A dictionary containing functions associated with this node.

    node_type : str
        The type of the node, which can be 'one-step' or 'multi-step'.

    device_related : bool
        A boolean indicating whether the node is related to device control.

    need_response : bool
        A boolean indicating whether a response is needed from this node.

    is_initialized : bool
        A boolean indicating whether the node has been initialized.

    is_marked : bool
        A boolean indicating whether the node is marked.

    child : TreeNode or None
        A reference to the child node if one exists, otherwise None.

    sibling : TreeNode or None
        A reference to the sibling node if one exists, otherwise None.

    Methods:
    --------
    run(*args):
        Execute the data processing functions associated with this node.

    Notes:
    ------
    - This class is used to represent data-processing nodes in a control sequence tree
      where each node corresponds to a data processing step in the control sequence.

    - The `node_funcs` attribute contains a dictionary of functions associated with this
      node, which are executed during different data processing steps.

    - The `node_type` attribute specifies whether the node is a 'one-step' node or a
      'multi-step' node.

    - The `device_related` attribute indicates whether the node is related to device
      control.

    - The `need_response` attribute indicates whether a response is expected from this
      node when it is executed.

    - The `is_marked` attribute can be used to mark the node for special handling or
      to indicate its status.
    """

    def __init__(
        self,
        feature_name,
        func_dict,
        *,
        node_type="one-step",
        device_related=False,
        need_response=False,
        **kwargs,
    ):
        super().__init__(
            feature_name,
            func_dict,
            node_type=node_type,
            device_related=device_related,
            need_response=need_response,
        )
        self.is_marked = False

    def run(self, *args):
        """
        Execute the data processing functions associated with this node.

        This method is used to execute the data processing functions associated with
        this node during the control sequence. It initializes the node if not already
        initialized and determines whether the current frame meets the criteria to
        execute the main data processing function.

        Parameters:
        ----------
        *args : any
            Additional arguments to pass to the data processing functions.

        Returns:
        -------
        tuple
            A tuple containing the result of executing the main data processing
            function and a boolean indicating whether the node execution is complete
            (True if complete, otherwise False).
        """

        if self.is_marked:
            return None, True

        # initialize the node when first time entering it
        if not self.is_initialized:
            self.node_funcs["init"]()
            self.is_initialized = True

        # to decide whether it is the target frame
        if not self.node_funcs["pre-main"](*args):
            return False, False

        result = self.node_funcs["main"](*args)

        if self.node_type == "multi-step" and not self.node_funcs["end"]():
            return result, False

        # erase flag when exit the node
        self.is_initialized = False
        return result, True


class Container:
    """
    Container class for managing a control sequence tree.

    This class is responsible for managing a control sequence tree, which consists of
    nodes representing different actions or steps in the control sequence. It provides
    methods for resetting the tree and performing cleanup operations on specified nodes.

    Parameters:
    ----------
    root : TreeNode or None, optional
        The root node of the control sequence tree. Default is None.

    cleanup_list : list of TreeNode, optional
        A list of nodes containing 'cleanup' functions to be executed when the
        container is closed. Default is an empty list.

    Attributes:
    ----------
    root : TreeNode or None
        The root node of the control sequence tree.

    curr_node : TreeNode or None
        The currently running node in the tree.

    end_flag : bool
        A flag indicating whether the control sequence execution should stop.

    cleanup_list : list of TreeNode
        A list of nodes containing 'cleanup' functions to be executed when the
        container is closed.

    is_closed : bool
        A boolean indicating whether the container is closed.

    Methods:
    --------
    reset():
        Reset the container's state, including the current node and end flag.

    cleanup():
        Execute 'cleanup' functions for specified nodes in the tree.

    Notes:
    ------
    - The `Container` class is used to manage the execution of a control sequence
      tree. It maintains the state of the control sequence and provides methods
      for resetting the state and performing cleanup operations.

    - The `root` attribute represents the root node of the control sequence tree,
      which serves as the entry point for executing the control sequence.

    - The `curr_node` attribute tracks the currently running node in the control
      sequence.

    - The `end_flag` attribute is used to signal the termination of control sequence
      execution.

    - The `cleanup_list` attribute is a list of nodes that contain 'cleanup'
      functions. These functions are executed when the container is closed, allowing
      for resource cleanup.

    - The `is_closed` attribute indicates whether the container has been closed or not.
    """

    def __init__(self, root=None, cleanup_list=[]):
        self.root = root  # root node of the tree
        self.curr_node = None  # current running node
        self.end_flag = False  # stop running flag
        self.cleanup_list = (
            cleanup_list  # a list of nodes containing 'cleanup' functions.
        )
        self.is_closed = False

    def reset(self):
        """
        Reset the container's state, including the current node and end flag.

        This method resets the state of the container, including setting the current
        node to None and clearing the end flag. It prepares the container for running
        the control sequence from the beginning.
        """

        self.curr_node = None
        self.end_flag = False

    def cleanup(self):
        """
        Execute 'cleanup' functions for specified nodes in the tree.

        This method executes the 'cleanup' functions associated with nodes in the
        `cleanup_list`. These functions are typically used to perform resource
        cleanup or finalization when the container is closed. The 'cleanup_list'
        specifies which nodes should have their 'cleanup' functions executed.
        """

        for node in self.cleanup_list:
            try:
                node.node_funcs["cleanup"]()
            except Exception:
                pass
        self.is_closed = True


class SignalContainer(Container):
    """
    SignalContainer class for managing signal-based control sequences.

    This class is a specialized container for managing control sequences that consist
    of signal-based nodes. It extends the functionality of the base `Container` class
    and provides methods for running signal-based control sequences.

    Parameters:
    ----------
    root : TreeNode or None, optional
        The root node of the control sequence tree. Default is None.

    cleanup_list : list of TreeNode, optional
        A list of nodes containing 'cleanup' functions to be executed when the
        container is closed. Default is an empty list.

    number_of_execution : int, optional
        The number of times the control sequence should be executed. Default is 1.

    Attributes:
    ----------
    root : TreeNode or None
        The root node of the control sequence tree.

    curr_node : TreeNode or None
        The currently running node in the control sequence.

    end_flag : bool
        A flag indicating whether the control sequence execution should stop.

    cleanup_list : list of TreeNode
        A list of nodes containing 'cleanup' functions to be executed when the
        container is closed.

    is_closed : bool
        A boolean indicating whether the container is closed.

    number_of_execution : int
        The total number of times the control sequence should be executed.

    remaining_number_of_execution : int
        The remaining number of executions of the control sequence.

    Methods:
    --------
    reset():
        Reset the container's state, including the current node and end flag.

    run(*args, wait_response=False):
        Run the signal-based control sequence.

    Notes:
    ------
    - The `SignalContainer` class is designed for managing control sequences that are
      signal-based, typically used in applications involving devices and sensors.

    - It extends the functionality of the base `Container` class and provides methods
      for running signal-based control sequences.

    - The `number_of_execution` parameter specifies how many times the control
      sequence should be executed. The `remaining_number_of_execution` attribute keeps
      track of the remaining executions.
    """

    def __init__(self, root=None, cleanup_list=[], number_of_execution=1):
        super().__init__(root, cleanup_list)
        self.number_of_execution = number_of_execution
        self.remaining_number_of_execution = number_of_execution

    def reset(self):
        """
        Reset the container's state, including the current node and end flag.

        This method resets the state of the container, including setting the current
        node to None, clearing the end flag, and resetting the remaining number of
        executions. It prepares the container for running the control sequence from
        the beginning.
        """

        super().reset()
        self.remaining_number_of_execution = self.number_of_execution

    def run(self, *args, wait_response=False):
        """
        Run the signal-based control sequence.

        This method runs the signal-based control sequence by iterating through its
        nodes and executing them in order. It manages the execution of nodes and
        handles transitions between nodes based on their logic.

        Parameters:
        -----------
        *args : arguments
            Optional arguments to pass to the control sequence nodes.

        wait_response : bool, optional
            A flag indicating whether to wait for responses during execution.
            Default is False.

        Notes:
        ------
        - The `run` method is responsible for executing the control sequence nodes in
          the order defined by the control sequence tree.

        - It handles transitions between nodes, waits for responses if necessary, and
          tracks the remaining executions of the control sequence.
        """

        if self.end_flag or not self.root:
            self.end_flag = True
            return
        if not self.curr_node:
            self.curr_node = self.root
        while self.curr_node:
            logger.debug(f"running signal node: {self.curr_node.node_name}")
            try:
                result, is_end = self.curr_node.run(*args, wait_response=wait_response)
            except Exception:
                logger.debug(f"SignalContainer - {traceback.format_exc()}")
                self.end_flag = True
                self.cleanup()
                return
            if not is_end:
                return
            if result and self.curr_node.child:
                logger.debug(f"Signal running child of {self.curr_node.node_name} ")
                self.curr_node = self.curr_node.child
            elif self.curr_node.sibling:
                self.curr_node = self.curr_node.sibling
            else:
                self.curr_node = None
                if self.remaining_number_of_execution > 0:
                    self.remaining_number_of_execution -= 1
                    self.end_flag = self.end_flag or (
                        self.remaining_number_of_execution == 0
                    )
                return

            if self.curr_node.device_related:
                return


class DataContainer(Container):
    """
    DataContainer class for managing data-based control sequences.

    This class is a specialized container for managing control sequences that involve
    data-based nodes. It extends the functionality of the base `Container` class and
    provides methods for running data-based control sequences.

    Parameters:
    ----------
    root : TreeNode or None, optional
        The root node of the control sequence tree. Default is None.

    cleanup_list : list of TreeNode, optional
        A list of nodes containing 'cleanup' functions to be executed when the
        container is closed. Default is an empty list.

    Methods:
    --------
    run(*args):
        Run the data-based control sequence.

    Notes:
    ------
    - The `DataContainer` class is designed for managing control sequences that are
      data-based, typically used in applications involving data processing and
      analysis.

    - It extends the functionality of the base `Container` class and provides methods
      for running data-based control sequences.

    - The `run` method is responsible for executing the data-based control sequence
      nodes in the order defined by the control sequence tree. It handles transitions
      between nodes and manages node cleanup when necessary.
    """

    def __init__(self, root=None, cleanup_list=[]):
        super().__init__(root, cleanup_list)

    def run(self, *args):
        """
        Run the data-based control sequence.

        This method runs the data-based control sequence by iterating through its
        nodes and executing them in order. It manages the execution of nodes, handles
        transitions between nodes, and performs node cleanup when necessary.

        Parameters:
        -----------
        *args : arguments
            Optional arguments to pass to the control sequence nodes.

        Notes:
        ------
        - The `run` method is responsible for executing the data-based control
          sequence nodes in the order defined by the control sequence tree.

        - It handles transitions between nodes, waits for responses if necessary,
          and performs cleanup for nodes marked as not needing a response and having
          a 'one-step' node type.
        """

        if self.end_flag or not self.root:
            return
        if not self.curr_node:
            self.curr_node = self.root
        while self.curr_node:
            try:
                result, is_end = self.curr_node.run(*args)
            except Exception:
                logger.debug(f"DataContainer - {traceback.format_exc()}")
                if (
                    self.curr_node.need_response is False
                    and self.curr_node.node_type == "one-step"
                ):
                    try:
                        logger.debug(
                            f"Datacontainer cleanup node {self.curr_node.node_name}"
                        )
                        self.curr_node.node_funcs.get("cleanup", dummy_func)()
                    except Exception:
                        logger.debug(
                            f"The node({self.curr_node.node_name}) is not closed "
                            f"correctly! Please check the cleanup function"
                        )
                        pass
                    self.curr_node.is_marked = True
                    result, is_end = False, True
                else:
                    # terminate the container.
                    # the signal container may stuck there waiting a response,
                    # the cleanup function of that node should give it a fake
                    # response to make it stop
                    self.end_flag = True
                    self.cleanup()
                    return
            # print('Data running node:', self.curr_node.node_name,
            #       'get result:', result)
            if not is_end:
                return
            if result and self.curr_node.child:
                # print('Data running child of', self.curr_node.node_name)
                self.curr_node = self.curr_node.child
            elif self.curr_node.sibling:
                self.curr_node = self.curr_node.sibling
            else:
                self.curr_node = None
                return

            if self.curr_node.device_related or self.curr_node.need_response:
                return


def get_registered_funcs(feature_module, func_type="signal"):
    """
    Get a dictionary of registered functions for a feature module.

    This function retrieves a dictionary of registered functions for a given feature
    module and function type (signal or data). It ensures that essential functions
    such as 'init', 'main', and 'end' are present in the dictionary, and assigns them
    default dummy functions if they are missing.

    Parameters:
    ----------
    feature_module : module
        The feature module containing the configuration table of functions.

    func_type : str, optional
        The type of functions to retrieve, either 'signal' (default) or 'data'.

    Returns:
    -------
    dict
        A dictionary of registered functions for the specified function type.

    Notes:
    ------
    - This function is typically used to retrieve a dictionary of functions defined
      in a feature module's configuration table. The dictionary includes 'init',
      'main', and 'end' functions, and optionally 'pre-main' for data functions and
      'main-response' for signal functions.

    - If any of the essential functions is missing in the configuration table, this
      function assigns default dummy functions to ensure the dictionary is complete.

    - The `dummy_func` function is used as a default for functions that do nothing,
      and `dummy_True` is used as a default for functions that return True.
    """

    func_dict = feature_module.config_table.get(func_type, {})

    if "init" not in func_dict:
        func_dict["init"] = dummy_func
    if "main" not in func_dict:
        func_dict["main"] = dummy_True
    if "end" not in func_dict:
        func_dict["end"] = dummy_True
    if func_type == "data" and "pre-main" not in func_dict:
        func_dict["pre-main"] = dummy_True
    if func_type == "signal" and "main-response" not in func_dict:
        func_dict["main-response"] = dummy_True
    return func_dict


def load_features(model, feature_list):
    """
    Load and organize a list of feature modules into a child-sibling tree structure.

    This function takes a list of feature modules and organizes them into a
    child-sibling tree structure, creating SignalNodes and DataNodes for each
    feature module. It also handles shared variables and cleanup functions for
    the nodes.

    Parameters:
    ----------
    model : object
        The model or system to which the features are applied.

    feature_list : list
        A list of dictionaries or tuples representing the feature modules and
        their configurations.

    Returns:
    -------
    SignalContainer
        A container containing the root of the SignalNode tree and a cleanup list
        for signal nodes.

    DataContainer
        A container containing the root of the DataNode tree and a cleanup list for
        data nodes.

    Notes:
    ------
    - This function creates SignalNodes and DataNodes for each feature module in
      the feature_list, organizing them into a child-sibling tree structure.

    - Shared variables are handled by creating or updating variables in the
      `shared_variables` dictionary.

    - Cleanup functions are added to the cleanup lists for signal and data nodes
      as needed.

    - The nested functions `create_node` and `build_feature_tree` assist in
      creating and organizing the nodes.

    - This function returns SignalContainer and DataContainer instances containing
      the root nodes and cleanup lists for signal and data nodes.

    - SignalNodes represent signal processing tasks, and DataNodes represent data
      processing tasks within the feature modules.
    """

    signal_cleanup_list, data_cleanup_list = [], []
    shared_variables = {}

    def create_node(feature_dict):
        """
        Create SignalNode and DataNode instances for a feature module.

        This function takes a feature dictionary, creates SignalNode and DataNode
        instances, and handles node configurations, including 'need_response' and
        'device_related' properties.

        Parameters:
        ----------
        feature_dict : dict
            A dictionary containing the feature module's name, arguments, and
            node configuration.

        Returns:
        -------
        SignalNode
            A SignalNode instance for the feature module.

        DataNode
            A DataNode instance for the feature module.

        Notes:
        ------
        - This function creates SignalNode and DataNode instances based on the
          feature dictionary's information.

        - It handles configurations for 'need_response' and 'device_related' based
          on the feature module's signal and data functions.

        - The created nodes are returned for inclusion in the tree structure.
        """

        args = ()
        if "args" in feature_dict:
            args = list(feature_dict["args"])
            for i, arg in enumerate(args):
                if type(arg) is dict and arg.get("type", None) == "shared_list":
                    variable_name = arg.get("name", "temp")
                    if variable_name not in shared_variables:
                        shared_variables[variable_name] = list(arg["value"])
                    args[i] = shared_variables[variable_name]
        feature = feature_dict["name"](model, *args)

        node_config = feature.config_table.get("node", {})
        # if signal function has a waiting func,
        # then the nodes are 'need_response' nodes
        if "main-response" in feature.config_table.get("signal", {}):
            node_config["need_response"] = True
            node_config["device_related"] = True
        if "node" in feature_dict:
            for k, v in feature_dict["node"].items():
                node_config[k] = v
        # 'multi-step' must set to be 'device_related'
        if node_config.get("node_type", "") == "multi-step":
            node_config["device_related"] = True

        signal_node = SignalNode(
            feature_dict["name"].__name__,
            get_registered_funcs(feature, "signal"),
            **node_config,
        )
        data_node = DataNode(
            feature_dict["name"].__name__,
            get_registered_funcs(feature, "data"),
            **node_config,
        )

        if "cleanup" in feature.config_table.get("signal", {}):
            signal_cleanup_list.append(signal_node)
        if "cleanup" in feature.config_table.get("data", {}):
            data_cleanup_list.append(data_node)

        return signal_node, data_node

    def build_feature_tree(feature_list):
        """
        Build a child-sibling tree structure from a feature list.

        This function recursively builds a child-sibling tree structure from a list
        of feature modules. It creates SignalNode and DataNode instances for each
        feature module and organizes them into the tree structure.

        Parameters:
        ----------
        feature_list : list
            A list of dictionaries and tuples representing feature modules and their
            configurations.

        Returns:
        -------
        SignalNode
            The root SignalNode of the tree structure.

        DataNode
            The root DataNode of the tree structure.

        SignalNode
            The last SignalNode in the tree structure.

        DataNode
            The last DataNode in the tree structure.

        Notes:
        ------
        - This function recursively builds a child-sibling tree structure for the
          given feature list.

        - It returns the root SignalNode, root DataNode, last SignalNode, and last
          DataNode in the tree structure.

        - The last SignalNode and last DataNode are used to track the previous
          nodes for creating sibling relationships.
        """

        signal_root, data_root = None, None
        pre_signal, pre_data = None, None
        for temp in feature_list:
            if type(temp) is dict:
                signal_head, data_head = create_node(temp)
                signal_tail = signal_head
                data_tail = data_head
            else:
                signal_head, data_head, signal_tail, data_tail = build_feature_tree(
                    temp
                )
                if type(temp) is tuple:
                    signal_head.device_related = True
                    data_head.device_related = True
                    signal_tail.child = signal_head
                    data_tail.child = data_head
            if pre_signal:
                pre_signal.sibling = signal_head
                pre_data.sibling = data_head
            else:
                signal_root = signal_head
                data_root = data_head
            pre_signal = signal_tail
            pre_data = data_tail

        return signal_root, data_root, pre_signal, pre_data

    signal_root, data_root, pre_signal, pre_data = build_feature_tree(feature_list)
    return SignalContainer(signal_root, signal_cleanup_list), DataContainer(
        data_root, data_cleanup_list
    )


def dummy_True(*args):
    """
    Dummy function that always returns True.

    This function serves as a placeholder for operations that need to return a
    Boolean value. It is designed to always return True.

    Parameters:
    ----------
    *args : tuple
        Variable-length argument list (unused).

    Returns:
    -------
    bool
        Always returns True.

    Notes:
    ------
    - This function is a simple placeholder that returns True and is often used in
      situations where a real function is not yet implemented or is not relevant
      for a specific context.
    """
    return True


def dummy_func(*args):
    """
    Dummy function with no operation.

    This function serves as a placeholder for operations that require a function
    but do not perform any actual computation. It does not have any side effects
    and simply does nothing when called.

    Parameters:
    ----------
    *args : tuple
        Variable-length argument list (unused).

    Returns:
    -------
    None

    Notes:
    ------
    - This function is used as a placeholder for situations where a function is
      expected but no real operation is needed.
    """

    pass
