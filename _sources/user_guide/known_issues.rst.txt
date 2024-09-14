============
Known Issues
============

This page lists known issues with the **navigate** software that currently do not have
an obvious solution. Please report any other issues you encounter on GitHub.

Slow Channel Switching
----------------------

When we operate multiple channels, there is a clear time delay between channels.
This is most obvious when operating in the continuous mode, or when you are acquiring
a Z-stack in the Per Z Laser Cycling mode.

This delay is associated with the time it takes to load the waveforms onto the DAQ
card. One possible solution is to write the waveforms to different channels on the
DAQ, but this would require that the analog/digital signals be combined physically.
For example, if CH00 was delivered on AO0, and CH01 was delivered on AO1, but both
were communicating with a single laser, then the signals could be combined and
delivered to the laser. However, a more obvious solution would be to reduce the time
necessary to load the waveforms onto the DAQ card. One immediate way to do this is by
reducing the DAQ sampling rate, but this would reduce the resolution of the waveforms
. More sophisticated DAQ systems, including an FPGA, could also be used to eliminate
this delay.
