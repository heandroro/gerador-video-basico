# Ollama — Guia de Uso no Gerador de Vídeo

Documentação sobre a integração com o [Ollama](https://ollama.com), servidor local de modelos de linguagem/visão utilizado para sugerir transições entre imagens automaticamente.

---

## O que é o Ollama?

Ollama é uma ferramenta que permite executar modelos de IA (incluindo modelos multimodais com visão) localmente na sua máquina, sem enviar dados para a nuvem. Neste projeto, ele é usado exclusivamente para analisar pares de imagens e sugerir qual tipo de transição é mais adequado para a sequência.

---

## Instalação

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Baixe o instalador em: https://ollama.com/download/windows

---

## Modelo Utilizado: `llava`

O projeto usa o modelo **LLaVA** (Large Language and Vision Assistant), que aceita imagens como entrada junto com texto, permitindo descrever e comparar cenas visuais.

### Download do modelo
```bash
ollama pull llava
```

> O modelo tem aproximadamente **4 GB**. O download é feito apenas uma vez.

---

## Iniciando o servidor

O Ollama precisa estar rodando como servidor antes de abrir a aplicação:

```bash
ollama serve
```

O servidor ficará disponível em:
```
http://localhost:11434
```

> **Dica:** No macOS, o Ollama pode ser iniciado automaticamente como um serviço de sistema. Verifique com `ollama ps`.

---

## Como a integração funciona

### Fluxo de sugestão

```
┌─────────────────────┐
│  Par de imagens     │  (img_atual + img_próxima)
│  selecionadas       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  core/ai_suggester  │  Codifica imagens em base64
│  TransitionSuggester│  Monta prompt contextual
└──────────┬──────────┘
           │  POST /api/chat (multimodal)
           ▼
┌─────────────────────┐
│   Ollama (llava)    │  Analisa cores, composição
│   localhost:11434   │  e relação entre as imagens
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Resposta JSON      │  { "type": "crossfade",
│  com tipo e motivo  │    "duration": 1.0,
└──────────┬──────────┘    "reason": "..." }
           │
           ▼
┌─────────────────────┐
│  Aplicado na        │  individual_transitions[img]
│  timeline           │  visível na linha do tempo
└─────────────────────┘
```

### Prompt enviado ao modelo

O prompt instrui o modelo a:
1. Analisar a **imagem de origem** (atual)
2. Analisar a **imagem de destino** (próxima)
3. Considerar cores dominantes, composição e tema
4. Responder **somente** com JSON contendo `type`, `duration` e `reason`

Exemplo de resposta esperada:
```json
{
  "type": "crossfade",
  "duration": 1.2,
  "reason": "As imagens têm cores similares e a dissolução suave mantém a continuidade visual."
}
```

---

## Tipos de transição reconhecidos pela IA

| Tipo | Descrição |
|------|-----------|
| `none` | Corte direto |
| `fade` | Fade para preto |
| `crossfade` | Dissolve suave |
| `slide_left` | Slide para esquerda |
| `slide_right` | Slide para direita |
| `slide_up` | Slide para cima |
| `slide_down` | Slide para baixo |
| `wipe_left` | Wipe para esquerda |
| `wipe_right` | Wipe para direita |
| `wipe_up` | Wipe para cima |
| `wipe_down` | Wipe para baixo |
| `blur` | Desfoque |
| `fadewhite` | Fade para branco |
| `radial` | Varredura circular |
| `circleopen` | Círculo que abre |
| `circleclose` | Círculo que fecha |
| `pixelize` | Pixelização |
| `smoothleft` | Deslize suave esquerda |
| `smoothright` | Deslize suave direita |

---

## Verificando disponibilidade

A aplicação testa automaticamente se o Ollama está acessível ao iniciar. O método `is_ai_available()` em `core/ai_suggester.py` faz uma requisição GET para `http://localhost:11434` e retorna `True` se o servidor responder.

Se o Ollama não estiver rodando:
- O botão **"🤖 Sugerir Transições com IA"** exibe `⚠️ IA não disponível (inicie Ollama)`
- As funcionalidades de sugestão ficam desabilitadas
- A geração de vídeo funciona normalmente sem IA

---

## Uso na interface

### Via botão na aba Linha do Tempo

1. Adicione pelo menos **2 imagens** na lista de mídia
2. Na aba **⏱️ Linha do Tempo**, clique em **"🤖 Sugerir Transições com IA"**
3. O status exibe o progresso: `🔄 Analisando par 1/3...`
4. Ao concluir: `✓ 3 transições sugeridas!`
5. As transições aparecem na segunda linha da timeline com cores indicativas

### Via aba Sugestões IA

1. Ative transições no painel de configuração
2. Vá até a aba **"🤖 Sugestões IA"**
3. Clique em **"Analisar Imagens"**
4. O log exibe o resultado de cada par analisado com o motivo da escolha

---

## Modelos alternativos

O Ollama suporta outros modelos com capacidade de visão que podem ser testados:

| Modelo | Tamanho | Comando |
|--------|---------|---------|
| `llava` | ~4 GB | `ollama pull llava` |
| `llava:13b` | ~8 GB | `ollama pull llava:13b` |
| `llava-llama3` | ~5 GB | `ollama pull llava-llama3` |
| `moondream` | ~1.7 GB | `ollama pull moondream` |

> Para usar um modelo diferente, altere `self.model` em `core/ai_suggester.py`.

---

## Solução de problemas

### Servidor não responde
```bash
# Verificar se está rodando
curl http://localhost:11434

# Reiniciar
ollama serve
```

### Modelo não encontrado
```bash
ollama list          # listar modelos disponíveis
ollama pull llava    # baixar novamente
```

### Resposta inválida da IA
- O prompt inclui instrução para responder **somente JSON**
- Se a IA retornar texto livre, o parser usa `re.search` para extrair o JSON embutido
- Em caso de falha total, a sugestão é ignorada e a transição permanece inalterada

### Porta em uso
Se a porta `11434` estiver ocupada por outro processo:
```bash
# macOS / Linux
lsof -i :11434
kill -9 <PID>
```

---

## Recursos não explorados e possibilidades futuras

### 1. Análise de conteúdo semântico das imagens

Atualmente a IA apenas **sugere transições**. O modelo `llava` é capaz de muito mais:

- **Gerar legendas automáticas** para cada imagem (alt-text, descrição de cena)
- **Detectar pessoas, objetos e cenários** e usar isso para ordenar as imagens logicamente
- **Classificar humor/tom visual** (alegre, melancólico, tenso) para sugerir ritmo e duração
- **Gerar títulos/subtítulos** para sobrepor nas imagens durante o vídeo

```python
# Exemplo: pedir descrição completa de uma imagem
payload = {
    "model": "llava",
    "messages": [{
        "role": "user",
        "content": "Descreva esta imagem em detalhes: cenário, pessoas, cores, emoção.",
        "images": [base64_image]
    }]
}
```

---

### 2. Sugestão de duração baseada no conteúdo

A duração de cada imagem hoje é definida manualmente ou distribuída igualmente. A IA poderia:

- Sugerir **mais tempo para imagens complexas** (paisagens cheias de detalhes)
- Sugerir **menos tempo para imagens simples** (fundos lisos, close-ups)
- Relacionar a duração com o **ritmo da música** (batidas por minuto)

---

### 3. Geração de texto para narração / legenda

Usando modelos de texto puro (sem visão), o Ollama poderia gerar:

- **Roteiro de narração** baseado na sequência de imagens
- **Hashtags e descrições** para redes sociais a partir do conteúdo do vídeo
- **Títulos para slides** usando o tema detectado nas imagens

Modelos adequados: `llama3`, `mistral`, `phi3`

```python
# Exemplo: gerar narração para uma sequência de cenas
prompt = "Crie uma narração curta em português para um vídeo com as seguintes cenas: " + cenas
```

---

### 4. Análise de áudio com IA local

O Ollama não processa áudio diretamente, mas poderia ser combinado com:

- **Whisper (via Ollama ou local)** → transcrever letras ou falas do MP3
- Usar a transcrição para **sincronizar imagens com o conteúdo da música**
- Detectar **mudanças de ritmo** para posicionar transições nos momentos certos

Modelo: `whisper` (disponível como serviço separado ou via `openai-whisper` Python)

---

### 5. Ordenação inteligente das imagens

Em vez de o usuário ordenar manualmente, a IA poderia:

- **Agrupar imagens por tema/cenário** automaticamente
- **Criar uma narrativa visual** (início → meio → fim) com base no conteúdo
- **Detectar duplicatas ou imagens muito similares** e sugerir remoção

---

### 6. Geração de thumbnail do vídeo

O modelo de visão poderia analisar todas as imagens e:

- Escolher a **mais representativa** para usar como thumbnail
- Sugerir **composição ideal** para capa (qual imagem + qual recorte)
- Gerar uma **descrição para o thumbnail** (texto de sobreposição sugerido)

---

### 7. API REST com múltiplos clientes

O servidor Ollama expõe uma API REST completa que pode ser consumida por outros clientes além do Python:

| Endpoint | Método | Uso |
|----------|--------|-----|
| `/api/generate` | POST | Geração simples (texto) |
| `/api/chat` | POST | Chat com histórico (usado atualmente) |
| `/api/embeddings` | POST | Vetor semântico de texto/imagem |
| `/api/tags` | GET | Listar modelos instalados |
| `/api/show` | POST | Detalhes de um modelo |
| `/api/pull` | POST | Baixar modelo via API |

```bash
# Listar modelos via curl
curl http://localhost:11434/api/tags

# Gerar embedding de texto
curl -X POST http://localhost:11434/api/embeddings \
  -d '{"model": "llava", "prompt": "paisagem ao pôr do sol"}'
```

---

### 8. Embeddings para similaridade visual

A API `/api/embeddings` pode gerar vetores numéricos que representam o conteúdo semântico de uma imagem ou texto. Com isso seria possível:

- **Medir similaridade entre imagens** (cosine similarity) para agrupar cenas relacionadas
- **Encontrar imagens redundantes** que deveriam ser removidas ou combinadas
- **Recomendar ordem de exibição** baseada em progressão semântica

---

### 9. Execução em streaming

A API suporta **respostas em streaming** (`"stream": true`), o que permitiria:

- Exibir o raciocínio da IA em tempo real na interface enquanto analisa
- Mostrar progresso palavra a palavra em vez de aguardar a resposta completa
- Melhor experiência para análises longas com muitas imagens

```python
# Exemplo de consumo em stream
import requests, json

response = requests.post(
    "http://localhost:11434/api/chat",
    json={..., "stream": True},
    stream=True
)
for line in response.iter_lines():
    chunk = json.loads(line)
    print(chunk["message"]["content"], end="", flush=True)
```

---

### 10. Modelos especializados em visão

Além do `llava`, outros modelos disponíveis no Ollama têm características distintas:

| Modelo | Ponto forte | Quando usar |
|--------|-------------|-------------|
| `llava:13b` | Maior precisão | Análise detalhada de cenas complexas |
| `llava-llama3` | Base Llama 3 mais recente | Melhor compreensão de contexto |
| `moondream` | Levíssimo (~1.7 GB) | Dispositivos com pouca RAM |
| `bakllava` | Boa relação custo/precisão | Alternativa ao llava padrão |
| `llava-phi3` | Base Phi-3 da Microsoft | Rápido e eficiente |
| `cogvlm` | Foco em OCR e diagramas | Imagens com texto ou gráficos |

---

### 11. Contexto persistente entre análises

Atualmente cada par de imagens é analisado de forma independente. Com o endpoint `/api/chat` e histórico de mensagens, seria possível:

- Manter **contexto acumulado** da sequência toda ("já vimos praia, floresta, agora cidade...")
- Pedir à IA para criar uma **narrativa coerente** ao longo de todas as imagens
- Usar o histórico para **evitar sugestões repetidas** de transição

---

## Links úteis

- Site oficial: https://ollama.com
- Modelos disponíveis: https://ollama.com/library
- Repositório: https://github.com/ollama/ollama
- Documentação da API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Modelo LLaVA: https://ollama.com/library/llava
- Modelo Moondream (leve): https://ollama.com/library/moondream
- Whisper (transcrição de áudio): https://github.com/openai/whisper
