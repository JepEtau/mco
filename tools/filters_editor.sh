#!/bin/sh

pyside6-uic common/ui/ui_widget_app_controls.ui   -o common/ui/widget_app_controls_ui.py
pyside6-uic common/ui/ui_widget_controls.ui       -o common/ui/widget_controls_ui.py
pyside6-uic filters_editor/ui/ui_widget_selection.ui      -o filters_editor/ui/widget_selection_ui.py
pyside6-uic logger/ui_logger.ui -o logger/ui_logger.py

export NO_AT_BRIDGE=1
python filters_editor.py