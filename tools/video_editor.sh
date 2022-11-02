#!/bin/sh

pyside6-uic common/ui/ui_widget_app_controls.ui   -o common/ui/widget_app_controls_ui.py
pyside6-uic common/ui/ui_widget_controls.ui       -o common/ui/widget_controls_ui.py
pyside6-uic video_editor/ui/ui_widget_selection.ui      -o video_editor/ui/widget_selection_ui.py
pyside6-uic video_editor/ui/ui_widget_geometry.ui       -o video_editor/ui/widget_geometry_ui.py
pyside6-uic video_editor/ui/ui_widget_replace.ui        -o video_editor/ui/widget_replace_ui.py
pyside6-uic video_editor/ui/ui_widget_curves.ui         -o video_editor/ui/widget_curves_ui.py
pyside6-uic video_editor/ui/ui_widget_curves_selection.ui   -o video_editor/ui/widget_curves_selection_ui.py
pyside6-uic logger/ui_logger.ui -o logger/ui_logger.py

export NO_AT_BRIDGE=1
python video_editor.py