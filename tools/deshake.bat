
pyside6-uic .\ui\ui\ui_widget_player_ctrl.ui      -o .\ui\ui\ui_widget_player_ctrl.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_player_ctrl.py

pyside6-uic .\ui\ui\ui_widget_deshake.ui          -o .\ui\ui\ui_widget_deshake.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_deshake.py

pyside6-uic .\ui\ui\ui_widget_selection.ui         -o .\ui\ui\ui_widget_selection.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_selection.py

python .\deshake.py
