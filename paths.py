"""
Localiza arquivos de recursos (ícone, etc.) tanto rodando via
`python main.py` (modo desenvolvimento) quanto no `.exe` gerado pelo
PyInstaller (modo "congelado").
"""

import sys
from pathlib import Path


def caminho_recurso(relativo: str) -> Path:
    """
    Resolve o caminho de um arquivo de recurso do projeto.

    Em modo congelado, o PyInstaller define `sys._MEIPASS` apontando para a
    pasta onde os dados empacotados (via `datas` no .spec) foram colocados.
    Em modo desenvolvimento, usamos a raiz do projeto (pasta deste arquivo).
    """
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relativo
