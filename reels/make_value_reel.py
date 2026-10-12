"""Render a 9:16 text reel (1080x1920, 30fps) about value over effort.

Usage: python3 reels/make_value_reel.py  -> reels/value-over-effort.mp4
"""
import os
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG = (14, 14, 16)
FG = (245, 245, 240)
MUTED = (160, 160, 165)
ACCENT = (110, 220, 95)
FONT_DIR = "/usr/share/fonts/opentype/inter"
BOLD = os.path.join(FONT_DIR, "Inter-Bold.otf")
REG = os.path.join(FONT_DIR, "Inter-Regular.otf")

# (kind, number, headline, subline, seconds)
SLIDES = [
    ("hook", None, "Working hard\nisn't enough.", "5 rules that actually\nmove the needle", 3.0),
    ("point", "01", "Value > effort", "Nobody pays for your hours.\nThey pay for what you deliver.", 4.5),
    ("point", "02", "Solve real\nproblems", "Find what people care about —\nand would pay to fix.", 4.5),
    ("point", "03", "Build valuable\nskills", "Get better at the things\nthat make you more useful.", 4.5),
    ("point", "04", "Measure\nresults", "Track outcomes,\nnot time spent.", 4.5),
    ("point", "05", "Use leverage", "Multiply your output with\ntech, systems & people.", 4.5),
    ("cta", None, "Which one are\nyou working on?", "Follow for more", 3.0),
]
TOTAL = sum(s[4] for s in SLIDES)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def text_block(draw, text, font, x, y, fill, spacing):
    draw.multiline_text((x, y), text, font=font, fill=fill, spacing=spacing)
    box = draw.multiline_textbbox((x, y), text, font=font, spacing=spacing)
    return box[3]


def render(slide, local_t, global_t):
    kind, num, head, sub, dur = slide
    img = Image.new("RGB", (W, H), BG)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Progress bar along the top.
    ImageDraw.Draw(img).rectangle([0, 0, int(W * global_t / TOTAL), 12], fill=ACCENT)

    x = 100
    out = 1 - ease_out((local_t - (dur - 0.25)) / 0.25)  # quick fade at slide end

    def anim(delay):
        p = ease_out((local_t - delay) / 0.45)
        return int(255 * p * out), int(60 * (1 - p))

    y = 620 if kind == "point" else 700
    if num:
        a, dy = anim(0.0)
        d.text((x, y - 230 + dy), num, font=ImageFont.truetype(BOLD, 190), fill=ACCENT + (a,))
    a, dy = anim(0.12 if num else 0.0)
    head_font = ImageFont.truetype(BOLD, 120 if kind != "cta" else 104)
    bottom = text_block(d, head, head_font, x, y + dy, FG + (a,), 18)
    d.rectangle([x, bottom + 50 + dy, x + 140, bottom + 60 + dy], fill=ACCENT + (a,))
    a, dy = anim(0.35)
    sub_font = ImageFont.truetype(REG if kind != "cta" else BOLD, 56)
    text_block(d, sub, sub_font, x, bottom + 110 + dy,
               (ACCENT if kind == "cta" else MUTED) + (a,), 20)

    img.paste(layer, (0, 0), layer)
    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(here, "value-over-effort.mp4")
    with tempfile.TemporaryDirectory() as tmp:
        frame, start = 0, 0.0
        for slide in SLIDES:
            for i in range(int(round(slide[4] * FPS))):
                render(slide, i / FPS, start + i / FPS).save(os.path.join(tmp, f"{frame:05d}.png"))
                frame += 1
            start += slide[4]
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
            "-i", os.path.join(tmp, "%05d.png"),
            "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-shortest",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium",
            "-c:a", "aac", "-movflags", "+faststart", out_path,
        ], check=True)
    print(out_path)


if __name__ == "__main__":
    main()
