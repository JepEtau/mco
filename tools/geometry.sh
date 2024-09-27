#!/bin/sh


pyside6-uic ./ui/ui/ui_widget_player_ctrl.ui -o ./ui/ui/ui_widget_player_ctrl.py
python ./_utils/patch_ui.py --file ./ui/ui/ui_widget_player_ctrl.py

pyside6-uic ./ui/ui/ui_widget_geometry.ui -o ./ui/ui/ui_widget_geometry.py
python ./_utils/patch_ui.py --file ./ui/ui/ui_widget_geometry.py

pyside6-uic ./ui/ui/ui_widget_selection.ui -o ./ui/ui/ui_widget_selection.py
python ./_utils/patch_ui.py --file ./ui/ui/ui_widget_selection.py

# pyside6-uic ./tools/logger/ui_logger.ui -o tools/logger/ui_logger.py
# python ./tools/resources/patch_ui.py --file ./tools/logger/ui_logger.py

export NO_AT_BRIDGE=1
python geometry.py
