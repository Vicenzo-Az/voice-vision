"""Ponto de entrada do Voice Vision."""

import sys
import traceback

from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

from paths import caminho_recurso
from ui.main_window import MainWindow

# Identificador único do app. No Windows, isso faz o ícone correto aparecer
# na barra de tarefas (em vez do ícone genérico do python.exe) quando o app
# roda via `python main.py`. No .exe empacotado isso já funciona por padrão,
# mas não custa manter para os dois casos.
APP_USER_MODEL_ID = "VoiceVision.App.1"


def _configurar_icone_barra_tarefas() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        # Falha aqui não é crítica — o app continua funcionando, só o
        # agrupamento/ícone na barra de tarefas pode não ficar perfeito.
        pass


def _aplicar_tema_escuro(app: QApplication) -> None:
    app.setStyle("Fusion")

    cor_janela = QColor(30, 30, 30)
    cor_base = QColor(24, 24, 24)
    cor_campo = QColor(37, 37, 38)
    cor_texto = QColor(230, 230, 230)
    cor_texto_fraco = QColor(140, 140, 140)
    cor_destaque = QColor(79, 140, 255)
    cor_desabilitado = QColor(110, 110, 110)

    paleta = QPalette()
    paleta.setColor(QPalette.ColorRole.Window, cor_janela)
    paleta.setColor(QPalette.ColorRole.WindowText, cor_texto)
    paleta.setColor(QPalette.ColorRole.Base, cor_base)
    paleta.setColor(QPalette.ColorRole.AlternateBase, cor_campo)
    paleta.setColor(QPalette.ColorRole.ToolTipBase, cor_campo)
    paleta.setColor(QPalette.ColorRole.ToolTipText, cor_texto)
    paleta.setColor(QPalette.ColorRole.Text, cor_texto)
    paleta.setColor(QPalette.ColorRole.Button, cor_campo)
    paleta.setColor(QPalette.ColorRole.ButtonText, cor_texto)
    paleta.setColor(QPalette.ColorRole.BrightText, QColor(255, 90, 90))
    paleta.setColor(QPalette.ColorRole.Link, cor_destaque)
    paleta.setColor(QPalette.ColorRole.Highlight, cor_destaque)
    paleta.setColor(QPalette.ColorRole.HighlightedText, QColor(15, 15, 15))
    paleta.setColor(QPalette.ColorRole.PlaceholderText, cor_texto_fraco)

    paleta.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, cor_desabilitado)
    paleta.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, cor_desabilitado)
    paleta.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, cor_desabilitado)

    app.setPalette(paleta)


def main() -> None:
    _configurar_icone_barra_tarefas()

    app = QApplication(sys.argv)
    app.setApplicationName("Voice Vision")
    app.setOrganizationName("VoiceVision")

    _aplicar_tema_escuro(app)

    icone = QIcon(str(caminho_recurso("assets/icon.ico")))
    app.setWindowIcon(icone)

    try:
        janela = MainWindow()
        janela.setWindowIcon(icone)
    except Exception:
        # No .exe "windowed" não existe console para ver o erro, então
        # mostramos numa caixa de diálogo em vez de a janela simplesmente
        # não abrir sem explicação.
        QMessageBox.critical(
            None,
            "Erro ao iniciar",
            "Não foi possível iniciar o Voice Vision:\n\n" + traceback.format_exc(),
        )
        sys.exit(1)

    janela.resize(560, 680)
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
