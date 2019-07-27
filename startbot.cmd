@echo off
:1
%Python3%/python.exe -u SINoWhite.py 1> logs/SINoWhite.log 2>logs/SINoWhite.err
timeout /t 3 /nobreak
goto :1
pause & exit