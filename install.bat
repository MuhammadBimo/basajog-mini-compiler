@echo off
REM ============================================================
REM  install.bat - Installer otomatis BasaJog Mini Compiler
REM  Nggawe virtual environment + masang library sing dibutuhake
REM  Cara nganggo : dobel-klik file iki, utawa ketik "install.bat"
REM ============================================================
setlocal

echo ============================================================
echo   Installer BasaJog Mini Compiler
echo ============================================================
echo.

REM --- 1. Cek Python wis kepasang apa durung ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python ora ketemu ing PATH.
    echo         Pasang Python 3.10+ dhisik saka https://www.python.org
    echo         Aja lali centhang "Add Python to PATH" pas masang.
    echo.
    pause
    exit /b 1
)

echo [1/3] Python ketemu:
python --version
echo.

REM --- 2. Gawe virtual environment 'COM_venv' ---
if exist "COM_venv\Scripts\python.exe" (
    echo [2/3] Virtual environment 'COM_venv' wis ana, dilewati.
) else (
    echo [2/3] Nggawe virtual environment 'COM_venv'...
    python -m venv COM_venv
    if errorlevel 1 (
        echo [ERROR] Gagal nggawe virtual environment.
        pause
        exit /b 1
    )
)
echo.

REM --- 3. Pasang library saka requirements.txt ---
echo [3/3] Masang library (matplotlib, networkx)...
call "COM_venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Gagal masang library. Cek koneksi internet banjur jajal maneh.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   RAMPUNG! Instalasi kasil.
echo.
echo   Carane mlaku-ake compiler:
echo     1. Aktifake venv : COM_venv\Scripts\activate
echo     2. Jalanke       : python main.py program.bj
echo     3. Test          : python test_compiler.py
echo ============================================================
echo.
pause
endlocal
