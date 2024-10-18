
pyside6-uic .\ui\ui\ui_widget_player_ctrl.ui      -o .\ui\ui\ui_widget_player_ctrl.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_player_ctrl.py

pyside6-uic .\ui\ui\ui_widget_replace.ui          -o .\ui\ui\ui_widget_replace.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_replace.py

pyside6-uic .\ui\ui\ui_widget_selection.ui         -o .\ui\ui\ui_widget_selection.py
python .\_utils\patch_ui.py --file .\ui\ui\ui_widget_selection.py

python .\replace.py
