## 0.2.0 (2025-06-27)

### Feat

- add sampling rate display and reduce plot rate
- **HeaterController**: keep measurement data in plot after stopping heating
- add COM port validation check before device connection and timeout
- enhance data handling, logging, and device initialization
- **main_window.py**: add preview plot and refactor plot management
- **config_editor.py**: add com port and path pickers to config editor for better configurability
- add configuration editor dialog
- add persistent save path and index for measurement files
- **about_window.py**: add about window with version and author information
- add icon
- **main_window.py**: add temperature display
- **config.py**: make adam baud rate configurable
- **adam_4021_config.py**: add adam4021 config module and fix address formatting in adam4011

### Fix

- **config_editor.py**: resolve E721 type comparison errors
- **HeaterController**: prevent duplication of datapoints
- **HeaterController**: correct output setting on stop and reset
- add exception handling in set_output to prevent errors
- restructure setup process for ADAM modules
- add units to UI labels (mV for input, V for output); add None check in set_meas_connection method in HeaterController
- update font fallback to arial and LiberationsSans
- **Heater**: ensure measurement clearing only when self.meas exists
- **deps**: revert PySide6 suite to 6.9.0 to fix plot display
- **adam_4520.py**: raise exception if adam modules not found
- ensure correct voltage format and data precision
- correct voltage units and initial output handling
- **main_window.py**: fix calibration assignment mypy error

### Refactor

- streamline heating control and time calculations
- restructure Heater into dedicated controller with new processing loop
- **main_window**: improve widget cleanup and measurement display logic
- rename files to snake_case, update imports, fixed adam4021 command
