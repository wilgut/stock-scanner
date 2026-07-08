@echo off
cd /d "%~dp0"
if exist tv_sessionid.txt set /p TV_SESSIONID=<tv_sessionid.txt
echo Iniciando Scanner de Acciones en http://localhost:8877 ...
start http://localhost:8877
python app.py
pause
