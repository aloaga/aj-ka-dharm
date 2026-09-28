import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zoneinfo import ZoneInfo

WIDTH = 800
HEIGHT = 480

LATITUDE = 22.5726
LONGITUDE = 88.3639
TIMEZONE = 5.5
TIMEZONE_NAME = "Asia/Kolkata"

API_URL = "https://api.navamsha.in/api/v1/panchang/full"


def get_font(size, bold=False):
    if bold:
        path = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
    else:
        path = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"

    if not os.path.exists(path):
        raise FileNotFoundError(f"Font not found: {path}")

    return ImageFont.truetype(path, size)


def get_panchang():
    api_key = os.environ["NAVAMSHA_API_KEY"]

    now = datetime.now(ZoneInfo(TIMEZONE_NAME))

    payload = {
        "year": now.year,
        "month": now.month,
        "date": now.day,
        "hours": now.hour,
        "minutes": now.minute,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE,
    }

    response = requests.post(
        API_URL,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("statusCode") != 200:
        raise RuntimeError(f"Navamsha API error: {result}")

    return result["output"]


def text_width(draw, text, font):
    box = draw.textbbox((0, 0), text, font=font)
    return box[2] - box[0]


def centered(draw, text, y, font, center_x=400):
    width = text_width(draw, text, font)
    draw.text(
        (center_x - width // 2, y),
        text,
        fill=0,
        font=font,
    )


def make_dashboard(data):
    image = Image.new("1", (WIDTH, HEIGHT), 1)
    draw = ImageDraw.Draw(image)

    title_font = get_font(28, True)
    section_font = get_font(20, True)
    body_font = get_font(18)
    body_bold = get_font(18, True)
    small_font = get_font(16)

    # Outer frame
    draw.rectangle(
        (12, 12, WIDTH - 13, HEIGHT - 13),
        outline=0,
        width=2,
    )

    draw.rectangle(
        (20, 20, WIDTH - 21, HEIGHT - 21),
        outline=0,
        width=1,
    )

    # Decorative corner flourishes
    corners = [
        (30, 30, 1, 1),
        (WIDTH - 30, 30, -1, 1),
        (30, HEIGHT - 30, 1, -1),
        (WIDTH - 30, HEIGHT - 30, -1, -1),
    ]

    for x, y, sx, sy in corners:
        draw.line(
            (x, y, x + 18 * sx, y),
            fill=0,
            width=2,
        )
        draw.line(
            (x, y, x, y + 18 * sy),
            fill=0,
            width=2,
        )

    # Header
    centered(draw, "आज का धर्म", 28, title_font)

    draw.line(
        (45, 70, WIDTH - 45, 70),
        fill=0,
        width=2,
    )

    # Left devotional mandala
    cx = 125
    cy = 145

    draw.ellipse(
        (cx - 65, cy - 65, cx + 65, cy + 65),
        outline=0,
        width=2,
    )

    draw.ellipse(
        (cx - 55, cy - 55, cx + 55, cy + 55),
        outline=0,
        width=1,
    )

    # Mandala dots
    for dx, dy in [
        (0, -48),
        (34, -34),
        (48, 0),
        (34, 34),
        (0, 48),
        (-34, 34),
        (-48, 0),
        (-34, -34),
    ]:
        draw.ellipse(
            (cx + dx - 2, cy + dy - 2,
             cx + dx + 2, cy + dy + 2),
            fill=0,
        )

    om_font = get_font(58, True)

    om_width = text_width(draw, "ॐ", om_font)

    draw.text(
        (cx - om_width // 2, 105),
        "ॐ",
        fill=0,
        font=om_font,
    )

    centered(draw, "शिव", 174, body_bold, cx)
    centered(draw, "ॐ नमः शिवाय", 202, small_font, cx)

    # Panchang heading
    centered(draw, "आज का पंचांग", 245, section_font, cx)

    tithi = data.get("tithi", {})
    nakshatra = data.get("nakshatra", {})
    weekday = data.get("weekday", {})

    tithi_name = tithi.get("name", "—")
    paksha = tithi.get("paksha", "")

    if paksha:
        tithi_display = f"{paksha} — {tithi_name}"
    else:
        tithi_display = tithi_name

    nakshatra_display = nakshatra.get("name", "—")

    rows = [
        ("वार", weekday.get("name", "—")),
        ("तिथि", tithi_display),
        ("नक्षत्र", nakshatra_display),
    ]

    y = 285

    for label, value in rows:
        draw.text(
            (45, y),
            label,
            fill=0,
            font=small_font,
        )

        value_width = text_width(draw, value, small_font)

        draw.text(
            (335 - value_width, y),
            value,
            fill=0,
            font=small_font,
        )

        for x in range(125, 315, 8):
            draw.point((x, y + 10), fill=0)

        y += 28

    # Divider
    divider_x = 390

    draw.line(
        (divider_x, 95, divider_x, 425),
        fill=0,
        width=2,
    )

    # Small lotus/diya style center marker
    draw.polygon(
        [
            (divider_x, 255),
            (divider_x - 7, 263),
            (divider_x, 271),
            (divider_x + 7, 263),
        ],
        outline=0,
    )

    # Right section helper
    right_center = 585

    def right_header(text, y):
        left = 425
        right = 745
        height = 32

        draw.rounded_rectangle(
            (left, y, right, y + height),
            radius=7,
            fill=0,
        )

        width = text_width(draw, text, section_font)

        draw.text(
            (
                right_center - width // 2,
                y + 3,
            ),
            text,
            fill=1,
            font=section_font,
        )

    def right_centered(text, y, font):
        centered(draw, text, y, font, right_center)

    # Shloka
    right_header("आज का श्लोक", 105)

    right_centered(
        "कर्मण्येवाधिकारस्ते",
        150,
        body_bold,
    )

    right_centered(
        "मा फलेषु कदाचन ।",
        178,
        body_bold,
    )

    # Meaning
    right_header("अर्थ", 215)

    right_centered(
        "अपने कर्म पर ध्यान दें;",
        258,
        small_font,
    )

    right_centered(
        "उसके फल की चिंता न करें।",
        282,
        small_font,
    )

    # Message
    right_header("आज का संदेश", 315)

    right_centered(
        "धैर्य और निष्ठा से",
        358,
        small_font,
    )

    right_centered(
        "किया गया कर्म भी साधना है।",
        382,
        small_font,
    )

    # Bottom sankalp
    draw.line(
        (45, 425, WIDTH - 45, 425),
        fill=0,
        width=2,
    )

    centered(
        draw,
        "आज का संकल्प",
        432,
        small_font,
    )

    # Convert to the exact 1-bit bitmap format expected by ESP32.
    pixels = image.load()

    with open("dashboard.bin", "wb") as f:
        for y in range(HEIGHT):
            for byte_x in range(0, WIDTH, 8):
                value = 0

                for bit in range(8):
                    x = byte_x + bit

                    # White pixel = 1
                    if pixels[x, y] == 0:
                        value |= (1 << (7 - bit))

                f.write(bytes([value]))


def main():
    print("Requesting Panchang data...")
    data = get_panchang()

    print("Panchang received successfully.")
    print("Tithi:", data.get("tithi"))
    print("Nakshatra:", data.get("nakshatra"))
    print("Weekday:", data.get("weekday"))

    make_dashboard(data)

    size = os.path.getsize("dashboard.bin")

    print(f"dashboard.bin created: {size} bytes")

    if size != 48000:
        raise RuntimeError(
            f"Wrong bitmap size: {size}. Expected 48000 bytes."
        )


if __name__ == "__main__":
    main()
