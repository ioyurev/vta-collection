@echo off
if not exist vta_collection\ui mkdir vta_collection\ui

REM Обработка всех UI файлов в assets/
for %%f in (assets\*.ui) do (
    echo Processing %%f...
    pyside6-uic %%f > vta_collection/ui/%%~nf.py
)

REM Очистка импортов во всех сгенерированных файлах
for %%f in (vta_collection\ui\*.py) do (
    echo Cleaning imports in %%f...
    autoflake -i --remove-all-unused-imports %%f
)

REM Обработка ресурсов
if exist assets\resources.qrc (
    echo Processing resources.qrc...
    pyside6-rcc assets\resources.qrc > vta_collection\ui\resources_rc.py
)

echo Done!
