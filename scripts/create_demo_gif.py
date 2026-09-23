"""Generate a short animated preview of the daily digest experience."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


WIDTH = 800
HEIGHT = 450
FRAME_COUNT = 24
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assets" / "digest-demo.gif"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a readable Windows font with a bundled-font fallback."""
    candidates = (
        [r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"]
        if bold
        else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"]
    )
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_frame(frame_number: int) -> Image.Image:
    """Render one animation frame for the digest preview."""
    image = Image.new("RGB", (WIDTH, HEIGHT), "#f4f1ea")
    draw = ImageDraw.Draw(image)
    title_font = load_font(34, bold=True)
    body_font = load_font(17)
    small_font = load_font(13)

    draw.rectangle((0, 0, WIDTH, 14), fill="#d66b4d")
    draw.text((54, 42), "SECOND BRAIN", font=small_font, fill="#d66b4d")
    draw.text((54, 68), "Daily Digest", font=title_font, fill="#252a2e")
    draw.text((54, 116), "Your reading queue, distilled.", font=body_font, fill="#687077")
    draw.line((54, 155, WIDTH - 54, 155), fill="#d9d3ca", width=2)

    cards = [
        ("Hacker News", "The tools changing how we think", "A concise view of today's most useful ideas."),
        ("TechCrunch", "A calmer way to follow technology", "Key context, without the endless scroll."),
        ("MachineLearning", "Small models are getting remarkably capable", "The signal worth carrying into tomorrow."),
    ]
    visible_cards = min(3, max(0, (frame_number - 3) // 5 + 1))
    for index, (source, headline, summary) in enumerate(cards[:visible_cards]):
        top = 180 + index * 73
        progress = min(1.0, max(0.0, (frame_number - (3 + index * 5)) / 4))
        left = int(54 + (1 - progress) * 28)
        draw.rounded_rectangle((left, top, WIDTH - 54, top + 57), radius=8, fill="#fffdf9", outline="#ded8cf", width=1)
        draw.rectangle((left, top, left + 5, top + 57), fill="#d66b4d")
        draw.text((left + 18, top + 9), source.upper(), font=small_font, fill="#d66b4d")
        draw.text((left + 18, top + 27), headline, font=body_font, fill="#252a2e")
        draw.text((left + 438, top + 29), summary[:31], font=small_font, fill="#687077")

    if frame_number >= 19:
        draw.rounded_rectangle((54, 393, WIDTH - 54, 421), radius=14, fill="#252a2e")
        draw.text((WIDTH // 2 - 113, 400), "3 stories ready to read", font=small_font, fill="#f4f1ea")
    return image


def main() -> None:
    """Render and save the animated GIF preview."""
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    frames = [draw_frame(number) for number in range(FRAME_COUNT)]
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=120,
        loop=0,
        optimize=False,
    )
    print(f"Saved GIF to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()