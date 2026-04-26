import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional, Dict, Any
import os
import threading
from PIL import Image, ImageTk
from core.transitions import TRANSITION_TYPES, TRANSITION_LABELS
from core.ai_suggester import get_suggester, is_ai_available


class VideoGeneratorApp:
    """Main GUI application for the video generator."""
    
    SUPPORTED_IMAGES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
    SUPPORTED_VIDEOS = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gerador de Vídeo")
        self.root.geometry("950x850")
        self.root.minsize(850, 800)
        
        self.media_paths: List[str] = []
        self.audio_path: Optional[str] = None
        self.audio_duration: float = 0
        self.output_path: Optional[str] = None
        self.thumbnail_refs: List[ImageTk.PhotoImage] = []
        
        self.transition_enabled = tk.BooleanVar(value=False)
        self.global_transition_type = tk.StringVar(value="crossfade")
        self.global_transition_duration = tk.DoubleVar(value=1.0)
        self.individual_transitions: Dict[str, Dict[str, Any]] = {}
        
        self.individual_enabled = tk.BooleanVar(value=False)
        self.individual_type = tk.StringVar(value="crossfade")
        self.individual_duration = tk.DoubleVar(value=1.0)
        
        self.image_durations: Dict[int, float] = {}
        self.default_image_duration = tk.DoubleVar(value=3.0)
        self._selected_image_index: Optional[int] = None
        
        self._undo_stack: List[Dict] = []
        self._max_undo = 10
        
        self.ai_suggestions_enabled = tk.BooleanVar(value=False)
        self._ai_available = is_ai_available()
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tab_media = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(tab_media, text="📁 Mídia")
        
        self.tab_timeline = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.tab_timeline, text="⏱️ Linha do Tempo")
        
        self.tab_ai = ttk.Frame(self.notebook, padding="5")
        self.notebook.add(self.tab_ai, text="🤖 Sugestões IA")
        
        self._setup_media_tab(tab_media)
        self._setup_timeline_tab(self.tab_timeline)
        self._setup_ai_tab(self.tab_ai)
        
        self._setup_bottom_controls(main_frame)
    
    def _setup_media_tab(self, parent: ttk.Frame) -> None:
        """Setup the media tab with internal sub-tabs."""
        media_notebook = ttk.Notebook(parent)
        media_notebook.pack(fill=tk.BOTH, expand=True)

        tab_visual = ttk.Frame(media_notebook, padding="5")
        media_notebook.add(tab_visual, text="🖼️ Imagens / Vídeo")

        tab_audio = ttk.Frame(media_notebook, padding="5")
        media_notebook.add(tab_audio, text="🎵 Áudio")

        # ── Aba: Imagens / Vídeo ──────────────────────────────────────
        media_btn_frame = ttk.Frame(tab_visual)
        media_btn_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(
            media_btn_frame,
            text="Adicionar Imagens",
            command=self._add_images
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            media_btn_frame,
            text="Adicionar Vídeo",
            command=self._add_video
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            media_btn_frame,
            text="Remover Selecionado",
            command=self._remove_selected
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            media_btn_frame,
            text="Limpar Tudo",
            command=self._clear_media
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            media_btn_frame,
            text="↑ Subir",
            command=self._move_up
        ).pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Button(
            media_btn_frame,
            text="↓ Descer",
            command=self._move_down
        ).pack(side=tk.RIGHT)

        list_frame = ttk.Frame(tab_visual)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.media_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        self.media_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.media_listbox.bind('<<ListboxSelect>>', self._on_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.media_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.media_listbox.config(yscrollcommand=scrollbar.set)

        preview_frame = ttk.LabelFrame(tab_visual, text="Pré-visualização", padding="5")
        preview_frame.pack(fill=tk.X, pady=(10, 0))

        self.preview_label = ttk.Label(preview_frame, text="Selecione uma mídia para visualizar")
        self.preview_label.pack(pady=10)

        # ── Aba: Áudio ────────────────────────────────────────────────
        audio_group = ttk.LabelFrame(tab_audio, text="Arquivo de Áudio MP3", padding="10")
        audio_group.pack(fill=tk.X, pady=(0, 10))

        audio_inner = ttk.Frame(audio_group)
        audio_inner.pack(fill=tk.X)

        ttk.Button(
            audio_inner,
            text="Selecionar MP3",
            command=self._select_audio
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.audio_label = ttk.Label(audio_inner, text="Nenhum arquivo selecionado")
        self.audio_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        output_group = ttk.LabelFrame(tab_audio, text="Local de Salvamento", padding="10")
        output_group.pack(fill=tk.X, pady=(0, 10))

        output_inner = ttk.Frame(output_group)
        output_inner.pack(fill=tk.X)

        ttk.Button(
            output_inner,
            text="Escolher Local",
            command=self._select_output
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.output_label = ttk.Label(output_inner, text="Nenhum local selecionado")
        self.output_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _setup_timeline_tab(self, parent: ttk.Frame) -> None:
        """Setup the timeline tab."""
        # ── Linha do Tempo ────────────────────────────────────────────────
        timeline_frame = ttk.LabelFrame(parent, text="Linha do Tempo (arraste para reordenar)", padding="10")
        timeline_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        self.timeline_canvas = tk.Canvas(timeline_frame, height=160, bg="white")
        self.timeline_canvas.pack(fill=tk.BOTH, expand=True)

        self._drag_data = {"index": None, "start_x": 0}
        self.timeline_canvas.bind("<ButtonPress-1>", self._on_drag_start)
        self.timeline_canvas.bind("<B1-Motion>", self._on_drag_motion)
        self.timeline_canvas.bind("<ButtonRelease-1>", self._on_drag_end)

        # ── Duração total ─────────────────────────────────────────────────
        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(5, 5))

        self.timeline_total_label = ttk.Label(info_frame, text="Duração total: 0:00", font=("TkDefaultFont", 11, "bold"))
        self.timeline_total_label.pack(side=tk.LEFT)

        self.timeline_audio_label = ttk.Label(info_frame, text="")
        self.timeline_audio_label.pack(side=tk.RIGHT)

        # ── Botão Gerar Vídeo ─────────────────────────────────────────────
        self.generate_btn = ttk.Button(
            parent,
            text="▶ Gerar Vídeo",
            command=self._generate_video
        )
        self.generate_btn.pack(fill=tk.X, pady=(0, 5))

        # ── Botão Sugerir Transições com IA ───────────────────────────────
        ai_trans_frame = ttk.Frame(parent)
        ai_trans_frame.pack(fill=tk.X, pady=(0, 8))

        self.ai_suggest_btn = ttk.Button(
            ai_trans_frame,
            text="🤖 Sugerir Transições com IA",
            command=self._suggest_transitions_with_ai
        )
        self.ai_suggest_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.ai_trans_status = ttk.Label(ai_trans_frame, text="")
        self.ai_trans_status.pack(side=tk.LEFT)

        # ── Sub-abas ──────────────────────────────────────────────────────
        sub_notebook = ttk.Notebook(parent)
        sub_notebook.pack(fill=tk.BOTH, expand=False)

        tab_transitions = ttk.Frame(sub_notebook, padding="5")
        sub_notebook.add(tab_transitions, text="🔀 Transições")

        tab_duration = ttk.Frame(sub_notebook, padding="5")
        sub_notebook.add(tab_duration, text="⏱️ Duração individual e geral")

        self._setup_transition_ui(tab_transitions)
        self._setup_duration_ui(tab_duration)

    def _setup_duration_ui(self, parent: ttk.Frame) -> None:
        """Setup duration controls (general and individual)."""
        config_frame = ttk.LabelFrame(parent, text="Duração Geral", padding="10")
        config_frame.pack(fill=tk.X, pady=(0, 10))

        auto_frame = ttk.Frame(config_frame)
        auto_frame.pack(fill=tk.X, pady=(0, 10))

        self.auto_distribute_var = tk.BooleanVar(value=False)

        ttk.Button(
            auto_frame,
            text="📊 Distribuir pelo Áudio",
            command=self._distribute_by_audio
        ).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Separator(auto_frame, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        ttk.Label(auto_frame, text="Duração total manual:").pack(side=tk.LEFT, padx=(0, 5))

        self.manual_duration_var = tk.DoubleVar(value=60.0)
        self.manual_duration_spin = ttk.Spinbox(
            auto_frame,
            from_=5.0,
            to=600.0,
            increment=5.0,
            textvariable=self.manual_duration_var,
            width=6
        )
        self.manual_duration_spin.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(auto_frame, text="s").pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            auto_frame,
            text="Aplicar",
            command=self._apply_manual_duration
        ).pack(side=tk.LEFT)

        self.duration_source_label = ttk.Label(auto_frame, text="", foreground="gray")
        self.duration_source_label.pack(side=tk.LEFT, padx=(10, 0))

        default_frame = ttk.Frame(config_frame)
        default_frame.pack(fill=tk.X)

        ttk.Label(default_frame, text="Duração padrão por imagem:").pack(side=tk.LEFT, padx=(0, 10))

        self.default_duration_spin = ttk.Spinbox(
            default_frame,
            from_=1.0,
            to=30.0,
            increment=0.5,
            textvariable=self.default_image_duration,
            width=6
        )
        self.default_duration_spin.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Label(default_frame, text="segundos").pack(side=tk.LEFT, padx=(0, 20))

        ttk.Button(
            default_frame,
            text="Aplicar a Todas",
            command=self._apply_default_duration
        ).pack(side=tk.LEFT)

        individual_frame = ttk.LabelFrame(parent, text="Duração Individual", padding="5")
        individual_frame.pack(fill=tk.X, pady=(10, 10))

        time_row1 = ttk.Frame(individual_frame)
        time_row1.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(time_row1, text="Início:").pack(side=tk.LEFT, padx=(0, 5))

        self.start_minutes_var = tk.IntVar(value=0)
        self.start_minutes_spin = ttk.Spinbox(
            time_row1, from_=0, to=60, increment=1,
            textvariable=self.start_minutes_var, width=3, state="disabled"
        )
        self.start_minutes_spin.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(time_row1, text=":").pack(side=tk.LEFT)

        self.start_seconds_var = tk.DoubleVar(value=0.0)
        self.start_seconds_spin = ttk.Spinbox(
            time_row1, from_=0, to=59.9, increment=0.5,
            textvariable=self.start_seconds_var, width=5, state="disabled"
        )
        self.start_seconds_spin.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(time_row1, text="Fim:").pack(side=tk.LEFT, padx=(0, 5))

        self.end_minutes_var = tk.IntVar(value=0)
        self.end_minutes_spin = ttk.Spinbox(
            time_row1, from_=0, to=60, increment=1,
            textvariable=self.end_minutes_var, width=3
        )
        self.end_minutes_spin.pack(side=tk.LEFT, padx=(0, 2))
        ttk.Label(time_row1, text=":").pack(side=tk.LEFT)

        self.end_seconds_var = tk.DoubleVar(value=3.0)
        self.end_seconds_spin = ttk.Spinbox(
            time_row1, from_=0, to=59.9, increment=0.5,
            textvariable=self.end_seconds_var, width=5
        )
        self.end_seconds_spin.pack(side=tk.LEFT, padx=(0, 15))

        self.apply_individual_btn = ttk.Button(
            time_row1,
            text="✓ Aplicar",
            command=self._on_timeline_duration_change,
            width=10
        )
        self.apply_individual_btn.pack(side=tk.LEFT)

        time_row2 = ttk.Frame(individual_frame)
        time_row2.pack(fill=tk.X)

        ttk.Label(time_row2, text="Duração:").pack(side=tk.LEFT, padx=(0, 5))
        self.duration_display_label = ttk.Label(time_row2, text="0:00", font=("TkDefaultFont", 10, "bold"))
        self.duration_display_label.pack(side=tk.LEFT, padx=(0, 20))

        self.timeline_item_label = ttk.Label(time_row2, text="⬆️ Selecione uma imagem")
        self.timeline_item_label.pack(side=tk.LEFT)

        self.end_minutes_spin.bind("<Return>", lambda e: self._on_timeline_duration_change())
        self.end_seconds_spin.bind("<Return>", lambda e: self._on_timeline_duration_change())
        self.end_minutes_spin.bind("<<Increment>>", lambda e: self._update_duration_display())
        self.end_minutes_spin.bind("<<Decrement>>", lambda e: self._update_duration_display())
        self.end_seconds_spin.bind("<<Increment>>", lambda e: self._update_duration_display())
        self.end_seconds_spin.bind("<<Decrement>>", lambda e: self._update_duration_display())

        actions_frame = ttk.LabelFrame(parent, text="Ações", padding="10")
        actions_frame.pack(fill=tk.X)

        actions_row = ttk.Frame(actions_frame)
        actions_row.pack(fill=tk.X)

        ttk.Button(
            actions_row,
            text="⧉ Duplicar Imagem",
            command=self._duplicate_selected
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Separator(actions_row, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.undo_btn = ttk.Button(
            actions_row,
            text="↩ Desfazer",
            command=self._undo_timeline
        )
        self.undo_btn.pack(side=tk.LEFT)

        self.loop_info_label = ttk.Label(actions_frame, text="Selecione uma imagem na timeline para duplicá-la")
        self.loop_info_label.pack(pady=(5, 0), anchor="w")

    def _apply_default_duration(self) -> None:
        """Apply default duration to all images."""
        default = self.default_image_duration.get()
        for i, path in enumerate(self.media_paths):
            if self._is_image(path):
                self.image_durations[i] = default
        self._update_timeline()
    
    def _distribute_by_audio(self) -> None:
        """Distribute image durations by audio length."""
        if self.audio_duration <= 0:
            self.duration_source_label.config(text="⚠️ Carregue um áudio primeiro!")
            return
        
        if not self.media_paths:
            self.duration_source_label.config(text="⚠️ Adicione imagens primeiro!")
            return
        
        self._save_state()
        self._distribute_durations_to_audio(force=True)
        
        image_count = len([p for p in self.media_paths if self._is_image(p)])
        duration_per = self.audio_duration / image_count if image_count > 0 else 0
        self.duration_source_label.config(text=f"✓ Distribuído: {duration_per:.1f}s por imagem")
    
    def _apply_manual_duration(self) -> None:
        """Apply manual duration to distribute images."""
        if not self.media_paths:
            self.duration_source_label.config(text="⚠️ Adicione imagens primeiro!")
            return
        
        total_duration = self.manual_duration_var.get()
        image_paths = [p for p in self.media_paths if self._is_image(p)]
        
        if not image_paths:
            return
        
        self._save_state()
        
        duration_per_image = total_duration / len(image_paths)
        
        for i, path in enumerate(self.media_paths):
            if self._is_image(path):
                self.image_durations[i] = duration_per_image
        
        self.default_image_duration.set(round(duration_per_image, 1))
        self._update_timeline()
        self._update_timeline_selection()
        
        self.duration_source_label.config(text=f"✓ Distribuído: {duration_per_image:.1f}s por imagem")
    
    def _save_state(self) -> None:
        """Save current state for undo."""
        state = {
            "media_paths": self.media_paths.copy(),
            "image_durations": self.image_durations.copy()
        }
        self._undo_stack.append(state)
        
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
    
    def _undo_timeline(self) -> None:
        """Undo last timeline change."""
        if not self._undo_stack:
            self.loop_info_label.config(text="⚠️ Nada para desfazer")
            return
        
        state = self._undo_stack.pop()
        
        self.media_paths = state["media_paths"]
        self.image_durations = state["image_durations"]
        
        self.media_listbox.delete(0, tk.END)
        for path in self.media_paths:
            self.media_listbox.insert(tk.END, os.path.basename(path))
        
        self._update_timeline()
        
        remaining = len(self._undo_stack)
        self.loop_info_label.config(text=f"✓ Desfeito! ({remaining} ações restantes)")
    
    def _suggest_transitions_with_ai(self) -> None:
        """Suggest transitions for all image pairs using AI."""
        image_paths = [p for p in self.media_paths if self._is_image(p)]
        
        if len(image_paths) < 2:
            self.ai_trans_status.config(text="⚠️ Adicione pelo menos 2 imagens")
            return
        
        self._ai_available = is_ai_available()
        
        if not self._ai_available:
            self.ai_trans_status.config(text="⚠️ IA não disponível (inicie Ollama)")
            return
        
        self.ai_suggest_btn.config(state="disabled")
        self.ai_trans_status.config(text="🔄 Analisando imagens...")
        self.root.update()
        
        import threading
        thread = threading.Thread(target=self._suggest_transitions_thread, args=(image_paths,))
        thread.daemon = True
        thread.start()
    
    def _suggest_transitions_thread(self, image_paths: List[str]) -> None:
        """Thread to get AI suggestions for transitions."""
        try:
            from core.ai_suggester import TransitionSuggester
            
            suggester = TransitionSuggester()
            
            self.transition_enabled.set(True)
            self.root.after(0, self._on_transition_toggle)
            
            total_pairs = len(image_paths) - 1
            
            for i in range(total_pairs):
                img1 = image_paths[i]
                img2 = image_paths[i + 1]
                
                self.root.after(0, lambda idx=i, total=total_pairs: 
                    self.ai_trans_status.config(text=f"🔄 Analisando par {idx+1}/{total}..."))
                
                result = suggester.suggest_transition(img1, img2)
                print(f"[DEBUG] IA sugeriu para {os.path.basename(img1)}: {result}")
                
                if result and result.get("type"):
                    trans_type = result["type"]
                    trans_duration = result.get("duration", 1.0)
                    
                    self.individual_transitions[img1] = {
                        "type": trans_type,
                        "duration": trans_duration
                    }
                    print(f"[DEBUG] Transição aplicada: {img1} -> {trans_type}")
            
            self.root.after(0, self._on_ai_suggestions_complete, total_pairs)
            
        except Exception as e:
            self.root.after(0, lambda: self.ai_trans_status.config(text=f"❌ Erro: {str(e)[:30]}"))
            self.root.after(0, lambda: self.ai_suggest_btn.config(state="normal"))
    
    def _on_ai_suggestions_complete(self, count: int) -> None:
        """Handle AI suggestions completion."""
        self.ai_suggest_btn.config(state="normal")
        self.ai_trans_status.config(text=f"✓ {count} transições sugeridas!")
        self._update_timeline()
    
    def _duplicate_selected(self) -> None:
        """Duplicate the currently selected image and insert it right after."""
        index = self._selected_image_index
        if index is None:
            selection = self.media_listbox.curselection()
            if selection:
                index = selection[0]
            else:
                self.loop_info_label.config(text="⚠️ Selecione uma imagem na timeline primeiro")
                return
        
        if index >= len(self.media_paths):
            return
        
        path = self.media_paths[index]
        if not self._is_image(path):
            self.loop_info_label.config(text="⚠️ Só é possível duplicar imagens")
            return
        
        self._save_state()
        
        # Copy duration of source
        src_duration = self.image_durations.get(index, self.default_image_duration.get())
        
        # Shift all indices > insert_pos up by 1
        insert_pos = index + 1
        new_durations = {}
        for old_idx, dur in self.image_durations.items():
            if old_idx < insert_pos:
                new_durations[old_idx] = dur
            else:
                new_durations[old_idx + 1] = dur
        new_durations[insert_pos] = src_duration
        self.image_durations = new_durations
        
        self.media_paths.insert(insert_pos, path)
        self.media_listbox.insert(insert_pos, os.path.basename(path))
        
        self._selected_image_index = insert_pos
        self.media_listbox.selection_clear(0, tk.END)
        self.media_listbox.selection_set(insert_pos)
        self.media_listbox.see(insert_pos)
        
        self._update_timeline()
        self._update_timeline_selection()
        
        name = os.path.basename(path)
        self.loop_info_label.config(text=f"✓ '{name}' duplicada na posição {insert_pos + 1}")
    
    def _distribute_durations_to_audio(self, force: bool = False) -> None:
        """Distribute image durations equally to match audio duration."""
        if self.audio_duration <= 0:
            return
        
        if not force:
            self._update_timeline()
            return
        
        image_paths = [p for p in self.media_paths if self._is_image(p)]
        if not image_paths:
            return
        
        duration_per_image = self.audio_duration / len(image_paths)
        
        for i, path in enumerate(self.media_paths):
            if self._is_image(path):
                self.image_durations[i] = duration_per_image
        
        self.default_image_duration.set(round(duration_per_image, 1))
        
        self._update_timeline()
        self._update_timeline_selection()
    
    def _on_timeline_duration_change(self) -> None:
        """Handle individual duration change."""
        if self._selected_image_index is None:
            selection = self.media_listbox.curselection()
            if selection:
                self._selected_image_index = selection[0]
            else:
                self.timeline_item_label.config(text="⚠️ Clique em uma imagem na linha do tempo primeiro!")
                return
        
        index = self._selected_image_index
        if index >= len(self.media_paths):
            self.timeline_item_label.config(text="⚠️ Clique em uma imagem na linha do tempo primeiro!")
            return
        
        path = self.media_paths[index]
        
        if self._is_image(path):
            start_time = (self.start_minutes_var.get() * 60) + self.start_seconds_var.get()
            end_time = (self.end_minutes_var.get() * 60) + self.end_seconds_var.get()
            
            new_duration = end_time - start_time
            
            if new_duration < 0.5:
                new_duration = 0.5
                end_time = start_time + 0.5
                self.end_minutes_var.set(int(end_time // 60))
                self.end_seconds_var.set(end_time % 60)
            
            self.image_durations[index] = new_duration
            
            self.duration_source_label.config(text="")
            
            self._update_timeline()
            self._highlight_selected_block()
            self._update_duration_display()
            
            name = os.path.basename(path)
            self.timeline_item_label.config(text=f"✓ {name} aplicado!")
    
    def _update_duration_display(self) -> None:
        """Update the duration display label."""
        start_time = (self.start_minutes_var.get() * 60) + self.start_seconds_var.get()
        end_time = (self.end_minutes_var.get() * 60) + self.end_seconds_var.get()
        duration = max(0, end_time - start_time)
        
        mins = int(duration // 60)
        secs = duration % 60
        self.duration_display_label.config(text=f"{mins}:{secs:04.1f}")
    
    def _get_start_time_for_index(self, target_index: int) -> float:
        """Calculate the start time for a given media index."""
        start_time = 0.0
        for i, path in enumerate(self.media_paths):
            if i >= target_index:
                break
            if self._is_image(path):
                start_time += self.image_durations.get(i, self.default_image_duration.get())
            else:
                try:
                    from moviepy.editor import VideoFileClip
                    with VideoFileClip(path) as clip:
                        start_time += clip.duration
                except:
                    start_time += 10
        return start_time
    
    def _update_timeline(self) -> None:
        """Update the timeline visualization."""
        self.timeline_canvas.delete("all")
        
        if not self.media_paths:
            self.timeline_total_label.config(text="Duração total: 0:00")
            return
        
        canvas_width = self.timeline_canvas.winfo_width()
        if canvas_width < 10:
            canvas_width = 800
        
        canvas_height = 160
        bar_height = 40
        bar_y = 10
        
        trans_bar_y = bar_y + bar_height + 5
        trans_bar_height = 25
        
        total_duration = 0
        items = []
        
        for i, path in enumerate(self.media_paths):
            name = os.path.basename(path)
            if self._is_image(path):
                duration = self.image_durations.get(i, self.default_image_duration.get())
            else:
                duration = 0
                try:
                    from moviepy.editor import VideoFileClip
                    with VideoFileClip(path) as clip:
                        duration = clip.duration
                except:
                    duration = 10
            
            items.append({"path": path, "name": name, "duration": duration})
            total_duration += duration
        
        if total_duration == 0:
            return
        
        colors = ["#4CAF50", "#2196F3", "#FF9800", "#9C27B0", "#F44336", "#00BCD4", "#FFEB3B", "#795548"]
        
        x = 10
        available_width = canvas_width - 20
        self._timeline_blocks = []
        
        for i, item in enumerate(items):
            width = max(30, (item["duration"] / total_duration) * available_width)
            color = colors[i % len(colors)]
            
            rect_id = self.timeline_canvas.create_rectangle(
                x, bar_y, x + width, bar_y + bar_height,
                fill=color, outline="white", width=2,
                tags=f"block_{i}"
            )
            
            display_name = item["name"][:15] + "..." if len(item["name"]) > 15 else item["name"]
            text1_id = self.timeline_canvas.create_text(
                x + width/2, bar_y + bar_height/2 - 8,
                text=display_name, fill="white", font=("TkDefaultFont", 8, "bold"),
                tags=f"block_{i}"
            )
            
            dur = item["duration"]
            if dur >= 60:
                mins = int(dur // 60)
                secs = dur % 60
                duration_text = f"{mins}:{secs:04.1f}"
            else:
                duration_text = f"{dur:.1f}s"
            
            text2_id = self.timeline_canvas.create_text(
                x + width/2, bar_y + bar_height/2 + 8,
                text=duration_text, fill="white", font=("TkDefaultFont", 9),
                tags=f"block_{i}"
            )
            
            self._timeline_blocks.append({
                "index": i,
                "x1": x,
                "x2": x + width,
                "rect_id": rect_id
            })
            
            self.timeline_canvas.tag_bind(f"block_{i}", "<Button-1>", lambda e, idx=i: self._on_timeline_click(idx))
            self.timeline_canvas.tag_bind(f"block_{i}", "<Enter>", lambda e, idx=i: self._on_timeline_hover(idx, True))
            self.timeline_canvas.tag_bind(f"block_{i}", "<Leave>", lambda e, idx=i: self._on_timeline_hover(idx, False))
            
            x += width
        
        if self.transition_enabled.get() and len(items) > 1:
            self.timeline_canvas.create_text(
                10, trans_bar_y + trans_bar_height/2,
                text="Transições:", fill="#666", font=("TkDefaultFont", 8),
                anchor="w"
            )
            
            trans_colors = {
                "crossfade": "#E91E63",
                "fade": "#9C27B0", 
                "slide_left": "#3F51B5",
                "slide_right": "#2196F3",
                "slide_up": "#00BCD4",
                "slide_down": "#009688",
                "wipe_left": "#4CAF50",
                "wipe_right": "#8BC34A",
                "blur": "#FF9800",
                "none": "#9E9E9E"
            }
            
            for i in range(len(self._timeline_blocks) - 1):
                block = self._timeline_blocks[i]
                next_block = self._timeline_blocks[i + 1]
                
                trans_x = block["x2"]
                trans_width = 20
                
                path = items[i]["path"]
                if path in self.individual_transitions:
                    trans_type = self.individual_transitions[path].get("type", self.global_transition_type.get())
                    trans_dur = self.individual_transitions[path].get("duration", self.global_transition_duration.get())
                else:
                    trans_type = self.global_transition_type.get()
                    trans_dur = self.global_transition_duration.get()
                
                trans_color = trans_colors.get(trans_type, "#E91E63")
                
                self.timeline_canvas.create_polygon(
                    trans_x - 5, trans_bar_y,
                    trans_x + 15, trans_bar_y + trans_bar_height/2,
                    trans_x - 5, trans_bar_y + trans_bar_height,
                    fill=trans_color, outline="white", width=1,
                    tags=f"trans_{i}"
                )
                
                trans_label = trans_type.replace("_", " ").title()[:6]
                self.timeline_canvas.create_text(
                    trans_x + 5, trans_bar_y + trans_bar_height + 10,
                    text=f"{trans_label} {trans_dur}s", fill="#666", font=("TkDefaultFont", 7),
                    tags=f"trans_{i}"
                )
        
        scale_y = trans_bar_y + trans_bar_height + 25 if self.transition_enabled.get() and len(items) > 1 else bar_y + bar_height + 15
        
        self.timeline_canvas.create_line(10, scale_y, canvas_width - 10, scale_y, fill="#ccc")
        
        if total_duration >= 60:
            step = max(10, int(total_duration / 10))
            for i in range(0, int(total_duration) + 1, step):
                tick_x = 10 + (i / total_duration) * available_width
                self.timeline_canvas.create_line(tick_x, scale_y - 5, tick_x, scale_y + 5, fill="#999")
                tick_mins = int(i // 60)
                tick_secs = int(i % 60)
                tick_label = f"{tick_mins}:{tick_secs:02d}"
                self.timeline_canvas.create_text(tick_x, scale_y + 15, text=tick_label, fill="#666", font=("TkDefaultFont", 8))
        else:
            for i in range(0, int(total_duration) + 1, max(1, int(total_duration / 10))):
                tick_x = 10 + (i / total_duration) * available_width
                self.timeline_canvas.create_line(tick_x, scale_y - 5, tick_x, scale_y + 5, fill="#999")
                self.timeline_canvas.create_text(tick_x, scale_y + 15, text=f"{i}s", fill="#666", font=("TkDefaultFont", 8))
        
        mins = int(total_duration // 60)
        secs = int(total_duration % 60)
        
        if self.audio_duration > 0:
            diff = total_duration - self.audio_duration
            if diff < -0.5:
                diff_abs = abs(diff)
                diff_mins = int(diff_abs // 60)
                diff_secs = int(diff_abs % 60)
                self.timeline_total_label.config(
                    text=f"⚠️ Duração: {mins}:{secs:02d} (faltam {diff_mins}:{diff_secs:02d} para o áudio)",
                    foreground="red"
                )
            elif diff > 0.5:
                diff_mins = int(diff // 60)
                diff_secs = int(diff % 60)
                self.timeline_total_label.config(
                    text=f"⚠️ Duração: {mins}:{secs:02d} (excede {diff_mins}:{diff_secs:02d} do áudio)",
                    foreground="orange"
                )
            else:
                self.timeline_total_label.config(
                    text=f"✓ Duração: {mins}:{secs:02d} (igual ao áudio)",
                    foreground="green"
                )
        else:
            self.timeline_total_label.config(
                text=f"Duração total: {mins}:{secs:02d}",
                foreground="black"
            )
        
        self._highlight_selected_block()
    
    def _on_timeline_click(self, index: int) -> None:
        """Handle click on a timeline block."""
        if index < len(self.media_paths):
            self._selected_image_index = index
            
            self.media_listbox.selection_clear(0, tk.END)
            self.media_listbox.selection_set(index)
            self.media_listbox.see(index)
            
            path = self.media_paths[index]
            self._show_preview(path)
            self._update_individual_controls()
            self._update_timeline_selection()
            self._highlight_selected_block()
    
    def _on_timeline_hover(self, index: int, entering: bool) -> None:
        """Handle hover over a timeline block."""
        if not hasattr(self, '_timeline_blocks') or index >= len(self._timeline_blocks):
            return
        
        block = self._timeline_blocks[index]
        rect_id = block["rect_id"]
        
        if entering:
            self.timeline_canvas.itemconfig(rect_id, width=4)
            self.timeline_canvas.config(cursor="hand2")
        else:
            selection = self.media_listbox.curselection()
            selected_index = selection[0] if selection else -1
            
            if index == selected_index:
                self.timeline_canvas.itemconfig(rect_id, width=4, outline="#FFD700")
            else:
                self.timeline_canvas.itemconfig(rect_id, width=2, outline="white")
            self.timeline_canvas.config(cursor="")
    
    def _highlight_selected_block(self) -> None:
        """Highlight the currently selected block in the timeline."""
        if not hasattr(self, '_timeline_blocks'):
            return
        
        selection = self.media_listbox.curselection()
        selected_index = selection[0] if selection else -1
        
        for block in self._timeline_blocks:
            rect_id = block["rect_id"]
            if block["index"] == selected_index:
                self.timeline_canvas.itemconfig(rect_id, outline="#FFD700", width=4)
            else:
                self.timeline_canvas.itemconfig(rect_id, outline="white", width=2)
    
    def _on_drag_start(self, event) -> None:
        """Handle drag start on timeline."""
        if not hasattr(self, '_timeline_blocks'):
            return
        
        x = event.x
        bar_y = 35
        bar_height = 50
        
        if not (bar_y <= event.y <= bar_y + bar_height):
            return
        
        for block in self._timeline_blocks:
            if block["x1"] <= x <= block["x2"]:
                self._drag_data["index"] = block["index"]
                self._drag_data["start_x"] = x
                self.timeline_canvas.config(cursor="fleur")
                
                self.media_listbox.selection_clear(0, tk.END)
                self.media_listbox.selection_set(block["index"])
                self._show_preview(self.media_paths[block["index"]])
                self._update_timeline_selection()
                break
    
    def _on_drag_motion(self, event) -> None:
        """Handle drag motion on timeline."""
        if self._drag_data["index"] is None:
            return
        
        if not hasattr(self, '_timeline_blocks') or len(self._timeline_blocks) < 2:
            return
        
        x = event.x
        current_index = self._drag_data["index"]
        
        for block in self._timeline_blocks:
            if block["index"] != current_index:
                mid_x = (block["x1"] + block["x2"]) / 2
                
                if block["index"] < current_index and x < mid_x:
                    self._drag_data["target"] = block["index"]
                    self._show_drop_indicator(block["x1"])
                    return
                elif block["index"] > current_index and x > mid_x:
                    self._drag_data["target"] = block["index"]
                    self._show_drop_indicator(block["x2"])
                    return
        
        self._drag_data["target"] = None
        self._hide_drop_indicator()
    
    def _on_drag_end(self, event) -> None:
        """Handle drag end on timeline."""
        self.timeline_canvas.config(cursor="")
        self._hide_drop_indicator()
        
        if self._drag_data["index"] is None:
            return
        
        source_index = self._drag_data["index"]
        target_index = self._drag_data.get("target")
        
        self._drag_data = {"index": None, "start_x": 0}
        
        if target_index is not None and target_index != source_index:
            self._reorder_media(source_index, target_index)
    
    def _show_drop_indicator(self, x: float) -> None:
        """Show drop indicator line."""
        self.timeline_canvas.delete("drop_indicator")
        bar_y = 35
        bar_height = 50
        self.timeline_canvas.create_line(
            x, bar_y - 5, x, bar_y + bar_height + 5,
            fill="#FF0000", width=3, tags="drop_indicator"
        )
    
    def _hide_drop_indicator(self) -> None:
        """Hide drop indicator line."""
        self.timeline_canvas.delete("drop_indicator")
    
    def _reorder_media(self, source_index: int, target_index: int) -> None:
        """Reorder media in the list."""
        if source_index == target_index:
            return
        
        self._save_state()
        
        # Snapshot current durations as ordered list before reorder
        old_dur_list = [
            self.image_durations.get(i, self.default_image_duration.get())
            for i in range(len(self.media_paths))
        ]
        
        path = self.media_paths.pop(source_index)
        self.media_paths.insert(target_index, path)
        
        # Apply same reorder to durations list
        dur = old_dur_list.pop(source_index)
        old_dur_list.insert(target_index, dur)
        
        # Rebuild image_durations dict from reordered list
        self.image_durations = {
            i: old_dur_list[i]
            for i in range(len(self.media_paths))
            if self._is_image(self.media_paths[i])
        }
        
        self.media_listbox.delete(0, tk.END)
        for p in self.media_paths:
            self.media_listbox.insert(tk.END, os.path.basename(p))
        
        self.media_listbox.selection_set(target_index)
        self.media_listbox.see(target_index)
        
        self._update_timeline()
        self._update_timeline_selection()
        self._highlight_selected_block()
    
    def _update_timeline_selection(self) -> None:
        """Update timeline controls based on selection."""
        selection = self.media_listbox.curselection()
        
        if not selection:
            self.timeline_item_label.config(text="Selecione uma imagem na aba Mídia")
            self._selected_image_index = None
            return
        
        index = selection[0]
        if index >= len(self.media_paths):
            self._selected_image_index = None
            return
        
        self._selected_image_index = index
        
        path = self.media_paths[index]
        name = os.path.basename(path)
        
        if self._is_image(path):
            start_time = self._get_start_time_for_index(index)
            duration = self.image_durations.get(index, self.default_image_duration.get())
            end_time = start_time + duration
            
            self.start_minutes_var.set(int(start_time // 60))
            self.start_seconds_var.set(round(start_time % 60, 1))
            self.end_minutes_var.set(int(end_time // 60))
            self.end_seconds_var.set(round(end_time % 60, 1))
            
            self._update_duration_display()
            
            self.timeline_item_label.config(text=f"📷 {name}")
            self.end_minutes_spin.config(state="normal")
            self.end_seconds_spin.config(state="normal")
            self.apply_individual_btn.config(state="normal")
        else:
            self.timeline_item_label.config(text=f"🎬 {name} (duração fixa)")
            self.end_minutes_spin.config(state="disabled")
            self.end_seconds_spin.config(state="disabled")
            self.apply_individual_btn.config(state="disabled")
    
    def _setup_ai_tab(self, parent: ttk.Frame) -> None:
        """Setup the AI suggestions tab."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ai_state = "normal" if self._ai_available else "disabled"
        ai_text = "Ativar Sugestões IA" if self._ai_available else "Ollama não disponível"
        
        self.ai_check = ttk.Checkbutton(
            header_frame,
            text=ai_text,
            variable=self.ai_suggestions_enabled,
            state=ai_state,
            command=self._on_ai_toggle
        )
        self.ai_check.pack(side=tk.LEFT, padx=(0, 15))
        
        self.ai_analyze_btn = ttk.Button(
            header_frame,
            text="🔍 Analisar Imagens",
            command=self._request_ai_suggestions,
            state="disabled"
        )
        self.ai_analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.ai_status_label = ttk.Label(header_frame, text="")
        self.ai_status_label.pack(side=tk.LEFT)
        
        if not self._ai_available:
            info_label = ttk.Label(
                parent,
                text="Para usar sugestões IA:\n\n"
                     "1. Instale Ollama: brew install ollama\n"
                     "2. Inicie o servidor: ollama serve\n"
                     "3. Baixe o modelo: ollama pull llava\n"
                     "4. Reinicie esta aplicação",
                justify=tk.LEFT
            )
            info_label.pack(pady=20)
            return
        
        chat_frame = ttk.LabelFrame(parent, text="💬 Chat com IA", padding="10")
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.chat_history = tk.Text(
            chat_frame,
            wrap=tk.WORD,
            height=10,
            state="disabled",
            font=("TkDefaultFont", 10)
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        chat_scrollbar = ttk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_history.yview)
        self.chat_history.config(yscrollcommand=chat_scrollbar.set)
        
        self.chat_history.tag_configure("user", font=("TkDefaultFont", 10, "bold"), foreground="#0066cc")
        self.chat_history.tag_configure("ai", font=("TkDefaultFont", 10), foreground="#009900")
        self.chat_history.tag_configure("system", font=("TkDefaultFont", 9, "italic"), foreground="#666666")
        self.chat_history.tag_configure("config", font=("TkDefaultFont", 10, "bold"), foreground="#cc6600")
        
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X)
        
        self.chat_entry = ttk.Entry(input_frame, font=("TkDefaultFont", 10))
        self.chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.chat_entry.bind("<Return>", self._on_chat_enter)
        
        self.chat_send_btn = ttk.Button(
            input_frame,
            text="Enviar",
            command=self._send_chat_message
        )
        self.chat_send_btn.pack(side=tk.RIGHT)
        
        self._add_chat_message(
            "IA",
            "Olá! Descreva o estilo de transições que você deseja.\n"
            "Exemplos: 'transições suaves', 'estilo dramático', 'vídeo de viagem'",
            "ai"
        )
        
        details_frame = ttk.LabelFrame(parent, text="Detalhes das Sugestões", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        self.ai_details_text = tk.Text(
            details_frame,
            wrap=tk.WORD,
            height=8,
            state="disabled",
            font=("TkDefaultFont", 10)
        )
        self.ai_details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        ai_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.ai_details_text.yview)
        ai_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ai_details_text.config(yscrollcommand=ai_scrollbar.set)
        
        self.ai_details_text.tag_configure("header", font=("TkDefaultFont", 11, "bold"))
        self.ai_details_text.tag_configure("image", font=("TkDefaultFont", 10, "bold"), foreground="#0066cc")
        self.ai_details_text.tag_configure("transition", foreground="#009900")
        self.ai_details_text.tag_configure("reason", foreground="#666666")
    
    def _setup_bottom_controls(self, parent: ttk.Frame) -> None:
        """Setup bottom controls (progress bar)."""
        progress_frame = ttk.Frame(parent)
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)

        status_row = ttk.Frame(progress_frame)
        status_row.pack(fill=tk.X, pady=(5, 0))

        self.status_label = ttk.Label(status_row, text="")
        self.status_label.pack(side=tk.LEFT)

        self.timer_label = ttk.Label(status_row, text="", foreground="gray", font=("TkDefaultFont", 9))
        self.timer_label.pack(side=tk.RIGHT)
    
    def _setup_transition_ui(self, parent: ttk.Frame) -> None:
        """Setup the transition configuration UI."""
        transition_frame = ttk.LabelFrame(parent, text="Transições", padding="5")
        transition_frame.pack(fill=tk.X, pady=(0, 10))
        
        global_frame = ttk.Frame(transition_frame)
        global_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.transition_check = ttk.Checkbutton(
            global_frame,
            text="Ativar transições",
            variable=self.transition_enabled,
            command=self._on_transition_toggle
        )
        self.transition_check.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(global_frame, text="Tipo:").pack(side=tk.LEFT, padx=(0, 5))
        
        self._transition_values = [TRANSITION_LABELS[t] for t in TRANSITION_TYPES]
        self._label_to_key = {v: k for k, v in TRANSITION_LABELS.items()}
        self.global_type_combo = ttk.Combobox(
            global_frame,
            values=self._transition_values,
            state="disabled",
            width=20
        )
        self.global_type_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.global_type_combo.set(TRANSITION_LABELS["crossfade"])
        self.global_type_combo.bind("<<ComboboxSelected>>", self._on_global_type_change)
        
        ttk.Label(global_frame, text="Duração:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.global_duration_spin = ttk.Spinbox(
            global_frame,
            from_=0.5,
            to=3.0,
            increment=0.1,
            textvariable=self.global_transition_duration,
            width=5,
            state="disabled"
        )
        self.global_duration_spin.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(global_frame, text="s").pack(side=tk.LEFT)
        
        self.individual_frame = ttk.LabelFrame(transition_frame, text="Transição Individual (após imagem selecionada)", padding="5")
        self.individual_frame.pack(fill=tk.X, pady=(5, 0))
        
        individual_inner = ttk.Frame(self.individual_frame)
        individual_inner.pack(fill=tk.X)
        
        self.individual_check = ttk.Checkbutton(
            individual_inner,
            text="Personalizar",
            variable=self.individual_enabled,
            command=self._on_individual_toggle,
            state="disabled"
        )
        self.individual_check.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(individual_inner, text="Tipo:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.individual_type_combo = ttk.Combobox(
            individual_inner,
            values=self._transition_values,
            state="disabled",
            width=20
        )
        self.individual_type_combo.pack(side=tk.LEFT, padx=(0, 15))
        self.individual_type_combo.set(TRANSITION_LABELS["crossfade"])
        self.individual_type_combo.bind("<<ComboboxSelected>>", self._on_individual_type_change)
        
        ttk.Label(individual_inner, text="Duração:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.individual_duration_spin = ttk.Spinbox(
            individual_inner,
            from_=0.5,
            to=3.0,
            increment=0.1,
            textvariable=self.individual_duration,
            width=5,
            state="disabled"
        )
        self.individual_duration_spin.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Label(individual_inner, text="s").pack(side=tk.LEFT)
        
        self.individual_status = ttk.Label(self.individual_frame, text="Selecione uma imagem para configurar")
        self.individual_status.pack(pady=(5, 0))
    
    def _on_transition_toggle(self) -> None:
        """Handle transition enable/disable toggle."""
        enabled = self.transition_enabled.get()
        state = "readonly" if enabled else "disabled"
        spin_state = "normal" if enabled else "disabled"
        
        self.global_type_combo.config(state=state)
        self.global_duration_spin.config(state=spin_state)
        
        if self._ai_available:
            ai_state = "normal" if enabled else "disabled"
            self.ai_check.config(state=ai_state)
            if not enabled:
                self.ai_suggestions_enabled.set(False)
                self.ai_status_label.config(text="")
        
        self._update_individual_controls()
    
    def _on_ai_toggle(self) -> None:
        """Handle AI suggestions toggle."""
        enabled = self.ai_suggestions_enabled.get()
        if self._ai_available:
            btn_state = "normal" if enabled else "disabled"
            self.ai_analyze_btn.config(state=btn_state)
        
        if enabled and self.media_paths:
            self._clear_ai_details()
            self._add_ai_detail("Sugestões IA ativadas. Clique em 'Analisar Imagens' ou adicione novas imagens.\n", "header")
    
    def _request_ai_suggestions(self) -> None:
        """Request AI suggestions for current images."""
        image_paths = [p for p in self.media_paths if self._is_image(p)]
        
        if len(image_paths) < 2:
            self.ai_status_label.config(text="Adicione pelo menos 2 imagens")
            return
        
        self.ai_status_label.config(text="Analisando imagens...")
        self.ai_analyze_btn.config(state="disabled")
        self._clear_ai_details()
        self._add_ai_detail("🔍 Iniciando análise das imagens...\n\n", "header")
        
        self.notebook.select(self.tab_ai)
        
        def on_suggestion(index: int, path: str, transition: str, reason: str):
            self.root.after(0, lambda: self._apply_ai_suggestion(index, path, transition, reason))
        
        def on_complete(transitions: dict):
            self.root.after(0, lambda: self._on_ai_complete(transitions))
        
        suggester = get_suggester()
        suggester.suggest_all_async(image_paths, on_suggestion, on_complete)
    
    def _apply_ai_suggestion(self, index: int, path: str, transition: str, reason: str) -> None:
        """Apply a single AI suggestion."""
        if path not in self.individual_transitions:
            self.individual_transitions[path] = {
                "type": transition,
                "duration": self.global_transition_duration.get(),
                "ai_suggested": True,
                "reason": reason
            }
        
        name = os.path.basename(path)
        label = TRANSITION_LABELS.get(transition, transition)
        
        self._add_ai_detail(f"📷 {name}\n", "image")
        self._add_ai_detail(f"   Transição: ", "")
        self._add_ai_detail(f"{label}\n", "transition")
        if reason:
            self._add_ai_detail(f"   Motivo: {reason}\n", "reason")
        self._add_ai_detail("\n", "")
        
        self.ai_status_label.config(text=f"Analisando... ({index + 1})")
        self._update_listbox_display()
    
    def _on_ai_complete(self, transitions: dict) -> None:
        """Handle AI suggestions completion."""
        count = len(transitions)
        self.ai_status_label.config(text=f"✓ {count} sugestões aplicadas")
        self.ai_analyze_btn.config(state="normal")
        self._update_individual_controls()
        
        self._add_ai_detail("─" * 40 + "\n", "")
        self._add_ai_detail(f"✅ Análise concluída! {count} transições sugeridas.\n", "header")
        self._add_ai_detail("Você pode modificar qualquer sugestão na aba Linha do Tempo.", "reason")
    
    def _clear_ai_details(self) -> None:
        """Clear the AI details text area."""
        if hasattr(self, 'ai_details_text'):
            self.ai_details_text.config(state="normal")
            self.ai_details_text.delete("1.0", tk.END)
            self.ai_details_text.config(state="disabled")
    
    def _add_ai_detail(self, text: str, tag: str = "") -> None:
        """Add text to the AI details area."""
        if hasattr(self, 'ai_details_text'):
            self.ai_details_text.config(state="normal")
            if tag:
                self.ai_details_text.insert(tk.END, text, tag)
            else:
                self.ai_details_text.insert(tk.END, text)
            self.ai_details_text.see(tk.END)
            self.ai_details_text.config(state="disabled")
    
    def _add_chat_message(self, sender: str, message: str, tag: str = "") -> None:
        """Add a message to the chat history."""
        if hasattr(self, 'chat_history'):
            self.chat_history.config(state="normal")
            self.chat_history.insert(tk.END, f"{sender}: ", tag)
            self.chat_history.insert(tk.END, f"{message}\n\n")
            self.chat_history.see(tk.END)
            self.chat_history.config(state="disabled")
    
    def _on_chat_enter(self, event) -> None:
        """Handle Enter key in chat entry."""
        self._send_chat_message()
    
    def _send_chat_message(self) -> None:
        """Send a chat message to the AI."""
        if not hasattr(self, 'chat_entry'):
            return
        
        message = self.chat_entry.get().strip()
        if not message:
            return
        
        self.chat_entry.delete(0, tk.END)
        self._add_chat_message("Você", message, "user")
        
        self.chat_send_btn.config(state="disabled")
        self.chat_entry.config(state="disabled")
        
        suggester = get_suggester()
        suggester.chat_suggestion_async(message, self._on_chat_response)
    
    def _on_chat_response(self, result: dict) -> None:
        """Handle AI chat response."""
        self.root.after(0, lambda: self._process_chat_response(result))
    
    def _process_chat_response(self, result: dict) -> None:
        """Process the AI chat response in the main thread."""
        self.chat_send_btn.config(state="normal")
        self.chat_entry.config(state="normal")
        
        if not result.get("success"):
            self._add_chat_message("IA", result.get("message", "Erro desconhecido"), "system")
            return
        
        message = result.get("message", "")
        transition = result.get("transition")
        duration = result.get("duration")
        
        self._add_chat_message("IA", message, "ai")
        
        if transition and transition != "none":
            self.transition_enabled.set(True)
            self._on_transition_toggle()
            
            self.global_transition_type.set(transition)
            self.global_type_combo.set(TRANSITION_LABELS.get(transition, transition))
            
            if duration:
                self.global_transition_duration.set(duration)
            
            config_msg = f"✓ Configurado: {TRANSITION_LABELS.get(transition, transition)}"
            if duration:
                config_msg += f" ({duration}s)"
            self._add_chat_message("Sistema", config_msg, "config")
            
            num_images = len([p for p in self.media_paths if self._is_image(p)])
            if num_images < 2:
                self._add_chat_message(
                    "Sistema", 
                    "⚠️ Adicione pelo menos 2 imagens para ver as transições no vídeo.", 
                    "system"
                )
            
        elif transition == "none":
            self.transition_enabled.set(False)
            self._on_transition_toggle()
            self._add_chat_message("Sistema", "✓ Transições desativadas", "config")
    
    def _on_global_type_change(self, event) -> None:
        """Handle global transition type change."""
        label = self.global_type_combo.get()
        key = self._label_to_key.get(label, "crossfade")
        self.global_transition_type.set(key)
    
    def _on_individual_toggle(self) -> None:
        """Handle individual transition toggle."""
        selection = self.media_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.media_paths) - 1:
            return
        
        path = self.media_paths[index]
        enabled = self.individual_enabled.get()
        
        if enabled:
            state = "readonly"
            spin_state = "normal"
            label = self.individual_type_combo.get()
            trans_type = self._label_to_key.get(label, self.global_transition_type.get())
            
            self.individual_transitions[path] = {
                "type": trans_type,
                "duration": self.individual_duration.get()
            }
        else:
            state = "disabled"
            spin_state = "disabled"
            if path in self.individual_transitions:
                del self.individual_transitions[path]
        
        self.individual_type_combo.config(state=state)
        self.individual_duration_spin.config(state=spin_state)
        self._update_listbox_display()
    
    def _on_individual_type_change(self, event) -> None:
        """Handle individual transition type change."""
        selection = self.media_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self.media_paths) - 1:
            return
        
        path = self.media_paths[index]
        if path not in self.individual_transitions:
            return
        
        label = self.individual_type_combo.get()
        key = self._label_to_key.get(label, "crossfade")
        self.individual_transitions[path]["type"] = key
    
    def _update_individual_controls(self) -> None:
        """Update individual transition controls based on selection."""
        selection = self.media_listbox.curselection()
        
        if not self.transition_enabled.get():
            self.individual_check.config(state="disabled")
            self.individual_type_combo.config(state="disabled")
            self.individual_duration_spin.config(state="disabled")
            self.individual_status.config(text="Ative as transições primeiro")
            return
        
        if not selection:
            self.individual_check.config(state="disabled")
            self.individual_type_combo.config(state="disabled")
            self.individual_duration_spin.config(state="disabled")
            self.individual_status.config(text="Selecione uma imagem para configurar")
            return
        
        index = selection[0]
        
        if index >= len(self.media_paths) - 1:
            self.individual_check.config(state="disabled")
            self.individual_type_combo.config(state="disabled")
            self.individual_duration_spin.config(state="disabled")
            self.individual_status.config(text="Última imagem não tem transição após ela")
            return
        
        path = self.media_paths[index]
        
        if not self._is_image(path):
            self.individual_check.config(state="disabled")
            self.individual_type_combo.config(state="disabled")
            self.individual_duration_spin.config(state="disabled")
            self.individual_status.config(text="Transições só funcionam com imagens")
            return
        
        self.individual_check.config(state="normal")
        
        if path in self.individual_transitions:
            self.individual_enabled.set(True)
            trans = self.individual_transitions[path]
            self.individual_type_combo.set(TRANSITION_LABELS.get(trans["type"], "Crossfade (Dissolve)"))
            self.individual_duration.set(trans["duration"])
            self.individual_type_combo.config(state="readonly")
            self.individual_duration_spin.config(state="normal")
            
            if trans.get("ai_suggested") and trans.get("reason"):
                status_text = f"🤖 {trans['reason']}"
            elif trans.get("ai_suggested"):
                status_text = "🤖 Sugerido pela IA"
            else:
                status_text = "★ Transição personalizada"
            self.individual_status.config(text=status_text)
        else:
            self.individual_enabled.set(False)
            global_key = self.global_transition_type.get()
            self.individual_type_combo.set(TRANSITION_LABELS.get(global_key, "Crossfade (Dissolve)"))
            self.individual_duration.set(self.global_transition_duration.get())
            self.individual_type_combo.config(state="disabled")
            self.individual_duration_spin.config(state="disabled")
            self.individual_status.config(text="Usando transição global")
    
    def _update_listbox_display(self) -> None:
        """Update listbox to show which items have custom transitions."""
        selection = self.media_listbox.curselection()
        selected_index = selection[0] if selection else None
        
        self.media_listbox.delete(0, tk.END)
        
        for i, path in enumerate(self.media_paths):
            name = os.path.basename(path)
            if path in self.individual_transitions:
                trans = self.individual_transitions[path]
                if trans.get("ai_suggested"):
                    name = f"🤖 {name}"
                else:
                    name = f"★ {name}"
            self.media_listbox.insert(tk.END, name)
        
        if selected_index is not None:
            self.media_listbox.selection_set(selected_index)
        
    def _add_images(self) -> None:
        """Add image files to the media list."""
        filetypes = [
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
            ("Todos os arquivos", "*.*")
        ]
        paths = filedialog.askopenfilenames(
            title="Selecionar Imagens",
            filetypes=filetypes
        )
        
        if paths:
            if self.media_paths and self._is_video(self.media_paths[0]):
                if messagebox.askyesno(
                    "Substituir Vídeo",
                    "Já existe um vídeo selecionado. Deseja substituir por imagens?"
                ):
                    self._clear_media()
                else:
                    return
            
            for path in paths:
                if path not in self.media_paths:
                    index = len(self.media_paths)
                    self.media_paths.append(path)
                    self.media_listbox.insert(tk.END, os.path.basename(path))
                    self.image_durations[index] = self.default_image_duration.get()
            
            self._update_timeline()
            
            if self.ai_suggestions_enabled.get() and self.transition_enabled.get():
                self._request_ai_suggestions()
                    
    def _add_video(self) -> None:
        """Add a video file to the media list."""
        filetypes = [
            ("Vídeos", "*.mp4 *.avi *.mov *.mkv *.webm"),
            ("Todos os arquivos", "*.*")
        ]
        path = filedialog.askopenfilename(
            title="Selecionar Vídeo",
            filetypes=filetypes
        )
        
        if path:
            if self.media_paths:
                if messagebox.askyesno(
                    "Substituir Mídia",
                    "Já existem arquivos selecionados. Deseja substituir por este vídeo?"
                ):
                    self._clear_media()
                else:
                    return
            
            self.media_paths.append(path)
            self.media_listbox.insert(tk.END, os.path.basename(path))
            self._update_timeline()
            
    def _remove_selected(self) -> None:
        """Remove the selected item from the media list."""
        selection = self.media_listbox.curselection()
        if selection:
            index = selection[0]
            self.media_listbox.delete(index)
            del self.media_paths[index]
            # Rebuild image_durations shifting all indices above the removed one down by 1
            new_durations = {}
            for old_idx, dur in self.image_durations.items():
                if old_idx < index:
                    new_durations[old_idx] = dur
                elif old_idx > index:
                    new_durations[old_idx - 1] = dur
                # old_idx == index is dropped
            self.image_durations = new_durations
            self._clear_preview()
            self._update_timeline()
            
    def _clear_media(self) -> None:
        """Clear all media from the list."""
        self.media_listbox.delete(0, tk.END)
        self.media_paths.clear()
        self.individual_transitions.clear()
        self.image_durations.clear()
        self._clear_preview()
        self._update_individual_controls()
        self._update_timeline()
        
    def _move_up(self) -> None:
        """Move selected item up in the list."""
        selection = self.media_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self._save_state()
            self.media_paths[index], self.media_paths[index-1] = \
                self.media_paths[index-1], self.media_paths[index]

            dur_a = self.image_durations.get(index-1)
            dur_b = self.image_durations.get(index)
            if dur_b is not None:
                self.image_durations[index-1] = dur_b
            elif index-1 in self.image_durations:
                del self.image_durations[index-1]
            if dur_a is not None:
                self.image_durations[index] = dur_a
            elif index in self.image_durations:
                del self.image_durations[index]

            item = self.media_listbox.get(index)
            self.media_listbox.delete(index)
            self.media_listbox.insert(index-1, item)
            self.media_listbox.selection_set(index-1)
            self._update_timeline()
            self._update_timeline_selection()
            self._highlight_selected_block()
            
    def _move_down(self) -> None:
        """Move selected item down in the list."""
        selection = self.media_listbox.curselection()
        if selection and selection[0] < len(self.media_paths) - 1:
            index = selection[0]
            self._save_state()
            self.media_paths[index], self.media_paths[index+1] = \
                self.media_paths[index+1], self.media_paths[index]

            dur_a = self.image_durations.get(index)
            dur_b = self.image_durations.get(index+1)
            if dur_b is not None:
                self.image_durations[index] = dur_b
            elif index in self.image_durations:
                del self.image_durations[index]
            if dur_a is not None:
                self.image_durations[index+1] = dur_a
            elif index+1 in self.image_durations:
                del self.image_durations[index+1]

            item = self.media_listbox.get(index)
            self.media_listbox.delete(index)
            self.media_listbox.insert(index+1, item)
            self.media_listbox.selection_set(index+1)
            self._update_timeline()
            self._update_timeline_selection()
            self._highlight_selected_block()
            
    def _on_select(self, event) -> None:
        """Handle selection change in the media list."""
        selection = self.media_listbox.curselection()
        if selection:
            index = selection[0]
            path = self.media_paths[index]
            self._show_preview(path)
            self._update_individual_controls()
            self._update_timeline_selection()
            self._highlight_selected_block()
            
    def _show_preview(self, path: str) -> None:
        """Show preview of the selected media file."""
        if self._is_image(path):
            try:
                img = Image.open(path)
                img.thumbnail((200, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.thumbnail_refs.append(photo)
                self.preview_label.config(image=photo, text="")
            except Exception as e:
                self.preview_label.config(image="", text=f"Erro ao carregar: {e}")
        elif self._is_video(path):
            self.preview_label.config(image="", text=f"Vídeo: {os.path.basename(path)}")
        else:
            self.preview_label.config(image="", text="Formato não suportado")
            
    def _clear_preview(self) -> None:
        """Clear the preview area."""
        self.preview_label.config(image="", text="Selecione uma mídia para visualizar")
        
    def _select_audio(self) -> None:
        """Select the MP3 audio file."""
        filetypes = [
            ("Arquivos MP3", "*.mp3"),
            ("Todos os arquivos", "*.*")
        ]
        path = filedialog.askopenfilename(
            title="Selecionar Áudio MP3",
            filetypes=filetypes
        )
        
        if path:
            self.audio_path = path
            self.audio_label.config(text=os.path.basename(path))
            
            try:
                from moviepy.editor import AudioFileClip
                with AudioFileClip(path) as audio:
                    self.audio_duration = audio.duration
                    mins = int(self.audio_duration // 60)
                    secs = int(self.audio_duration % 60)
                    self.timeline_audio_label.config(text=f"🎵 Áudio: {mins}:{secs:02d}")
                    
                    self.manual_duration_var.set(self.audio_duration)
                    self.duration_source_label.config(text=f"Áudio carregado: {mins}:{secs:02d}")
            except:
                self.audio_duration = 0
                self.duration_source_label.config(text="")
            
    def _select_output(self) -> None:
        """Select the output file location."""
        path = filedialog.asksaveasfilename(
            title="Salvar Vídeo Como",
            defaultextension=".mp4",
            filetypes=[("Vídeo MP4", "*.mp4")]
        )
        
        if path:
            self.output_path = path
            self.output_label.config(text=os.path.basename(path))
            
    def _is_image(self, path: str) -> bool:
        """Check if file is a supported image."""
        return path.lower().endswith(self.SUPPORTED_IMAGES)
    
    def _is_video(self, path: str) -> bool:
        """Check if file is a supported video."""
        return path.lower().endswith(self.SUPPORTED_VIDEOS)
    
    def _validate_inputs(self) -> bool:
        """Validate all inputs before generating."""
        if not self.media_paths:
            messagebox.showerror("Erro", "Selecione pelo menos uma imagem ou vídeo.")
            return False
            
        if not self.audio_path:
            messagebox.showerror("Erro", "Selecione um arquivo de áudio MP3.")
            return False
            
        if not self.output_path:
            messagebox.showerror("Erro", "Escolha o local para salvar o vídeo.")
            return False
            
        return True
    
    def _update_progress(self, value: float) -> None:
        """Update the progress bar (thread-safe)."""
        self.root.after(0, lambda: self.progress_var.set(value * 100))
        
    def _generate_video(self) -> None:
        """Start video generation in a separate thread."""
        if not self._validate_inputs():
            return
            
        self.generate_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Gerando vídeo...")
        self.progress_var.set(0)
        
        import time
        self._generation_start_time = time.time()
        self._generation_timer_running = True
        self._tick_timer()
        
        thread = threading.Thread(target=self._generate_video_thread)
        thread.daemon = True
        thread.start()
        
    def _generate_video_thread(self) -> None:
        """Video generation thread."""
        try:
            from core.video_generator import VideoGenerator
            
            print("=" * 50)
            print("[DEBUG] INICIANDO GERAÇÃO DE VÍDEO")
            print(f"[DEBUG] Transições ativadas: {self.transition_enabled.get()}")
            print(f"[DEBUG] Tipo global: {self.global_transition_type.get()}")
            print(f"[DEBUG] Duração global: {self.global_transition_duration.get()}")
            print(f"[DEBUG] Transições individuais: {self.individual_transitions}")
            print(f"[DEBUG] Durações das imagens: {self.image_durations}")
            print(f"[DEBUG] Media paths: {self.media_paths}")
            print("=" * 50)
            
            generator = VideoGenerator(self.output_path, self.audio_path)
            generator.generate(
                self.media_paths,
                self._update_progress,
                self.transition_enabled.get(),
                self.global_transition_type.get(),
                self.global_transition_duration.get(),
                self.individual_transitions,
                self.image_durations if self.image_durations else None
            )
            
            self.root.after(0, self._on_generation_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._on_generation_error(str(e)))
            
    def _tick_timer(self) -> None:
        """Update the elapsed time label every second."""
        if not self._generation_timer_running:
            return
        import time
        elapsed = int(time.time() - self._generation_start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_label.config(text=f"⏱ {mins:02d}:{secs:02d}")
        self._timer_after_id = self.root.after(1000, self._tick_timer)
    
    def _stop_timer(self) -> None:
        """Stop the elapsed time ticker."""
        self._generation_timer_running = False
        if hasattr(self, '_timer_after_id'):
            self.root.after_cancel(self._timer_after_id)
    
    def _on_generation_complete(self) -> None:
        """Handle successful video generation."""
        self._stop_timer()
        import time
        elapsed = int(time.time() - self._generation_start_time)
        mins, secs = divmod(elapsed, 60)
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Vídeo gerado com sucesso!")
        self.timer_label.config(text=f"⏱ {mins:02d}:{secs:02d}")
        self.progress_var.set(100)
        messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{self.output_path}")
        
    def _on_generation_error(self, error: str) -> None:
        """Handle video generation error."""
        self._stop_timer()
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Erro na geração")
        self.timer_label.config(text="")
        self.progress_var.set(0)
        messagebox.showerror("Erro", f"Erro ao gerar vídeo:\n{error}")


def run_app() -> None:
    """Run the application."""
    root = tk.Tk()
    app = VideoGeneratorApp(root)
    root.mainloop()
