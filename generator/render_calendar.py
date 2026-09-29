import json
import os
from PIL import Image, ImageDraw, ImageFont


# ============================================================
# AJ KA DHARM
# 800 x 480 E-PAPER CALENDAR RENDERER
# ============================================================

WIDTH = 800
HEIGHT = 480

INPUT_FILE = "calendar_data.json"
OUTPUT_FILE = "dashboard.bin"


# ============================================================
# FONTS
# ============================================================

FONT_DIR = "/usr/share/fonts/truetype/noto"

FONT_REGULAR = os.path.join(
    FONT_DIR,
    "NotoSansDevanagari-Regular.ttf"
)

FONT_BOLD = os.path.join(
    FONT_DIR,
    "NotoSansDevanagari-Bold.ttf"
)

FONT_LATIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_LATIN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


# ============================================================
# HINDI MONTH / WEEKDAY HELPERS
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
# DRAWING HELPERS
# ============================================================

def center_text(draw, box, text, fnt, fill=0):
    x1, y1, x2, y2 = box

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=fnt
    )

    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = x1 + ((x2 - x1) - tw) // 2
    y = y1 + ((y2 - y1) - th) // 2 - bbox[1]

    draw.text(
        (x, y),
        text,
        font=fnt,
        fill=fill
    )


def draw_sun_icon(draw, x, y):
    draw.ellipse(
        (x + 5, y + 5, x + 19, y + 19),
        outline=0,
        width=2
    )

    rays = [
        ((12, 0), (12, 5)),
        ((12, 19), (12, 24)),
        ((0, 12), (5, 12)),
        ((19, 12), (24, 12)),
        ((3, 3), (7, 7)),
        ((17, 17), (21, 21)),
        ((17, 7), (21, 3)),
        ((3, 21), (7, 17)),
    ]

    for a, b in rays:
        draw.line(
            (
                x + a[0],
                y + a[1],
                x + b[0],
                y + b[1],
            ),
            fill=0,
            width=2
        )


def draw_moon_icon(draw, x, y):
    draw.arc(
        (x, y, x + 24, y + 24),
        55,
        305,
        fill=0,
        width=2
    )


def draw_border(draw):
    # Outer border
    draw.rectangle(
        (8, 8, WIDTH - 9, HEIGHT - 9),
        outline=0,
        width=2
    )

    # Inner border
    draw.rectangle(
        (14, 14, WIDTH - 15, HEIGHT - 15),
        outline=0,
        width=1
    )

    # Corner ornaments
    size = 12

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
                x + sx * size,
                y
            ),
            fill=0,
            width=2
        )

        draw.line(
            (
                x,
                y,
                x,
                y + sy * size
            ),
            fill=0,
            width=2
        )

        draw.rectangle(
            (
                x + sx * 4 - 2,
                y + sy * 4 - 2,
                x + sx * 4 + 2,
                y + sy * 4 + 2,
            ),
            fill=0
        )


# ============================================================
# CALENDAR GRID
# ============================================================

def build_calendar_grid(days):
    """
    Creates a 6 x 7 grid.

    Python weekday:
        Monday = 0
        Sunday = 6

    Calendar display:
        Sunday -> Saturday
    """

    if not days:
        return []

    first = days[0]

    first_weekday = (
        __import__("datetime")
        .date.fromisoformat(
            first["date"]
        ).weekday()
    )

    # Convert Monday=0...Sunday=6
    # to Sunday=0...Saturday=6
    sunday_index = (first_weekday + 1) % 7

    grid = [None] * sunday_index

    grid.extend(days)

    while len(grid) % 7 != 0:
        grid.append(None)

    while len(grid) < 42:
        grid.append(None)

    return [
        grid[i:i + 7]
        for i in range(0, len(grid), 7)
    ]


# ============================================================
# MAIN RENDERER
# ============================================================

def main():

    print("Loading calendar data...")

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    days = data["days"]

    month = data["month"]
    month_hindi = data["month_hindi"]
    year = data["year"]

    # --------------------------------------------------------
    # Canvas
    # --------------------------------------------------------

    image = Image.new(
        "1",
        (WIDTH, HEIGHT),
        1
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Fonts
    # --------------------------------------------------------

    title_font = font(
        FONT_BOLD,
        28
    )

    subtitle_font = font(
        FONT_REGULAR,
        14
    )

    time_font = font(
        FONT_LATIN_BOLD,
        13
    )

    weekday_font = font(
        FONT_BOLD,
        12
    )

    date_font = font(
        FONT_LATIN_BOLD,
        20
    )

    tithi_font = font(
        FONT_REGULAR,
        11
    )

    festival_font = font(
        FONT_BOLD,
        9
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
        (220, 25, 580, 61),
        f"{month_hindi} {year}",
        title_font
    )

    center_text(
        draw,
        (230, 57, 570, 79),
        f"{MONTHS_EN[month]}  |  भाद्रपद — आश्विन",
        subtitle_font
    )

    # --------------------------------------------------------
    # Sunrise / Sunset
    # --------------------------------------------------------

    first_day = days[0]

    draw_sun_icon(
        draw,
        34,
        34
    )

    draw.text(
        (64, 38),
        first_day["sunrise"],
        font=time_font,
        fill=0
    )

    draw_sun_icon(
        draw,
        34,
        62
    )

    draw.text(
        (64, 66),
        first_day["sunset"],
        font=time_font,
        fill=0
    )

    # --------------------------------------------------------
    # Moonrise / Moonset
    # --------------------------------------------------------

    draw_moon_icon(
        draw,
        690,
        34
    )

    draw.text(
        (720, 38),
        first_day["moonrise"],
        font=time_font,
        fill=0
    )

    draw_moon_icon(
        draw,
        690,
        62
    )

    draw.text(
        (720, 66),
        first_day["moonset"],
        font=time_font,
        fill=0
    )

    # Decorative diamonds
    draw.polygon(
        [(205, 49), (211, 43), (217, 49), (211, 55)],
        fill=0
    )

    draw.polygon(
        [(583, 49), (589, 43), (595, 49), (589, 55)],
        fill=0
    )

    # --------------------------------------------------------
    # Calendar area
    # --------------------------------------------------------

    grid_x = 25
    grid_y = 91
    grid_w = 750
    header_h = 28

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

    for col, weekday in enumerate(weekdays):

        x1 = grid_x + col * cell_w
        x2 = x1 + cell_w - 1

        draw.rectangle(
            (x1, grid_y, x2, grid_y + header_h),
            fill=0
        )

        center_text(
            draw,
            (
                x1,
                grid_y,
                x2,
                grid_y + header_h
            ),
            weekday,
            weekday_font,
            fill=1
        )

    # --------------------------------------------------------
    # Grid
    # --------------------------------------------------------

    calendar_grid = build_calendar_grid(days)

    today = data.get(
        "today",
        ""
    )

    y = grid_y + header_h

    for row in calendar_grid:

        for col, item in enumerate(row):

            x1 = grid_x + col * cell_w
            x2 = x1 + cell_w - 1
            y2 = y + cell_h - 1

            # Cell outline
            draw.rectangle(
                (x1, y, x2, y2),
                outline=0,
                width=1
            )

            if item is None:
                continue

            item_date = item["date"]

            is_today = (
                item_date == today
            )

            # ------------------------------------------------
            # Today highlight
            # ------------------------------------------------

            if is_today:

                draw.rectangle(
                    (
                        x1 + 1,
                        y + 1,
                        x2 - 1,
                        y2 - 1
                    ),
                    fill=0
                )

                text_fill = 1

            else:

                text_fill = 0

            # ------------------------------------------------
            # Date
            # ------------------------------------------------

            draw.text(
                (
                    x1 + 6,
                    y + 4
                ),
                str(item["day"]),
                font=date_font,
                fill=text_fill
            )

            # ------------------------------------------------
            # Tithi
            # ------------------------------------------------

            tithi = item.get(
                "tithi",
                ""
            )

            draw.text(
                (
                    x1 + 6,
                    y + 27
                ),
                tithi,
                font=tithi_font,
                fill=text_fill
            )

            # ------------------------------------------------
            # Festival
            # ------------------------------------------------

            festival = item.get(
                "festival",
                ""
            )

            if festival:

                draw.text(
                    (
                        x1 + 6,
                        y + 42
                    ),
                    festival[:12],
                    font=festival_font,
                    fill=text_fill
                )

        y += cell_h

    # --------------------------------------------------------
    # Convert to exact 1-bit raw bitmap
    # --------------------------------------------------------

    image = image.convert("1")

    raw = image.tobytes()

    expected_size = (
        WIDTH * HEIGHT // 8
    )

    if len(raw) != expected_size:

        raise RuntimeError(
            f"Invalid bitmap size: "
            f"{len(raw)} bytes; "
            f"expected {expected_size}"
        )

    with open(
        OUTPUT_FILE,
        "wb"
    ) as f:

        f.write(raw)

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
        f"Output: {OUTPUT_FILE}"
    )
    print(
        f"Size: {len(raw)} bytes"
    )
    print(
        "Expected: 48000 bytes"
    )


if __name__ == "__main__":
    main()
