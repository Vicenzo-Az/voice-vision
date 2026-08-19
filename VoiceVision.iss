; Script do Inno Setup para o Voice Vision.
;
; O QUE ISSO FAZ:
; Empacota a pasta "dist\VoiceVision" (gerada pelo build.bat/PyInstaller) em
; um único instalador "Voice Vision Setup.exe", que:
;   - instala o app em Arquivos de Programas (ou onde o usuário escolher)
;   - cria atalho no Menu Iniciar (e opcionalmente na Área de Trabalho)
;   - registra o app em "Aplicativos instalados", com desinstalador
;
; COMO USAR:
; 1. Rode build.bat primeiro (precisa existir a pasta dist\VoiceVision).
; 2. Instale o Inno Setup: https://jrsoftware.org/isinfo.php
; 3. Abra este arquivo (VoiceVision.iss) com o Inno Setup Compiler e
;    clique em "Compile" (ou rode via linha de comando, veja o README).
; 4. O instalador final aparece em: instalador\VoiceVision-Setup-1.0.0.exe

#define MyAppName "Voice Vision"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Voice Vision"
#define MyAppExeName "VoiceVision.exe"
#define MyBuildDir "dist\VoiceVision"

[Setup]
; Identificador único do app — gerado uma vez e mantido entre versões, para
; que o Windows reconheça atualizações como "o mesmo programa" em vez de
; instalar duas cópias lado a lado.
AppId={{A6B1E2C4-6F3B-4C1D-9E52-7D4F1B0E9A11}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
OutputDir=instalador
OutputBaseFilename=VoiceVision-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\icon.ico
; Instala só para o usuário atual por padrão (não exige clique em "Executar
; como administrador"). Troque para "admin" se preferir instalar para todos
; os usuários da máquina.
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Área de Trabalho"; GroupDescription: "Atalhos adicionais:"; Flags: unchecked

[Files]
; Copia TUDO que está dentro de dist\VoiceVision (o .exe + todas as DLLs e
; dados do ctranslate2/faster-whisper) para a pasta de instalação.
Source: "{#MyBuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir {#MyAppName} agora"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Remove a pasta de instalação inteira...
Type: filesandordirs; Name: "{app}"
; ...e também os modelos do Whisper baixados pelo app, que ficam fora da
; pasta de instalação (veja pasta_modelos() em services/transcriber.py).
; Assim, desinstalar remove tudo que o app criou, sem deixar nada para trás.
Type: filesandordirs; Name: "{localappdata}\VoiceVision"
