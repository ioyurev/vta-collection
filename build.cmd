call uic.cmd
if not exist pyinstaller mkdir pyinstaller
cd pyinstaller
python ../devtools/splash_gen.py
pyinstaller ../vta_collection/__main__.py -n vta-collection --noconfirm -i ../assets/icon.png --exclude-module matplotlib --splash splash.png
xcopy ..\LICENSE .\dist\vta-collection\
xcopy ..\LICENSE_RU .\dist\vta-collection\
