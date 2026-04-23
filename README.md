# Gerador de Vídeo a partir de Mídia e Áudio

Aplicação desktop Python que gera vídeos MP4 combinando imagens ou vídeo com um arquivo MP3.

## Funcionalidades

- **Uma única imagem** → exibida durante toda a duração do MP3
- **Múltiplas imagens** → distribuídas igualmente pela duração do MP3
- **Arquivo de vídeo** → áudio original removido, MP3 substitui

O áudio MP3 **sempre predomina** em todos os casos.

## Requisitos

- Python 3.8+
- FFmpeg instalado no sistema

## Instalação

1. Clone o repositório:
```bash
git clone <repo-url>
cd gerador-video-basico
```

2. Crie um ambiente virtual (recomendado):
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale o FFmpeg (se ainda não tiver):
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Baixe de https://ffmpeg.org/download.html
```

## Uso

Execute a aplicação:
```bash
python main.py
```

### Interface

1. **Adicionar Mídia**: Clique em "Adicionar Imagens" ou "Adicionar Vídeo"
2. **Reordenar**: Use os botões "↑ Subir" e "↓ Descer" para reordenar imagens
3. **Selecionar Áudio**: Clique em "Selecionar MP3" para escolher o áudio
4. **Escolher Saída**: Clique em "Escolher Local" para definir onde salvar
5. **Gerar**: Clique em "Gerar Vídeo" e aguarde a conclusão

## Formatos Suportados

### Imagens
- JPG, JPEG, PNG, BMP, GIF, WEBP

### Vídeos
- MP4, AVI, MOV, MKV, WEBM

### Áudio
- MP3

## Estrutura do Projeto

```
gerador-video-basico/
├── main.py              # Ponto de entrada
├── gui/
│   └── app.py           # Interface gráfica Tkinter
├── core/
│   └── video_generator.py  # Lógica de geração
├── requirements.txt     # Dependências
└── README.md            # Este arquivo
```

## Licença

MIT
