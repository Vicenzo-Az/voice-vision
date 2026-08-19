@echo off
setlocal

echo ================================
echo  Voice Vision - build do .exe
echo ================================
echo.

if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo Falha ao criar o ambiente virtual. Verifique se o Python esta no PATH.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat

echo Instalando dependencias do projeto...
pip install -r requirements.txt
if errorlevel 1 goto :erro

echo Instalando PyInstaller...
pip install -r requirements-build.txt
if errorlevel 1 goto :erro

echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo.
echo Gerando executavel (isso pode levar alguns minutos)...
pyinstaller --noconfirm VoiceVision.spec
if errorlevel 1 goto :erro

echo.
echo ================================
echo  Build concluido com sucesso!
echo  Executavel em: dist\VoiceVision\VoiceVision.exe
echo ================================
echo.
echo Dica: para distribuir, copie a pasta inteira "dist\VoiceVision",
echo nao apenas o .exe -- ele depende dos arquivos ao lado dele.
pause
exit /b 0

:erro
echo.
echo Ocorreu um erro durante o build. Veja as mensagens acima.
pause
exit /b 1
