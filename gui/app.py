import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Optional
import os
import threading
from PIL import Image, ImageTk


class VideoGeneratorApp:
    """Main GUI application for the video generator."""
    
    SUPPORTED_IMAGES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
    SUPPORTED_VIDEOS = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Gerador de Vídeo")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        self.media_paths: List[str] = []
        self.audio_path: Optional[str] = None
        self.output_path: Optional[str] = None
        self.thumbnail_refs: List[ImageTk.PhotoImage] = []
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        media_frame = ttk.LabelFrame(main_frame, text="Mídia (Imagens ou Vídeo)", padding="5")
        media_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        media_btn_frame = ttk.Frame(media_frame)
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
        
        list_frame = ttk.Frame(media_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.media_listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=8)
        self.media_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.media_listbox.bind('<<ListboxSelect>>', self._on_select)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.media_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.media_listbox.config(yscrollcommand=scrollbar.set)
        
        preview_frame = ttk.LabelFrame(main_frame, text="Pré-visualização", padding="5")
        preview_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Selecione uma mídia para visualizar")
        self.preview_label.pack(pady=10)
        
        audio_frame = ttk.LabelFrame(main_frame, text="Áudio MP3", padding="5")
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        audio_inner = ttk.Frame(audio_frame)
        audio_inner.pack(fill=tk.X)
        
        ttk.Button(
            audio_inner,
            text="Selecionar MP3",
            command=self._select_audio
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.audio_label = ttk.Label(audio_inner, text="Nenhum arquivo selecionado")
        self.audio_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        output_frame = ttk.LabelFrame(main_frame, text="Arquivo de Saída", padding="5")
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        output_inner = ttk.Frame(output_frame)
        output_inner.pack(fill=tk.X)
        
        ttk.Button(
            output_inner,
            text="Escolher Local",
            command=self._select_output
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.output_label = ttk.Label(output_inner, text="Nenhum local selecionado")
        self.output_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        self.status_label = ttk.Label(progress_frame, text="")
        self.status_label.pack(pady=(5, 0))
        
        self.generate_btn = ttk.Button(
            main_frame,
            text="Gerar Vídeo",
            command=self._generate_video
        )
        self.generate_btn.pack(pady=10)
        
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
                    self.media_paths.append(path)
                    self.media_listbox.insert(tk.END, os.path.basename(path))
                    
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
            
    def _remove_selected(self) -> None:
        """Remove the selected item from the media list."""
        selection = self.media_listbox.curselection()
        if selection:
            index = selection[0]
            self.media_listbox.delete(index)
            del self.media_paths[index]
            self._clear_preview()
            
    def _clear_media(self) -> None:
        """Clear all media from the list."""
        self.media_listbox.delete(0, tk.END)
        self.media_paths.clear()
        self._clear_preview()
        
    def _move_up(self) -> None:
        """Move selected item up in the list."""
        selection = self.media_listbox.curselection()
        if selection and selection[0] > 0:
            index = selection[0]
            self.media_paths[index], self.media_paths[index-1] = \
                self.media_paths[index-1], self.media_paths[index]
            
            item = self.media_listbox.get(index)
            self.media_listbox.delete(index)
            self.media_listbox.insert(index-1, item)
            self.media_listbox.selection_set(index-1)
            
    def _move_down(self) -> None:
        """Move selected item down in the list."""
        selection = self.media_listbox.curselection()
        if selection and selection[0] < len(self.media_paths) - 1:
            index = selection[0]
            self.media_paths[index], self.media_paths[index+1] = \
                self.media_paths[index+1], self.media_paths[index]
            
            item = self.media_listbox.get(index)
            self.media_listbox.delete(index)
            self.media_listbox.insert(index+1, item)
            self.media_listbox.selection_set(index+1)
            
    def _on_select(self, event) -> None:
        """Handle selection change in the media list."""
        selection = self.media_listbox.curselection()
        if selection:
            index = selection[0]
            path = self.media_paths[index]
            self._show_preview(path)
            
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
        
        thread = threading.Thread(target=self._generate_video_thread)
        thread.daemon = True
        thread.start()
        
    def _generate_video_thread(self) -> None:
        """Video generation thread."""
        try:
            from core.video_generator import VideoGenerator
            
            generator = VideoGenerator(self.output_path, self.audio_path)
            generator.generate(self.media_paths, self._update_progress)
            
            self.root.after(0, self._on_generation_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._on_generation_error(str(e)))
            
    def _on_generation_complete(self) -> None:
        """Handle successful video generation."""
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Vídeo gerado com sucesso!")
        self.progress_var.set(100)
        messagebox.showinfo("Sucesso", f"Vídeo salvo em:\n{self.output_path}")
        
    def _on_generation_error(self, error: str) -> None:
        """Handle video generation error."""
        self.generate_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Erro na geração")
        self.progress_var.set(0)
        messagebox.showerror("Erro", f"Erro ao gerar vídeo:\n{error}")


def run_app() -> None:
    """Run the application."""
    root = tk.Tk()
    app = VideoGeneratorApp(root)
    root.mainloop()
