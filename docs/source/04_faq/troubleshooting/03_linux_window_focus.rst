.. _linux-window-focus:

Linux clicks bring another window forward
=========================================

On some Linux desktops, clicking inside **navigate** can unexpectedly bring an
application behind it to the front. This has been observed on Ubuntu 24.04 with
GNOME using an X11 session, particularly in blank areas below the Channels tab
and around the histogram or image display. Moving, resizing, or maximizing a
window can affect which areas trigger the problem.

Check for desktop updates
-------------------------

This symptom can come from the desktop's window handling. A related problem is
tracked in `Ubuntu bug 2026194
<https://bugs.launchpad.net/ubuntu/+source/mutter/+bug/2026194>`_. Older versions
of Mutter, GNOME's window manager, could use an incorrect area to decide which
window receives a mouse click. GTK, a toolkit used by GNOME desktop components,
also had a startup issue that could contribute to this behavior. **navigate**
uses Tk for its own interface, but it is still affected by the desktop managing
its windows.

1. Finish any acquisition, save your work, and close **navigate**.
2. Install the supported updates for your Linux distribution. On Ubuntu, open
   :guilabel:`Software Updater` and install the available updates, including
   Mutter and GTK packages. Use the system updater rather than installing Python
   packages with :command:`pip`.
3. **Restart the computer.** Restarting **navigate** alone does not reload the
   libraries already in use by the desktop session.
4. Launch **navigate** again. For a test without microscope hardware, activate
   your usual Python environment and run:

   .. code-block:: bash

      navigate -sh

5. Leave another application behind **navigate** and click the areas that
   previously caused trouble. Repeat after moving and resizing the main window,
   and check detached tabs and popup windows as well. Clicking **navigate**
   should keep the clicked window in front without briefly flashing another
   application forward.

In one Ubuntu 24.04 GNOME/X11 investigation, updating Mutter from
``46.0-1ubuntu9`` to ``46.2-1ubuntu0.24.04.18`` and GTK 4 from
``4.14.2+ds-1ubuntu1`` to ``4.14.5+ds-0ubuntu0.10``, followed by a reboot,
resolved the observed main-window focus switching. The verification used
**navigate** without an application-level click-activation workaround. These are
the tested package versions, not minimum requirements for every distribution;
use the supported updates offered for your system.

If the problem continues
------------------------

Record the following when reporting the issue through the `navigate issue
tracker <https://github.com/TheDeanLab/navigate/issues>`_:

* Your Linux distribution, desktop, and session type (X11 or Wayland). If unsure,
  these terminal commands can help:

  .. code-block:: bash

     cat /etc/os-release
     printf '%s\n' "$XDG_CURRENT_DESKTOP" "$XDG_SESSION_TYPE"

* The installed Mutter and GTK versions. On Ubuntu 24.04, run:

  .. code-block:: bash

     dpkg-query -W libmutter-14-0 libgtk-4-1

* Whether you restarted the computer after updating, which window and region you
  clicked, and whether resizing, display scaling, or automatic login affects the
  behavior.
* The approximate incident time and the corresponding :file:`debug.log` from
  :file:`~/.navigate/logs/`. Ordinary logs may not record mouse delivery or
  desktop focus changes, so the absence of an error does not by itself rule out
  this problem.

Upstream references
-------------------

* `Mutter correction to X11 window input regions
  <https://github.com/GNOME/mutter/commit/6bd920b355d12395dbf00b99374fc1f23783caaf>`_.
* `GTK correction to window-manager detection during startup
  <https://github.com/GNOME/gtk/commit/ec14f9a4c696f795c94bf51ab48c598995729625>`_.
