import os
from typing import List, Optional, Callable
from moviepy.editor import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    CompositeVideoClip
)
from PIL import Image


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
    
    def generate_from_multiple_images(
        self,
        image_paths: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Generate video from multiple images distributed equally over audio duration.
        
        Args:
            image_paths: List of paths to image files
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
        """
        self._load_audio()
        
        if progress_callback:
            progress_callback(0.1)
        
        num_images = len(image_paths)
        duration_per_image = self.audio_duration / num_images
        
        clips = []
        resized_paths = []
        
        try:
            for i, img_path in enumerate(image_paths):
                resized_path = self._resize_image_to_fit(img_path)
                resized_paths.append(resized_path)
                
                clip = ImageClip(resized_path).set_duration(duration_per_image)
                clips.append(clip)
                
                if progress_callback:
                    progress_callback(0.1 + (0.3 * (i + 1) / num_images))
            
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip = final_clip.set_audio(self.audio_clip)
            
            if progress_callback:
                progress_callback(0.5)
            
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
    
    def generate(
        self,
        media_paths: List[str],
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> None:
        """
        Generate video based on the type and number of media files.
        
        Args:
            media_paths: List of paths to media files (images or video)
            progress_callback: Optional callback for progress updates (0.0 to 1.0)
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
            for path in media_paths:
                if not self._is_image(path):
                    raise ValueError(f"Multiple files mode only supports images: {path}")
            self.generate_from_multiple_images(media_paths, progress_callback)
