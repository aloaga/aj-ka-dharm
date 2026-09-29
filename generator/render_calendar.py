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
    "NotoSansDevanagari-Regular.ttf",
)

FONT_DEV_BOLD = os.path.join(
    DEVANAGARI_DIR,
    "NotoSansDevanagari-Bold.ttf",
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

def center_text(draw, box, text, fnt, fill=0):
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


def fit_text(draw, text, fnt, max_width):
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


def format_time_12h(time_string):
    """
    Convert HH:MM into 12-hour format with AM/PM.

    Examples:
        05:19 -> 05:19 AM
        17:53 -> 05:53 PM
        00:05 -> 12:05 AM
        12:10 -> 12:10 PM
    """
    if not time_string:
        return ""

    hour, minute = time_string.split(":")
    hour = int(hour)

    suffix = "AM" if hour < 12 else "PM"

    display_hour = hour % 12
    if display_hour == 0:
        display_hour = 12

    return f"{display_hour:02d}:{minute} {suffix}"


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
# SUN ICON
# ============================================================

def draw_sun_icon(draw, x, y):
    cx = x + 14
    cy = y + 14
    radius = 7

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

    rays = [
        (cx, cy - 17, cx, cy - 11),
        (cx, cy + 11, cx, cy + 17),
        (cx - 17, cy, cx - 11, cy),
        (cx + 11, cy, cx + 17, cy),
        (cx - 12, cy - 12, cx - 8, cy - 8),
        (cx + 8, cy + 8, cx + 12, cy + 12),
        (cx + 8, cy - 8, cx + 12, cy - 12),
        (cx - 12, cy + 12, cx - 8, cy + 8),
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
# CRESCENT MOON ICON
# ============================================================

def draw_moon_icon(draw, x, y):
    cx = x + 13
    cy = y + 13

    draw.ellipse(
        (
            cx - 12,
            cy - 12,
            cx + 12,
            cy + 12,
        ),
        fill=0,
    )

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
# HINDU SWASTIK SYMBOL
# ============================================================

def draw_swastik(draw, x, y, size=24):
    """
    Draw a simple traditional Hindu swastik as a vector symbol.
    x/y represent the top-left of the symbol's bounding area.
    """

    cx = x + size // 2
    cy = y + size // 2
    arm = 9
    hook = 6

    width = 3

    # Central vertical and horizontal strokes.
    draw.line(
        (cx, cy - arm, cx, cy + arm),
        fill=0,
        width=width,
    )

    draw.line(
        (cx - arm, cy, cx + arm, cy),
        fill=0,
        width=width,
    )

    # Clockwise bent ends.
    draw.line(
        (cx, cy - arm, cx + hook, cy - arm),
        fill=0,
        width=width,
    )

    draw.line(
        (cx + arm, cy, cx + arm, cy + hook),
        fill=0,
        width=width,
    )

    draw.line(
        (cx, cy + arm, cx - hook, cy + arm),
        fill=0,
        width=width,
    )

    draw.line(
        (cx - arm, cy, cx - arm, cy - hook),
        fill=0,
        width=width,
    )


# ============================================================
# HINDU MONTH LABEL
# ============================================================

def hindu_month_label(year, month):
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

    print("Loading calendar data...")

    with open(
        INPUT_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    days = data["days"]
    year = data["year"]
    month = data["month"]

    month_hindi = data["month_hindi"]

    # --------------------------------------------------------
    # IMPORTANT:
    # The generator now creates TOMORROW'S calendar.
    # Read the target date from calendar_data.json so the
    # correct day is highlighted.
    #
    # Fallback to today's Kolkata date if target_date is not
    # present, keeping the renderer backwards-compatible.
    # --------------------------------------------------------

    target_date_string = data.get(
        "target_date",
        datetime.now(TIMEZONE).date().isoformat(),
    )

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

    draw = ImageDraw.Draw(image)

    # ========================================================
    # FONTS
    # ========================================================

    title_font = load_font(
        FONT_DEV_BOLD,
        28,
    )

    # Hindu month is intentionally 2 points larger than
    # the previous 14-point version.
    hindu_month_header_font = load_font(
        FONT_DEV_BOLD,
        16,
    )

    time_font = load_font(
        FONT_LATIN_BOLD,
        14,
    )

    weekday_font = load_font(
        FONT_DEV_BOLD,
        14,
    )

    date_font = load_font(
        FONT_LATIN_BOLD,
        18,
    )

    # These remain at the enlarged 14-point size.
    tithi_font = load_font(
        FONT_DEV_BOLD,
        14,
    )

    festival_font = load_font(
        FONT_DEV_BOLD,
        14,
    )

    # --------------------------------------------------------
    # Border
    # --------------------------------------------------------

    draw_border(draw)

    # ========================================================
    # HEADER — FINAL CLEAN BALANCED LAYOUT
    # Three balanced zones: sun/times, centered month + Samvat,
    # and moon/times. The center texts use identical typography.
    # ========================================================

    hindu_month = hindu_month_label(
        year,
        month,
    )

    samvat_year = (
        year + 57
        if month >= 4
        else year + 56
    )

    samvat_text = (
        f"विक्रम संवत {samvat_year}"
    )

    header_center_font = load_font(
        FONT_DEV_BOLD,
        22,
    )

    hindu_bbox = draw.textbbox(
        (0, 0),
        hindu_month,
        font=header_center_font,
    )

    samvat_bbox = draw.textbbox(
        (0, 0),
        samvat_text,
        font=header_center_font,
    )

    hindu_width = (
        hindu_bbox[2]
        - hindu_bbox[0]
    )

    samvat_width = (
        samvat_bbox[2]
        - samvat_bbox[0]
    )

    center_gap = 24

    combined_center_width = (
        hindu_width
        + center_gap
        + samvat_width
    )

    center_start_x = (
        WIDTH
        - combined_center_width
    ) // 2

    center_y = 47

    hindu_height = (
        hindu_bbox[3]
        - hindu_bbox[1]
    )

    samvat_height = (
        samvat_bbox[3]
        - samvat_bbox[1]
    )

    draw.text(
        (
            center_start_x,
            center_y
            - hindu_height // 2,
        ),
        hindu_month,
        font=header_center_font,
        fill=0,
    )

    draw.text(
        (
            center_start_x
            + hindu_width
            + center_gap,
            center_y
            - samvat_height // 2,
        ),
        samvat_text,
        font=header_center_font,
        fill=0,
    )

    # Astronomical times in 12-hour AM/PM format.
    sunrise = format_time_12h(
        days[0].get(
            "sunrise",
            "",
        )
    )

    sunset = format_time_12h(
        days[0].get(
            "sunset",
            "",
        )
    )

    moonrise = format_time_12h(
        days[0].get(
            "moonrise",
            "",
        )
    )

    moonset = format_time_12h(
        days[0].get(
            "moonset",
            "",
        )
    )

    # Left: sun and two timings. The icon is vertically centered
    # between the two timing lines.
    left_icon_x = 45
    left_icon_y = 35
    left_time_x = 82

    draw_sun_icon(
        draw,
        left_icon_x,
        left_icon_y,
    )

    draw.text(
        (
            left_time_x,
            35,
        ),
        sunrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            left_time_x,
            62,
        ),
        sunset,
        font=time_font,
        fill=0,
    )

    # Right: moon and two timings. Same icon-to-text spacing
    # as the left block.
    right_icon_x = 663
    right_icon_y = 35
    right_time_x = 700

    draw_moon_icon(
        draw,
        right_icon_x,
        right_icon_y,
    )

    draw.text(
        (
            right_time_x,
            35,
        ),
        moonrise,
        font=time_font,
        fill=0,
    )

    draw.text(
        (
            right_time_x,
            62,
        ),
        moonset,
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

    calendar_bottom = HEIGHT - 15

    calendar_height = (
        calendar_bottom
        - (
            grid_y
            + weekday_h
        )
    )

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
    # CALENDAR GRID
    # ========================================================

    grid = build_grid(days)

    row_count = len(grid)

    cell_h = (
        calendar_height
        // row_count
    )

    y = (
        grid_y
        + weekday_h
    )

    for row_index, row in enumerate(
        grid
    ):

        if row_index == row_count - 1:
            row_y2 = calendar_bottom
        else:
            row_y2 = y + cell_h

        actual_cell_h = (
            row_y2 - y
        )

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

            y2 = row_y2 - 1

            # Cell outline
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

            item_date = item["date"]

            # ------------------------------------------------
            # IMPORTANT:
            # Highlight the target date generated by the
            # calendar data, rather than the machine's current
            # date.
            # ------------------------------------------------

            is_today = (
                item_date
                == target_date_string
            )

            # ------------------------------------------------
            # Current-day highlight
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

            # =================================================
            # DATE — LARGE LEFT
            # =================================================

            date_x = x1 + 7

            draw.text(
                (
                    date_x,
                    y + 4,
                ),
                str(item["day"]),
                font=date_font,
                fill=text_fill,
            )

            # =================================================
            # TITHI — RIGHT OF DATE
            # =================================================

            tithi = item.get(
                "tithi",
                "",
            )

            tithi_box = draw.textbbox(
                (0, 0),
                tithi,
                font=tithi_font,
            )

            tithi_width = (
                tithi_box[2]
                - tithi_box[0]
            )

            tithi_x = (
                x2
                - 7
                - tithi_width
            )

            minimum_tithi_x = (
                date_x
                + 38
            )

            if tithi_x < minimum_tithi_x:
                tithi_x = minimum_tithi_x

            draw.text(
                (
                    tithi_x,
                    y + 8,
                ),
                tithi,
                font=tithi_font,
                fill=text_fill,
            )

            # =================================================
            # FESTIVAL — BELOW
            # =================================================

            festival = item.get(
                "festival",
                "",
            )

            if festival:

                festival_left = (
                    x1 + 7
                )

                festival_right = (
                    x2 - 7
                )

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
                    (0, 0),
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

                festival_y = (
                    y
                    + min(
                        36,
                        actual_cell_h - 23,
                    )
                )

                draw.text(
                    (
                        festival_x,
                        festival_y,
                    ),
                    festival_text,
                    font=festival_font,
                    fill=text_fill,
                )

        y = row_y2

    # ========================================================
    # RAW 1-BIT BITMAP
    # ========================================================

    image = image.convert("1")

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
    print("========================================")
    print("CALENDAR RENDER COMPLETE")
    print("========================================")
    print(f"Month: {month_hindi} {year}")
    print(f"Target date: {target_date_string}")
    print(f"Rows: {row_count}")
    print(f"Cell height: {cell_h}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Size: {len(raw)} bytes")
    print("Expected: 48000 bytes")
    print()


if __name__ == "__main__":
    main()
