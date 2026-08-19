"""
Janela principal do Voice Vision.

A transcrição roda em uma QThread separada (via classe Worker) para que a
interface continue responsiva enquanto o faster-whisper processa o áudio.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThread, Signal, Slot
from PySide6.QtGui import QClipboard, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.transcriber import (
    AJUDA_IDIOMA,
    AJUDA_MODELO,
    IDIOMAS_DISPONIVEIS,
    MODELOS_DISPONIVEIS,
    Transcriber,
    pasta_modelos,
)

# Extensões de áudio aceitas (usadas no filtro do diálogo e no drag & drop)
EXTENSOES_AUDIO = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}

ORGANIZACAO = "VoiceVision"
APLICATIVO = "VoiceVision"


class Worker(QThread):
    """Executa a transcrição em uma thread separada."""

    progresso = Signal(str)
    percentual = Signal(int)
    concluido = Signal(str, str)  # texto, idioma_detectado
    cancelado = Signal()
    erro = Signal(str)

    def __init__(self, transcriber: Transcriber, caminho_audio: Path, modelo: str, idioma):
        super().__init__()
        self._transcriber = transcriber
        self._caminho_audio = caminho_audio
        self._modelo = modelo
        self._idioma = idioma
        self._cancelado = False

    def cancelar(self) -> None:
        self._cancelado = True

    def run(self) -> None:
        try:
            resultado = self._transcriber.transcrever(
                caminho_audio=self._caminho_audio,
                nome_modelo=self._modelo,
                idioma=self._idioma,
                progresso=self.progresso.emit,
                percentual=self.percentual.emit,
                deve_cancelar=lambda: self._cancelado,
            )
            if self._cancelado:
                self.cancelado.emit()
            else:
                self.concluido.emit(resultado.texto, resultado.idioma_detectado)
        except Exception as exc:  # noqa: BLE001 - queremos mostrar qualquer erro ao usuário
            self.erro.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Voice Vision")
        self.setMinimumWidth(540)

        self._transcriber = Transcriber()
        self._worker: Worker | None = None
        self._caminho_audio: Path | None = None
        self._settings = QSettings(ORGANIZACAO, APLICATIVO)

        self.setAcceptDrops(True)

        self._montar_interface()
        self._aplicar_estilo()
        self._carregar_preferencias()

    # ------------------------------------------------------------------ UI

    def _criar_botao_ajuda(self, titulo: str, texto: str) -> QPushButton:
        """Pequeno botão '?' que mostra informações detalhadas ao ser clicado."""
        botao = QPushButton("?")
        botao.setObjectName("botaoAjuda")
        botao.setFixedSize(20, 20)
        botao.setCursor(Qt.CursorShape.PointingHandCursor)
        botao.setToolTip("Mais informações")
        botao.clicked.connect(lambda: QMessageBox.information(self, titulo, texto))
        return botao

    def _montar_interface(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        titulo = QLabel("🎙  Voice Vision")
        titulo.setObjectName("titulo")
        subtitulo = QLabel("Transcrição de áudio com Whisper")
        subtitulo.setObjectName("subtitulo")
        layout.addWidget(titulo)
        layout.addWidget(subtitulo)

        # --- seleção de arquivo ---
        layout.addWidget(QLabel("Arquivo de áudio"))
        linha_arquivo = QHBoxLayout()
        self.campo_arquivo = QPlainTextEdit()
        self.campo_arquivo.setReadOnly(True)
        self.campo_arquivo.setFixedHeight(36)
        self.campo_arquivo.setPlaceholderText(
            "Nenhum arquivo selecionado (ou arraste um arquivo de áudio aqui)"
        )
        botao_selecionar = QPushButton("Selecionar arquivo")
        botao_selecionar.clicked.connect(self._selecionar_arquivo)
        linha_arquivo.addWidget(self.campo_arquivo)
        linha_arquivo.addWidget(botao_selecionar)
        layout.addLayout(linha_arquivo)

        # --- modelo e idioma (cada um com um botão de ajuda "?") ---
        linha_opcoes = QHBoxLayout()

        coluna_modelo = QVBoxLayout()
        linha_label_modelo = QHBoxLayout()
        linha_label_modelo.setSpacing(6)
        linha_label_modelo.addWidget(QLabel("Modelo"))
        linha_label_modelo.addWidget(self._criar_botao_ajuda("Sobre o modelo", AJUDA_MODELO))
        linha_label_modelo.addStretch()
        coluna_modelo.addLayout(linha_label_modelo)
        self.combo_modelo = QComboBox()
        self.combo_modelo.addItems(MODELOS_DISPONIVEIS)
        self.combo_modelo.setCurrentText("small")
        self.combo_modelo.currentTextChanged.connect(self._salvar_preferencias)
        coluna_modelo.addWidget(self.combo_modelo)

        coluna_idioma = QVBoxLayout()
        linha_label_idioma = QHBoxLayout()
        linha_label_idioma.setSpacing(6)
        linha_label_idioma.addWidget(QLabel("Idioma"))
        linha_label_idioma.addWidget(self._criar_botao_ajuda("Sobre o idioma", AJUDA_IDIOMA))
        linha_label_idioma.addStretch()
        coluna_idioma.addLayout(linha_label_idioma)
        self.combo_idioma = QComboBox()
        self.combo_idioma.addItems(IDIOMAS_DISPONIVEIS.keys())
        self.combo_idioma.currentTextChanged.connect(self._salvar_preferencias)
        coluna_idioma.addWidget(self.combo_idioma)

        linha_opcoes.addLayout(coluna_modelo)
        linha_opcoes.addLayout(coluna_idioma)
        layout.addLayout(linha_opcoes)

        # --- botões transcrever / parar ---
        linha_transcricao = QHBoxLayout()
        self.botao_transcrever = QPushButton("TRANSCREVER")
        self.botao_transcrever.setObjectName("botaoPrincipal")
        self.botao_transcrever.clicked.connect(self._iniciar_transcricao)

        self.botao_parar = QPushButton("Parar Transcrição")
        self.botao_parar.setObjectName("botaoParar")
        self.botao_parar.setEnabled(False)
        self.botao_parar.clicked.connect(self._parar_transcricao)

        linha_transcricao.addWidget(self.botao_transcrever, 2)
        linha_transcricao.addWidget(self.botao_parar, 1)
        layout.addLayout(linha_transcricao)

        # --- status e progresso ---
        self.label_status = QLabel("● Pronto para transcrever")
        self.label_status.setObjectName("status")
        self.label_status.setToolTip(f"Modelos são salvos em: {pasta_modelos()}")
        layout.addWidget(self.label_status)

        self.barra_progresso = QProgressBar()
        self.barra_progresso.setRange(0, 100)
        self.barra_progresso.setValue(0)
        self.barra_progresso.setTextVisible(True)
        layout.addWidget(self.barra_progresso)

        # --- área de transcrição ---
        layout.addWidget(QLabel("Transcrição"))
        self.area_texto = QPlainTextEdit()
        self.area_texto.setPlaceholderText("O texto transcrito aparecerá aqui...")
        layout.addWidget(self.area_texto)

        # --- ações finais ---
        linha_acoes = QHBoxLayout()
        self.botao_salvar = QPushButton("Salvar .txt")
        self.botao_salvar.clicked.connect(self._salvar_transcricao)
        self.botao_salvar.setEnabled(False)

        self.botao_copiar = QPushButton("Copiar texto")
        self.botao_copiar.clicked.connect(self._copiar_transcricao)
        self.botao_copiar.setEnabled(False)

        self.botao_abrir_pasta = QPushButton("Abrir pasta do áudio")
        self.botao_abrir_pasta.clicked.connect(self._abrir_pasta_audio)
        self.botao_abrir_pasta.setEnabled(False)

        linha_acoes.addWidget(self.botao_salvar)
        linha_acoes.addWidget(self.botao_copiar)
        linha_acoes.addWidget(self.botao_abrir_pasta)
        layout.addLayout(linha_acoes)

    def _aplicar_estilo(self) -> None:
        # A base de cores (janela, campos, texto) já vem do QPalette escuro
        # aplicado em main.py — aqui só cuidamos de detalhes específicos
        # (título, botões de destaque, botão de ajuda, barra de progresso).
        self.setStyleSheet(
            """
            QWidget { font-family: 'Segoe UI'; font-size: 13px; }
            #titulo { font-size: 20px; font-weight: 600; color: #f2f2f2; }
            #subtitulo { color: #9a9a9a; margin-bottom: 8px; }
            #status { color: #cfcfcf; margin-top: 4px; }

            QPushButton {
                padding: 8px 14px;
                border-radius: 6px;
                border: 1px solid #3d3d3d;
                background: #2a2a2a;
                color: #e6e6e6;
            }
            QPushButton:hover { background: #333333; }
            QPushButton:disabled { color: #6e6e6e; background: #232323; border-color: #2e2e2e; }

            #botaoPrincipal {
                background: #4f8cff;
                color: #0f0f0f;
                font-weight: 600;
                border: none;
                padding: 10px;
            }
            #botaoPrincipal:hover { background: #6c9fff; }
            #botaoPrincipal:disabled { background: #274a86; color: #7f92b8; }

            #botaoParar {
                background: transparent;
                color: #ff6b6b;
                border: 1px solid #7a3535;
                padding: 10px;
            }
            #botaoParar:hover { background: #3a2323; }
            #botaoParar:disabled { color: #6e6e6e; border-color: #2e2e2e; }

            #botaoAjuda {
                padding: 0px;
                border-radius: 10px;
                border: 1px solid #4a4a4a;
                background: #333333;
                color: #cfcfcf;
                font-weight: 600;
            }
            #botaoAjuda:hover { background: #3d3d3d; color: #ffffff; }

            QComboBox, QPlainTextEdit {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 6px;
                background: #1e1e1e;
                color: #e6e6e6;
            }
            QComboBox QAbstractItemView {
                background: #232323;
                color: #e6e6e6;
                selection-background-color: #4f8cff;
                selection-color: #0f0f0f;
            }

            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                background: #1e1e1e;
                color: #e6e6e6;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #4f8cff;
                border-radius: 5px;
            }
            """
        )

    # -------------------------------------------------------------- ações

    def _selecionar_arquivo(self) -> None:
        pasta_inicial = self._settings.value("ultima_pasta", "")
        caminho, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo de áudio",
            pasta_inicial,
            "Áudio (*.mp3 *.wav *.m4a *.ogg *.flac);;Todos os arquivos (*.*)",
        )
        if caminho:
            self._definir_arquivo(Path(caminho))

    def _definir_arquivo(self, caminho: Path) -> None:
        self._caminho_audio = caminho
        self.campo_arquivo.setPlainText(str(caminho))
        self.botao_abrir_pasta.setEnabled(True)
        self._settings.setValue("ultima_pasta", str(caminho.parent))

    # --------------------------------------------------------- drag & drop

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and Path(urls[0].toLocalFile()).suffix.lower() in EXTENSOES_AUDIO:
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls = event.mimeData().urls()
        if not urls:
            return
        caminho = Path(urls[0].toLocalFile())
        if caminho.suffix.lower() not in EXTENSOES_AUDIO:
            QMessageBox.warning(
                self, "Formato não suportado",
                f"'{caminho.suffix}' não é um formato de áudio suportado.",
            )
            return
        self._definir_arquivo(caminho)
        event.acceptProposedAction()

    # ---------------------------------------------------------- preferências

    def _carregar_preferencias(self) -> None:
        modelo = self._settings.value("modelo", "small")
        idioma = self._settings.value("idioma", "Português")
        if modelo in MODELOS_DISPONIVEIS:
            self.combo_modelo.setCurrentText(modelo)
        if idioma in IDIOMAS_DISPONIVEIS:
            self.combo_idioma.setCurrentText(idioma)

    def _salvar_preferencias(self) -> None:
        self._settings.setValue("modelo", self.combo_modelo.currentText())
        self._settings.setValue("idioma", self.combo_idioma.currentText())

    # -------------------------------------------------------- transcrição

    def _iniciar_transcricao(self) -> None:
        if self._caminho_audio is None:
            QMessageBox.warning(self, "Atenção", "Selecione um arquivo de áudio primeiro.")
            return

        modelo = self.combo_modelo.currentText()
        idioma_label = self.combo_idioma.currentText()
        idioma = IDIOMAS_DISPONIVEIS[idioma_label]

        self.botao_transcrever.setEnabled(False)
        self.botao_parar.setEnabled(True)
        self.botao_salvar.setEnabled(False)
        self.botao_copiar.setEnabled(False)
        self.area_texto.clear()
        self.barra_progresso.setValue(0)
        self.label_status.setText("● Iniciando...")

        self._worker = Worker(self._transcriber, self._caminho_audio, modelo, idioma)
        self._worker.progresso.connect(self._on_progresso)
        self._worker.percentual.connect(self._on_percentual)
        self._worker.concluido.connect(self._on_concluido)
        self._worker.cancelado.connect(self._on_cancelado)
        self._worker.erro.connect(self._on_erro)
        self._worker.start()

    def _parar_transcricao(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancelar()
            self.botao_parar.setEnabled(False)
            self.label_status.setText("● Cancelando...")

    @Slot(str)
    def _on_progresso(self, mensagem: str) -> None:
        self.label_status.setText(f"● {mensagem}")

    @Slot(int)
    def _on_percentual(self, pct: int) -> None:
        self.barra_progresso.setValue(pct)

    @Slot(str, str)
    def _on_concluido(self, texto: str, idioma_detectado: str) -> None:
        self.area_texto.setPlainText(texto)
        self.label_status.setText(f"● Concluído — idioma detectado: {idioma_detectado}")
        self.botao_transcrever.setEnabled(True)
        self.botao_parar.setEnabled(False)
        self.botao_salvar.setEnabled(True)
        self.botao_copiar.setEnabled(True)

    @Slot()
    def _on_cancelado(self) -> None:
        self.label_status.setText("● Transcrição cancelada")
        self.barra_progresso.setValue(0)
        self.botao_transcrever.setEnabled(True)
        self.botao_parar.setEnabled(False)

    @Slot(str)
    def _on_erro(self, mensagem: str) -> None:
        self.label_status.setText("● Ocorreu um erro")
        self.barra_progresso.setValue(0)
        self.botao_transcrever.setEnabled(True)
        self.botao_parar.setEnabled(False)
        QMessageBox.critical(self, "Erro na transcrição", mensagem)

    def _copiar_transcricao(self) -> None:
        texto = self.area_texto.toPlainText()
        if not texto:
            return
        QApplication.clipboard().setText(texto, QClipboard.Mode.Clipboard)
        self.label_status.setText("● Transcrição copiada para a área de transferência")

    def _salvar_transcricao(self) -> None:
        if self._caminho_audio is None:
            return

        sugestao = str(self._caminho_audio.with_suffix("").with_name(
            self._caminho_audio.stem + "_transcricao.txt"
        ))
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar transcrição", sugestao, "Texto (*.txt)"
        )
        if caminho:
            Path(caminho).write_text(self.area_texto.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "Salvo", f"Transcrição salva em:\n{caminho}")

    def _abrir_pasta_audio(self) -> None:
        if self._caminho_audio is None:
            return
        pasta = self._caminho_audio.parent
        if sys.platform == "win32":
            os.startfile(pasta)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", str(pasta)])
        else:
            subprocess.run(["xdg-open", str(pasta)])

    def closeEvent(self, event) -> None:  # noqa: N802 - método do Qt
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancelar()
            self._worker.wait(2000)
        event.accept()
