@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Publicar Scanner en internet

echo ==========================================================
echo   Publicar el Scanner en internet (Vercel)
echo ==========================================================
echo.

call vercel whoami >nul 2>&1
if errorlevel 1 (
  echo No hay sesion de Vercel iniciada en esta PC.
  echo.
  echo Se va a abrir el navegador para que inicies sesion.
  echo Elige "Continue with GitHub" y luego vuelve a esta ventana.
  echo.
  pause
  call vercel login
  echo.
)

echo Publicando la version actual...
echo Esto tarda un par de minutos. No cierres esta ventana.
echo.

call vercel --prod --yes

echo.
echo ==========================================================
echo   Terminado.
echo.
echo   Si arriba aparece una direccion que empieza por https,
echo   la publicacion salio bien. Comprueba la app en:
echo   https://stock-scanner-six-delta.vercel.app
echo.
echo   Si aparece algun error, copia el texto y pasamelo.
echo ==========================================================
echo.
pause
