@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Anotador SINAN - gera xlsx anotado a partir de DBF do Sinan NET
echo.
if "%~1"=="" (
  echo Como usar: arraste um ou mais arquivos .DBF do Sinan NET sobre este arquivo anotar.bat.
  echo O xlsx e o relatorio .log.txt sao gravados na mesma pasta de cada DBF.
  echo.
  pause
  exit /b 1
)
rem sys.path (incl. app\) is fixed by python\python313._pth; the interpreter ignores PYTHONPATH/PYTHONHOME of the machine
"%~dp0python\python.exe" -m sinan_anotador --tab "%~dp0app\tab_sinannet" %*
echo.
echo Terminado. Confira o arquivo ^<nome^>_anotado.log.txt ao lado de cada DBF.
pause
