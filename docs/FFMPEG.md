# FFmpeg — Recursos a Explorar

Documentação dos recursos FFmpeg que **ainda não foram implementados** neste projeto e que podem enriquecer futuras versões.

Referência oficial dos filtros: **https://ffmpeg.org/ffmpeg-filters.html**

---

## Recursos Atualmente Utilizados

O projeto usa FFmpeg de forma indireta via [MoviePy](https://zulko.github.io/moviepy/), que o chama internamente para:

| Recurso | Como é usado |
|---|---|
| Codec de vídeo `libx264` | Exportação do MP4 final |
| Codec de áudio `aac` | Codificação do áudio no MP4 |
| Concatenação de clipes | `concatenate_videoclips()` |
| Composição de clipes | `CompositeVideoClip()` |
| Crossfade / Fade | `crossfadein()` / `crossfadeout()` |
| Subclip (corte por duração) | `subclip(0, duration)` |

---

## Recursos a Explorar

### 1. Transições Nativas com `xfade`

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#xfade

O filtro `xfade` nativo do FFmpeg oferece mais de 40 tipos de transição sem depender de composição frame-a-frame via MoviePy, resultando em desempenho muito superior para projetos longos.

Exemplos de transições disponíveis:
- `fade`, `fadeblack`, `fadewhite`
- `wipeleft`, `wiperight`, `wipeup`, `wipedown`
- `slideleft`, `slideright`, `slideup`, `slidedown`
- `circlecrop`, `rectcrop`
- `dissolve`, `pixelize`, `radial`
- `smoothleft`, `smoothright`, `smoothup`, `smoothdown`
- `hblur`, `hlwind`, `hrwind`, `vuwind`, `vdwind`

**Caso de uso:** substituir as transições atuais (implementadas frame-a-frame) por chamadas diretas ao FFmpeg, ganhando performance significativa.

---

### 2. Zoom e Pan — Efeito Ken Burns

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#zoompan

O filtro `zoompan` cria o efeito clássico de documentário — zoom suave e movimento de câmera sobre imagens estáticas.

Parâmetros principais:
- `z` — expressão do fator de zoom ao longo do tempo (ex: `z='min(zoom+0.0015,1.5)'`)
- `x` / `y` — posição do quadro ao longo do tempo
- `d` — duração em frames
- `s` — tamanho de saída (ex: `1920x1080`)

**Caso de uso:** dar vida às imagens sem precisar de vídeo real — muito usado em slideshows cinematográficos e documentários.

---

### 3. Ajuste de Cor e Imagem

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#eq

Filtros para ajustar visualmente cada imagem antes de compor o vídeo:

| Filtro | Descrição |
|---|---|
| `eq` | Brilho, contraste, saturação, gamma |
| `hue` | Rotação de matiz e saturação |
| `colorbalance` | Balanço de cor por sombras/meios-tons/altas-luzes |
| `colorchannelmixer` | Mistura de canais RGB |
| `vignette` | Escurecimento nas bordas estilo fotográfico |

**Caso de uso:** permitir ao usuário ajustar visualmente cada imagem sem precisar de um editor externo.

---

### 4. Texto e Legendas

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#drawtext

Inserir texto diretamente no vídeo com controle de fonte, posição, cor e animação.

| Filtro | Descrição |
|---|---|
| `drawtext` | Texto estático ou animado com expressões de tempo (`%{pts}`) |
| `subtitles` | Renderização de arquivos `.srt` / `.ass` |

**Caso de uso:** adicionar título, créditos ou legendas automáticas sobre as imagens sem ferramenta externa.

---

### 5. Sobreposição e Marca d'Água

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#overlay

Sobrepor imagens, logos ou marcas d'água com controle de posição e transparência.

| Filtro | Descrição |
|---|---|
| `overlay` | Sobreposição com coordenadas x/y |
| `alphamerge` | Combinar canal alfa externo |
| `colorkey` | Remoção de fundo por cor específica |
| `chromakey` | Chroma key (fundo verde/azul) |

**Caso de uso:** adicionar logo, marca d'água ou sobreposição de elementos gráficos ao vídeo final.

---

### 6. Filtros de Áudio

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#Audio-Filters

O áudio atual é inserido sem nenhum processamento. Recursos disponíveis:

| Filtro | Descrição |
|---|---|
| `afade` | Fade in/out no áudio |
| `volume` | Ajuste de volume |
| `dynaudnorm` | Normalização dinâmica de volume |
| `aecho` | Efeito de eco |
| `atempo` | Alteração de velocidade sem alterar tom |
| `silencedetect` | Detectar silêncios para sincronização automática |

**Caso de uso:** normalizar volume do MP3, aplicar fade out no final do vídeo, sincronizar trocas de imagem com batidas do áudio.

---

### 7. Múltiplos Formatos e Qualidades de Exportação

**Documentação:** https://ffmpeg.org/ffmpeg-codecs.html

Atualmente o projeto exporta apenas H.264 + AAC. Outras opções:

| Codec de Vídeo | Uso |
|---|---|
| `libx265` (HEVC) | Arquivo menor com mesma qualidade |
| `libvpx-vp9` | WebM para web |
| `libaom-av1` | AV1 — máxima compressão moderna |
| `prores_ks` | Edição profissional (macOS) |
| `gif` | GIF animado |

Parâmetros de qualidade úteis:
- `-crf` — controle de qualidade constante (0–51 para H.264; menor = melhor)
- `-preset` — velocidade vs. qualidade (`ultrafast` → `veryslow`)
- `-b:v` — bitrate fixo de vídeo

**Caso de uso:** oferecer perfis de exportação (web, alta qualidade, arquivo pequeno).

---

### 8. Aceleração por Hardware

**Documentação:** https://trac.ffmpeg.org/wiki/HWAccelIntro

Usar GPU para codificação, drasticamente mais rápido em máquinas compatíveis:

| Encoder | Plataforma |
|---|---|
| `h264_videotoolbox` | Apple Silicon / macOS |
| `h264_nvenc` | NVIDIA |
| `h264_amf` | AMD |
| `h264_qsv` | Intel Quick Sync |

**Caso de uso:** reduzir tempo de exportação em projetos com muitas imagens ou transições pesadas.

---

### 9. Geração de Thumbnail Automático

**Documentação:** https://ffmpeg.org/ffmpeg-filters.html#thumbnail

O filtro `thumbnail` seleciona automaticamente o frame mais representativo de um vídeo.

**Caso de uso:** gerar prévia do resultado antes da exportação completa, exibindo uma miniatura do vídeo gerado diretamente na interface.

---

## Próximos Passos Sugeridos

Por ordem de impacto vs. esforço de implementação:

| Prioridade | Recurso | Ganho |
|---|---|---|
| 1 | **`xfade` nativo** | Maior ganho de performance imediato |
| 2 | **Zoom/Pan (Ken Burns)** | Diferencial visual significativo |
| 3 | **Fade de áudio (`afade`)** | Polimento profissional no resultado final |
| 4 | **`drawtext`** | Títulos e créditos sem ferramenta externa |
| 5 | **Hardware acceleration** | Escala para projetos grandes |
| 6 | **Múltiplos formatos de exportação** | Flexibilidade para diferentes plataformas |
| 7 | **Ajuste de cor (`eq`)** | Controle criativo por imagem |
| 8 | **Sobreposição / marca d'água** | Necessidade comum em produção |
| 9 | **Thumbnail automático** | Melhoria de UX na interface |
