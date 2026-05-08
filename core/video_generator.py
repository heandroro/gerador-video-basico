import os
import subprocess
from typing import List, Optional, Callable, Dict, Any
from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip
)
from PIL import Image
from core.transitions import apply_transition, TRANSITION_TYPES, XFADE_TYPE_MAP


class VideoGenerator:
    """Generates MP4 videos from images or video with MP3 audio."""
    
    SUPPORTED_IMAGES = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
    SUPPORTED_VIDEOS = ('.mp4', '.avi', '.mov', '.mkv', '.webm')
    
    def __init__(self, output_path: str, audio_path: str):
        """
        Initialize the video generator.
        
        Args:
            output_path: Path for the output MP4 file
            audio_path: Path to the MP3 audio file
        """
        self.output_path = output_path
        self.audio_path = audio_path
        self.audio_clip: Optional[AudioFileClip] = None
        self.audio_duration: float = 0
        
        # Target resolution for output
        self.target_width = 1920
        self.target_height = 1080
        
        # Temp directory for intermediate files
        import tempfile
        self.temp_dir = tempfile.gettempdir()
        
    def _load_audio(self) -> None:
        """Load the audio file and get its duration."""
        self.audio_clip = AudioFileClip(self.audio_path)
        self.audio_duration = self.audio_clip.duration
        
    def _resize_image_to_fit(self, image_path: str, target_size: tuple = (1920, 1080)) -> str:
        """
        Resize image to fit target size while maintaining aspect ratio.
        Adds black bars if needed.
        
        Args:
            image_path: Path to the image
            target_size: Target resolution (width, height)
            
        Returns:
            Path to the resized image (temporary file)
        """
        img = Image.open(image_path)
        img = img.convert('RGB')
        
        target_w, target_h = target_size
        img_w, img_h = img.size
        
        scale = min(target_w / img_w, target_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        final_img = Image.new('RGB', target_size, (0, 0, 0))
        paste_x = (target_w - new_w) // 2
        paste_y = (target_h - new_h) // 2
        final_img.paste(img_resized, (paste_x, paste_y))
        
        temp_path = image_path + '_resized.jpg'
        final_img.save(temp_path, 'JPEG', quality=95)
        
        return temp_path
    
    def _is_image(self, path: str) -> bool:
        """Check if file is a supported image."""
        return path.lower().endswith(self.SUPPORTED_IMAGES)
    
    def _is_video(self, path: str) -> bool:
        """Check if file is a supported video."""
        return path.lower().endswith(self.SUPPORTED_VIDEOS)
    
    def generate_from_single_image(
        self, 
        image_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Generate video from a single image displayed for the entire audio duration.
        
        Args:
            image_path: Path to the image file
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
        """
        self._load_audio()
        
        if progress_callback:
            progress_callback(0.1)
        
        resized_path = self._resize_image_to_fit(image_path)
        
        try:
            clip = ImageClip(resized_path).set_duration(self.audio_duration)
            clip = clip.set_audio(self.audio_clip)
            
            if progress_callback:
                progress_callback(0.3)
            
            clip.write_videofile(
                self.output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            if progress_callback:
                progress_callback(1.0)
                
        finally:
            if os.path.exists(resized_path):
                os.remove(resized_path)
            if self.audio_clip:
                self.audio_clip.close()
    
    def _generate_with_ffmpeg_xfade(
        self,
        resized_paths: List[str],
        durations: List[float],
        transitions_list: List[tuple],
        progress_callback: Optional[Callable[[float], None]]
    ) -> None:
        """Generate video using FFmpeg xfade filter pipeline (fast path)."""
        n = len(resized_paths)
        cmd = ["ffmpeg", "-y"]
        for i, rpath in enumerate(resized_paths):
            cmd.extend(["-loop", "1", "-t", f"{durations[i]:.4f}", "-i", rpath])
        audio_index = n
        cmd.extend(["-i", self.audio_path])

        if progress_callback:
            progress_callback(0.3)

        # Build filter_complex
        if not transitions_list or n == 1:
            concat_inputs = "".join(f"[{i}:v]" for i in range(n))
            filter_complex = f"{concat_inputs}concat=n={n}:v=1:a=0[vout]"
        else:
            parts = []
            cumulative_offset = 0.0
            current_label = "[0:v]"
            for i, (trans_type, trans_dur) in enumerate(transitions_list):
                trans_dur = min(trans_dur, durations[i] * 0.9, durations[i + 1] * 0.9)
                if trans_type == "none":
                    xfade_name = "fade"
                    trans_dur = 1 / 24.0
                else:
                    xfade_name = XFADE_TYPE_MAP.get(trans_type) or "dissolve"
                cumulative_offset += durations[i] - trans_dur
                is_last = (i == len(transitions_list) - 1)
                next_input = f"[{i + 1}:v]"
                out_label = "[vout]" if is_last else f"[v{i + 1}]"
                parts.append(
                    f"{current_label}{next_input}"
                    f"xfade=transition={xfade_name}"
                    f":duration={trans_dur:.4f}:offset={cumulative_offset:.4f}"
                    f"{out_label}"
                )
                current_label = out_label
            filter_complex = ";".join(parts)

        if progress_callback:
            progress_callback(0.5)

        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[vout]",
            "-map", f"{audio_index}:a",
            "-t", str(self.audio_duration),
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            self.output_path,
        ])

        print(f"[DEBUG] FFmpeg xfade cmd: {' '.join(cmd)}")
        proc = subprocess.run(cmd, capture_output=True, text=True)

        if proc.returncode != 0:
            print(f"[DEBUG] FFmpeg stderr:\n{proc.stderr[-2000:]}")
            raise RuntimeError(f"FFmpeg falhou:\n{proc.stderr[-500:]}")

        if progress_callback:
            progress_callback(1.0)

    def _generate_with_moviepy(
        self,
        resized_paths: List[str],
        durations: List[float],
        transitions_list: List[tuple],
        transition_enabled: bool,
        progress_callback: Optional[Callable[[float], None]]
    ) -> None:
        """Generate video using MoviePy pipeline (fallback for blur transitions)."""
        clips = []
        for i, rpath in enumerate(resized_paths):
            clips.append(ImageClip(rpath).set_duration(durations[i]))
            if progress_callback:
                progress_callback(0.2 + (0.2 * (i + 1) / len(resized_paths)))

        if transition_enabled and len(clips) > 1:
            final_clip = clips[0]
            for i, (trans_type, trans_dur) in enumerate(transitions_list):
                final_clip = apply_transition(final_clip, clips[i + 1], trans_type, trans_dur)
                if progress_callback:
                    progress_callback(0.4 + (0.2 * (i + 1) / len(transitions_list)))
        else:
            final_clip = concatenate_videoclips(clips, method="compose")

        if final_clip.duration > self.audio_duration:
            final_clip = final_clip.subclip(0, self.audio_duration)

        final_clip = final_clip.set_audio(self.audio_clip)

        if progress_callback:
            progress_callback(0.6)

        final_clip.write_videofile(
            self.output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            logger=None
        )

        if progress_callback:
            progress_callback(1.0)

    def generate_from_multiple_images(
        self,
        image_paths: List[str],
        progress_callback: Optional[Callable[[float], None]] = None,
        transition_enabled: bool = False,
        global_transition_type: str = "crossfade",
        global_transition_duration: float = 1.0,
        individual_transitions: Optional[Dict[str, Dict[str, Any]]] = None,
        image_durations: Optional[Dict[int, float]] = None
    ) -> None:
        """
        Generate video from multiple images with custom durations.
        Uses FFmpeg xfade pipeline when possible; falls back to MoviePy for blur.
        """
        self._load_audio()

        if progress_callback:
            progress_callback(0.1)

        num_images = len(image_paths)
        individual_transitions = individual_transitions or {}
        image_durations = image_durations or {}

        durations = [
            image_durations.get(i, self.audio_duration / num_images)
            for i in range(num_images)
        ]

        transitions_list = []
        if transition_enabled and num_images > 1:
            for i in range(num_images - 1):
                path = image_paths[i]
                if path in individual_transitions:
                    t_type = individual_transitions[path].get("type", global_transition_type)
                    t_dur = individual_transitions[path].get("duration", global_transition_duration)
                else:
                    t_type = global_transition_type
                    t_dur = global_transition_duration
                transitions_list.append((t_type, t_dur))

        has_blur = any(t_type == "blur" for t_type, _ in transitions_list)

        print(f"[DEBUG] durations: {durations}")
        print(f"[DEBUG] transitions: {transitions_list}")
        print(f"[DEBUG] audio_duration: {self.audio_duration}")
        print(f"[DEBUG] pipeline: {'moviepy (blur)' if has_blur else 'ffmpeg xfade'}")

        resized_paths = []
        try:
            for img_path in image_paths:
                resized_paths.append(self._resize_image_to_fit(img_path))

            if has_blur:
                self._generate_with_moviepy(
                    resized_paths, durations, transitions_list,
                    transition_enabled, progress_callback
                )
            else:
                self._generate_with_ffmpeg_xfade(
                    resized_paths, durations,
                    transitions_list if transition_enabled else [],
                    progress_callback
                )
        finally:
            for path in resized_paths:
                if os.path.exists(path):
                    os.remove(path)
            if self.audio_clip:
                self.audio_clip.close()
    
    def generate_from_video(
        self,
        video_path: str,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Generate video from existing video file, replacing audio with MP3.
        
        Args:
            video_path: Path to the video file
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
        """
        self._load_audio()
        
        if progress_callback:
            progress_callback(0.1)
        
        video_clip = VideoFileClip(video_path)
        
        try:
            video_clip = video_clip.without_audio()
            
            if video_clip.duration > self.audio_duration:
                video_clip = video_clip.subclip(0, self.audio_duration)
            elif video_clip.duration < self.audio_duration:
                video_clip = video_clip.loop(duration=self.audio_duration)
            
            if progress_callback:
                progress_callback(0.3)
            
            final_clip = video_clip.set_audio(self.audio_clip)
            
            final_clip.write_videofile(
                self.output_path,
                fps=24,
                codec='libx264',
                audio_codec='aac',
                logger=None
            )
            
            if progress_callback:
                progress_callback(1.0)
                
        finally:
            video_clip.close()
            if self.audio_clip:
                self.audio_clip.close()
    
    def generate_from_multiple_media(
        self,
        media_paths: List[str],
        progress_callback: Optional[Callable[[float], None]] = None,
        transition_enabled: bool = False,
        global_transition_type: str = "crossfade",
        global_transition_duration: float = 1.0,
        individual_transitions: Optional[Dict[str, Dict[str, Any]]] = None,
        image_durations: Optional[Dict[int, float]] = None
    ) -> None:
        """
        Generate video from multiple media files (images and/or videos).
        
        Args:
            media_paths: List of paths to media files (images or videos)
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
            transition_enabled: Whether to apply transitions between clips
            global_transition_type: Default transition type
            global_transition_duration: Default transition duration in seconds
            individual_transitions: Dict mapping image paths to custom transition settings
            image_durations: Dict mapping image indices to display duration in seconds
        """
        self._load_audio()
        
        if progress_callback:
            progress_callback(0.1)
        
        num_media = len(media_paths)
        individual_transitions = individual_transitions or {}
        image_durations = image_durations or {}
        
        print(f"[DEBUG] generate_from_multiple_media: {num_media} items")
        print(f"[DEBUG] image_durations: {image_durations}")
        
        clips = []
        resized_paths = []
        durations = []
        
        try:
            for i, path in enumerate(media_paths):
                if self._is_image(path):
                    # Handle image: resize and create ImageClip
                    resized_path = self._resize_image_to_fit(path)
                    resized_paths.append(resized_path)
                    
                    if image_durations and i in image_durations:
                        duration = image_durations[i]
                        print(f"[DEBUG] Imagem {i}: duração personalizada {duration}s")
                    else:
                        duration = self.audio_duration / num_media
                        print(f"[DEBUG] Imagem {i}: duração calculada {duration}s")
                    
                    durations.append(duration)
                    clip = ImageClip(resized_path).set_duration(duration)
                    clips.append(clip)
                    
                elif self._is_video(path):
                    # Handle video: extract clip and resize if needed
                    print(f"[DEBUG] Vídeo {i}: processando {path}")
                    
                    # Get video duration
                    try:
                        with VideoFileClip(path) as video:
                            video_duration = video.duration
                            if image_durations and i in image_durations:
                                target_duration = image_durations[i]
                            else:
                                target_duration = video_duration
                    except Exception as e:
                        print(f"[WARN] Não foi possível obter duração do vídeo: {e}")
                        target_duration = self.audio_duration / num_media
                    
                    # Load video and resize to target resolution
                    video_clip = VideoFileClip(path)
                    # Use manual resize approach to avoid PIL ANTIALIAS issue
                    from moviepy.video.fx.resize import resize
                    try:
                        video_clip = resize(video_clip, newsize=(self.target_width, self.target_height))
                    except AttributeError:
                        # Fallback: resize using alternative method
                        from PIL import Image
                        import numpy as np
                        
                        def resize_frame(frame):
                            img = Image.fromarray(frame)
                            # Use Resampling.LANCZOS for newer Pillow, fallback to BILINEAR
                            try:
                                resample = Image.Resampling.LANCZOS
                            except AttributeError:
                                resample = Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.BILINEAR
                            img_resized = img.resize((self.target_width, self.target_height), resample)
                            return np.array(img_resized)
                        
                        video_clip = video_clip.fl_image(resize_frame)
                    
                    if target_duration < video_clip.duration:
                        video_clip = video_clip.subclip(0, target_duration)
                    else:
                        video_clip = video_clip.set_duration(target_duration)
                    
                    # Don't add to resized_paths (video clip object handles its own file)
                    durations.append(target_duration)
                    clips.append(video_clip)
                    
                else:
                    raise ValueError(f"Unsupported file format: {path}")
                
                if progress_callback:
                    progress_callback(0.1 + (0.2 * (i + 1) / num_media))
            
            if progress_callback:
                progress_callback(0.3)
            
            # Build transitions list
            transitions_list = []
            for i in range(len(clips) - 1):
                path = media_paths[i]
                trans = individual_transitions.get(path, {})
                trans_type = trans.get("type", global_transition_type)
                trans_dur = trans.get("duration", global_transition_duration)
                transitions_list.append((trans_type, trans_dur))
            
            print(f"[DEBUG] Transições: {transitions_list}")
            
            # Use MoviePy for all cases (including videos)
            self._generate_with_moviepy_clips(
                clips, durations, transitions_list, transition_enabled, progress_callback
            )
            
        finally:
            for clip in clips:
                try:
                    clip.close()
                except:
                    pass
            # Only remove temporary resized image files (those ending with _resized.jpg)
            for rpath in resized_paths:
                if rpath and os.path.exists(rpath) and rpath.endswith('_resized.jpg'):
                    try:
                        os.remove(rpath)
                    except:
                        pass
            if self.audio_clip:
                self.audio_clip.close()
    
    def _generate_with_moviepy_clips(
        self,
        clips: List[Any],
        durations: List[float],
        transitions_list: List[tuple],
        transition_enabled: bool,
        progress_callback: Optional[Callable[[float], None]]
    ) -> None:
        """Generate video from pre-loaded clips using MoviePy."""
        if not clips:
            raise ValueError("No clips provided")
        
        num_clips = len(clips)
        
        if progress_callback:
            progress_callback(0.4)
        
        if not transition_enabled or num_clips == 1:
            final_clip = concatenate_videoclips(clips, method="compose")
        else:
            # Apply transitions
            processed_clips = []
            for i, clip in enumerate(clips):
                if i < len(transitions_list):
                    trans_type, trans_dur = transitions_list[i]
                    if trans_type == "none":
                        trans_dur = 0
                    trans_dur = min(trans_dur, durations[i] * 0.9, durations[i + 1] * 0.9 if i + 1 < len(durations) else trans_dur)
                    
                    if trans_dur > 0 and trans_type != "none":
                        clip = clip.set_duration(durations[i] - trans_dur / 2)
                    else:
                        clip = clip.set_duration(durations[i])
                processed_clips.append(clip)
            
            final_clip = concatenate_videoclips(processed_clips, method="compose")
        
        if progress_callback:
            progress_callback(0.6)
        
        # Add audio
        if self.audio_clip:
            final_clip = final_clip.set_audio(self.audio_clip.subclip(0, min(final_clip.duration, self.audio_duration)))
        
        if progress_callback:
            progress_callback(0.7)
        
        # Write output
        final_clip.write_videofile(
            self.output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=os.path.join(self.temp_dir, 'temp-audio.m4a'),
            remove_temp=True,
            logger=None
        )
        
        final_clip.close()
        
        if progress_callback:
            progress_callback(1.0)
    
    def generate(
        self,
        media_paths: List[str],
        progress_callback: Optional[Callable[[float], None]] = None,
        transition_enabled: bool = False,
        global_transition_type: str = "crossfade",
        global_transition_duration: float = 1.0,
        individual_transitions: Optional[Dict[str, Dict[str, Any]]] = None,
        image_durations: Optional[Dict[int, float]] = None
    ) -> None:
        """
        Generate video based on the type and number of media files.
        
        Args:
            media_paths: List of paths to media files (images or video)
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
            transition_enabled: Whether to apply transitions between images
            global_transition_type: Default transition type for all images
            global_transition_duration: Default transition duration in seconds
            individual_transitions: Dict mapping image paths to custom transition settings
            image_durations: Dict mapping image indices to display duration in seconds
        """
        if not media_paths:
            raise ValueError("No media files provided")
        
        if len(media_paths) == 1:
            path = media_paths[0]
            if self._is_video(path):
                self.generate_from_video(path, progress_callback)
            elif self._is_image(path):
                self.generate_from_single_image(path, progress_callback)
            else:
                raise ValueError(f"Unsupported file format: {path}")
        else:
            self.generate_from_multiple_media(
                media_paths,
                progress_callback,
                transition_enabled,
                global_transition_type,
                global_transition_duration,
                individual_transitions,
                image_durations
            )
