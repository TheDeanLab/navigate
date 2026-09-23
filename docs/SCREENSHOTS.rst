Refreshing documentation screenshots
====================================

Run the capture script from the repository root with the Navigate environment
and documentation dependencies installed::

    python docs/capture_gui.py --list
    python docs/capture_gui.py --all

All selected captures replace their previous files, including popups. The
``menus`` and ``tutorials`` groups cover the menu walkthrough and the feature,
multicamera, and ilastik examples. Use ``--group``, ``--capture``, or ``--manifest``
for a smaller refresh. Outputs belong in ``docs/source/images/``; tutorial pages
should reference these shared images instead of keeping local copies.

For a complete unattended capture, use Linux with an X11 virtual display::

    xvfb-run -a -s "-screen 0 3200x2200x24" \
        python docs/capture_gui.py --all --passes 3 --delay-ms 100

The script uses synthetic hardware and illustrative settings. It does not run
an experiment. Use a disposable user profile when installed plugins or personal
configuration could affect screenshots. Native macOS menus can block Tk's event
loop or expose no capturable bounds; capture menus on X11. On an interactive
desktop, keep other windows and system overlays away during capture.

Review every generated image for clipping, blank controls, or overlapping
windows. Then build the documentation::

    conda run -n navigate make -C docs html -j 15

Check image references throughout ``docs/source/``, including case studies and
contributor tutorials, and remove unused historical GUI images. A successful
capture run alone does not verify that every documentation page uses it.

Preserved case-study results
---------------------------

``source/images/case-studies/`` contains the original beam and tissue images,
autofocus plots, segmentation result, and CSV example with historical GUI
chrome removed. These are lossless crops, not new measurements or simulations.
``case_study_image_sources.json`` records the source commit, original file, and
crop bounds so each image can be reproduced from Git history. Do not replace
experimental results with synthetic screenshots when refreshing the interface.
