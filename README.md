# Gerador de Vídeo a partir de Mídia e Áudio

Aplicação desktop Python que gera vídeos MP4 combinando imagens ou vídeo com um arquivo MP3.

## Funcionalidades

- **Uma única imagem** → exibida durante toda a duração do MP3
- **Múltiplas imagens** → distribuídas igualmente ou com durações individuais
- **Linha do Tempo Visual** → arraste blocos para reordenar, visualize transições
- **Controle de Duração** → defina início/fim de cada imagem em minutos e segundos
- **Transições** → efeitos visuais entre imagens (global ou individual)
- **Sugestões IA** → Ollama analisa imagens e sugere transições automaticamente
- **Loop/Repetição** → repita intervalos de imagens para preencher o áudio
- **Desfazer** → até 10 ações podem ser desfeitas (Ctrl+Z)
- **Validação** → compara duração total com o áudio

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

5. (Opcional) Configure o Ollama para sugestões IA:
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh
```

   Baixe o modelo de visão:
```bash
ollama pull llava
```

   Inicie o servidor antes de abrir a aplicação:
```bash
ollama serve
```

   O servidor ficará disponível em `http://localhost:11434`.

## Uso

Execute a aplicação:
```bash
python main.py
```

### Interface

1. **Adicionar Mídia**: Clique em "Adicionar Imagens" ou "Adicionar Vídeo"
2. **Linha do Tempo**: Arraste os blocos para reordenar as imagens
3. **Configurar Duração**: Use os botões para distribuir pelo áudio ou definir manualmente
4. **Duração Individual**: Clique em uma imagem na timeline e defina início/fim
5. **Configurar Transições**: Ative transições e escolha tipo/duração
6. **Sugestões IA**: Clique em "🤖 Sugerir Transições com IA" para análise automática
7. **Loop**: Selecione um intervalo de imagens e repita para preencher o áudio
8. **Selecionar Áudio**: Clique em "Selecionar MP3" para escolher o áudio
9. **Escolher Saída**: Clique em "Escolher Local" para definir onde salvar
10. **Gerar**: Clique em "Gerar Vídeo" e aguarde a conclusão

### Linha do Tempo

A timeline visual mostra:
- **Blocos coloridos** → cada imagem com duração proporcional
- **Setas de transição** → segunda linha mostra tipo e duração de cada transição
- **Escala de tempo** → marcações em minutos:segundos
- **Status de duração** → comparação com o áudio (verde/vermelho/laranja)
- **Arrastar e soltar** → reordene imagens clicando e arrastando os blocos

### Duração das Imagens

#### Distribuição Rápida
- **"📊 Distribuir pelo Áudio"** → divide igualmente pela duração do MP3
- **"Aplicar" (manual)** → divide pelo tempo total que você informar

#### Controle Individual
1. Clique em uma imagem na timeline ou na lista
2. Defina o **Tempo de Início** (MM:SS) - calculado automaticamente
3. Defina o **Tempo de Fim** (MM:SS)
4. Clique "✓ Aplicar"
5. A duração é calculada: Fim - Início

#### Validação
- **⚠️ Vermelho** → duração das imagens é menor que o áudio (falta tempo)
- **⚠️ Laranja** → duração excede o áudio (sobra tempo)
- **✓ Verde** → duração igual ao áudio

### Transições

#### Tipos Disponíveis
- **Nenhum** - Corte direto entre imagens
- **Fade** - Escurece para preto e clareia
- **Crossfade** - Dissolve suave entre imagens
- **Slide** - Desliza em 4 direções (esquerda, direita, cima, baixo)
- **Wipe** - Cortina em 4 direções
- **Blur** - Desfoca e foca
- **Fade Branco** - Escurece para branco e clareia
- **Radial** - Varredura circular cinematográfica
- **Círculo Abre** - Círculo que se expande revelando a próxima imagem
- **Círculo Fecha** - Círculo que fecha sobre a imagem atual
- **Pixelizar** - Pixelização digital entre imagens
- **Suave Esquerda / Suave Direita** - Deslize suave moderno

> Os tipos **Fade Branco**, **Radial**, **Círculo Abre/Fecha**, **Pixelizar** e **Suave Esquerda/Direita** utilizam o pipeline FFmpeg nativo (xfade) e têm desempenho superior aos demais.

#### Configuração Global
- Marque "Ativar transições" para habilitar
- Escolha o tipo de transição padrão
- Defina a duração (0.5s a 3.0s)

#### Configuração Individual
- Selecione uma imagem na lista
- Marque "Personalizar" para definir transição específica
- Imagens com transição personalizada são marcadas com ★

#### Sugestões IA na Timeline
- Clique em "🤖 Sugerir Transições com IA" na aba Timeline
- A IA analisa cada par de imagens consecutivas
- Transições sugeridas aparecem na segunda linha da timeline
- Cores indicam o tipo de transição (rosa=crossfade, roxo=fade, etc.)

### Loop / Repetição

Repete um intervalo de imagens para preencher a duração do áudio:

1. Defina "De imagem:" e "Até imagem:" (ex: 1 a 3)
2. Escolha quantas vezes repetir
3. Clique "Selecionar Todas" para usar todas as imagens
4. Clique "Aplicar Loop" ou "Preencher até Áudio"

- **Aplicar Loop** → repete N vezes o intervalo selecionado
- **Preencher até Áudio** → repete até completar a duração do MP3

### Desfazer

- **Botão ↩ Desfazer** → reverte a última ação
- **Ctrl+Z** → atalho de teclado
- Guarda até **10 ações** na memória
- Ações desfeitas: distribuição de duração, loop, reordenação
- Mostra quantas ações restam após desfazer

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
│  │ Lista Mídia │  │   Timeline   │  │  Config Duração   │   │
│  │  + Preview  │  │  Drag&Drop   │  │  Início/Fim       │   │
│  └─────────────┘  └──────────────┘  └───────────────────┘   │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │ Transições  │  │  Loop/Undo   │  │ Sugestões IA      │   │
│  │ Global/Indiv│  │  ↩ Desfazer  │  │ 🤖 Análise        │   │
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
│ - Concatenação  │ │ - wipe        │ │ - Sugestões     │
│ - Durações      │ │ - blur        │ │   automáticas   │
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
   - A duração do áudio é exibida para referência

2. **Processamento de Mídia**
   - **Uma imagem**: Exibida durante toda a duração do áudio
   - **Múltiplas imagens**: Usa durações individuais definidas pelo usuário
   - **Vídeo**: Áudio original removido, ajustado para duração do MP3

3. **Durações Personalizadas**
   - Cada imagem pode ter duração definida individualmente (início/fim)
   - Validação compara duração total com o áudio
   - Distribuição pode ser feita pelo áudio ou manualmente

4. **Redimensionamento**
   - Todas as imagens são redimensionadas para 1920x1080 (Full HD)
   - Proporção original mantida com barras pretas se necessário

5. **Aplicação de Transições** (se ativadas)
   - Para cada par de imagens consecutivas, aplica o efeito escolhido
   - Transições individuais têm prioridade sobre a global
   - Sugestões da IA podem ser aplicadas automaticamente

6. **Composição Final**
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

# Gerar com durações e transições personalizadas
gen.generate(
    media_paths=["img1.jpg", "img2.jpg", "img3.jpg"],
    transition_enabled=True,
    global_transition_type="crossfade",
    global_transition_duration=1.0,
    individual_transitions={
        "img1.jpg": {"type": "slide_left", "duration": 0.5}
    },
    image_durations={
        "img1.jpg": 5.0,   # 5 segundos
        "img2.jpg": 3.0,   # 3 segundos
        "img3.jpg": 4.0    # 4 segundos
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
├── docs/
│   └── FFMPEG.md        # Recursos FFmpeg a explorar
├── requirements.txt     # Dependências
└── README.md            # Este arquivo
```

## Documentação Adicional

- [docs/FFMPEG.md](docs/FFMPEG.md) — Recursos FFmpeg utilizados e funcionalidades a explorar em versões futuras

## Licença

MIT
