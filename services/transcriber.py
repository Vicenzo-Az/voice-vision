"""
Serviço de transcrição de áudio usando faster-whisper.

Este módulo NÃO conhece nada de interface gráfica. Ele apenas expõe uma
função/worker que transcreve um arquivo e reporta progresso através de
callbacks. Isso mantém a lógica de negócio separada da UI (PySide6).
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from faster_whisper import WhisperModel


# Idiomas que aparecerão no combo da interface -> código usado pelo faster-whisper
IDIOMAS_DISPONIVEIS = {
    "Português": "pt",
    "Inglês": "en",
    "Espanhol": "es",
    "Automático (detectar)": None,
}

MODELOS_DISPONIVEIS = ["tiny", "base", "small", "medium"]

AJUDA_MODELO = (
    "O modelo define o equilíbrio entre velocidade e precisão da transcrição:\n\n"
    "• tiny — o mais rápido, mas com mais erros. Bom para testes rápidos.\n"
    "• base — rápido, precisão um pouco melhor que o tiny.\n"
    "• small — bom equilíbrio entre velocidade e qualidade. Recomendado para a maioria dos casos.\n"
    "• medium — mais preciso, principalmente com sotaques, ruído de fundo ou áudio de baixa "
    "qualidade, porém mais lento e consome mais memória.\n\n"
    "Na primeira vez que você usa um modelo, ele é baixado da internet (uma única vez) e fica "
    "salvo localmente para as próximas transcrições."
)

AJUDA_IDIOMA = (
    "Define o idioma do áudio a ser transcrito.\n\n"
    "Selecionar o idioma correto (em vez de 'Automático') deixa a transcrição mais rápida e "
    "mais precisa, pois o modelo não precisa gastar tempo detectando o idioma.\n\n"
    "Use 'Automático (detectar)' quando não souber o idioma do áudio com certeza, ou quando o "
    "arquivo tiver trechos em mais de um idioma."
)


def pasta_modelos() -> Path:
    """
    Pasta onde os modelos do Whisper ficam armazenados localmente.

    Usamos um local fixo e previsível (fora da pasta do app) em vez do cache
    padrão do huggingface_hub, para que o usuário saiba exatamente onde os
    modelos baixados ficam — tanto rodando com `python main.py` quanto no
    `.exe` gerado pelo PyInstaller (onde a pasta do app pode ser somente
    leitura ou temporária, dependendo de como foi instalado).
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    pasta = base / "VoiceVision" / "modelos"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


@dataclass
class ResultadoTranscricao:
    texto: str
    idioma_detectado: str
    caminho_audio: Path


class Transcriber:
    """
    Encapsula o carregamento do modelo e a transcrição.

    O modelo só é carregado na primeira chamada de `transcrever`, para não
    consumir RAM enquanto o app está parado (conforme decidido no histórico).
    """

    def __init__(self) -> None:
        self._model: Optional[WhisperModel] = None
        self._modelo_carregado: Optional[str] = None

    def _garantir_modelo(self, nome_modelo: str, progresso: Callable[[str], None]) -> None:
        if self._model is None or self._modelo_carregado != nome_modelo:
            progresso(f"Carregando modelo '{nome_modelo}'...")
            self._model = WhisperModel(
                nome_modelo,
                device="cpu",
                compute_type="int8",
                download_root=str(pasta_modelos()),
            )
            self._modelo_carregado = nome_modelo

    def transcrever(
        self,
        caminho_audio: Path,
        nome_modelo: str,
        idioma: Optional[str],
        progresso: Callable[[str], None] = lambda msg: None,
        percentual: Callable[[int], None] = lambda pct: None,
        deve_cancelar: Callable[[], bool] = lambda: False,
    ) -> ResultadoTranscricao:
        """
        Transcreve um arquivo de áudio.

        Args:
            caminho_audio: caminho do arquivo de áudio.
            nome_modelo: um de MODELOS_DISPONIVEIS.
            idioma: código de idioma (ex: "pt") ou None para detecção automática.
            progresso: callback chamado com mensagens de status (texto).
            percentual: callback chamado com o progresso em % (0-100), baseado
                na duração total do áudio (info.duration).
            deve_cancelar: callback que, se retornar True, interrompe a transcrição
                assim que possível (checado entre segmentos).
        """
        self._garantir_modelo(nome_modelo, progresso)
        assert self._model is not None

        progresso("Analisando áudio...")
        percentual(0)
        segments, info = self._model.transcribe(
            str(caminho_audio),
            language=idioma,
            task="transcribe",
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=True,
        )

        duracao_total = max(info.duration, 0.001)  # evita divisão por zero
        partes: list[str] = []
        for segmento in segments:
            if deve_cancelar():
                progresso("Transcrição cancelada.")
                break

            texto = segmento.text.strip()
            if texto:
                partes.append(texto)

            # segmento.end é o tempo (em segundos) já processado do áudio
            pct = min(int((segmento.end / duracao_total) * 100), 100)
            percentual(pct)
            progresso(f"Transcrevendo... ({segmento.end:.0f}s de {duracao_total:.0f}s)")

        if not deve_cancelar():
            percentual(100)

        texto_final = "\n".join(partes)
        return ResultadoTranscricao(
            texto=texto_final,
            idioma_detectado=info.language,
            caminho_audio=caminho_audio,
        )
