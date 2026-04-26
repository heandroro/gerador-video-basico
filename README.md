# Gerador de Vídeo a partir de Mídia e Áudio

Aplicação desktop Python que gera vídeos MP4 combinando imagens ou vídeo com um arquivo MP3.

## Funcionalidades

- **Uma única imagem** → exibida durante toda a duração do MP3
- **Múltiplas imagens** → distribuídas igualmente pela duração do MP3
- **Arquivo de vídeo** → áudio original removido, MP3 substitui
- **Transições** → efeitos visuais entre imagens com configuração global e individual
- **Sugestões IA** → Ollama analisa imagens e sugere transições automaticamente (opcional)

O áudio MP3 **sempre predomina** em todos os casos.

## Requisitos

- Python 3.8+
- FFmpeg instalado no sistema
- Ollama (opcional, para sugestões IA)

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
3. **Configurar Transições**: Ative transições e escolha tipo/duração (veja abaixo)
4. **Selecionar Áudio**: Clique em "Selecionar MP3" para escolher o áudio
5. **Escolher Saída**: Clique em "Escolher Local" para definir onde salvar
6. **Gerar**: Clique em "Gerar Vídeo" e aguarde a conclusão

### Transições

#### Tipos Disponíveis
- **Nenhum** - Corte direto entre imagens
- **Fade** - Escurece para preto e clareia
- **Crossfade** - Dissolve suave entre imagens
- **Slide** - Desliza em 4 direções (esquerda, direita, cima, baixo)
- **Wipe** - Cortina em 4 direções
- **Blur** - Desfoca e foca

#### Configuração Global
- Marque "Ativar transições" para habilitar
- Escolha o tipo de transição padrão
- Defina a duração (0.5s a 3.0s)

#### Configuração Individual
- Selecione uma imagem na lista
- Marque "Personalizar" para definir transição específica
- Imagens com transição personalizada são marcadas com ★

#### Sugestões IA (Ollama)
- Instale Ollama: `brew install ollama`
- Baixe um modelo de visão: `ollama pull llava`
- Inicie o Ollama: `ollama serve`
- Marque "🤖 Sugestões IA" na interface
- Ao adicionar imagens, a IA analisa e sugere transições
- Imagens com sugestão IA são marcadas com 🤖

## Formatos Suportados

### Imagens
- JPG, JPEG, PNG, BMP, GIF, WEBP

### Vídeos
- MP4, AVI, MOV, MKV, WEBM

### Áudio
- MP3

## Como Funciona

### Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                               │
│                    (Ponto de entrada)                        │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      gui/app.py                              │
│                 (Interface Tkinter)                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Lista Mídia │  │  Transições  │  │  Barra Progresso  │   │
│  │  + Preview  │  │ Global/Indiv │  │   + Status        │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
│ video_generator │ │  transitions  │ │  ai_suggester   │
│     .py         │ │     .py       │ │     .py         │
│                 │ │               │ │                 │
│ - ImageClip     │ │ - crossfade   │ │ - Ollama API    │
│ - VideoFileClip │ │ - fade        │ │ - Modelo llava  │
│ - AudioFileClip │ │ - slide       │ │ - Análise visual│
│ - Concatenação  │ │ - wipe        │ │                 │
│ - Exportação    │ │ - blur        │ │                 │
└────────┬────────┘ └───────────────┘ └─────────────────┘
         │
         ▼
┌─────────────────┐
│     FFmpeg      │
│  (Codificação)  │
└─────────────────┘
```

### Fluxo de Geração de Vídeo

1. **Carregamento do Áudio**
   - O arquivo MP3 é carregado usando MoviePy
   - A duração do áudio determina a duração total do vídeo

2. **Processamento de Mídia**
   - **Uma imagem**: Exibida durante toda a duração do áudio
   - **Múltiplas imagens**: Tempo dividido igualmente (ex: 60s de áudio ÷ 6 imagens = 10s cada)
   - **Vídeo**: Áudio original removido, ajustado para duração do MP3

3. **Redimensionamento**
   - Todas as imagens são redimensionadas para 1920x1080 (Full HD)
   - Proporção original mantida com barras pretas se necessário

4. **Aplicação de Transições** (se ativadas)
   - Para cada par de imagens consecutivas, aplica o efeito escolhido
   - Transições individuais têm prioridade sobre a global

5. **Composição Final**
   - Clips são concatenados em sequência
   - Áudio MP3 é adicionado à trilha sonora
   - Vídeo é exportado em MP4 (codec H.264 + AAC)

### Módulos em Detalhe

#### `core/video_generator.py`
Classe principal `VideoGenerator` com métodos:
- `generate_from_single_image()` - Uma imagem + áudio
- `generate_from_multiple_images()` - Várias imagens + áudio + transições
- `generate_from_video()` - Vídeo existente + substituição de áudio
- `generate()` - Método unificado que detecta o tipo automaticamente

#### `core/transitions.py`
Funções de transição usando MoviePy:
- `create_crossfade_transition()` - Dissolve com sobreposição
- `create_fade_transition()` - Fade para preto
- `create_slide_transition()` - Deslizamento em 4 direções
- `create_wipe_transition()` - Cortina revelando próxima imagem
- `create_blur_transition()` - Desfoque gradual
- `apply_transition()` - Função principal que seleciona e aplica

#### `core/ai_suggester.py`
Integração com Ollama para sugestões inteligentes:
- Usa modelo de visão `llava` para analisar imagens
- Envia pares de imagens consecutivas para análise
- IA considera cores, composição e tema para sugerir transição
- Executa em thread separada para não travar a interface

### Exemplo de Uso Programático

```python
from core.video_generator import VideoGenerator

# Criar gerador
gen = VideoGenerator(
    output_path="meu_video.mp4",
    audio_path="musica.mp3"
)

# Gerar com transições
gen.generate(
    media_paths=["img1.jpg", "img2.jpg", "img3.jpg"],
    transition_enabled=True,
    global_transition_type="crossfade",
    global_transition_duration=1.0,
    individual_transitions={
        "img1.jpg": {"type": "slide_left", "duration": 0.5}
    }
)
```

## Estrutura do Projeto

```
gerador-video-basico/
├── main.py              # Ponto de entrada
├── gui/
│   ├── __init__.py
│   └── app.py           # Interface gráfica Tkinter
├── core/
│   ├── __init__.py
│   ├── video_generator.py  # Lógica de geração
│   ├── transitions.py      # Efeitos de transição
│   └── ai_suggester.py     # Sugestões IA com Ollama
├── requirements.txt     # Dependências
└── README.md            # Este arquivo
```

## Licença

MIT
