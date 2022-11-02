#!/bin/sh

pyside6-uic common/ui/ui_widget_app_controls.ui        -o common/ui/widget_app_controls_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_comparisons.ui         -o merge_stabilize/ui/widget_comparisons_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_controls.ui            -o merge_stabilize/ui/widget_controls_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_selection.ui           -o merge_stabilize/ui/widget_selection_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_stitching_curves.ui    -o merge_stabilize/ui/widget_stitching_curves_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_stitching.ui           -o merge_stabilize/ui/widget_stitching_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_stabilize.ui       -o merge_stabilize/ui/widget_stabilize_ui.py
pyside6-uic merge_stabilize/ui/ui_widget_geometry.ui     -o merge_stabilize/ui/widget_geometry_ui.py
pyside6-uic logger/ui_logger.ui -o logger/ui_logger.py

export NO_AT_BRIDGE=1
python merge_stabilize.py