@echo off
for /r "c:\" %%i in (python.exe) do if exist "%%i" "%%i" -m pip install Pillow reportlab & exit
