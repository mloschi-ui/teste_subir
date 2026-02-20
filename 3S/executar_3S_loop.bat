@echo off
cd /d "%~dp0"

echo Iniciando loop da API 3S - Lista de Posicoes de Veiculos...
echo.

:loop
echo Executando chamada da API...
python lista_pos_vei_3S.py
echo.
echo Aguardando 10 segundos antes da próxima execução...
timeout /t 10 /nobreak >nul
echo.
goto loop
