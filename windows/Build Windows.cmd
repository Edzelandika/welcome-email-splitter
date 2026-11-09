@echo off
setlocal
cd /d "%~dp0.."
py -3 -m venv windows\.venv
if errorlevel 1 goto fail
windows\.venv\Scripts\python -m pip install -r windows\requirements.txt
if errorlevel 1 goto fail
windows\.venv\Scripts\python -m unittest -v test_splitter.py
if errorlevel 1 goto fail
windows\.venv\Scripts\python -m PyInstaller --noconfirm --clean --onefile --windowed --collect-all tkinterdnd2 --paths . --name "Welcome Email Splitter" --distpath windows\dist --workpath windows\build --specpath windows windows\app.py
if errorlevel 1 goto fail
echo Done: windows\dist\Welcome Email Splitter.exe
pause
exit /b 0
:fail
echo Build failed. Review the error above. Python 3 must be installed to build.
pause
exit /b 1
