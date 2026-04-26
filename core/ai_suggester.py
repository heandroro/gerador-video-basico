"""
AI-powered transition suggester using Ollama with vision models.
"""

import base64
import json
import re
import threading
from typing import Optional, Callable, Dict, List, Tuple
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

from core.transitions import TRANSITION_TYPES


VISION_MODELS = ["llava", "llava-llama3", "bakllava", "llava:13b", "llava:34b"]

CHAT_PROMPT = """Você é um assistente especializado em transições de vídeo.
O usuário está criando um slideshow de imagens e precisa de ajuda para configurar as transições.

Transições disponíveis:
- none: corte direto (rápido, ação)
- fade: escurece para preto (dramático, mudança de cena)
- crossfade: dissolve suave (calmo, elegante, suave)
- slide_left, slide_right: deslize horizontal (sequencial, viagem, timeline)
- slide_up, slide_down: deslize vertical (listas, progresso)
- wipe_left, wipe_right: cortina horizontal (revelação, comparação)
- wipe_up, wipe_down: cortina vertical (antes/depois)
- blur: desfoque (sonhador, suave, artístico)

Durações recomendadas:
- Rápido: 0.5s
- Normal: 1.0s
- Suave/Lento: 1.5s a 2.0s
- Dramático: 2.0s a 3.0s

Baseado no pedido do usuário, responda em JSON:
{
  "transition": "tipo_da_transicao",
  "duration": 1.0,
  "message": "explicação amigável em português do que você configurou"
}

Se o usuário pedir para desativar transições, use: {"transition": "none", "duration": 0, "message": "..."}
Se não entender o pedido, responda com uma mensagem de ajuda.

Pedido do usuário: """

SUGGESTION_PROMPT = """Analise estas duas imagens consecutivas de um slideshow de vídeo.
Com base no conteúdo visual, cores, composição e clima, sugira o melhor efeito de transição.

Transições disponíveis:
- crossfade: dissolve suave, bom para cenas similares ou clima calmo
- fade: escurece para preto, bom para mudanças de cena ou efeito dramático
- slide_left/slide_right: deslize horizontal, bom para conteúdo sequencial
- slide_up/slide_down: deslize vertical, bom para listas ou hierarquias
- wipe_left/wipe_right: cortina horizontal, bom para revelações ou comparações
- wipe_up/wipe_down: cortina vertical, bom para antes/depois ou progresso
- blur: transição com desfoque, bom para mudanças suaves ou sonhadoras
- none: corte direto, bom para conteúdo rápido ou ação

Responda no formato JSON:
{"transition": "nome_da_transicao", "reason": "explicação breve em português do porquê"}

Exemplo: {"transition": "crossfade", "reason": "Ambas imagens têm tons azuis similares e clima tranquilo"}"""


class TransitionSuggester:
    """Suggests transitions between images using Ollama vision models."""
    
    def __init__(self, model: str = "llava"):
        self.model = model
        self._available = False
        self._cache: Dict[str, Dict] = {}
        self._check_availability()
    
    def _check_availability(self) -> None:
        """Check if Ollama is available and model is installed."""
        if not OLLAMA_AVAILABLE:
            self._available = False
            return
        
        try:
            models = ollama.list()
            model_names = [m.model.split(":")[0] for m in models.models]
            
            if self.model.split(":")[0] in model_names:
                self._available = True
            else:
                for vm in VISION_MODELS:
                    if vm.split(":")[0] in model_names:
                        self.model = vm
                        self._available = True
                        break
        except Exception:
            self._available = False
    
    @property
    def is_available(self) -> bool:
        """Check if the suggester is available."""
        return self._available
    
    def _image_to_base64(self, image_path: str) -> str:
        """Convert image file to base64 string."""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_cache_key(self, image1_path: str, image2_path: str) -> str:
        """Generate cache key for image pair."""
        return f"{image1_path}|{image2_path}"
    
    def _parse_response(self, response_text: str) -> Tuple[str, str]:
        """Parse AI response to extract transition and reason."""
        try:
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                transition = data.get("transition", "crossfade").lower()
                reason = data.get("reason", "")
                return transition, reason
        except (json.JSONDecodeError, AttributeError):
            pass
        
        response_lower = response_text.lower()
        for trans_type in TRANSITION_TYPES:
            if trans_type in response_lower:
                return trans_type, ""
        
        return "crossfade", ""
    
    def suggest_transition(
        self,
        image1_path: str,
        image2_path: str
    ) -> Optional[Dict[str, str]]:
        """
        Suggest a transition between two images.
        
        Args:
            image1_path: Path to the first image
            image2_path: Path to the second image
            
        Returns:
            Dict with 'type' and 'reason', or None if unavailable
        """
        if not self._available:
            return None
        
        cache_key = self._get_cache_key(image1_path, image2_path)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": SUGGESTION_PROMPT,
                    "images": [image1_path, image2_path]
                }]
            )
            
            transition, reason = self._parse_response(response.message.content)
            
            if transition not in TRANSITION_TYPES:
                transition = "crossfade"
            
            result = {"type": transition, "reason": reason}
            self._cache[cache_key] = result
            return result
            
        except Exception as e:
            print(f"AI suggestion error: {e}")
            return None
    
    def suggest_all_transitions(
        self,
        image_paths: List[str],
        callback: Optional[Callable[[int, str, str, str], None]] = None
    ) -> Dict[str, Dict[str, any]]:
        """
        Suggest transitions for all consecutive image pairs.
        
        Args:
            image_paths: List of image paths
            callback: Optional callback(index, image_path, transition, reason) for progress
            
        Returns:
            Dict mapping image paths to transition configs
        """
        transitions = {}
        
        for i in range(len(image_paths) - 1):
            img1 = image_paths[i]
            img2 = image_paths[i + 1]
            
            suggestion = self.suggest_transition(img1, img2)
            
            if suggestion:
                transitions[img1] = {
                    "type": suggestion["type"],
                    "duration": 1.0,
                    "ai_suggested": True,
                    "reason": suggestion.get("reason", "")
                }
                
                if callback:
                    callback(i, img1, suggestion["type"], suggestion.get("reason", ""))
        
        return transitions
    
    def suggest_all_async(
        self,
        image_paths: List[str],
        callback: Optional[Callable[[int, str, str, str], None]] = None,
        done_callback: Optional[Callable[[Dict], None]] = None
    ) -> threading.Thread:
        """
        Suggest transitions asynchronously in a background thread.
        
        Args:
            image_paths: List of image paths
            callback: Optional callback(index, image_path, transition) for each suggestion
            done_callback: Optional callback(transitions_dict) when complete
            
        Returns:
            The background thread
        """
        def worker():
            transitions = self.suggest_all_transitions(image_paths, callback)
            if done_callback:
                done_callback(transitions)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
    
    def chat_suggestion(self, user_message: str) -> Dict[str, any]:
        """
        Process a chat message and return transition configuration.
        
        Args:
            user_message: User's request in natural language
            
        Returns:
            Dict with 'transition', 'duration', 'message', and 'success'
        """
        if not self._available:
            return {
                "success": False,
                "message": "Ollama não está disponível. Inicie o servidor com 'ollama serve'."
            }
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": CHAT_PROMPT + user_message
                }]
            )
            
            response_text = response.message.content
            
            try:
                json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    transition = data.get("transition", "crossfade").lower()
                    duration = float(data.get("duration", 1.0))
                    message = data.get("message", "Configuração aplicada!")
                    
                    if transition not in TRANSITION_TYPES and transition != "none":
                        transition = "crossfade"
                    
                    duration = max(0.5, min(3.0, duration))
                    
                    return {
                        "success": True,
                        "transition": transition,
                        "duration": duration,
                        "message": message
                    }
            except (json.JSONDecodeError, ValueError):
                pass
            
            return {
                "success": True,
                "transition": None,
                "duration": None,
                "message": response_text
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao processar: {str(e)}"
            }
    
    def chat_suggestion_async(
        self,
        user_message: str,
        callback: Callable[[Dict], None]
    ) -> threading.Thread:
        """
        Process chat message asynchronously.
        
        Args:
            user_message: User's request
            callback: Function to call with result
            
        Returns:
            The background thread
        """
        def worker():
            result = self.chat_suggestion(user_message)
            callback(result)
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread


_suggester_instance: Optional[TransitionSuggester] = None


def get_suggester() -> TransitionSuggester:
    """Get or create the global suggester instance."""
    global _suggester_instance
    if _suggester_instance is None:
        _suggester_instance = TransitionSuggester()
    return _suggester_instance


def is_ai_available() -> bool:
    """Check if AI suggestions are available."""
    return get_suggester().is_available
