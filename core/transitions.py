"""
Transition effects for video generation.
Simplified and working implementation.
"""

import numpy as np
from moviepy.editor import (
    VideoClip,
    ImageClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips
)
from PIL import Image, ImageFilter


TRANSITION_TYPES = [
    "none",
    "fade",
    "crossfade",
    "slide_left",
    "slide_right",
    "slide_up",
    "slide_down",
    "wipe_left",
    "wipe_right",
    "wipe_up",
    "wipe_down",
    "blur"
]

TRANSITION_LABELS = {
    "none": "Nenhum (Corte)",
    "fade": "Fade (Escurecer)",
    "crossfade": "Crossfade (Dissolve)",
    "slide_left": "Slide Esquerda",
    "slide_right": "Slide Direita",
    "slide_up": "Slide Cima",
    "slide_down": "Slide Baixo",
    "wipe_left": "Wipe Esquerda",
    "wipe_right": "Wipe Direita",
    "wipe_up": "Wipe Cima",
    "wipe_down": "Wipe Baixo",
    "blur": "Blur (Desfoque)"
}


def create_crossfade_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    duration: float
) -> CompositeVideoClip:
    """Create a crossfade (dissolve) transition between two clips."""
    clip1_with_fade = clip1.crossfadeout(duration)
    clip2_with_fade = clip2.crossfadein(duration).set_start(clip1.duration - duration)
    
    total_duration = clip1.duration + clip2.duration - duration
    return CompositeVideoClip([clip1_with_fade, clip2_with_fade]).set_duration(total_duration)


def create_fade_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    duration: float
) -> CompositeVideoClip:
    """Create a fade to black transition between two clips."""
    half = duration / 2
    
    clip1_faded = clip1.crossfadeout(half)
    
    black = ColorClip(size=clip1.size, color=(0, 0, 0), duration=duration)
    black = black.set_start(clip1.duration - half)
    
    clip2_faded = clip2.crossfadein(half).set_start(clip1.duration)
    
    total_duration = clip1.duration + clip2.duration
    return CompositeVideoClip([clip1_faded, black, clip2_faded]).set_duration(total_duration)


def create_slide_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    duration: float,
    direction: str = "left"
) -> VideoClip:
    """Create a slide transition between two clips."""
    w, h = clip1.size
    fps = 24
    
    frame1 = clip1.get_frame(0)
    frame2 = clip2.get_frame(0)
    
    def make_transition_frame(t):
        progress = min(1.0, t / duration)
        
        if direction == "left":
            offset = int(w * progress)
            result = np.zeros_like(frame1)
            if offset < w:
                result[:, :w-offset] = frame1[:, offset:]
            if offset > 0:
                result[:, w-offset:] = frame2[:, :offset]
        elif direction == "right":
            offset = int(w * progress)
            result = np.zeros_like(frame1)
            if offset < w:
                result[:, offset:] = frame1[:, :w-offset]
            if offset > 0:
                result[:, :offset] = frame2[:, w-offset:]
        elif direction == "up":
            offset = int(h * progress)
            result = np.zeros_like(frame1)
            if offset < h:
                result[:h-offset, :] = frame1[offset:, :]
            if offset > 0:
                result[h-offset:, :] = frame2[:offset, :]
        elif direction == "down":
            offset = int(h * progress)
            result = np.zeros_like(frame1)
            if offset < h:
                result[offset:, :] = frame1[:h-offset, :]
            if offset > 0:
                result[:offset, :] = frame2[h-offset:, :]
        else:
            result = frame1
        
        return result
    
    transition_clip = VideoClip(make_transition_frame, duration=duration).set_fps(fps)
    
    pre = clip1.subclip(0, max(0, clip1.duration - duration)) if clip1.duration > duration else None
    post = clip2.subclip(min(duration, clip2.duration)) if clip2.duration > duration else None
    
    clips = []
    if pre is not None and pre.duration > 0:
        clips.append(pre)
    clips.append(transition_clip)
    if post is not None and post.duration > 0:
        clips.append(post)
    
    if len(clips) == 1:
        return clips[0]
    return concatenate_videoclips(clips, method="compose")


def create_wipe_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    duration: float,
    direction: str = "left"
) -> VideoClip:
    """Create a wipe transition between two clips."""
    w, h = clip1.size
    fps = 24
    
    frame1 = clip1.get_frame(0)
    frame2 = clip2.get_frame(0)
    
    def make_transition_frame(t):
        progress = min(1.0, t / duration)
        result = frame1.copy()
        
        if direction == "left":
            split = int(w * progress)
            if split > 0:
                result[:, :split] = frame2[:, :split]
        elif direction == "right":
            split = int(w * (1 - progress))
            if split < w:
                result[:, split:] = frame2[:, split:]
        elif direction == "up":
            split = int(h * progress)
            if split > 0:
                result[:split, :] = frame2[:split, :]
        elif direction == "down":
            split = int(h * (1 - progress))
            if split < h:
                result[split:, :] = frame2[split:, :]
        
        return result
    
    transition_clip = VideoClip(make_transition_frame, duration=duration).set_fps(fps)
    
    pre = clip1.subclip(0, max(0, clip1.duration - duration)) if clip1.duration > duration else None
    post = clip2.subclip(min(duration, clip2.duration)) if clip2.duration > duration else None
    
    clips = []
    if pre is not None and pre.duration > 0:
        clips.append(pre)
    clips.append(transition_clip)
    if post is not None and post.duration > 0:
        clips.append(post)
    
    if len(clips) == 1:
        return clips[0]
    return concatenate_videoclips(clips, method="compose")


def create_blur_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    duration: float
) -> VideoClip:
    """Create a blur transition between two clips."""
    w, h = clip1.size
    fps = 24
    
    frame1 = clip1.get_frame(0)
    frame2 = clip2.get_frame(0)
    
    img1_pil = Image.fromarray(frame1)
    img2_pil = Image.fromarray(frame2)
    
    def make_transition_frame(t):
        progress = min(1.0, t / duration)
        
        blur_radius = int(15 * (1 - abs(progress - 0.5) * 2))
        blur_radius = max(0, blur_radius)
        
        if progress < 0.5:
            if blur_radius > 0:
                blurred = img1_pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            else:
                blurred = img1_pil
        else:
            if blur_radius > 0:
                blurred = img2_pil.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            else:
                blurred = img2_pil
        
        return np.array(blurred)
    
    transition_clip = VideoClip(make_transition_frame, duration=duration).set_fps(fps)
    
    pre = clip1.subclip(0, max(0, clip1.duration - duration)) if clip1.duration > duration else None
    post = clip2.subclip(min(duration, clip2.duration)) if clip2.duration > duration else None
    
    clips = []
    if pre is not None and pre.duration > 0:
        clips.append(pre)
    clips.append(transition_clip)
    if post is not None and post.duration > 0:
        clips.append(post)
    
    if len(clips) == 1:
        return clips[0]
    return concatenate_videoclips(clips, method="compose")


def apply_transition(
    clip1: ImageClip,
    clip2: ImageClip,
    transition_type: str,
    duration: float
) -> VideoClip:
    """
    Apply a transition between two clips.
    
    Args:
        clip1: First clip
        clip2: Second clip
        transition_type: Type of transition from TRANSITION_TYPES
        duration: Transition duration in seconds
        
    Returns:
        Combined clip with transition applied
    """
    duration = min(duration, clip1.duration * 0.9, clip2.duration * 0.9)
    
    if transition_type == "none":
        return concatenate_videoclips([clip1, clip2], method="compose")
    
    elif transition_type == "fade":
        return create_fade_transition(clip1, clip2, duration)
    
    elif transition_type == "crossfade":
        return create_crossfade_transition(clip1, clip2, duration)
    
    elif transition_type.startswith("slide_"):
        direction = transition_type.replace("slide_", "")
        return create_slide_transition(clip1, clip2, duration, direction)
    
    elif transition_type.startswith("wipe_"):
        direction = transition_type.replace("wipe_", "")
        return create_wipe_transition(clip1, clip2, duration, direction)
    
    elif transition_type == "blur":
        return create_blur_transition(clip1, clip2, duration)
    
    else:
        return concatenate_videoclips([clip1, clip2], method="compose")
