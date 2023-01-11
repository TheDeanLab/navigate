# Copyright (c) 2021-2022  The University of Texas Southwestern Medical Center.
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

from aslm.controller.sub_controllers.camera_view_controller import CameraViewController
import pytest
import random

class TestCameraViewController():
    
    @pytest.fixture(autouse=True)
    def setup_class(self, dummy_controller):
        c = dummy_controller
        self.v = dummy_controller.view
        
        self.camera_view = CameraViewController(self.v.camera_waveform.camera_tab, c)

    def test_init(self):

        assert isinstance(self.camera_view, CameraViewController)

    
    def test_slider_update(self, monkeypatch):
        
        # Testing it can be triggered, other functions within are tested later
        self.image = (int(random.random()),int(random.random()))
        self.reset = False
        def mock_retrieve(slider_index, channel_display_index):
            self.x = int(random.random())
            self.y = int(random.random())
            self.image = (self.x,self.y)
        def mock_reset():
            self.reset = True
        monkeypatch.setattr(self.camera_view, "retrieve_image_slice_from_volume", mock_retrieve)
        monkeypatch.setattr(self.camera_view, "reset_display", mock_reset)
        event = type('Event', (object,), {})()

        self.camera_view.slider_update(event)

        assert self.image == (self.x,self.y)
        assert self.reset == True

    def test_update_display_state(self):
        pass


    def test_get_absolute_position(self, monkeypatch):
        
        def mock_winfo_pointerx():
            self.x = int(random.random())
            return self.x
        def mock_winfo_pointery():
            self.y = int(random.random())
            return self.y
        monkeypatch.setattr(self.v, 'winfo_pointerx', mock_winfo_pointerx)
        monkeypatch.setattr(self.v, 'winfo_pointery', mock_winfo_pointery)
        
        # call the function under test
        x, y = self.camera_view.get_absolute_position()
        
        # make assertions about the return value
        assert x == self.x
        assert y == self.y

    def test_popup_menu(self, monkeypatch):
        
        # create a fake event object
        self.startx = int(random.random())
        self.starty = int(random.random())
        event = type('Event', (object,), {'x': self.startx, 'y': self.starty})()
        self.grab_released = False
        self.x = int(random.random())
        self.y = int(random.random())
        self.absx = int(random.random())
        self.absy = int(random.random())


        # monkey patch the get_absolute_position method to return specific values
        def mock_get_absolute_position():
            self.absx = int(random.random())
            self.absy = int(random.random())
            return self.absx, self.absy
        monkeypatch.setattr(self.camera_view, 'get_absolute_position', mock_get_absolute_position)

        def mock_tk_popup(x, y):
            self.x = x
            self.y = y
        def mock_grab_release():
            self.grab_released = True
        monkeypatch.setattr(self.camera_view.menu, 'tk_popup', mock_tk_popup)
        monkeypatch.setattr(self.camera_view.menu, 'grab_release', mock_grab_release)

        # call the function under test
        self.camera_view.popup_menu(event)

        
        # make assertions about the state of the view object
        assert self.camera_view.move_to_x == self.startx
        assert self.camera_view.move_to_y == self.starty
        assert self.x == self.absx
        assert self.y == self.absy
        assert self.grab_released == True

    @pytest.mark.parametrize("name", ['minmax', 'image'])
    @pytest.mark.parametrize("data", [[random.randint(0, 49), random.randint(50, 100)]])
    def test_initialize(self, name, data):
        
        self.camera_view.initialize(name, data)

        # Checking values
        if name == 'minmax':
            assert self.camera_view.image_palette['Min'].get() == data[0]
            assert self.camera_view.image_palette['Max'].get() == data[1]
        if name == 'image':
            assert self.camera_view.image_metrics['Frames'].get() == data[0]

    
    def test_set_mode(self):

        # Test default mode
        self.camera_view.set_mode()
        assert self.camera_view.mode == ''
        assert self.camera_view.menu.entrycget("Move Here", 'state') == 'disabled'

        # Test 'live' mode
        self.camera_view.set_mode('live')
        assert self.camera_view.mode == 'live'
        assert self.camera_view.menu.entrycget("Move Here", 'state') == 'normal'

        # Test 'stop' mode
        self.camera_view.set_mode('stop')
        assert self.camera_view.mode == 'stop'
        assert self.camera_view.menu.entrycget("Move Here", 'state') == 'normal'

        # Test invalid mode
        self.camera_view.set_mode('invalid')
        assert self.camera_view.mode == 'invalid'
        assert self.camera_view.menu.entrycget("Move Here", 'state') == 'disabled'


    def test_move_stage(self):

        microscope_name = self.camera_view.parent_controller.configuration['experiment']['MicroscopeState']['microscope_name']
        zoom_value = self.camera_view.parent_controller.configuration['experiment']['MicroscopeState']['zoom']
        pixel_size = self.camera_view.parent_controller.configuration['configuration']['microscopes'][microscope_name]['zoom']['pixel_size'][zoom_value]
        
        current_center_x = (self.camera_view.zoom_rect[0][0] + self.camera_view.zoom_rect[0][1]) / 2
        current_center_y = (self.camera_view.zoom_rect[1][0] + self.camera_view.zoom_rect[1][1]) / 2
        
        
        offset_x = (self.camera_view.move_to_x - current_center_x) / self.camera_view.zoom_scale * self.camera_view.canvas_width_scale * pixel_size
        offset_y = (self.camera_view.move_to_y - current_center_y) / self.camera_view.zoom_scale * self.camera_view.canvas_width_scale * pixel_size

        