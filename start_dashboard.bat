@echo off
echo Ativando ambiente virtual...

call "%~dp0.venv\Scripts\activate.bat"

IF ERRORLEVEL 1 (
    echo [ERRO] Falha ao ativar o ambiente virtual!
    pause
    exit /b
)

echo Ambiente virtual ativado com sucesso!
echo Iniciando o dashboard...

REM Vai para a pasta do projeto
cd /d "%~dp0"

REM Abre o Streamlit numa nova aba
start cmd /k "streamlit run ML2_dashboard_preditivo.py --server.address=0.0.0.0"

REM Espera 5 segundos pro Streamlit subir
timeout /t 5 >nul

REM Abre o ngrok numa nova aba já apontando pra porta 8501
start cmd /k "ngrok http 8501"

echo ==============================================
echo Dashboard rodando!
echo Copie o link do terminal do ngrok que abrir :)
echo ==============================================
pause