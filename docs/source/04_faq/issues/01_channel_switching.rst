.. _issue_slow_channel_switching:

======================
Slow Channel Switching
======================

When multiple channels are enabled, a delay can appear between channels. This is most visible in continuous acquisition or while acquiring a z-stack with :guilabel:`Per Z Laser Cycling`.

The main source of delay is waveform loading time on the DAQ card. One approach is to pre-route different channel waveforms to different DAQ outputs and combine signals in hardware where appropriate. A simpler mitigation is to lower the DAQ sampling rate, which reduces waveform load time but also reduces waveform resolution.

More advanced DAQ systems (for example, FPGA-based control) can reduce or eliminate this delay further.
