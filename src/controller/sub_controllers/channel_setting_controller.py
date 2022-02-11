from controller.sub_controllers.widget_functions import validate_wrapper
from controller.sub_controllers.gui_controller import GUI_Controller


class Channel_Setting_Controller(GUI_Controller):
    def __init__(self, view, parent_controller=None, verbose=False):
        super().__init__(view, parent_controller, verbose)

        # num: numbers of channels
        self.num = 5
        # 'live': acquire mode is set to 'continuous'
        self.mode = 'stop'
        self.channel_controllers = []
        self.in_initialization = True
        self.event_id = None

        # add validation functions to spinbox
        for i in range(self.num):
            validate_wrapper(self.view.exptime_pulldowns[i])
            validate_wrapper(self.view.interval_spins[i])
            validate_wrapper(self.view.laserpower_pulldowns[i])

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
        if not widgets:
            return
        for i in range(self.num):
            if type == 'variable':
                widgets[i].set(value)
            else:
                widgets[i]['values'] = value

        self.show_verbose_info(name, 'in channel has been initialized')

    def set_values(self, value):
        """
        # set channel values according to channel id
        # the value should be a dict {
        # 'channel_id': {
            'is_selected': True(False),
            'laser': ,
            'filter': ,
            'camera_exposure_time': ,
            'laser_power': ,
            'interval_time':}
        }
        """
        prefix = 'channel_'
        for channel in value:
            channel_id = int(channel[len(prefix):]) - 1
            channel_vals = self.get_vals_by_channel(channel_id)
            if not channel_vals:
                return
            channel_value = value[channel]
            for name in channel_vals:
                channel_vals[name].set(channel_value[name])
                if name == 'camera_exposure_time':
                    self.view.exptime_pulldowns[channel_id].validate()
                elif name == 'interval_time':
                    self.view.interval_spins[channel_id].validate()
                elif name == 'laser_power':
                    self.view.laserpower_pulldowns[channel_id].validate()

        self.show_verbose_info('channel has been set new value')

    def get_values(self):
        """
        # return all the selected channels' setting values
        # for example, if channel_1 and channel_2 is selected, it will return
        # { 'channel_1': {
        #           'is_selected': True,
        #           'laser': ,
        #           'laser_index': ,
        #           'filter': ,
        #           'filter_position': ,
        #           'camera_exposure_time': ,
        #           'laser_power': ,
        #           'interval_time': 
        #        },
        # 'channel_2': {
        #           'is_selected': True,
        #           'laser': ,
        #           'laser_index': ,
        #           'filter': ,
        #           'filter_position': ,
        #           'camera_exposure_time': ,
        #           'laser_power': ,
        #           'interval_time': 
        #        }
        # }
        """
        prefix = 'channel_'
        channel_settings = {}
        for i in range(self.num):
            channel_vals = self.get_vals_by_channel(i)
            # if this channel is selected, then get all the settings of it
            if channel_vals['is_selected'].get():
                try:
                    temp = {
                        'is_selected': True,
                        'laser': channel_vals['laser'].get(),
                        'laser_index': self.get_index('laser', channel_vals['laser'].get()),
                        'filter': channel_vals['filter'].get(),
                        'filter_position': self.get_index('filter', channel_vals['filter'].get()),
                        'camera_exposure_time': float(channel_vals['camera_exposure_time'].get()),
                        'laser_power': channel_vals['laser_power'].get(),
                        'interval_time': channel_vals['interval_time'].get()
                    }
                except:
                    return None
                channel_settings[prefix+str(i+1)] = temp
        return channel_settings

    def set_spinbox_range_limits(self, settings):
        """
        # this function will set the spinbox widget's values of from_, to, step
        """
        temp_dict = {
            'laser_power': self.view.laserpower_pulldowns,
            'camera_exposure_time': self.view.exptime_pulldowns,
            'interval_time': self.view.interval_spins
        }
        for k in temp_dict:
            widgets = temp_dict[k]
            for i in range(self.num):
                widgets[i].configure(from_=settings[k]['min'])
                widgets[i].configure(to=settings[k]['max'])
                widgets[i].configure(increment=settings[k]['step'])

    def channel_callback(self, channel_id, widget_name):
        """
        # in 'live' mode (when acquire mode is set to 'continuous') and a channel is selected,
        # any change of the channel setting will influence devices instantly
        # this function will call the central controller to response user's request
        """
        channel_vals = self.get_vals_by_channel(channel_id)

        def func(*args):
            if self.in_initialization:
                return
            if widget_name != 'is_selected' and channel_vals['is_selected'].get() is False:
                return
            if widget_name == 'camera_exposure_time':
                self.parent_controller.execute('recalculate_timepoint')
            if self.mode == 'live':
                # validate values: all the selected channel should not be empty if 'is_selcted'
                if channel_vals['is_selected'].get():
                    try:
                        assert(channel_vals['laser'].get() and channel_vals['filter'].get())
                        float(channel_vals['laser_power'].get())
                        float(channel_vals['camera_exposure_time'].get())
                        float(channel_vals['interval_time'].get())
                    except:
                        if self.event_id:
                            self.view.after_cancel(self.event_id)
                        return
                # call central controller
                if self.event_id:
                    self.view.after_cancel(self.event_id)
                self.event_id = self.view.after(500, lambda: self.parent_controller.execute('channel', channel_id+1, widget_name, channel_vals[widget_name].get()))

            self.show_verbose_info('channel setting has been changed')
        return func

    def get_widgets(self, name):
        """
        # get all the widgets according to name
        # name should be: is_selected, laser, filter, camera_exposure_time, laser_power, interval_time
        """
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

        return type, result

    def get_vals_by_channel(self, index):
        """
        # this function return all the variables according channel_id
        """
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

    def get_index(self, dropdown_name, value):
        type, widget = self.get_widgets(dropdown_name)
        if type != 'variable' and value:
            values = widget[0]['values']
            return values.index(value)
        return -1
