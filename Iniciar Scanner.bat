@echo off
cd /d "%~dp0"
echo Iniciando Scanner de Acciones en http://localhost:8877 ...
start http://localhost:8877
python app.py
pause
