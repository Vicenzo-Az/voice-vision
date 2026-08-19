# 🎙️ Voice Vision

App desktop para Windows que transcreve áudio para texto localmente, usando
[faster-whisper](https://github.com/SYSTRAN/faster-whisper) — sem enviar
nada para a nuvem. Interface em dark mode, feita com PySide6.

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/UI-PySide6-41cd52?logo=qt&logoColor=white)
![Whisper](https://img.shields.io/badge/ASR-faster--whisper-orange)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)
[![Latest release](https://img.shields.io/github/v/release/Vicenzo-Az/voice-vision?label=vers%C3%A3o&color=4f8cff)](https://github.com/Vicenzo-Az/voice-vision/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/Vicenzo-Az/voice-vision/total?label=downloads&color=4f8cff)](https://github.com/Vicenzo-Az/voice-vision/releases/latest)

### [⬇️ Baixar Voice Vision](https://github.com/Vicenzo-Az/voice-vision/releases/latest)

![Voice Vision screenshot](docs/screenshot.png)

<!--
  Dica: troque este bloco por um screenshot ou GIF real do app rodando.
  Ex.: ![Voice Vision screenshot](docs/screenshot.png)
  Um GIF curto mostrando arrastar um áudio -> transcrever -> copiar
  costuma ser o que mais chama atenção em um perfil do GitHub.
-->

## Sumário

- [Baixar](#️-baixar-voice-vision)
- [Funcionalidades](#o-que-já-está-pronto)
- [Como rodar (desenvolvimento)](#como-rodar-desenvolvimento)
- [Gerando o .exe](#gerando-o-exe)
- [Gerando o instalador](#gerando-o-instalador-inno-setup)
- [Estrutura do projeto](#estrutura)
- [Licença](#licença)

## Estrutura

```
VoiceVision/
├── main.py                   # ponto de entrada, tema escuro, ícone
├── paths.py                  # localiza recursos (ícone) em dev e no .exe
├── requirements.txt
├── requirements-build.txt    # só o PyInstaller, usado na hora de gerar o .exe
├── build.bat                 # gera o .exe com um clique (Windows)
├── VoiceVision.spec          # configuração do PyInstaller
├── VoiceVision.iss           # script do Inno Setup (gera o instalador)
├── assets/
│   └── icon.ico               # ícone do app
├── ui/
│   └── main_window.py     # interface PySide6
└── services/
    └── transcriber.py     # lógica do faster-whisper
```

## Como rodar (desenvolvimento)

```powershell
cd VoiceVision
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## O que já está pronto

- Selecionar arquivo de áudio (.mp3, .wav, .m4a, .ogg, .flac)
- **Arrastar e soltar** um arquivo de áudio direto na janela
- Escolher modelo (tiny/base/small/medium) e idioma, cada um com um botão
  **"?"** ao lado explicando as opções em detalhe
- Transcrever em segundo plano (QThread) sem travar a interface
- **Botão "Parar Transcrição"**, para interromper uma transcrição em andamento
- **Barra de progresso real** (baseada na duração do áudio já processada)
- Status textual em tempo real
- Exibir o texto transcrito na janela
- Salvar a transcrição como `.txt` onde você quiser
- **Copiar a transcrição** para a área de transferência com um clique
- Abrir a pasta do áudio original
- **Lembra o último modelo, idioma e pasta usados** entre execuções (via `QSettings`)
- **Dark mode** em todo o app, incluindo diálogos nativos (salvar arquivo, mensagens)
- **Ícone próprio na barra de tarefas** do Windows, tanto em desenvolvimento
  quanto no `.exe`
- Mensagens de erro amigáveis (via QMessageBox)

O modelo do faster-whisper só é carregado na primeira vez que você clica em
"Transcrever" (evita gastar RAM com o app parado) e fica em cache entre
transcrições subsequentes, na mesma sessão.

### Sobre a barra de progresso

O faster-whisper processa o áudio em segmentos e informa, para cada um, o
tempo (`segmento.end`) já processado. A barra usa `segmento.end / duração
total do áudio` para estimar o percentual — não é uma medição de CPU, é uma
estimativa baseada em quanto do áudio já foi transcrito.

### Sobre o botão "Parar Transcrição"

A transcrição roda segmento por segmento; ao clicar em "Parar", o app avisa
a thread de trabalho para interromper assim que o segmento atual terminar
(não dá para interromper no meio de um segmento, pois o faster-whisper não
permite isso). Na prática a resposta costuma ser bem rápida. O texto
transcrito até o momento da parada é descartado — se quiser aproveitar um
resultado parcial, é melhor deixar terminar.

### Sobre o dark mode

O tema escuro é aplicado via `QPalette` (em `main.py`, função
`_aplicar_tema_escuro`), não só um stylesheet — por isso ele também escurece
diálogos nativos do Windows abertos pelo Qt, como o de "Salvar arquivo" e as
caixas de mensagem, além dos widgets da própria janela.

### Onde as preferências ficam salvas

O `QSettings` grava no local padrão do sistema operacional (no Windows, no
Registro, em `HKEY_CURRENT_USER\Software\VoiceVision\VoiceVision`). Não
precisa criar nenhum arquivo manualmente.

### Onde o modelo do Whisper fica salvo

Em vez do cache padrão do `huggingface_hub` (que pode variar), o app salva
os modelos baixados em um local fixo e previsível:

```
%LOCALAPPDATA%\VoiceVision\modelos
```

Isso vale tanto rodando com `python main.py` quanto no `.exe` — assim o
modelo baixado numa execução continua disponível na próxima, mesmo depois
de reinstalar o app. Esse caminho aparece como dica (tooltip) se você passar
o mouse sobre a linha de status no app.

A estratégia escolhida é **baixar o modelo na primeira execução** (precisa
de internet uma vez; `.exe`/instalador inicial menor). Se no futuro você
quiser a estratégia de embutir o modelo (100% offline), me avise — dá para
adicionar os arquivos do modelo em `datas` no `.spec` e apontar o
`download_root` para essa pasta embutida.

---

## Gerando o .exe

### O jeito fácil: `build.bat`

Na pasta do projeto, dê duplo clique em `build.bat` (ou rode pelo
PowerShell/CMD). Ele cria o ambiente virtual se precisar, instala tudo,
limpa builds antigos e roda o PyInstaller com a configuração já pronta em
`VoiceVision.spec`.

Ao final, o app fica em:

```
dist\VoiceVision\VoiceVision.exe
```

**Importante:** para distribuir sem instalador, copie a pasta
`dist\VoiceVision` inteira, não só o `.exe` — ele depende dos arquivos ao
lado (DLLs do ctranslate2, etc.). Pode compactar essa pasta em um `.zip`.
Se você vai gerar o instalador (próxima seção), não precisa fazer isso
manualmente.

### Por que um `.spec` em vez de só `pyinstaller main.py`?

O `faster-whisper` depende do `ctranslate2`, que traz bibliotecas nativas
(`.dll`) e arquivos de dados que o PyInstaller **não** detecta sozinho por
padrão. O `VoiceVision.spec` já resolve isso usando `collect_all()` para:

- `faster_whisper`
- `ctranslate2`
- `av` (decodificação de áudio)
- `tokenizers`
- `huggingface_hub`

Também escolhemos o modo **onedir** (uma pasta com o `.exe` + dependências)
em vez de **onefile** (um único `.exe`). Onefile parece mais "limpo", mas
empacotar bibliotecas nativas pesadas como as do `ctranslate2` num único
arquivo costuma causar erros de DLL ou inicialização bem mais lenta. Onedir
é mais robusto para esse caso — e é justamente essa pasta (`dist\VoiceVision`)
que o instalador do Inno Setup empacota.

### Se algo der errado no build

- **`ModuleNotFoundError` ao abrir o `.exe`**: normalmente falta algum
  pacote no `collect_all`. Rode o app pelo terminal
  (`dist\VoiceVision\VoiceVision.exe`, direto no CMD, não por duplo clique)
  para ver o traceback completo e me avise qual módulo faltou.
- **Antivírus/SmartScreen bloqueando o `.exe`**: comum em executáveis
  gerados com PyInstaller sem certificado de assinatura. Não indica
  problema no código.
- **Build muito lento ou `.exe` gigante**: normal — `ctranslate2` e as
  dependências de ML são pesadas (algumas centenas de MB na pasta final).
- **Erro ao iniciar sem mensagem nenhuma**: o `main.py` já captura exceções
  na inicialização e mostra numa caixa de diálogo. Se mesmo assim não
  aparecer nada, rode pelo CMD.

---

## Gerando o instalador (Inno Setup)

O instalador transforma a pasta `dist\VoiceVision` num único
`VoiceVision-Setup-1.0.0.exe` que instala o app de verdade: atalho no Menu
Iniciar, opção de atalho na Área de Trabalho, e entrada em "Aplicativos
instalados" com desinstalador.

### 1. Instalar o Inno Setup

Baixe e instale (gratuito): https://jrsoftware.org/isdl.php

### 2. Gerar a pasta `dist\VoiceVision`

Rode `build.bat` normalmente (ver seção acima) — o instalador empacota o
que estiver em `dist\VoiceVision`, então esse passo precisa vir antes.

### 3. Compilar o instalador

**Pela interface:** abra `VoiceVision.iss` com o "Inno Setup Compiler"
(instalado no passo 1) e clique em **Build > Compile** (ou aperte `Ctrl+F9`).

**Pela linha de comando** (útil para automatizar):

```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" VoiceVision.iss
```

O instalador final aparece em:

```
instalador\VoiceVision-Setup-1.0.0.exe
```

Esse é o arquivo que você distribui — o usuário final só precisa dele.

### O que o `VoiceVision.iss` já configura

- Nome, versão e ícone do app (usa o mesmo `assets\icon.ico`)
- Instalação padrão em `Arquivos de Programas\Voice Vision`, sem exigir
  privilégio de administrador (`PrivilegesRequired=lowest`)
- Atalho no Menu Iniciar sempre; atalho na Área de Trabalho como opção
  (checkbox desmarcado por padrão) durante a instalação
- Desinstalador automático, incluindo remover a pasta de instalação **e**
  os modelos do Whisper baixados (`%LOCALAPPDATA%\VoiceVision`) — a
  desinstalação não deixa nada para trás
- Assistente em português (usa o pacote de idioma `BrazilianPortuguese`
  do próprio Inno Setup)
- Opção de abrir o app automaticamente ao final da instalação

**Um detalhe importante:** como a desinstalação apaga os modelos baixados,
uma reinstalação vai precisar baixá-los de novo (internet necessária na
primeira transcrição pós-reinstalação). Se no futuro preferir preservar os
modelos entre desinstalações — por exemplo, para o caso de reinstalar uma
versão nova sem perder o que já foi baixado — é só remover a segunda linha
do bloco `[UninstallDelete]` no `.iss`.

### Atualizando a versão

Ao lançar uma nova versão do app, edite a linha `#define MyAppVersion` no
topo do `VoiceVision.iss` antes de recompilar — isso aparece em
"Aplicativos instalados" do Windows e ajuda o Inno Setup a lidar
corretamente com atualizações (o `AppId` já fixo garante que ele reconheça
como o mesmo programa).

---

## Licença

Distribuído sob a licença MIT — veja [LICENSE](LICENSE) para o texto completo.