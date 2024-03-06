navigate.model.model.Model
==========================

.. currentmodule:: navigate.model.model

.. autoclass:: Model
   :members:
   :show-inheritance:
   :inherited-members:

   
   .. automethod:: __init__

   
   .. rubric:: Methods

   .. autosummary::
   
      ~Model.__init__
      ~Model.change_resolution
      ~Model.create_pipe
      ~Model.destroy_virtual_microscope
      ~Model.end_acquisition
      ~Model.get_active_microscope
      ~Model.get_camera_line_interval_and_exposure_time
      ~Model.get_data_buffer
      ~Model.get_feature_list
      ~Model.get_microscope_info
      ~Model.get_offset_variance_maps
      ~Model.get_stage_position
      ~Model.launch_virtual_microscope
      ~Model.load_feature_list_from_file
      ~Model.load_feature_list_from_str
      ~Model.load_feature_records
      ~Model.load_images
      ~Model.mark_saving_flags
      ~Model.move_stage
      ~Model.pause_data_thread
      ~Model.prepare_acquisition
      ~Model.release_pipe
      ~Model.reset_feature_list
      ~Model.resume_data_thread
      ~Model.run_acquisition
      ~Model.run_command
      ~Model.run_data_process
      ~Model.run_live_acquisition
      ~Model.simplified_data_process
      ~Model.snap_image
      ~Model.stop_stage
      ~Model.terminate
      ~Model.update_data_buffer
      ~Model.update_ilastik_setting
      ~Model.update_mirror
   
   

   
   
   .. rubric:: Attributes

   .. autosummary::
   
      ~Model.logger
      ~Model.configuration
      ~Model.plugin_acquisition_modes
      ~Model.virtual_microscopes
      ~Model.microscopes
      ~Model.active_microscope
      ~Model.active_microscope_name
      ~Model.imaging_mode
      ~Model.image_count
      ~Model.acquisition_count
      ~Model.total_acquisition_count
      ~Model.total_image_count
      ~Model.current_exposure_time
      ~Model.pre_exposure_time
      ~Model.camera_wait_iterations
      ~Model.start_time
      ~Model.data_buffer
      ~Model.img_width
      ~Model.img_height
      ~Model.binning
      ~Model.data_buffer_positions
      ~Model.data_buffer_saving_flags
      ~Model.is_acquiring
      ~Model.f_position
      ~Model.max_entropy
      ~Model.focus_pos
      ~Model.signal_thread
      ~Model.data_thread
      ~Model.show_img_pipe
      ~Model.plot_pipe
      ~Model.event_queue
      ~Model.frame_id
      ~Model.injected_flag
      ~Model.is_live
      ~Model.is_save
      ~Model.stop_acquisition
      ~Model.stop_send_signal
      ~Model.pause_data_event
      ~Model.pause_data_ready_lock
      ~Model.ask_to_pause_data_thread
      ~Model.number_of_frames
      ~Model.image_writer
      ~Model.addon_feature
      ~Model.feature_list
   
   