import os
import requests
from PIL import Image, ImageDraw, ImageFont

WIDTH = 800
HEIGHT = 480

LATITUDE = 22.5726
LONGITUDE = 88.3639
TIMEZONE = "Asia/Kolkata"

API_URL = "https://www.navamsha.in/api/v1/panchang/full"


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Bold.ttf"
        if bold else
        "/usr/share/fonts/opentype/noto/NotoSansDevanagari-Regular.ttf",
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    raise FileNotFoundError("Devanagari font not found")


def get_panchang():
    api_key = os.environ["NAVAMSHA_API_KEY"]

    response = requests.post(
        API_URL,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "date": "2026-09-29",
            "latitude": LATITUDE,
            "longitude": LONGITUDE,
            "timezone": TIMEZONE,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def centered(draw, text, y, fnt):
    box = draw.textbbox((0, 0), text, font=fnt)
    x = (WIDTH - (box[2] - box[0])) // 2
    draw.text((x, y), text, fill=0, font=fnt)


def make_dashboard(data):
    image = Image.new("1", (WIDTH, HEIGHT), 1)
    draw = ImageDraw.Draw(image)

    title_font = font(30, True)
    section_font = font(22, True)
    body_font = font(20)
    small_font = font(17)

    # Outer manuscript-style frame
    draw.rectangle((12, 12, WIDTH - 13, HEIGHT - 13), outline=0, width=2)
    draw.rectangle((20, 20, WIDTH - 21, HEIGHT - 21), outline=0, width=1)

    # Header
    centered(draw, "आज का धर्म", 28, title_font)

    draw.line((45, 72, WIDTH - 45, 72), fill=0, width=2)

    # Decorative corner marks
    for x, y, sx, sy in [
        (32, 32, 1, 1),
        (WIDTH - 32, 32, -1, 1),
        (32, HEIGHT - 32, 1, -1),
        (WIDTH - 32, HEIGHT - 32, -1, -1),
    ]:
        draw.line((x, y, x + 16 * sx, y), fill=0, width=2)
        draw.line((x, y, x, y + 16 * sy), fill=0, width=2)

    # Left devotional panel
    draw.ellipse((55, 105, 205, 255), outline=0, width=2)
    draw.ellipse((65, 115, 195, 245), outline=0, width=1)

    centered_left = 130

    om_font = font(64, True)
    box = draw.textbbox((0, 0), "ॐ", font=om_font)
    draw.text(
        (
            centered_left - (box[2] - box[0]) // 2,
            125,
        ),
        "ॐ",
        fill=0,
        font=om_font,
    )

    box = draw.textbbox((0, 0), "शिव", font=section_font)
    draw.text(
        (centered_left - (box[2] - box[0]) // 2, 195),
        "शिव",
        fill=0,
        font=section_font,
    )

    box = draw.textbbox((0, 0), "ॐ नमः शिवाय", font=small_font)
    draw.text(
        (centered_left - (box[2] - box[0]) // 2, 225),
        "ॐ नमः शिवाय",
        fill=0,
        font=small_font,
    )

    # Panchang heading
    centered(draw, "आज का पंचांग", 270, section_font)

    # Basic Panchang information
    tithi = data.get("tithi", {})
    nakshatra = data.get("nakshatra", {})

    tithi_name = tithi.get("name", "—")
    nakshatra_name = nakshatra.get("name", "—")
    sunrise = data.get("sunrise", "—")
    sunset = data.get("sunset", "—")

    rows = [
        ("तिथि", str(tithi_name)),
        ("नक्षत्र", str(nakshatra_name)),
        ("सूर्योदय", str(sunrise)),
        ("सूर्यास्त", str(sunset)),
    ]

    y = 310

    for label, value in rows:
        draw.text((45, y), label, fill=0, font=small_font)

        box = draw.textbbox((0, 0), value, font=small_font)
        draw.text(
            (330 - (box[2] - box[0]), y),
            value,
            fill=0,
            font=small_font,
        )

        for x in range(165, 310, 7):
            draw.point((x, y + 12), fill=0)

        y += 28

    # Right panel
    divider_x = 390

    draw.line((divider_x, 100, divider_x, 445), fill=0, width=2)

    def header(text, y):
        draw.rounded_rectangle(
            (420, y, 750, y + 34),
            radius=8,
            fill=0,
        )
        box = draw.textbbox((0, 0), text, font=section_font)
        draw.text(
            (
                585 - (box[2] - box[0]) // 2,
                y + 3,
            ),
            text,
            fill=1,
            font=section_font,
        )

    header("आज का श्लोक", 105)

    centered_x = 585

    def centered_right(text, y, fnt):
        box = draw.textbbox((0, 0), text, font=fnt)
        draw.text(
            (centered_x - (box[2] - box[0]) // 2, y),
            text,
            fill=0,
            font=fnt,
        )

    centered_right("कर्मण्येवाधिकारस्ते", 155, body_font)
    centered_right("मा फलेषु कदाचन ।", 182, body_font)

    header("अर्थ", 220)

    centered_right("अपने कर्म पर ध्यान दें;", 266, small_font)
    centered_right("उसके फल की चिंता न करें।", 291, small_font)

    header("आज का संदेश", 325)

    centered_right("धैर्य और निष्ठा से", 370, small_font)
    centered_right("किया गया कर्म भी साधना है।", 395, small_font)

    # Bottom sankalp
    draw.line((45, 445, WIDTH - 45, 445), fill=0, width=2)

    centered(draw, "आज का संकल्प", 450, small_font)

    image.save("dashboard.bin", format="BMP")


def main():
    data = get_panchang()

    # Temporary diagnostic output.
    print("Panchang API response received.")
    print(data)

    make_dashboard(data)


if __name__ == "__main__":
    main()
