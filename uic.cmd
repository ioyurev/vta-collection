if not exist vta_collection\ui mkdir vta_collection\ui
pyside6-uic assets/MainWindow.ui > vta_collection/ui/main_window.py
pyside6-uic assets\NewMeasurementDialog.ui > vta_collection/ui/new_measurement.py

autoflake -i --remove-all-unused-imports vta_collection/ui/main_window.py
autoflake -i --remove-all-unused-imports vta_collection/ui/new_measurement.py

pyside6-rcc assets\resources.qrc > vta_collection\ui\resources_rc.py
