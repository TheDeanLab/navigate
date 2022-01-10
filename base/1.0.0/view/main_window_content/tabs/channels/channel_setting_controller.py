from view.gui_controller import GUI_Controller

class Channel_Setting_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None):
        super().__init__(view, parent_controller)
        # num: nummbers of channels
        self.num = 5
        # 'instant': acquire mode is set to 'continuous'
        self.mode = 'instant'
        self.channel_controllers = []

        # widget command binds
        for i in range(self.num):
            channel_vals = self.get_vals_by_channel(i)
            for name in channel_vals:
                channel_vals[name].trace_add('write', self.channel_callback(i, name))


    def set_num(self, num):
        self.num = num

    def set_mode(self, mode=''):
        self.mode = mode

    def initialize(self, name, value):
        type, widgets = self.get_widgets(name)
        if not widgets: return
        for i in range(self.num):
            if type == 'variable':
                widgets[i].set(value)
            else:
                widgets[i]['values'] = value

    def set_values(self, channel_id, value):
        '''
        # set channel values according to channel id
        # the value should be a dict {
            'is_selected': True(False),
            'laser': ,
            'filter': ,
            'camera_exposure_time': ,
            'laser_power': ,
            'interval_time':}
        '''
        channel_vals = self.get_vals_by_channel(channel_id)
        if not channel_vals:
            return
        for name in value:
            channel_vals[name].set(value[name])

    def get_values(self):
        '''
        # return all the channels' setting values
        # todo: only the selected channel ?
        '''
        channel_settings = {}
        for i in range(self.num):
            channel_vals = self.get_vals_by_channel(i)
            # if this channel is selected, then get all the settings of it
            if channel_vals['is_selected'].get():
                temp = {
                    'is_selected': True,
                    'laser': channel_vals['laser'].get(),
                    'filter': channel_vals['filter'].get(),
                    'camera_exposure_time': channel_vals['camera_exposure_time'].get(),
                    'laser_power': channel_vals['laser_power'].get(),
                    'interval_time': channel_vals['interval_time'].get()
                }
                channel_settings['channel'+str(i)] = temp
        return channel_settings

    def channel_callback(self, channel_id, widget_name):
        '''
        # in 'instant' mode (when acquire mode is set to 'continuous') and a channel is selected,
        # any change of the channel setting will influence devices instantly
        # this function will call the central controller to response user's request
        '''
        channel_vals = self.get_vals_by_channel(channel_id)
        def func(*args):
            if self.mode == 'instant' and channel_vals['is_selected'].get():
                self.parent_controller.execute('channel', widget_name, channel_vals[widget_name].get())
        return func

    def get_widgets(self, name):
        '''
        # get all the widgets according to name
        # name should be: is_selected, laser, filter, camera_exposure_time, laser_power, interval_time
        '''
        result = None
        type = 'widget'
        if name == 'laser':
            result = self.view.laser_pulldowns
        elif name == 'filter':
            result = self.view.filterwheel_pulldowns
        elif name == 'camera_exposure_time':
            result = self.view.exptime_variables
            type = 'variable'
        elif name == 'laser_power':
            result = self.view.laserpower_pulldowns
        elif name == 'interval_time':
            result = self.view.interval_variables
            type = 'variable'
        elif name == 'is_selected':
            result = self.view.channel_variables
            type = 'variable'

        return (type, result)

    def get_vals_by_channel(self, index):
        '''
        # this function return all the variables according channel_id
        '''
        if index < 0 or index >= self.num:
            return {}
        result = {
            'is_selected': self.view.channel_variables[index],
            'laser': self.view.laser_variables[index],
            'filter': self.view.filterwheel_variables[index],
            'camera_exposure_time': self.view.exptime_variables[index],
            'laser_power': self.view.laserpower_variables[index],
            'interval_time': self.view.interval_variables[index]
        }
        return result

