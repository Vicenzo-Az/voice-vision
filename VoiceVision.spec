# -*- mode: python ; coding: utf-8 -*-
"""
Spec do PyInstaller para o Voice Vision.

Por que um .spec em vez de só flags de linha de comando?
faster-whisper depende do ctranslate2, que traz bibliotecas nativas (.dll)
e arquivos de dados que o PyInstaller não detecta sozinho. O `collect_all`
abaixo garante que tudo (código Python + binários + dados) seja incluído.

Modo escolhido: ONEDIR (uma pasta com o .exe + dependências), não ONEFILE.
Um .exe único é mais "bonito", mas empacotar ctranslate2 num único arquivo
costuma causar erros de DLL/inicialização lenta. Onedir é mais confiável
para esse tipo de dependência pesada em binários nativos.

Uso:
    pyinstaller --noconfirm VoiceVision.spec
(o build.bat já faz isso por você)
"""

from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Pacotes que precisam de coleta completa (código + binários nativos + dados)
PACOTES_COM_BINARIOS_NATIVOS = [
    "faster_whisper",
    "ctranslate2",
    "av",              # decodificação de áudio/vídeo usada pelo faster-whisper
    "tokenizers",
    "huggingface_hub",
]

for pacote in PACOTES_COM_BINARIOS_NATIVOS:
    d, b, h = collect_all(pacote)
    datas += d
    binaries += b
    hiddenimports += h

# O ícone também precisa ser incluído como DADO (não só como ícone do .exe),
# porque a janela carrega QIcon("assets/icon.ico") em tempo de execução
# (para o ícone da janela/barra de tarefas), via paths.caminho_recurso().
datas += [("assets/icon.ico", "assets")]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="VoiceVision",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # janela sem console (app "windowed")
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="VoiceVision",
)

