#!/bin/sh

pyside6-uic ./tools/ui/ui/ui_widget_app_controls.ui      -o ./tools/ui/ui/widget_app_controls_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_app_controls_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_controls.ui          -o ./tools/ui/ui/widget_controls_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_controls_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_selection.ui         -o ./tools/ui/ui/widget_selection_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_selection_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_geometry.ui          -o ./tools/ui/ui/widget_geometry_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_geometry_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_stabilize.ui         -o ./tools/ui/ui/widget_stabilize_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_stabilize_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_replace.ui           -o ./tools/ui/ui/widget_replace_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_replace_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_curves.ui            -o ./tools/ui/ui/widget_curves_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_curves_ui.py

pyside6-uic ./tools/ui/ui/ui_widget_curves_selection.ui  -o ./tools/ui/ui/widget_curves_selection_ui.py
python ./tools/resources/patch_ui.py --file ./tools/views/ui/widget_curves_selection_ui.py

pyside6-uic ./tools/logger/ui_logger.ui -o tools/logger/ui_logger.py
python ./tools/resources/patch_ui.py --file ./tools/logger/ui_logger.py

export NO_AT_BRIDGE=1
python ./tools/video_editor.py