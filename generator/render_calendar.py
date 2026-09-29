import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont


# ============================================================
# AJ KA DHARM
# PREMIUM 800 x 480 MONOCHROME CALENDAR
# ============================================================

WIDTH = 800
HEIGHT = 480

INPUT_FILE = "calendar_data.json"
OUTPUT_FILE = "dashboard.bin"

TIMEZONE = ZoneInfo("Asia/Kolkata")


# ============================================================
# FONT PATHS
# ============================================================

DEVANAGARI_DIR = "/usr/share/fonts/truetype/noto"

FONT_DEV_REGULAR = os.path.join(
    DEVANAGARI_DIR,
    "NotoSansDevanagari-Regular.ttf"
)

FONT_DEV_BOLD = os.path.join(
    DEVANAGARI_DIR,
    "NotoSansDevanagari-Bold.ttf"
)

FONT_LATIN = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans.ttf"
)

FONT_LATIN_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


def load_font(path, size):
    return ImageFont.truetype(path, size)


# ============================================================
# MONTH NAMES
# ============================================================

MONTHS_EN = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


# ============================================================
# TEXT HELPERS
# ============================================================

def center_text(
    draw,
    box,
    text,
    fnt,
    fill=0,
):
    x1, y1, x2, y2 = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=fnt,
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = x1 + ((x2 - x1) - tw) // 2

    y = (
        y1
        + ((y2 - y1) - th) // 2
        - bbox[1]
    )

    draw.text(
        (x, y),
        text,
        font=fnt,
        fill=fill,
    )


def fit_text(
    draw,
    text,
    fnt,
    max_width,
):
    if not text:
        return ""

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=fnt,
    )

    if bbox[2] - bbox[0] <= max_width:
        return text

    while len(text) > 1:

        text = text[:-1]

        candidate = text + "…"

        bbox = draw.textbbox(
            (0, 0),
            candidate,
            font=fnt,
        )

        if bbox[2] - bbox[0] <= max_width:
            return candidate

    return text


# ============================================================
# ORNAMENTAL BORDER
# ============================================================

def draw_border(draw):

    draw.rectangle(
        (
            8,
            8,
            WIDTH - 9,
            HEIGHT - 9,
        ),
        outline=0,
        width=2,
    )

    draw.rectangle(
        (
            14,
            14,
            WIDTH - 15,
            HEIGHT - 15,
        ),
        outline=0,
        width=1,
    )

    corners = [
        (20, 20, 1, 1),
        (WIDTH - 20, 20, -1, 1),
        (20, HEIGHT - 20, 1, -1),
        (WIDTH - 20, HEIGHT - 20, -1, -1),
    ]

    for x, y, sx, sy in corners:

        draw.line(
            (
                x,
                y,
                x + sx * 11,
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
                y + sy * 11,
            ),
            fill=0,
            width=2,
        )

        draw.rectangle(
            (
                x + sx * 3 - 2,
                y + sy * 3 - 2,
                x + sx * 3 + 2,
                y + sy * 3 + 2,
            ),
            fill=0,
        )


# ============================================================
# SIMPLE SUN ICON
# ============================================================

def draw_sun_icon(
    draw,
    x,
    y,
):
    """
    Clean classic sun.
    Slightly larger than the previous version.
    """

    cx = x + 14
    cy = y + 14
    radius = 7

    # Sun body
    draw.ellipse(
        (
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
        ),
        outline=0,
        width=2,
    )

    # Rays
    rays = [
        (cx, cy - 17, cx, cy - 11),
        (cx, cy + 11, cx, cy + 17),

        (cx - 17, cy, cx - 11, cy),
        (cx + 11, cy, cx + 17, cy),

        (
            cx - 12,
            cy - 12,
            cx - 8,
            cy - 8,
        ),

        (
            cx + 8,
            cy + 8,
            cx + 12,
            cy + 12,
        ),

        (
            cx + 8,
            cy - 8,
            cx + 12,
            cy - 12,
        ),

        (
            cx - 12,
            cy + 12,
            cx - 8,
            cy + 8,
        ),
    ]

    for x1, y1, x2, y2 in rays:

        draw.line(
            (
                x1,
                y1,
                x2,
                y2,
            ),
            fill=0,
            width=2,
        )


# ============================================================
# PROPER HALF-MOON / CRESCENT ICON
# ============================================================

def draw_moon_icon(
    draw,
    x,
    y,
):
    """
    Clean crescent / half-moon.

    Constructed from overlapping circles so it remains
    recognizable on a monochrome e-paper display.
    """

    cx = x + 13
    cy = y + 13

    # Outer moon
    draw.ellipse(
        (
            cx - 12,
            cy - 12,
            cx + 12,
            cy + 12,
        ),
        fill=0,
    )

    # Cut-out circle shifted right.
    # This creates a strong crescent shape.
    draw.ellipse(
        (
            cx - 4,
            cy - 12,
            cx + 15,
            cy + 12,
        ),
        fill=1,
    )


# ============================================================
# DIAMOND ORNAMENT
# ============================================================

def draw_diamond(
    draw,
    x,
    y,
):
    draw.polygon(
        [
            (x, y - 6),
            (x + 6, y),
            (x, y + 6),
            (x - 6, y),
        ],
        fill=0,
    )


# ============================================================
# HINDU MONTH LABEL
# ============================================================

def hindu_month_label(
    year,
    month,
):

    known = {
        (2026, 1): "पौष — माघ",
        (2026, 2): "माघ — फाल्गुन",
        (2026, 3): "फाल्गुन — चैत्र",
        (2026, 4): "चैत्र — वैशाख",
        (2026, 5): "वैशाख — ज्येष्ठ",
        (2026, 6): "ज्येष्ठ — आषाढ़",
        (2026, 7): "आषाढ़ — श्रावण",
        (2026, 8): "श्रावण — भाद्रपद",
        (2026, 9): "भाद्रपद — आश्विन",
        (2026, 10): "आश्विन — कार्तिक",
        (2026, 11): "कार्तिक — मार्गशीर्ष",
        (2026, 12): "मार्गशीर्ष — पौष",
    }

    return known.get(
        (year, month),
        "",
    )


# ============================================================
# CALENDAR GRID
# ============================================================

def build_grid(days):

    if not days:
        return []

    first_date = datetime.fromisoformat(
        days[0]["date"]
    ).date()

    sunday_offset = (
        first_date.weekday() + 1
    ) % 7

    grid = [None] * sunday_offset

    grid.extend(days)

    while len(grid) % 7 != 0:
        grid.append(None)

    while len(grid) < 42:
        grid.append(None)

    return [
        grid[i:i + 7]
        for i in range(
            0,
            len(grid),
            7,
        )
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "Loading calendar data..."
    )

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        data = json.load(file)

    days = data["days"]

    year = data["year"]
    month = data["month"]

    month_hindi = data[
        "month_hindi"
    ]

    today = datetime.now(
        TIMEZONE
    ).date()

    today_string = today.isoformat()

    # --------------------------------------------------------
    # Canvas
    # --------------------------------------------------------

    image = Image.new(
        "1",
        (
            WIDTH,
            HEIGHT,
        ),
        1,
    )

    draw = ImageDraw.Draw(
        image
    )

    # --------------------------------------------------------
    # Fonts
    # --------------------------------------------------------

    title_font = load_font(
        FONT_DEV_BOLD,
        27,
    )

    subtitle_hindi_font = load_font(
        FONT_DEV_REGULAR,
        13,
    )

    subtitle_latin_font = load_font(
        FONT_LATIN,
        12,
    )

    time_font = load_font(
        FONT_LATIN_BOLD,
        13,
    )

    weekday_font = load_font(
        FONT_DEV_BOLD,
        11,
    )

    date_font = load_font(
        FONT_LATIN_BOLD,
        19,
    )

    tithi_font = load_font(
        FONT_DEV_BOLD,
        10,
    )

    festival_font = load_font(
        FONT_DEV_BOLD,
        10,
    )

    # --------------------------------------------------------
    # Border
    # --------------------------------------------------------

    draw_border(draw)

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    center_text(
        draw,
        (
            220,
            22,
            580,
            57,
        ),
        f"{month_hindi} {year}",
        title_font,
    )

    hindu_month = hindu_month_label(
        year,
        month,
    )

    center_text(
        draw,
        (
            280,
            56,
            445,
            76,
        ),
        MONTHS_EN[month],
        subtitle_latin_font,
    )

    center_text(
        draw,
        (
            445,
            56,
            625,
            76,
        ),
        f"|  {hindu_month}",
        subtitle_hindi_font,
    )

    draw_diamond(
        draw,
        211,
        49,
    )

    draw_diamond(
        draw,
        589,
        49,
    )

    # --------------------------------------------------------
    # LEFT — SUN
    # --------------------------------------------------------

    first_day = days[0]

    draw_sun_icon(
        draw,
        32,
        32,
    )

    draw.text(
        (
            64,
            38,
        ),
        first_day["sunrise"],
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            64,
            67,
        ),
        first_day["sunset"],
        font=time_font,
        fill=0,
    )

    # --------------------------------------------------------
    # RIGHT — MOON
    # --------------------------------------------------------

    draw_moon_icon(
        draw,
        689,
        32,
    )

    draw.text(
        (
            720,
            38,
        ),
        first_day["moonrise"],
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            720,
            67,
        ),
        first_day["moonset"],
        font=time_font,
        fill=0,
    )

    # ========================================================
    # CALENDAR GEOMETRY
    # ========================================================

    grid_x = 25
    grid_y = 91
    grid_w = 750

    weekday_h = 27
    cell_w = grid_w // 7
    cell_h = 56

    weekdays = [
        "रविवार",
        "सोमवार",
        "मंगलवार",
        "बुधवार",
        "गुरुवार",
        "शुक्रवार",
        "शनिवार",
    ]

    # ========================================================
    # WEEKDAY HEADERS
    # ========================================================

    for column, weekday in enumerate(
        weekdays
    ):

        x1 = (
            grid_x
            + column * cell_w
        )

        x2 = (
            x1
            + cell_w
            - 1
        )

        draw.rectangle(
            (
                x1,
                grid_y,
                x2,
                grid_y + weekday_h,
            ),
            fill=0,
        )

        center_text(
            draw,
            (
                x1,
                grid_y,
                x2,
                grid_y + weekday_h,
            ),
            weekday,
            weekday_font,
            fill=1,
        )

    # ========================================================
    # CALENDAR CELLS
    # ========================================================

    grid = build_grid(days)

    y = (
        grid_y
        + weekday_h
    )

    for row in grid:

        for column, item in enumerate(
            row
        ):

            x1 = (
                grid_x
                + column * cell_w
            )

            x2 = (
                x1
                + cell_w
                - 1
            )

            y2 = (
                y
                + cell_h
                - 1
            )

            draw.rectangle(
                (
                    x1,
                    y,
                    x2,
                    y2,
                ),
                outline=0,
                width=1,
            )

            if item is None:
                continue

            item_date = item[
                "date"
            ]

            is_today = (
                item_date
                == today_string
            )

            if is_today:

                draw.rectangle(
                    (
                        x1 + 1,
                        y + 1,
                        x2 - 1,
                        y2 - 1,
                    ),
                    fill=0,
                )

                text_fill = 1

            else:

                text_fill = 0

            # ------------------------------------------------
            # Date
            # ------------------------------------------------

            date_x = x1 + 6

            draw.text(
                (
                    date_x,
                    y + 3,
                ),
                str(item["day"]),
                font=date_font,
                fill=text_fill,
            )

            # ------------------------------------------------
            # Tithi
            # ------------------------------------------------

            tithi = item.get(
                "tithi",
                "",
            )

            tithi_box = draw.textbbox(
                (
                    0,
                    0,
                ),
                tithi,
                font=tithi_font,
            )

            tithi_width = (
                tithi_box[2]
                - tithi_box[0]
            )

            tithi_x = (
                x2
                - 6
                - tithi_width
            )

            minimum_tithi_x = (
                date_x + 34
            )

            if tithi_x < minimum_tithi_x:
                tithi_x = minimum_tithi_x

            draw.text(
                (
                    tithi_x,
                    y + 7,
                ),
                tithi,
                font=tithi_font,
                fill=text_fill,
            )

            # ------------------------------------------------
            # Festival
            # ------------------------------------------------

            festival = item.get(
                "festival",
                "",
            )

            if festival:

                festival_left = x1 + 6
                festival_right = x2 - 6

                available_width = (
                    festival_right
                    - festival_left
                )

                festival_text = fit_text(
                    draw,
                    festival,
                    festival_font,
                    available_width,
                )

                festival_box = draw.textbbox(
                    (
                        0,
                        0,
                    ),
                    festival_text,
                    font=festival_font,
                )

                festival_width = (
                    festival_box[2]
                    - festival_box[0]
                )

                festival_x = (
                    x1
                    + (
                        cell_w
                        - festival_width
                    ) // 2
                )

                draw.text(
                    (
                        festival_x,
                        y + 33,
                    ),
                    festival_text,
                    font=festival_font,
                    fill=text_fill,
                )

        y += cell_h

    # ========================================================
    # RAW 1-BIT BITMAP
    # ========================================================

    image = image.convert(
        "1"
    )

    raw = image.tobytes()

    expected_size = (
        WIDTH
        * HEIGHT
        // 8
    )

    if len(raw) != expected_size:

        raise RuntimeError(
            f"Invalid bitmap size: "
            f"{len(raw)} bytes; "
            f"expected {expected_size}"
        )

    with open(
        OUTPUT_FILE,
        "wb",
    ) as file:

        file.write(raw)

    print()
    print(
        "========================================"
    )
    print(
        "CALENDAR RENDER COMPLETE"
    )
    print(
        "========================================"
    )
    print(
        f"Month: {month_hindi} {year}"
    )
    print(
        f"Today: {today_string}"
    )
    print(
        f"Output: {OUTPUT_FILE}"
    )
    print(
        f"Size: {len(raw)} bytes"
    )
    print(
        "Expected: 48000 bytes"
    )
    print()


if __name__ == "__main__":
    main()
