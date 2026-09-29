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
    return ImageFont.truetype(
        path,
        size
    )


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
# DRAW TEXT CENTERED
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


# ============================================================
# ORNAMENTAL BORDER
# ============================================================

def draw_border(draw):

    # Outer frame
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

    # Inner frame
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

    # Corner geometric ornaments
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
# SUN ICON
# ============================================================

def draw_sun_icon(
    draw,
    x,
    y,
):
    draw.ellipse(
        (
            x + 6,
            y + 6,
            x + 18,
            y + 18,
        ),
        outline=0,
        width=2,
    )

    rays = [
        (12, 0, 12, 5),
        (12, 19, 12, 24),
        (0, 12, 5, 12),
        (19, 12, 24, 12),
        (3, 3, 7, 7),
        (17, 17, 21, 21),
        (17, 7, 21, 3),
        (3, 21, 7, 17),
    ]

    for x1, y1, x2, y2 in rays:

        draw.line(
            (
                x + x1,
                y + y1,
                x + x2,
                y + y2,
            ),
            fill=0,
            width=2,
        )


# ============================================================
# MOON ICON
# ============================================================

def draw_moon_icon(
    draw,
    x,
    y,
):
    draw.arc(
        (
            x,
            y,
            x + 24,
            y + 24,
        ),
        55,
        305,
        fill=0,
        width=2,
    )


# ============================================================
# LOTUS / DIAMOND ORNAMENT
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
# DYNAMIC HINDU MONTH LABEL
# ============================================================

def hindu_month_label(
    year,
    month,
):
    """
    Month transition label.

    For the current 2026 Kolkata calendar this gives the
    approved September heading.

    Future month mappings can be expanded without changing
    the renderer.
    """

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

    # Python:
    # Monday = 0 ... Sunday = 6
    #
    # Display:
    # Sunday = 0 ... Saturday = 6

    sunday_offset = (
        first_date.weekday() + 1
    ) % 7

    grid = [None] * sunday_offset

    grid.extend(days)

    while len(grid) % 7 != 0:
        grid.append(None)

    # Keep the same spacious 6-row calendar
    # structure as the approved design.
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

    # --------------------------------------------------------
    # Current date in Kolkata
    # --------------------------------------------------------

    today = datetime.now(
        TIMEZONE
    ).date()

    today_string = today.isoformat()

    # --------------------------------------------------------
    # Image
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
        FONT_DEV_REGULAR,
        10,
    )

    festival_font = load_font(
        FONT_DEV_BOLD,
        8,
    )

    # --------------------------------------------------------
    # Border
    # --------------------------------------------------------

    draw_border(draw)

    # --------------------------------------------------------
    # Header title
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

    # --------------------------------------------------------
    # Header subtitle
    # --------------------------------------------------------

    hindu_month = hindu_month_label(
        year,
        month,
    )

    subtitle_y = 56

    center_text(
        draw,
        (
            280,
            subtitle_y,
            520,
            subtitle_y + 20,
        ),
        MONTHS_EN[month],
        subtitle_latin_font,
    )

    center_text(
        draw,
        (
            445,
            subtitle_y,
            620,
            subtitle_y + 20,
        ),
        f"|  {hindu_month}",
        subtitle_hindi_font,
    )

    # --------------------------------------------------------
    # Header ornaments
    # --------------------------------------------------------

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
    # Sunrise
    # --------------------------------------------------------

    first_day = days[0]

    draw_sun_icon(
        draw,
        34,
        34,
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

    # --------------------------------------------------------
    # Sunset
    # --------------------------------------------------------

    draw_sun_icon(
        draw,
        34,
        63,
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
    # Moonrise
    # --------------------------------------------------------

    draw_moon_icon(
        draw,
        690,
        34,
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

    # --------------------------------------------------------
    # Moonset
    # --------------------------------------------------------

    draw_moon_icon(
        draw,
        690,
        63,
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

    # --------------------------------------------------------
    # Calendar geometry
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Weekday headers
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Calendar cells
    # --------------------------------------------------------

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

            # Cell border
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

            # ------------------------------------------------
            # Today's black highlight
            # ------------------------------------------------

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
            # Gregorian date
            # ------------------------------------------------

            draw.text(
                (
                    x1 + 6,
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

            draw.text(
                (
                    x1 + 6,
                    y + 26,
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

                # Keep the text inside the cell.
                festival = festival[:13]

                draw.text(
                    (
                        x1 + 6,
                        y + 41,
                    ),
                    festival,
                    font=festival_font,
                    fill=text_fill,
                )

        y += cell_h

    # --------------------------------------------------------
    # Convert to raw 1-bit bitmap
    # --------------------------------------------------------

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
