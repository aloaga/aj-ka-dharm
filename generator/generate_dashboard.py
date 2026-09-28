import os
import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zoneinfo import ZoneInfo


WIDTH = 800
HEIGHT = 480

LATITUDE = 22.5726
LONGITUDE = 88.3639

TIMEZONE_NAME = "Asia/Kolkata"
TIMEZONE_OFFSET = 5.5

PANCHANG_URL = "https://api.navamsha.in/api/v1/panchang/full"
SUN_TIMES_URL = "https://api.navamsha.in/api/v1/panchang/sun-times"


# =================================================
# FONTS
# =================================================

def get_font(size, bold=False):

    if bold:
        path = (
            "/usr/share/fonts/truetype/noto/"
            "NotoSansDevanagari-Bold.ttf"
        )
    else:
        path = (
            "/usr/share/fonts/truetype/noto/"
            "NotoSansDevanagari-Regular.ttf"
        )

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Font not found: {path}"
        )

    return ImageFont.truetype(path, size)


# =================================================
# API
# =================================================

def get_panchang():

    api_key = os.environ["NAVAMSHA_API_KEY"]

    now = datetime.now(
        ZoneInfo(TIMEZONE_NAME)
    )

    payload = {
        "year": now.year,
        "month": now.month,
        "date": now.day,
        "hours": 7,
        "minutes": 0,
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "timezone": TIMEZONE_OFFSET,
    }

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
    }

    # -------------------------------------------------
    # MAIN PANCHANG
    # -------------------------------------------------

    response = requests.post(
        PANCHANG_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("statusCode") != 200:
        raise RuntimeError(
            f"Navamsha Panchang error: {result}"
        )

    output = result["output"]

    # -------------------------------------------------
    # SUNRISE / SUNSET
    # -------------------------------------------------

    sun_response = requests.post(
        SUN_TIMES_URL,
        headers=headers,
        json=payload,
        timeout=30,
    )

    sun_response.raise_for_status()

    sun_result = sun_response.json()

    if sun_result.get("statusCode") != 200:
        raise RuntimeError(
            f"Navamsha sun-times error: {sun_result}"
        )

    sun_output = sun_result["output"]

    output["sunrise"] = (
        sun_output["rise"]["local_datetime"][11:16]
    )

    output["sunset"] = (
        sun_output["set"]["local_datetime"][11:16]
    )

    return output


# =================================================
# TEXT HELPERS
# =================================================

def text_width(draw, text, font):

    box = draw.textbbox(
        (0, 0),
        text,
        font=font,
    )

    return box[2] - box[0]


def centered(
    draw,
    text,
    y,
    font,
    center_x=400,
):

    width = text_width(
        draw,
        text,
        font,
    )

    draw.text(
        (
            center_x - width // 2,
            y,
        ),
        text,
        fill=0,
        font=font,
    )


def right_aligned(
    draw,
    text,
    x,
    y,
    font,
):

    width = text_width(
        draw,
        text,
        font,
    )

    draw.text(
        (
            x - width,
            y,
        ),
        text,
        fill=0,
        font=font,
    )


# =================================================
# HINDI PANCHANG
# =================================================

def hindi_panchang(data):

    weekday = data.get(
        "weekday",
        {},
    )

    tithi = data.get(
        "tithi",
        {},
    )

    nakshatra = data.get(
        "nakshatra",
        {},
    )

    weekday_hi = {
        "Sunday": "रविवार",
        "Monday": "सोमवार",
        "Tuesday": "मंगलवार",
        "Wednesday": "बुधवार",
        "Thursday": "गुरुवार",
        "Friday": "शुक्रवार",
        "Saturday": "शनिवार",
    }

    paksha_hi = {
        "Shukla": "शुक्ल पक्ष",
        "Krishna": "कृष्ण पक्ष",
    }

    tithi_hi = {
        "Pratipada": "प्रतिपदा",
        "Dvitiya": "द्वितीया",
        "Tritiya": "तृतीया",
        "Chaturthi": "चतुर्थी",
        "Panchami": "पंचमी",
        "Shashthi": "षष्ठी",
        "Saptami": "सप्तमी",
        "Ashtami": "अष्टमी",
        "Navami": "नवमी",
        "Dashami": "दशमी",
        "Ekadashi": "एकादशी",
        "Dwadashi": "द्वादशी",
        "Trayodashi": "त्रयोदशी",
        "Chaturdashi": "चतुर्दशी",
        "Purnima": "पूर्णिमा",
        "Amavasya": "अमावस्या",
    }

    nakshatra_hi = {
        "Ashwini": "अश्विनी",
        "Bharani": "भरणी",
        "Krittika": "कृत्तिका",
        "Rohini": "रोहिणी",
        "Mrigashira": "मृगशिरा",
        "Ardra": "आर्द्रा",
        "Punarvasu": "पुनर्वसु",
        "Pushya": "पुष्य",
        "Ashlesha": "आश्लेषा",
        "Magha": "मघा",
        "Purva Phalguni": "पूर्वा फाल्गुनी",
        "Uttara Phalguni": "उत्तरा फाल्गुनी",
        "Hasta": "हस्त",
        "Chitra": "चित्रा",
        "Swati": "स्वाती",
        "Vishakha": "विशाखा",
        "Anuradha": "अनुराधा",
        "Jyeshtha": "ज्येष्ठा",
        "Mula": "मूल",
        "Purva Ashadha": "पूर्वाषाढ़ा",
        "Uttara Ashadha": "उत्तराषाढ़ा",
        "Shravana": "श्रवण",
        "Dhanishtha": "धनिष्ठा",
        "Shatabhisha": "शतभिषा",
        "Purva Bhadrapada": "पूर्वाभाद्रपद",
        "Uttara Bhadrapada": "उत्तराभाद्रपद",
        "Revati": "रेवती",
    }

    weekday_display = weekday_hi.get(
        weekday.get("name", ""),
        "—",
    )

    paksha_display = paksha_hi.get(
        tithi.get("paksha", ""),
        "",
    )

    tithi_display = tithi_hi.get(
        tithi.get("name", ""),
        "—",
    )

    if paksha_display:
        tithi_display = (
            f"{paksha_display} — {tithi_display}"
        )

    nakshatra_display = nakshatra_hi.get(
        nakshatra.get("name", ""),
        "—",
    )

    return {
        "weekday": weekday_display,
        "tithi": tithi_display,
        "nakshatra": nakshatra_display,
    }


# =================================================
# HINDI DATE
# =================================================

def hindi_date():

    now = datetime.now(
        ZoneInfo(TIMEZONE_NAME)
    )

    months_hi = {
        1: "जनवरी",
        2: "फ़रवरी",
        3: "मार्च",
        4: "अप्रैल",
        5: "मई",
        6: "जून",
        7: "जुलाई",
        8: "अगस्त",
        9: "सितम्बर",
        10: "अक्टूबर",
        11: "नवम्बर",
        12: "दिसम्बर",
    }

    hindi_digits = str.maketrans(
        "0123456789",
        "०१२३४५६७८९",
    )

    day = str(
        now.day
    ).translate(
        hindi_digits
    )

    year = str(
        now.year
    ).translate(
        hindi_digits
    )

    return (
        f"{day} "
        f"{months_hi[now.month]} "
        f"{year}"
    )


# =================================================
# DECORATIVE CORNERS
# =================================================

def draw_corner(
    draw,
    x,
    y,
    sx,
    sy,
):

    # Main temple-style L
    draw.line(
        (
            x,
            y,
            x + 30 * sx,
            y,
        ),
        fill=0,
        width=2,
    )

    draw.line(
        (
            x,
            y,
            x,
            y + 30 * sy,
        ),
        fill=0,
        width=2,
    )

    # Inner step
    draw.line(
        (
            x + 5 * sx,
            y + 5 * sy,
            x + 20 * sx,
            y + 5 * sy,
        ),
        fill=0,
        width=1,
    )

    draw.line(
        (
            x + 5 * sx,
            y + 5 * sy,
            x + 5 * sx,
            y + 20 * sy,
        ),
        fill=0,
        width=1,
    )

    # Small diamond
    cx = x + 17 * sx
    cy = y + 17 * sy

    draw.polygon(
        [
            (cx, cy - 4),
            (cx + 4 * sx, cy),
            (cx, cy + 4),
            (cx - 4 * sx, cy),
        ],
        outline=0,
    )


# =================================================
# MANDALA
# =================================================

def draw_mandala(
    draw,
    cx,
    cy,
):

    # Outer circle
    draw.ellipse(
        (
            cx - 56,
            cy - 56,
            cx + 56,
            cy + 56,
        ),
        outline=0,
        width=2,
    )

    # Middle circle
    draw.ellipse(
        (
            cx - 48,
            cy - 48,
            cx + 48,
            cy + 48,
        ),
        outline=0,
        width=1,
    )

    # Inner circle
    draw.ellipse(
        (
            cx - 38,
            cy - 38,
            cx + 38,
            cy + 38,
        ),
        outline=0,
        width=1,
    )

    # Eight petals
    points = [
        (0, -42),
        (30, -30),
        (42, 0),
        (30, 30),
        (0, 42),
        (-30, 30),
        (-42, 0),
        (-30, -30),
    ]

    for dx, dy in points:

        draw.ellipse(
            (
                cx + dx - 5,
                cy + dy - 5,
                cx + dx + 5,
                cy + dy + 5,
            ),
            outline=0,
            width=1,
        )

    # Eight outer dots
    for dx, dy in [
        (0, -51),
        (36, -36),
        (51, 0),
        (36, 36),
        (0, 51),
        (-36, 36),
        (-51, 0),
        (-36, -36),
    ]:

        draw.ellipse(
            (
                cx + dx - 2,
                cy + dy - 2,
                cx + dx + 2,
                cy + dy + 2,
            ),
            fill=0,
        )


# =================================================
# SUN ICON
# =================================================

def draw_sun_icon(
    draw,
    cx,
    cy,
):

    draw.ellipse(
        (
            cx - 5,
            cy - 5,
            cx + 5,
            cy + 5,
        ),
        outline=0,
        width=1,
    )

    for dx, dy in [
        (0, -9),
        (0, 9),
        (-9, 0),
        (9, 0),
    ]:

        draw.line(
            (
                cx + dx,
                cy + dy,
                cx + dx * 1.35,
                cy + dy * 1.35,
            ),
            fill=0,
            width=1,
        )


# =================================================
# CENTER DIVIDER ORNAMENT
# =================================================

def draw_divider_ornament(
    draw,
    x,
    y,
):

    draw.line(
        (
            x,
            y - 10,
            x,
            y + 10,
        ),
        fill=0,
        width=1,
    )

    draw.polygon(
        [
            (x, y - 7),
            (x + 7, y),
            (x, y + 7),
            (x - 7, y),
        ],
        outline=0,
    )

    draw.ellipse(
        (
            x - 2,
            y - 2,
            x + 2,
            y + 2,
        ),
        fill=0,
    )


# =================================================
# DASHBOARD
# =================================================

def make_dashboard(data):

    image = Image.new(
        "1",
        (
            WIDTH,
            HEIGHT,
        ),
        1,
    )

    draw = ImageDraw.Draw(image)

    # -------------------------------------------------
    # FONTS
    # -------------------------------------------------

    title_font = get_font(
        29,
        True,
    )

    header_font = get_font(
        19,
        True,
    )

    body_bold = get_font(
        18,
        True,
    )

    body_font = get_font(
        17,
    )

    small_font = get_font(
        15,
    )

    tiny_font = get_font(
        14,
    )

    panchang = hindi_panchang(
        data
    )

    date_display = hindi_date()

    # -------------------------------------------------
    # OUTER FRAME
    # -------------------------------------------------

    draw.rectangle(
        (
            10,
            10,
            WIDTH - 11,
            HEIGHT - 11,
        ),
        outline=0,
        width=2,
    )

    draw.rectangle(
        (
            18,
            18,
            WIDTH - 19,
            HEIGHT - 19,
        ),
        outline=0,
        width=1,
    )

    draw_corner(
        draw,
        30,
        30,
        1,
        1,
    )

    draw_corner(
        draw,
        WIDTH - 30,
        30,
        -1,
        1,
    )

    draw_corner(
        draw,
        30,
        HEIGHT - 30,
        1,
        -1,
    )

    draw_corner(
        draw,
        WIDTH - 30,
        HEIGHT - 30,
        -1,
        -1,
    )

    # -------------------------------------------------
    # HEADER
    # -------------------------------------------------

    centered(
        draw,
        "आज का धर्म",
        24,
        title_font,
    )

    # Draw weekday + separator + date manually.
    # This avoids unsupported Unicode bullet glyphs.

    weekday_text = panchang["weekday"]

    weekday_width = text_width(
        draw,
        weekday_text,
        small_font,
    )

    date_width = text_width(
        draw,
        date_display,
        small_font,
    )

    gap = 18

    separator_width = 8

    total_width = (
        weekday_width
        + gap
        + separator_width
        + gap
        + date_width
    )

    start_x = (
        400
        - total_width // 2
    )

    draw.text(
        (
            start_x,
            57,
        ),
        weekday_text,
        fill=0,
        font=small_font,
    )

    separator_x = (
        start_x
        + weekday_width
        + gap
    )

    draw.line(
        (
            separator_x,
            63,
            separator_x + 8,
            63,
        ),
        fill=0,
        width=2,
    )

    draw.text(
        (
            separator_x
            + separator_width
            + gap,
            57,
        ),
        date_display,
        fill=0,
        font=small_font,
    )

    # Header rule
    draw.line(
        (
            48,
            82,
            752,
            82,
        ),
        fill=0,
        width=2,
    )

    # -------------------------------------------------
    # LEFT PANEL
    # -------------------------------------------------

    left_center = 205

    # Smaller mandala for better breathing room.
    draw_mandala(
        draw,
        left_center,
        145,
    )

    # Om
    om_font = get_font(
        57,
        True,
    )

    centered(
        draw,
        "ॐ",
        105,
        om_font,
        left_center,
    )

    # Shiva
    centered(
        draw,
        "शिव",
        190,
        body_bold,
        left_center,
    )

    # Mantra
    centered(
        draw,
        "ॐ नमः शिवाय",
        216,
        small_font,
        left_center,
    )

    # -------------------------------------------------
    # PANCHANG HEADER
    # -------------------------------------------------

    centered(
        draw,
        "आज का पंचांग",
        242,
        header_font,
        left_center,
    )

    draw.line(
        (
            58,
            270,
            352,
            270,
        ),
        fill=0,
        width=1,
    )

    # -------------------------------------------------
    # PANCHANG ROWS
    # -------------------------------------------------

    rows = [
        (
            "वार",
            panchang["weekday"],
            False,
        ),
        (
            "तिथि",
            panchang["tithi"],
            False,
        ),
        (
            "नक्षत्र",
            panchang["nakshatra"],
            False,
        ),
        (
            "सूर्योदय",
            data.get(
                "sunrise",
                "—",
            ),
            True,
        ),
        (
            "सूर्यास्त",
            data.get(
                "sunset",
                "—",
            ),
            True,
        ),
    ]

    y = 280

    for label, value, sun_icon in rows:

        draw.text(
            (
                58,
                y,
            ),
            label,
            fill=0,
            font=small_font,
        )

        # Dotted leader
        for x in range(
            110,
            275,
            7,
        ):

            draw.point(
                (
                    x,
                    y + 9,
                ),
                fill=0,
            )

        if sun_icon:

            draw_sun_icon(
                draw,
                290,
                y + 10,
            )

        right_aligned(
            draw,
            value,
            350,
            y,
            small_font,
        )

        y += 27

    # -------------------------------------------------
    # CENTER DIVIDER
    # -------------------------------------------------

    divider_x = 390

    draw.line(
        (
            divider_x,
            98,
            divider_x,
            250,
        ),
        fill=0,
        width=1,
    )

    draw.line(
        (
            divider_x,
            276,
            divider_x,
            421,
        ),
        fill=0,
        width=1,
    )

    draw_divider_ornament(
        draw,
        divider_x,
        263,
    )

    # -------------------------------------------------
    # RIGHT PANEL
    # -------------------------------------------------

    right_center = 585

    def right_header(
        text,
        y,
    ):

        left = 425
        right = 745
        bottom = y + 30

        draw.rounded_rectangle(
            (
                left,
                y,
                right,
                bottom,
            ),
            radius=6,
            fill=0,
        )

        width = text_width(
            draw,
            text,
            header_font,
        )

        draw.text(
            (
                right_center
                - width // 2,
                y + 2,
            ),
            text,
            fill=1,
            font=header_font,
        )

    def right_text(
        text,
        y,
        font,
    ):

        centered(
            draw,
            text,
            y,
            font,
            right_center,
        )

    # -------------------------------------------------
    # SHLOKA
    # -------------------------------------------------

    right_header(
        "आज का श्लोक",
        105,
    )

    right_text(
        "कर्मण्येवाधिकारस्ते",
        149,
        body_bold,
    )

    right_text(
        "मा फलेषु कदाचन ।",
        176,
        body_bold,
    )

    # -------------------------------------------------
    # MEANING
    # -------------------------------------------------

    right_header(
        "अर्थ",
        211,
    )

    right_text(
        "अपने कर्म पर ध्यान दें;",
        252,
        small_font,
    )

    right_text(
        "उसके फल की चिंता न करें।",
        275,
        small_font,
    )

    # -------------------------------------------------
    # MESSAGE
    # -------------------------------------------------

    right_header(
        "आज का संदेश",
        308,
    )

    right_text(
        "धैर्य और निष्ठा से",
        349,
        small_font,
    )

    right_text(
        "किया गया कर्म भी साधना है।",
        372,
        small_font,
    )

    # -------------------------------------------------
    # SANKALP
    # -------------------------------------------------

    draw.line(
        (
            48,
            421,
            752,
            421,
        ),
        fill=0,
        width=2,
    )

    centered(
        draw,
        "आज का संकल्प",
        429,
        tiny_font,
    )

    # -------------------------------------------------
    # RAW 1-BIT BITMAP
    # -------------------------------------------------

    pixels = image.load()

    with open(
        "dashboard.bin",
        "wb",
    ) as f:

        for y in range(
            HEIGHT
        ):

            for byte_x in range(
                0,
                WIDTH,
                8,
            ):

                value = 0

                for bit in range(
                    8
                ):

                    x = (
                        byte_x
                        + bit
                    )

                    # White pixel = 1.
                    # Matches the current
                    # ESP32 display configuration.

                    if pixels[x, y] == 1:

                        value |= (
                            1
                            << (
                                7
                                - bit
                            )
                        )

                f.write(
                    bytes(
                        [value]
                    )
                )


# =================================================
# MAIN
# =================================================

def main():

    print(
        "Requesting Panchang data..."
    )

    data = get_panchang()

    print(
        "Panchang received successfully."
    )

    print(
        "Tithi:",
        data.get(
            "tithi"
        ),
    )

    print(
        "Nakshatra:",
        data.get(
            "nakshatra"
        ),
    )

    print(
        "Weekday:",
        data.get(
            "weekday"
        ),
    )

    print(
        "Sunrise:",
        data.get(
            "sunrise"
        ),
    )

    print(
        "Sunset:",
        data.get(
            "sunset"
        ),
    )

    make_dashboard(
        data
    )

    size = os.path.getsize(
        "dashboard.bin"
    )

    print(
        f"dashboard.bin created: "
        f"{size} bytes"
    )

    if size != 48000:

        raise RuntimeError(
            f"Wrong bitmap size: "
            f"{size}. "
            f"Expected 48000 bytes."
        )


if __name__ == "__main__":

    main()
