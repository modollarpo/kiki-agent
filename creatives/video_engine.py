import os
from pathlib import Path
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip, TextClip
from moviepy.video.fx.all import resize
from PIL import Image

class SyncCreateVideo:
    def __init__(self, bg_image_path, product, logo_path=None, font_path=None):
        self.bg_image_path = Path(bg_image_path)
        self.product = product
        self.logo_path = Path(logo_path) if logo_path else Path('assets/logo.png')
        self.font_path = font_path or 'assets/fonts/Inter-Bold.ttf'
        self.kiki_green = '#00ff88'
        self.duration = 5
        self.resolution = (1080, 1920)  # 9:16 vertical

    def make_video(self, output_path):
        # Background with subtle zoom-in
        bg_clip = ImageClip(str(self.bg_image_path)).set_duration(self.duration)
        bg_clip = bg_clip.resize(newsize=self.resolution)
        bg_clip = bg_clip.fx(resize, lambda t: 1 + 0.03 * t)  # 3% zoom over 5s

        # Brand logo (top-right)
        logo = Image.open(self.logo_path)
        logo_w = int(self.resolution[0] * 0.18)
        logo_h = int(logo_w * logo.height / logo.width)
        logo = logo.resize((logo_w, logo_h))
        logo_path_tmp = 'assets/_logo_tmp.png'
        logo.save(logo_path_tmp)
        logo_clip = (ImageClip(logo_path_tmp)
                     .set_duration(self.duration)
                     .set_position((self.resolution[0] - logo_w - 40, 40)))

        # High-contrast hook text (center)
        hook = self.product.get('hook', 'Your Next Best Seller')
        text_clip = (TextClip(hook, fontsize=110, font=self.font_path, color=self.kiki_green, method='label')
                     .set_position('center')
                     .set_duration(self.duration)
                     .margin(top=0, opacity=0))

        # SyncShield™: Safe zone check for text overlay
        # TikTok safe zone: avoid bottom 300px and right 200px for overlays
        # (approximate, can be tuned)
        text_box = text_clip.size
        text_x, text_y = (self.resolution[0] - text_box[0]) // 2, (self.resolution[1] - text_box[1]) // 2
        safe_top = 100
        safe_bottom = self.resolution[1] - 300
        safe_left = 40
        safe_right = self.resolution[0] - 200
        if not (safe_left < text_x < safe_right and safe_top < text_y < safe_bottom):
            raise ValueError("SyncShield™: Text overlay is outside TikTok safe zone.")

        # Compose layers
        video = CompositeVideoClip([bg_clip, logo_clip, text_clip], size=self.resolution)
        video = video.set_duration(self.duration)
        video.write_videofile(output_path, fps=30, codec='libx264', audio=False)
        if os.path.exists(logo_path_tmp):
            os.remove(logo_path_tmp)
        # SyncShield™ file size guardrail
        max_size_mb = 10
        file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise ValueError(f"SyncShield™: Output file exceeds {max_size_mb}MB (actual: {file_size_mb:.2f}MB)")
        print(f"✓ Video exported: {output_path} ({file_size_mb:.2f}MB)")
