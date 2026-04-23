#!/usr/bin/env python3
"""
Gerador de Vídeo a partir de Mídia e Áudio

Aplicação desktop que gera vídeos MP4 combinando imagens ou vídeo
com um arquivo MP3, onde o áudio MP3 sempre predomina.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import run_app


if __name__ == "__main__":
    run_app()
