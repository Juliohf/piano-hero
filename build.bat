@echo off
REM ============================================================
REM  Gera o executavel do Windows: dist\MoonlightRhythm.exe
REM  Basta dar um duplo-clique neste arquivo (ou rodar no terminal).
REM ============================================================
echo Instalando dependencias...
pip install pygame pyinstaller
echo.
echo Compilando o jogo...
pyinstaller --noconfirm --onefile --windowed --name MoonlightRhythm --add-data "assets;assets" main.py
echo.
echo ============================================================
echo  Pronto! O executavel esta em:  dist\MoonlightRhythm.exe
echo  (Os assets ja ficam embutidos dentro do .exe)
echo ============================================================
pause
