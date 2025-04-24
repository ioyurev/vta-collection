pyside6-uic assets/MainWindow.ui > vta_collection/ui/main_window.py
pyside6-uic assets\NewMeasurementDialog.ui > vta_collection/ui/new_measurement.py

autoflake -i --remove-all-unused-imports vta_collection/ui/main_window.py
autoflake -i --remove-all-unused-imports vta_collection/ui/new_measurement.py
